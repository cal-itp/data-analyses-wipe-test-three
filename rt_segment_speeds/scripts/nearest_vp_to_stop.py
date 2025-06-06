"""
Find nearest_vp_idx to the stop position 
using scipy KDTree.
"""
import datetime
import geopandas as gpd
import numpy as np
import pandas as pd
import sys

from loguru import logger
from pathlib import Path
from typing import Literal, Optional

from segment_speed_utils import helpers, neighbor, vp_transform
from update_vars import SEGMENT_GCS, GTFS_DATA_DICT
from segment_speed_utils.project_vars import SEGMENT_TYPES
import google.auth
credentials, project = google.auth.default()


def stop_times_for_all_trips(
    analysis_date: str,
) -> gpd.GeoDataFrame:
    """
    This is the stop times table for all trips.
    We will do nearest neighbors for every stop along a trip.
    """
    stop_times = helpers.import_scheduled_stop_times(
        analysis_date,
        columns = ["trip_instance_key", "shape_array_key",
                   "stop_sequence", "stop_id", "stop_pair", 
                   "stop_primary_direction", "stop_meters",
                   "geometry"],
        with_direction = True,
        get_pandas = True,
    )
    
    return stop_times


def stop_times_for_speedmaps(
    analysis_date: str
) -> gpd.GeoDataFrame:
    """
    This is the proxy stop times table for speedmaps that should 
    be concatenated with stop times for all trips.
    Filter for proxy_stop==1 (these are the extra "stops" we generate
    at the 1,000th meter).
    For segments that are shorter than 1,000m, stop to stop is fine.
    We will do nearest neighbors for these additional proxy stops and
    concatenate against results for all trips.
    """
    stop_time_col_order = [
        'trip_instance_key', 'shape_array_key',
        'stop_sequence', 'stop_sequence1', 
        'stop_id', 'stop_pair',
        'stop_primary_direction', 'geometry'
    ] 
    
    STOP_TIMES_FILE = GTFS_DATA_DICT.speedmap_segments.proxy_stop_times

    stop_times = gpd.read_parquet(
        f"{SEGMENT_GCS}{STOP_TIMES_FILE}_{analysis_date}.parquet",
        filters = [[("proxy_stop", "==", 1)]],
        storage_options = {"token": credentials.token}
    )
    
    stop_times = stop_times.reindex(columns = stop_time_col_order)
    
    return stop_times


def nearest_neighbor_for_stop(
    analysis_date: str,
    segment_type: Literal[SEGMENT_TYPES],
    config_path: Optional[Path] = GTFS_DATA_DICT
):
    """
    Set up nearest neighbors for RT stop times, which
    includes all trips. Use stop sequences for each trip.
    """
    start = datetime.datetime.now()

    dict_inputs = config_path[segment_type]
    
    EXPORT_FILE = f'{dict_inputs["stage2"]}_{analysis_date}'
    trip_stop_cols = [*dict_inputs["trip_stop_cols"]]
    
    stop_time_col_order = [
        'trip_instance_key', 'shape_array_key',
        'stop_sequence', 'stop_id', 'stop_pair',
        'stop_primary_direction', 'geometry'
    ] 
    
    if segment_type == "rt_stop_times":
        stop_times = stop_times_for_all_trips(analysis_date)
        stop_times = stop_times.reindex(columns = stop_time_col_order + ["stop_meters"])
    
    elif segment_type == "speedmap_segments":
        stop_times = stop_times_for_speedmaps(analysis_date)
        
        # TODO: speedmap segments does not have a stop_meters
        # neighbor.merge_stop_vp_for_nearest_neighbor will create it
        # but it might be more straightforward to project stop against shape now?
    
    else:
        print(f"{segment_type} is not valid")
    
    
    gdf = neighbor.merge_stop_vp_for_nearest_neighbor(stop_times, analysis_date)
    gdf = gdf.assign(
        opposite_direction = gdf.stop_primary_direction.map(vp_transform.OPPOSITE_DIRECTIONS)
    )

    vp_before, vp_after, vp_before_meters, vp_after_meters = np.vectorize(
        neighbor.two_nearest_neighbor_near_stop
    )(
        gdf.vp_primary_direction, 
        gdf.vp_geometry, 
        gdf.vp_idx,
        gdf.stop_geometry,
        gdf.opposite_direction,
        gdf.shape_geometry,
        gdf.stop_meters
    )

    gdf = gdf[trip_stop_cols + ["shape_array_key", "stop_meters"]]
    
    gdf = gdf.assign(
        prior_vp_idx = vp_before,
        subseq_vp_idx = vp_after,
        prior_vp_meters = vp_before_meters, 
        subseq_vp_meters = vp_after_meters
    )
        
    del stop_times
    
    gdf.to_parquet(f"{SEGMENT_GCS}{EXPORT_FILE}.parquet")
    
    end = datetime.datetime.now()
    logger.info(f"nearest neighbor for {segment_type} "
                f"{analysis_date}: {end - start}")   
          
    return


'''
if __name__ == "__main__":
    
    from segment_speed_utils.project_vars import analysis_date_list
    from dask import delayed, compute
    
    delayed_dfs = [
        delayed(nearest_neighbor_for_stop)(
            analysis_date = analysis_date,
            segment_type = segment_type,
            config_path = GTFS_DATA_DICT
        ) for analysis_date in analysis_date_list
    ]

    [compute(i)[0] for i in delayed_dfs]
'''