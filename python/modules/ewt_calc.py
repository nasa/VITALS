# Modified From: https://github.com/isofit/isofit/blob/dev/isofit/utils/ewt_from_reflectance.py
# Author: Erik Bolch, ebolch@contractor.usgs.gov
import xarray as xr
import netCDF4 as nc
import numpy as np
import os

import atexit
import logging
import time

import pandas as pd
from scipy.optimize import least_squares
from matplotlib import pyplot as plt

import ray
from multiprocessing import cpu_count
import numpy as np
from osgeo import gdal

from modules.emit_tools import emit_xarray, ortho_xr


# Modified from
def calc_ewt(
    filepath: str,
    outdir: str,
    #wl: np.array,
    n_cpu: int = (cpu_count() - 1),
    ewt_detection_limit: float = 0.5,
) -> None:
    """
    This function will calculate the equivalent water thickness (EWT) or canopy water content (CWC) from an EMIT .nc reflectance
    file using `ray` for parallelization,orthorectify if necessary, and write a cloud-optimized geotiff output.
    """
    # Get number of rows to break up in parallel
    emit_ds = xr.open_dataset(filepath, decode_coords='all')

    # Conditionals to manage emit_xarray vs normal emit file - #TODO the orthorectified attr needs some improvement in emit_tools.py
    if "spatial_ref" in list(emit_ds.variables.keys()):
        ortho_cwc = True
    else:
        ortho_cwc = False

    # Check if emit_xarray has been used to set wavelengths as a dimension
    if "wavelengths" not in emit_ds.dims:
        emit_ds = emit_xarray(filepath)

    # Get number of rows
    n_rows = emit_ds["reflectance"].shape[0]

    # Get Wavelength centers
    wvl = emit_ds["wavelengths"].data
    #wvl = wl
    # Initialize Ray Cluster
    # init_rfl = np.nan_to_num(emit_ds.reflectance.data[0,0,:].copy(),nan=-9999)
    # res_0, abs_co_w = invert_liquid_water(init_rfl, wvl, return_abs_co=True)
    
    ray.init(num_cpus=n_cpu)

    # Set up Line Breaks for parallel
    line_breaks = np.linspace(0, n_rows, n_cpu, dtype=int)
    line_breaks = [
        (line_breaks[n], line_breaks[n + 1]) for n in range(len(line_breaks) - 1)
    ]
    
    # Calculate EWT Results by Line
    result_list = [
        run_lines.remote(
            filepath,
            wvl,
            line_breaks[n],
        )
        for n in range(len(line_breaks))
    ]
    results = [ray.get(result) for result in result_list]

    ray.shutdown()

    # Concatenate Result
    cwc = np.concatenate(results, axis=0)
    # Mask Fill-Values
    cwc[cwc == -9999] = np.nan

    # Set up Output file
    coords = emit_ds.coords
    for key in ["wavelengths", "fwhm", "good_wavelengths"]:
        del coords[key]

    output_metadata = {}
    keep = [
        "flight_line",
        "time_coverage_start",
        "time_coverage_end",
        "easternmost_longitude",
        "northernmost_latitude",
        "westernmost_longitude",
        "southernmost_latitude",
        "spatialResolution",
        "spatial_ref",
        "geotransform",
        "day_night_flag",
        "title",
        "granule_id",
    ]
    for key in keep:
        output_metadata[key] = emit_ds.attrs[key]
    output_metadata[
        "title"
    ] = "EMIT Estimated Equivalent Water Thickness (EWT) / Canopy Water Content (CWC)"

    # Create Data Vars - Squeeze bands dim
    data_vars = {"cwc": (list(emit_ds.dims.keys())[0:2], cwc.squeeze())}

    ds_cwc = xr.Dataset(data_vars=data_vars, coords=coords, attrs=output_metadata)
    ds_cwc.cwc.attrs = {
        "long_name": "Canopy Water Content",
        "units": "g/cm^2",
        "_FillValue": -9999,
    }

    # Orthorectify if necessary
    if ortho_cwc == False:
        ds_cwc = ortho_xr(ds_cwc)

    # Create output cog
    ds_cwc.rio.to_raster(
        raster_path=f"{outdir}{filepath.split('/')[-1].split('.')[0]}_cwc.tif", driver="COG"
    )

    #return cwc


@ray.remote
def run_lines(
    rfl_file: str,
    wl: np.array,
    startstop: tuple,
    ewt_detection_limit: float = 0.5,
) -> None:
    start_line, stop_line = startstop

    # Outputs from emit_xarray will have nan values, need to reassign to -9999 if there are any
    rfl = np.nan_to_num(
        xr.open_dataset(rfl_file)["reflectance"][start_line:stop_line, :, :].data,
        nan=-9999,
    )
    rs, cs, zs = rfl.shape
    output_cwc = np.zeros((rs, cs, 1)) - 9999

    for r in range(rfl.shape[0]):
        for c in range(rfl.shape[1]):
            meas = rfl[r, c, :]
            if np.all(meas < 0):
                continue
            output_cwc[r, c, 0] = invert_liquid_water(
                meas, wl, ewt_detection_limit=0.5
            )[0]
        logging.info(f"CWC writing line {r}")
    return output_cwc


