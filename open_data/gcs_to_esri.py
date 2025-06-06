"""
Take datasets staged in GCS, create zipped shapefiles.

Print some info about the gdf
Double check metadata, esp field attributes and EPSG
"""
import geopandas as gpd
import glob
import intake
import os
import sys

from loguru import logger

import open_data_utils
from calitp_data_analysis.geography_utils import WGS84
from calitp_data_analysis import utils
from update_vars import analysis_date, RUN_ME

import google.auth
credentials, project = google.auth.default()

catalog = intake.open_catalog("./catalog.yml")

def print_info(gdf: gpd.GeoDataFrame):
    """
    Double check that the metadata is entered correctly and 
    that dtypes, CRS, etc are all standardized.
    """
    logger.info(f"CRS Info: {gdf.crs.name}, EPSG: {gdf.crs.to_epsg()}")
    logger.info(f"columns: {gdf.columns}")
    logger.info(f"{gdf.dtypes}")
    
    return
    
    
def remove_zipped_shapefiles():
    """
    Once local zipped shapefiles are created, 
    clean up after we don't need them
    """
    FILES = [f for f in glob.glob("*.zip")]
    print(f"list of parquet files to delete: {FILES}")
    
    for f in FILES:
        os.remove(f)
    return

def project_and_standardize_cols(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Project to WGS84, then standardize column names.
    """
    gdf = gdf.to_crs(WGS84).pipe(
            open_data_utils.standardize_column_names
        ).pipe(
            open_data_utils.remove_internal_keys
        )
    return gdf
    
    
if __name__=="__main__":
    assert os.getcwd().endswith("open_data"), "this script must be run from open_data directory!"

    logger.add("./logs/gcs_to_esri.log", retention="6 months")
    logger.add(sys.stderr, 
               format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}", 
               level="INFO")
        
    for d in RUN_ME :
        #  clunky way to add SSO credentials with bracket/key syntax
        gdf = catalog[d](geopandas_kwargs={"storage_options": {"token": credentials.token}}).read().pipe(project_and_standardize_cols)
        
        logger.info(f"********* {d} *************")
        print_info(gdf)

        # Zip the shapefile
        utils.make_zipped_shapefile(gdf, f"{d}.zip")
    