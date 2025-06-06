"""
Utility functions related to wrangling vehicle positions 
and segments.

Use this to see what shows up repeatedly 
and can be modularized in the future.
"""
import dask.dataframe as dd
import dask_geopandas as dg
import datetime
import geopandas as gpd
import pandas as pd

from typing import Union
from segment_speed_utils.project_vars import (GTFS_DATA_DICT,
                                              SEGMENT_GCS, 
                                              COMPILED_CACHED_VIEWS,
                                              RT_SCHED_GCS, 
                                              SCHED_GCS,
                                              PROJECT_CRS)
from calitp_data_analysis import utils
import google.auth
credentials, project = google.auth.default()

def import_scheduled_trips(
    analysis_date: str, 
    filters: tuple = None,
    columns: list = [
        "gtfs_dataset_key", "name", "trip_id", 
        "shape_id", "shape_array_key", 
        "route_id", "route_key", "direction_id",
        "route_short_name"
    ],
    get_pandas: bool = True
) -> Union[pd.DataFrame, dd.DataFrame]:
    """
    Get scheduled trips info (all operators) for single day, 
    and keep subset of columns.
    """
    TABLE = GTFS_DATA_DICT.schedule_downloads.trips
    FILE = f"{COMPILED_CACHED_VIEWS}{TABLE}_{analysis_date}.parquet"

    RENAME_DICT = {
        "gtfs_dataset_key": "schedule_gtfs_dataset_key"
    }
    
    if get_pandas:
        trips = pd.read_parquet(FILE, filters = filters, columns = columns)
    else:
        trips = dd.read_parquet(FILE, filters = filters, columns = columns)
    
    return (trips.drop_duplicates().reset_index(drop=True)
            .rename(columns = RENAME_DICT))


def import_scheduled_shapes(
    analysis_date: str, 
    filters: tuple = None,
    columns: list = ["shape_array_key", "geometry"],
    get_pandas: bool = True, 
    crs: str = PROJECT_CRS
) -> Union[gpd.GeoDataFrame, dg.GeoDataFrame]: 
    """
    Import shapes.
    """    
    TABLE = GTFS_DATA_DICT.schedule_downloads.shapes
    FILE = f"{COMPILED_CACHED_VIEWS}{TABLE}_{analysis_date}.parquet"
    
    if get_pandas: 
        shapes = gpd.read_parquet(
            FILE, filters = filters, columns = columns, storage_options = {"token": credentials.token}
        )
    else:
        shapes = dg.read_parquet(
            FILE, filters = filters, columns = columns
        )
    
    shapes = shapes.to_crs(crs)
        
    return shapes.drop_duplicates().reset_index(drop=True)


def import_scheduled_stop_times(
    analysis_date: str, 
    filters: tuple = None,
    columns: list = None,
    get_pandas: bool = False,
    with_direction: bool = False,
    crs: str = PROJECT_CRS,
) -> Union[dd.DataFrame, pd.DataFrame, dg.GeoDataFrame, gpd.GeoDataFrame]:
    """
    Get scheduled stop times.
    """
    if with_direction:
        TABLE = GTFS_DATA_DICT.rt_vs_schedule_tables.stop_times_direction
        FILE = f"{RT_SCHED_GCS}{TABLE}_{analysis_date}.parquet"
        
        if get_pandas:
            if columns is None or "geometry" in columns:
                stop_times = gpd.read_parquet(
                    FILE, filters = filters, columns = columns, storage_options = {"token": credentials.token}
                ).to_crs(crs)
            else:
                stop_times = pd.read_parquet(
                    FILE, filters = filters, columns = columns
                )
        else:
            stop_times = dg.read_parquet(
                FILE, filters = filters, columns = columns
            ).to_crs(crs)
            
    else:
        TABLE = GTFS_DATA_DICT.schedule_downloads.stop_times
        FILE = f"{COMPILED_CACHED_VIEWS}{TABLE}_{analysis_date}.parquet"
        
        if get_pandas:
            stop_times = pd.read_parquet(
                FILE, filters = filters, columns = columns
            )
        else:
            stop_times = dd.read_parquet(
                FILE, filters = filters, columns = columns
            )
    
    return stop_times.drop_duplicates().reset_index(drop=True)


