"""
Run nearest_vp_to_stop.py, 
interpolate_stop_arrivals.py,
calculate_speed_from_stop_arrivals.py
and aggregate_by_time_of_day.py 
for rt_stop_times.
"""
import sys

from dask import delayed, compute
from loguru import logger

from nearest_vp_to_stop import nearest_neighbor_for_stop
from interpolate_stop_arrival import interpolate_stop_arrivals
from stop_arrivals_to_speed import calculate_speed_from_stop_arrivals
from speeds_by_time_of_day import aggregate_by_time_of_day
from update_vars import GTFS_DATA_DICT
 
if __name__ == "__main__":
    
    from segment_speed_utils.project_vars import analysis_date_list
   
    segment_type = "rt_stop_times"
    print(f"segment_type: {segment_type}")
    
    LOG_FILE = "../logs/nearest_vp.log"
    logger.add(LOG_FILE, retention="3 months")
    logger.add(sys.stderr, 
               format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}", 
               level="INFO")
    
    delayed_dfs = [
        delayed(nearest_neighbor_for_stop)(
            analysis_date = analysis_date,
            segment_type = segment_type,
            config_path = GTFS_DATA_DICT
        ) for analysis_date in analysis_date_list
    ]

    [compute(i)[0] for i in delayed_dfs]
        
    logger.remove()

    
    LOG_FILE = "../logs/interpolate_stop_arrival.log"
    logger.add(LOG_FILE, retention="3 months")
    logger.add(sys.stderr, 
               format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}", 
               level="INFO")

    delayed_dfs = [
        delayed(interpolate_stop_arrivals)(
            analysis_date = analysis_date, 
            segment_type = segment_type, 
            config_path = GTFS_DATA_DICT
        ) for analysis_date in analysis_date_list
    ]
    
    [compute(i)[0] for i in delayed_dfs]

    logger.remove()
    
    
    LOG_FILE = "../logs/speeds_by_segment_trip.log"
    logger.add(LOG_FILE, retention="3 months")
    logger.add(sys.stderr, 
               format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}", 
               level="INFO")

    delayed_dfs = [
        delayed(calculate_speed_from_stop_arrivals)(
            analysis_date = analysis_date, 
            segment_type = segment_type,
            config_path = GTFS_DATA_DICT
        ) for analysis_date in analysis_date_list
    ]

    [compute(i)[0] for i in delayed_dfs]

    logger.remove()
    

    LOG_FILE = "../logs/speeds_timeofday.log"
    logger.add(LOG_FILE, retention="3 months")
    logger.add(sys.stderr, 
               format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}", 
               level="INFO")

    delayed_dfs = [
        delayed(aggregate_by_time_of_day)(
            analysis_date = analysis_date, 
            segment_type = segment_type,
            config_path = GTFS_DATA_DICT
        ) for analysis_date in analysis_date_list
    ]

    [compute(i)[0] for i in delayed_dfs]

    logger.remove()
    