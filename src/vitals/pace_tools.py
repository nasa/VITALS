"""
This file contains functions for working with PACE data, including opening, gridding,
    etc. Xarray and rasterio are heavily used to process PACE data. 

Author: Skye Caplan (NASA, SSAI)
Last updated: 03/31/2026

TODO: 
- Figure out better way to get aligned pixels but individual granule boundaries
"""
# Packages
import cartopy
import rasterio
import cf_xarray  # noqa: F401
import numpy as np
import pandas as pd
import xarray as xr
import rioxarray as rio
import cartopy.crs as ccrs
from rasterio.crs import CRS
from rasterio.enums import Resampling

def open_l2(fpath):
    """ 
    Opens a PACE L2 file as an xarray dataset, assigning lat/lons (and wavelength, 
        if the dataset is 3D) as coordinates.
    Args:
        fpath - path to a L2 PACE file 
    Returns:
        ds - xarray dataset
    """
    dt = xr.open_datatree(fpath)
    try:
        ds = xr.merge((
            dt.ds,
            dt["geophysical_data"].to_dataset(),
            dt["sensor_band_parameters"].coords,
            dt["navigation_data"].ds.set_coords(("longitude", "latitude")).coords,
            )
        )
        # Commenting out because only available in xarray>=2026.01.0
        #ds = ds.set_xindex(("latitude", "longitude"), xr.indexes.NDPointIndex)
    except:
        ds = xr.merge((
            dt.ds,
            dt["geophysical_data"].to_dataset(),
            dt["navigation_data"].ds.set_coords(("longitude", "latitude")).coords,
            )
        )
        #ds = ds.set_xindex(("latitude", "longitude"), xr.indexes.NDPointIndex)
        ds.load()
        dt.close()
    return ds

def mask_ds(ds, flag="CLDICE", reverse=False):
    """
    Mask a PACE OCI dataset for L2 flags. Default is to mask for clouds only
    Args:
        ds - xarray dataset containing "l2_flags" variable
        flag - str or list of l2 flag to mask for (see https://oceancolor.gsfc.nasa.gov/resources/atbd/ocl2flags/)
        reverse - boolean or list of booleans to keep only pixels with the desired flag. 
                  Default is False. E.g., set True to use "LAND" flag to mask water pixels. 
    Returns:
        Masked dataset
    """
    # Make sure flags are recognized by the package
    if ds["l2_flags"].cf.is_flag_variable:
        # If multiple flags, make sure reverse is also a list and then iterate
        if type(flag)==list:
            if type(reverse)!=list:
                reverse = [reverse for i in range(len(flag))]
            for f,r in zip(flag, reverse):
                if r == False:
                    ds = ds.where(~(ds["l2_flags"].cf == f))
                else:
                    ds = ds.where(ds["l2_flags"].cf == f)
                print(f"{f} mask applied")
            return ds
        else:
            if type(reverse)==list:
                reverse = reverse[0]
            if reverse == False:
                ds = ds.where(~(ds["l2_flags"].cf == flag))
            else:
                ds = ds.where((ds["l2_flags"].cf == flag))
            print(f"{flag} mask applied")
            return ds
    else:
        print("l2_flags not recognized as flag variable")
        return ds

def grid_data(src, resolution=None, dst_transform=None, dst_crs="epsg:4326", src_crs="epsg:4326", resampling=Resampling.nearest):
    """
    Grid a PACE OCI L2 dataset. Makes sure 3D variables are in (Z, Y, X) 
        dimension order, and all variables have spatial dims/crs assigned.
    Args:
        src - an xarray dataset or dataarray to reproject
        resolution - resolution of the output grid, in dst_crs units
        dst_crs - CRS of the output data
        resampling - resampling method (see rasterio.enums)
    Returns:
        dst - projected xr dataset
    """
    # Get names of dimensions
    wvl_var, x_dim, y_dim = None, None, None
    for dim in list(src.dims):
        if np.all([wvl_var, x_dim, y_dim]):
            break
        elif "wave" in dim:
            wvl_var = dim
            continue
        elif ("lon" in dim) or ("pixel" in dim):
            x_dim = dim
            continue
        elif ("lat" in dim) or ("number" in dim):
            y_dim = dim

    # Transpose if necessary and set spatial dims
    if (len(list(src.dims)) == 3) and (list(src.dims)[0] != wvl_var):
        src = src.transpose(wvl_var, ...)
    src = src.rio.set_spatial_dims(x_dim, y_dim)
    src = src.rio.write_crs(src_crs)

    # Calculating the default affine transform
    defaults = rasterio.warp.calculate_default_transform(
        src.rio.crs,
        dst_crs,
        src.rio.width,
        src.rio.height,
        left=np.nanmin(src["longitude"].data), 
        bottom=np.nanmin(src["latitude"].data),
        right=np.nanmax(src["longitude"].data),
        top=np.nanmax(src["latitude"].data),   
    )
    
    # Aligning that transform to our desired resolution using either supplied 
    #    transform or resolution
    if dst_transform is not None:
        # If we have a transform, overwrite any given resolution
        resolution = (dst_transform[0],-1*dst_transform[4])

    transform, width, height = rasterio.warp.aligned_target(*defaults, resolution)
    
    # If lat/lon arrays are 2D, grid the data using geoloc arrays
    if len(src["latitude"].dims) > 1:
        dst = src.rio.reproject(
            dst_crs=dst_crs,
            shape=(height, width),
            transform=transform,
            src_geoloc_array=(
                src["longitude"],
                src["latitude"],
            ),
            nodata=np.nan,
            resample=resampling,
        )
    # Else if 1D geoloc arrays, check for user-supplied transform and use it if so
    else:
        if dst_transform is not None:
            transform=dst_transform
        dst = src.rio.reproject(
            dst_crs=dst_crs,
            shape=(height, width),
            transform=transform,
            nodata=np.nan,
        )

    dst["x"] = dst["x"].round(9)
    dst["y"] = dst["y"].round(9)
    
    return dst.rename({"x":"longitude", "y":"latitude"})