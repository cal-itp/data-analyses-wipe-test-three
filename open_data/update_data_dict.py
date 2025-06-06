"""
Go through each dataset we publish from catalog.yml. 
Compare it to data_dictionary.yml to double
check that all the columns have an entry.

This script is useful when we make adjustments
to datasets we want to publish, and we 
need to add a corresponding entry to data_dictionary.yml, 
which is used to update column definitions in ESRI.
"""
import geopandas as gpd
import intake
import sys
import yaml

from loguru import logger
from pathlib import Path
from typing import Union

import open_data_utils
from update_vars import analysis_date
from supplement_meta import truncate_from_catalog

import google.auth
credentials, project = google.auth.default()

catalog = intake.open_catalog("catalog.yml")

def unpack_list_of_tables_as_dict(list_of_dict: list) -> dict:
    """
    In the yml, the datasets come as a list of dictionary items.
    Re-structure this as a dict so we can key into
    specific datasets.
    """
    dict_of_tables = {d["dataset_name"]: d for d in list_of_dict}
    
    return dict_of_tables


def new_columns_for_data_dict(
    open_data_catalog: Union[str, Path] = Path("catalog.yml"),
    data_dict_file: Union[str, Path] = Path("data_dictionary.yml")
) -> dict:
    """
    Return a dict of the datasets we publish along with 
    a list of columns that should be included.
    """
    catalog = intake.open_catalog(open_data_catalog)

    with open(Path(data_dict_file)) as f:
        data_dict = yaml.load(f, yaml.Loader)
              
    n_catalog_tables = len(catalog)
    
    # Unpack the table section of the data dictionary, which is a list, as a dict
    dict_of_tables = unpack_list_of_tables_as_dict(data_dict["tables"])
    
    n_dict_tables = len(dict_of_tables.keys())
    
    if n_dict_tables != n_catalog_tables:
        logger.error(
            f"There are {n_catalog_tables} tables in the "
            f"catalog and only {n_dict_tables} tables in the data dictionary."
        )
    
    new_cols_dict = {}
    
    for t in catalog:
        
        # Columns in our dataset
        FILE = catalog[t].urlpath
        gdf = gpd.read_parquet(FILE, storage_options = {'token': credentials.token}).pipe(
            open_data_utils.standardize_column_names
        ).pipe(
            open_data_utils.remove_internal_keys)
        gdf = gdf.rename(columns = truncate_from_catalog(t))
#        if "hq_" in t:
#            gdf = gdf.rename(columns = open_data_utils.RENAME_HQTA)
#        elif "speed" in t:
#            gdf = gdf.rename(columns = open_data_utils.RENAME_SPEED)
            
        col_list = gdf.columns.tolist()
                
        # Columns included in data dictionary
        cols_defined = [c for c in dict_of_tables[t].keys()]
                
        exclude_me = ["dataset_name", "geometry"]
        
        new_cols_dict[t] = [
            c for c in col_list 
            if c not in exclude_me and c not in cols_defined
        ]
        
    return new_cols_dict


if __name__ == "__main__":
    
    logger.add("./logs/data_dictionary.log", retention="3 months")
    logger.add(sys.stderr, 
               format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}",
               level="INFO")
    
    logger.info(f"Analysis date: {analysis_date}")
    
    cols_to_add = new_columns_for_data_dict()
    
    # Just print out ones where we are missing columns
    cols_to_add = {k:v for k,v in cols_to_add.items() if 
                   len(v) > 0}
    
    logger.info(f"Columns to add to data dict yml: {cols_to_add}")