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


# Function to convert a bounding box for use in leaflet notation

def convert_bounds(bbox, invert_y=False):
    """
    Helper method for changing bounding box representation to leaflet notation

    ``(lon1, lat1, lon2, lat2) -> ((lat1, lon1), (lat2, lon2))``
    """
    x1, y1, x2, y2 = bbox
    if invert_y:
        y1, y2 = y2, y1
    return ((y1, x1), (y2, x2))

# Functions to Build Dataframe
def get_shapely_object(result: earthaccess.results.DataGranule):
    """
    Create a shapely polygon of spatial coverage from results metadata.
    Will work for BoundingRectangles or GPolygons.
    """
    # Get Geometry Keys
    geo = result["umm"]["SpatialExtent"]["HorizontalSpatialDomain"]["Geometry"]
    keys = geo.keys()

    if "BoundingRectangles" in keys:
        bounding_rectangle = geo["BoundingRectangles"][0]
        # Create bbox tuple
        bbox_coords = (
            bounding_rectangle["WestBoundingCoordinate"],
            bounding_rectangle["SouthBoundingCoordinate"],
            bounding_rectangle["EastBoundingCoordinate"],
            bounding_rectangle["NorthBoundingCoordinate"],
        )
        # Create shapely geometry from bbox
        shape = box(*bbox_coords, ccw=True)
    elif "GPolygons" in keys:
        points = geo["GPolygons"][0]["Boundary"]["Points"]
        # Create shapely geometry from polygons
        shape = Polygon([[p["Longitude"], p["Latitude"]] for p in points])
    else:
        raise ValueError(
            "Provided result does not contain bounding boxes/polygons or is incompatible."
        )
    return shape

def get_png(result: earthaccess.results.DataGranule):
    """
    Retrieve a png browse image if it exists or first jpg in list of urls
    """
    https_links = [link for link in result.dataviz_links() if "https" in link]
    if len(https_links) == 1:
        browse = https_links[0]
    elif len(https_links) == 0:
        browse = "no browse image"
    else:
        browse = [png for png in https_links if ".png" in png][0]
    if any(browse) == 'no browse image':
        print("Some granules have no browse imagery.")
    return browse

def results_to_gdf(results: list):
    """
    Takes a list of results from earthaccess and converts to a geodataframe.
    """
    # Create Dataframe of Results Metadata
    results_df = pd.json_normalize(results)
    # Shorten column Names
    results_df.columns = [
        col.split(".")[-1] if "." in col else col for col in results_df.columns
    ]
    # Create shapely polygons for result
    geometries = [
        get_shapely_object(results[index]) for index in results_df.index.to_list()
    ]
    # Convert to GeoDataframe
    gdf = gpd.GeoDataFrame(results_df, geometry=geometries, crs="EPSG:4326")
    # Add browse imagery and data links and product shortname
    gdf["browse"] = [get_png(granule) for granule in results]
    gdf["shortname"] = [
        result["umm"]["CollectionReference"]["ShortName"] for result in results
    ]
    gdf["data"] = [granule.data_links() for granule in results]
    return gdf

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