# Functions Used in EWT Calculation


# https://github.com/isofit/isofit/blob/main/isofit/inversion/inverse_simple.py#L443C1-L511C24
def invert_liquid_water(
    rfl_meas: np.array,
    wl: np.array,
    l_shoulder: float = 850,
    r_shoulder: float = 1100,
    lw_init: tuple = (0.02, 0.3, 0.0002),
    lw_bounds: tuple = ([0, 0.5], [0, 1.0], [-0.0004, 0.0004]),
    ewt_detection_limit: float = 0.5,
    return_abs_co: bool = False,
):
    """Given a reflectance estimate, fit a state vector including liquid water path length
    based on a simple Beer-Lambert surface model.

    Args:
        rfl_meas:            surface reflectance spectrum
        wl:                  instrument wavelengths, must be same size as rfl_meas
        l_shoulder:          wavelength of left absorption feature shoulder
        r_shoulder:          wavelength of right absorption feature shoulder
        lw_init:             initial guess for liquid water path length, intercept, and slope
        lw_bounds:           lower and upper bounds for liquid water path length, intercept, and slope
        ewt_detection_limit: upper detection limit for ewt
        return_abs_co:       if True, returns absorption coefficients of liquid water

    Returns:
        solution: estimated liquid water path length, intercept, and slope based on a given surface reflectance
    """

    # params needed for liquid water fitting
    lw_feature_left = np.argmin(abs(l_shoulder - wl))
    lw_feature_right = np.argmin(abs(r_shoulder - wl))
    wl_sel = wl[lw_feature_left : lw_feature_right + 1]

    # adjust upper detection limit for ewt if specified
    if ewt_detection_limit != 0.5:
        lw_bounds[0][1] = ewt_detection_limit

    # load imaginary part of liquid water refractive index and calculate wavelength dependent absorption coefficient
    # __file__ should live at isofit/isofit/inversion/
    
    
    data_dir_path = "../data/"
    path_k = os.path.join(data_dir_path,"k_liquid_water_ice.csv")
    
    #isofit_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    #path_k = os.path.join(isofit_path, "data", "iop", "k_liquid_water_ice.xlsx")

    # k_wi = pd.read_excel(io=path_k, sheet_name="Sheet1", engine="openpyxl")
    # wl_water, k_water = get_refractive_index(
    #     k_wi=k_wi, a=0, b=982, col_wvl="wvl_6", col_k="T = 20°C"
    # )
    k_wi = pd.read_csv(path_k)
    wl_water, k_water = get_refractive_index(
        k_wi=k_wi, a=0, b=982, col_wvl="wvl_6", col_k="T = 20°C"
    )
    kw = np.interp(x=wl_sel, xp=wl_water, fp=k_water)
    abs_co_w = 4 * np.pi * kw / wl_sel

    rfl_meas_sel = rfl_meas[lw_feature_left : lw_feature_right + 1]

    x_opt = least_squares(
        fun=beer_lambert_model,
        x0=lw_init,
        jac="2-point",
        method="trf",
        bounds=(
            np.array([lw_bounds[ii][0] for ii in range(3)]),
            np.array([lw_bounds[ii][1] for ii in range(3)]),
        ),
        max_nfev=15,
        args=(rfl_meas_sel, wl_sel, abs_co_w),
    )

    solution = x_opt.x

    if return_abs_co:
        return solution, abs_co_w
    else:
        return solution

# https://github.com/isofit/isofit/blob/main/isofit/inversion/inverse_simple.py#L514C1-L532C17
def beer_lambert_model(x, y, wl, alpha_lw):
    """Function, which computes the vector of residuals between measured and modeled surface reflectance optimizing
    for path length of surface liquid water based on the Beer-Lambert attenuation law.

    Args:
        x:        state vector (liquid water path length, intercept, slope)
        y:        measurement (surface reflectance spectrum)
        wl:       instrument wavelengths
        alpha_lw: wavelength dependent absorption coefficients of liquid water

    Returns:
        resid: residual between modeled and measured surface reflectance
    """

    attenuation = np.exp(-x[0] * 1e7 * alpha_lw)
    rho = (x[1] + x[2] * wl) * attenuation
    resid = rho - y

    return resid

# https://github.com/isofit/isofit/blob/dev/isofit/core/common.py#L461C1-L488C26
def get_refractive_index(k_wi, a, b, col_wvl, col_k):
    """Convert refractive index table entries to numpy array.

    Args:
        k_wi:    variable
        a:       start line
        b:       end line
        col_wvl: wavelength column in pandas table
        col_k:   k column in pandas table

    Returns:
        wvl_arr: array of wavelengths
        k_arr:   array of imaginary parts of refractive index
    """

    wvl_ = []
    k_ = []

    for ii in range(a, b):
        wvl = k_wi.at[ii, col_wvl]
        k = k_wi.at[ii, col_k]
        wvl_.append(wvl)
        k_.append(k)

    wvl_arr = np.asarray(wvl_)
    k_arr = np.asarray(k_)

    return wvl_arr, k_arr
