# jldp_ras_funcs.py
# This script contains all functions that are to be used in the 04_Dangermound_Land_Cover.ipynb notebook
# Date: 12/05/2023
# Authors: Christiana Ade and Marie Johnson
###################################################

# import libraries
import os
import glob
import math
import earthaccess
import numpy as np
import pandas as pd
import xarray as xr
from osgeo import gdal
import rasterio as rio
import rioxarray as rxr
import geoviews as gv
import geopandas as gp
import pyproj
from shapely.ops import transform
from shapely.geometry import Polygon
import holoviews as hv

import json
from fsspec.implementations.http import HTTPFileSystem
from holoviews import opts

#########################################################
# Function for raster extraction
#########################################################

## The extract function used to get CWC and LST data values
def extract_raster_values(raster, shapefile_gdf, summary_stats=False):
    """
    Extracts the values for each pixel of a multi-band raster that intersects
    with polygons in a shapefile and outputs it as a dataframe that has the
    spectral information as well as all the attribute table information from
    the shapefile. Optionally computes summary statistics for each polygon.
    
    Parameters:
    raster (xarray.DataArray or xarray.Dataset): An xarray object with multi-band raster data.
    shapefile_gdf (geopandas.GeoDataFrame): A GeoDataFrame with shapefile data.
    summary_stats (bool): If True, compute summary statistics (mean, median) for each polygon.
    
    Returns:
    pandas.DataFrame: A DataFrame with each row being one pixel observation, columns for each band,
                      and all attributes from the shapefile, or summary statistics if selected.
    """
    
    dfs = []  # List to hold data from each polygon
    
    # Check if the input raster is a DataArray
    if isinstance(raster, xr.DataArray):
        # Convert DataArray to Dataset
        raster = raster.to_dataset(name='value')
    
    # Iterate through each polygon in the shapefile
    for _, row in shapefile_gdf.iterrows():
        # Clip the raster with the current polygon
        clipped_ds = raster.rio.clip([row.geometry], shapefile_gdf.crs)
        
        # Flatten the clipped raster data and reset index to convert to DataFrame
        flattened = clipped_ds.to_dataframe().reset_index()
        
        # Create a unique cell number
        flattened['cell_number'] = flattened['y'].astype(str) + "_" + flattened['x'].astype(str)
        
        # Add attributes from the shapefile
        for col in shapefile_gdf.columns:
            flattened[col] = row[col]
        
        # Append the prepared DataFrame to the list
        dfs.append(flattened)
    
    # Combine all the individual DataFrames into one
    final_df = pd.concat(dfs, ignore_index=True)
    
    # If summary statistics are requested
    if summary_stats:
        # Group by the shapefile's attributes and calculate mean and median
        stats_df = final_df.groupby(list(shapefile_gdf.columns)) \
                           .agg(['mean', 'median']) \
                           .reset_index()
        # Flatten the column multi-index
        stats_df.columns = ['_'.join(col).rstrip('_') for col in stats_df.columns.values]
        return stats_df
    
    return final_df



#########################################################
# Functions For interactive plotting
#########################################################

def hv_to_rio_geometry(hv_polygon: hv.Polygons) -> list:
    """Convert a HoloViews Polygons object to a GeoJSON-like geometry"""
    coordinates = [[x, y] for x, y in zip(hv_polygon["xs"], hv_polygon["ys"])]
    return [
        {
            "type": "Polygon",
            "coordinates": [coordinates],
        }
    ]

def hv_stream_to_rio_geometries(hv_polygon: hv.Polygons) -> list:
    """Convert a HoloViews polygon_stream object to a GeoJSON-like geometry"""

    geoms = [[x, y] for x, y in zip(hv_polygon["xs"], hv_polygon["ys"])]

    for geom in geoms:
        xs, ys = geom
        coordinates = [[x, y] for x, y in zip(xs, ys)]
        # Holoviews is stupid.
        coordinates.append(coordinates[0])

        yield [
            {
                "type": "Polygon",
                "coordinates": [coordinates],
            }
        ]



# Convert geometries - this is because of the difference between the 
# automatic webplotting in holoviews for images and the need to have the output polygon
# file be in the native (aka target_crs)
def transform_to_wgs84(geometry, original_crs='EPSG:3857', target_crs='EPSG:4326'):
    """
    Transform coordinates of a geometry from the original CRS to the target CRS.

    Args:
    geometry (shapely.geometry): The geometry to transform.
    original_crs (str): The original CRS of the geometry.
    target_crs (str): The target CRS to transform to.

    Returns:
    shapely.geometry: Transformed geometry.
    """
    project = pyproj.Transformer.from_crs(original_crs, target_crs, always_xy=True).transform
    return transform(project, geometry)

# Create the geodataframe required to use in the extract function 
# based on the streamed holoviews polygons 
def create_geodataframe(contents, transform_needed=True):
    """
    Create a GeoDataFrame from polygon data, with an option to transform coordinates.

    Args:
    contents (list): List of polygon data.
    transform_needed (bool): Flag to indicate if coordinate transformation is needed.

    Returns:
    geopandas.GeoDataFrame: GeoDataFrame with polygons and their unique identifiers.
    """
    transformed_polygons = []
    for feature in contents:
        for geom in feature:
            # Accessing 'coordinates' directly from geom
            polygon = Polygon(geom['coordinates'][0])
            if transform_needed:
                transformed_polygon = transform_to_wgs84(polygon)
            else:
                transformed_polygon = polygon
            transformed_polygons.append(transformed_polygon)
            
    # add a field called poly_fid based on the order in which the polygons were drawn 
    poly_fid = list(range(len(transformed_polygons)))
    poly_selected = gp.GeoDataFrame({'poly_fid': poly_fid, 'geometry': transformed_polygons})
    # set the crs
    poly_selected.set_crs("EPSG:4326", inplace=True)
    return poly_selected