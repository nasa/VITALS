"""
This module contains functions related to wrangling search data into helpful
structures or filtering results from earthaccess.

Author: Erik Bolch, ebolch@contractor.usgs.gov

"""
import os
import earthaccess
import pandas as pd
import geopandas as gpd
from shapely.geometry import MultiPolygon, Polygon, box
from shapely.geometry.polygon import orient

def get_vertices(result, lat_lon=True):
    """
    Gets the vertices of the geometry included in the umm metadata either in lat,lon or 
    lon,lat format. This list can be used to conduct a search as the polygon kwarg in
    the earthaccess.search_data function, or can be used with to make a folium.Polygon.

    result: an earthaccess.DataGranule (single result from list) 
    lat_lon: bool (order of coordinate pairs in list)
    """
    geometry = result['umm']['SpatialExtent']['HorizontalSpatialDomain']['Geometry']
    
    if 'GPolygons' in geometry.keys():
        exterior_ring = geometry['GPolygons'][0]['Boundary']['Points']
        coords = [(pt["Longitude"], pt["Latitude"]) for pt in exterior_ring]

    elif 'BoundingRectangles' in geometry.keys():
        br = geometry['BoundingRectangles'][0]
        west, south = br['WestBoundingCoordinate'], br['SouthBoundingCoordinate']
        east, north = br['EastBoundingCoordinate'], br['NorthBoundingCoordinate']
        coords = [
            (west, north),
            (west, south),
            (east, south),
            (east, north),
            (west, north)
        ]
    else:
        raise ValueError("No Polygon or BoundingRectangle in result.")      

    if lat_lon:
        return [(lat,lon) for lon, lat in coords] 
    return coords 

def get_asset_urls(result:earthaccess.DataGranule, contains=None, extension=None, first_only=False, s3=False):
    """
    Filter the RelatedUrls dict down to a list of the desired assets. Return URL list matching all provided criteria.
    
    result: List[dict] each having a 'URL' key.
    contains: substring describing the desired asset.
    extension: file extension of the desired asset (endswith).
    first_only: if True, return the first matching URL (or raise), otherwise return a list of all matches.
    s3: if True, retrieves s3 links rather than http.
    
    returns: str or List[str]
    """
    if extension is not None and not isinstance(extension, (list,tuple)):
        endswith_list = [extension]
    else:
       endswith_list = extension
    
    if contains is not None and not isinstance(contains, (list, tuple)):
        contains_list = [contains]
    else:
        contains_list = contains

    related_urls = result['umm']['RelatedUrls']

    if s3:
        startswith = "s3://"
    else:
        startswith = "https://"

    matched = [
        d["URL"]
        for d in related_urls
        for u in [d["URL"]]
        if (startswith is None or u.startswith(startswith))
        and (extension is None or any(sub in u for sub in endswith_list))
        and (contains is None or any(sub in u for sub in contains_list))
    ]
    
    if not matched:
        crit = []
        if startswith: crit.append(f"startswith={startswith!r}")
        if extension:   crit.append(f"extension={extension!r}")
        if contains:   crit.append(f"contains={contains!r}")
        raise ValueError(f"No assets found matching: {', '.join(crit)}")
    
    return matched[0] if first_only else matched

def download_granules(url_list, output_directory) -> None:
    """
    This function will authenticate using EDL credentials and download all granules in a list.
    """
    # Create output directory
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # EDL Authentication/Create .netrc if necessary
    earthaccess.login(persist=True)
    # Get requests https Session using Earthdata Login Info
    fs = earthaccess.get_requests_https_session()
    # Retrieve granule asset ID from URL (to maintain existing naming convention)
    for url in url_list:
        granule_asset_id = url.split("/")[-1]
        # Define Local Filepath
        fp = f"{output_directory}{granule_asset_id}"
        # Download the Granule Asset if it doesn't exist
        print(f"Downloading {granule_asset_id}...")
        if not os.path.isfile(fp):
            with fs.get(url, stream=True) as src:
                with open(fp, "wb") as dst:
                    for chunk in src.iter_content(chunk_size=64 * 1024 * 1024):
                        dst.write(chunk)