def import_scheduled_stops(
    analysis_date: str,
    filters: tuple = None,
    columns: list = None,
    get_pandas: bool = True,
    crs: str = PROJECT_CRS
) -> Union[gpd.GeoDataFrame, dg.GeoDataFrame]:
    """
    Get scheduled stops
    """
    TABLE = GTFS_DATA_DICT.schedule_downloads.stops
    FILE = f"{COMPILED_CACHED_VIEWS}{TABLE}_{analysis_date}.parquet"
    
    if get_pandas:
        if columns is None or "geometry" in columns:
            stops = gpd.read_parquet(
                FILE, filters = filters, columns = columns, storage_options = {"token": credentials.token}
            ).to_crs(crs)

        else:
            stops = pd.read_parquet(
                FILE, filters = filters, columns = columns
            )
    
    else:
        if columns is None or "geometry" in columns:
            stops = dg.read_parquet(
                FILE, filters = filters, columns = columns
            ).to_crs(crs)

        else:
            stops = dd.read_parquet(
                FILE, filters = filters, columns = columns
            )
    
    return stops.drop_duplicates().reset_index(drop=True)


def import_schedule_gtfs_key_organization_crosswalk(
    analysis_date: str,
    filters: tuple = None,
    columns: list = None,
) -> pd.DataFrame:
    """
    Get scheduled stops
    """
    TABLE = GTFS_DATA_DICT.schedule_tables.gtfs_key_crosswalk
    FILE = f"{SCHED_GCS}{TABLE}_{analysis_date}.parquet"
    
    crosswalk = pd.read_parquet(
        FILE, filters = filters, columns = columns
    )
    
    return crosswalk.drop_duplicates().reset_index(drop=True)


def import_unique_vp_trips(analysis_date: str) -> list:
    """
    Get the unique trip_instance_keys that are present
    on a given day in vp_usable.
    """
    TABLE = GTFS_DATA_DICT.speeds_tables.usable_vp
    FILE = f"{SEGMENT_GCS}{TABLE}_{analysis_date}"
    
    rt_trips = pd.read_parquet(
        FILE,
        columns = ["trip_instance_key"]
    ).trip_instance_key.unique().tolist()
    
    return rt_trips

def exclude_unusable_trips(
    vp_df: dd.DataFrame, 
    valid_trips: pd.DataFrame
) -> dd.DataFrame:
    """
    Supply a df of valid trips.
    Do an inner merge and pare down the vehicle positions df.
    `trip_id` may not be unique across operators, so 
    use `gtfs_dataset_key` and `trip_id`.
    """
    valid_vp_df = dd.merge(
        vp_df,
        valid_trips,
        on = ["gtfs_dataset_key", "trip_id"],
        how = "inner"
    ).reset_index(drop=True)
    
    return valid_vp_df


def remove_shapes_outside_ca(
    shapes: Union[gpd.GeoDataFrame, dg.GeoDataFrame],
    use_buffer: bool = False
) -> Union[gpd.GeoDataFrame, dg.GeoDataFrame]:
    """
    Remove shapes that are too far outside CA.
    We'll include border states with a gpd.sjoin(predicate='within')
    to make sure we get shapes that travel a tiny bit outside CA, but
    aren't ones like Amtrak.
    
    FlixBus is another like Amtrak, with far flung routes.
    """
    # Can't get relative path working within importable segment_speed_utils
    #us_states = catalog.us_states.read()
    # https://github.com/cal-itp/data-analyses/blob/main/_shared_utils/shared_utils/shared_data_catalog.yml
    us_states = gpd.read_file(
        "https://services.arcgis.com/ue9rwulIoeLEI9bj/"
        "arcgis/rest/services/US_StateBoundaries/FeatureServer/0/"
        "query?outFields=*&where=1%3D1&f=geojson"
    )
    
    border_states = ["CA", "NV", "AZ", "OR"]
    
    SHAPE_CRS = shapes.crs.to_epsg()

    # Filter to California
    ca = us_states.query(
        'STATE_ABBR in @border_states'
    ).dissolve()[["geometry"]].to_crs(SHAPE_CRS)
    
    # Buffer 10,000 meters to keep the bay in the Bay Area & turn this back to geodataframe
    if use_buffer:
        ca = ca.to_crs("EPSG:3310").buffer(10_000).to_frame('geometry').to_crs(SHAPE_CRS)
    
    # Be aggressive and keep if shape
    # is within (does not cross CA + border state boundaries)
    if isinstance(shapes, dg.GeoDataFrame):
        shapes_within_ca = dg.sjoin(
            shapes,
            ca,
            how = "inner",
            predicate = "within"
        ).drop(columns = "index_right")
    
    else:
        shapes_within_ca = gpd.sjoin(
            shapes,
            ca,
            how = "inner",
            predicate = "within",
        ).drop(columns = "index_right")
    
    return shapes_within_ca


def unique_list(my_list: list) -> list:
    """
    We try various groupings for segment averaging,
    and sometimes the same column will appear multiple times.
    
    https://stackoverflow.com/questions/7961363/removing-duplicates-in-lists
    # Ex: route_id will be in both shape stop and route dir; 
    this method maintains list order
    """
    return list(dict.fromkeys(my_list))