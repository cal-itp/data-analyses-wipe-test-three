"""
Functions for creating profiles for
transit operators.
~0.5 min per date.
"""
import datetime
import geopandas as gpd
import pandas as pd

from calitp_data_analysis import utils
from segment_speed_utils import gtfs_schedule_wrangling, helpers
from shared_utils.rt_utils import METERS_PER_MILE
from update_vars import GTFS_DATA_DICT, SCHED_GCS
from nacto_utils import route_typology_types

def schedule_stats_by_operator(
    analysis_date: str,
    group_cols: list = ["schedule_gtfs_dataset_key"]
) -> pd.DataFrame:
    """
    Get operator-level aggregations for n_trips,
    n_routes, n_shapes, n_stops, n_arrivals.
    """
    trips = helpers.import_scheduled_trips(
        analysis_date,
        columns = ["gtfs_dataset_key", "route_id",
                  "trip_instance_key", "shape_array_key"],
        get_pandas = True
    )
    
    stop_times = helpers.import_scheduled_stop_times(
        analysis_date,
        columns = ["schedule_gtfs_dataset_key", 
                   "trip_instance_key", "stop_id"],
        with_direction = True,
        get_pandas = True
    )
    
    nunique_cols = [
        "route_id", "trip_instance_key", "shape_array_key"
    ]
    trip_stats = (
        trips
        .groupby(group_cols, 
                 observed=True, group_keys=False, dropna=False)
        .agg({
            **{c: "nunique" for c in nunique_cols}
        }).reset_index()
        .rename(columns = {
            "route_id": "operator_n_routes",
            "trip_instance_key": "operator_n_trips",
            "shape_array_key": "operator_n_shapes",
        })
    )
    
    stop_time_stats = (
        stop_times
        .groupby(group_cols, 
                 observed=True, group_keys=False, dropna=False)
        .agg({
            "stop_id": "nunique",
            "trip_instance_key": "count"
        }).reset_index()
        .rename(columns = {
            "stop_id": "operator_n_stops",
            "trip_instance_key": "operator_n_arrivals"
       })
    )
    
    longest_shape = longest_shape_by_route(analysis_date)
    
    shape_stats = (
        longest_shape
        .groupby(group_cols, 
                 observed=True, group_keys=False, dropna=False)
        .agg({"route_length_miles": "sum"})
        .reset_index()
        .rename(columns = {
            "route_length_miles": "operator_route_length_miles"})
    )
    
    df = pd.merge(
        trip_stats,
        stop_time_stats,
        on = group_cols,
        how = "inner"
    ).merge(
        shape_stats,
        on = group_cols,
        how = "inner"
    )
    
    df = df.assign(
        operator_arrivals_per_stop = df.operator_n_arrivals.divide(
            df.operator_n_stops).round(2)
    )
    
    return df

    
def longest_shape_by_route(analysis_date: str) -> gpd.GeoDataFrame: 
    """
    Start with the longest shape for route-direction.
    Drop duplicates by route to keep longest shape per route.
    This will serve as our metric for operator's service area.
    Keep as gdf so we can plot.
    """
    route_cols = ["schedule_gtfs_dataset_key", "route_id"]
    
    gdf = gtfs_schedule_wrangling.longest_shape_by_route_direction(
        analysis_date
    ).sort_values(
        route_cols + ["route_length"], 
        ascending=[True for i in route_cols] + [False]
    ).drop_duplicates(subset=route_cols).reset_index(drop=True)
    
    gdf = gdf.assign(
        route_length_miles = gdf.route_length.divide(METERS_PER_MILE).round(2)
    )
    
    return gdf


def operator_typology_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """
    Get a count of how many routes (not route-dir) 
    have a certain primary typology.
    Rename columns following this pattern: is_rapid to n_rapid_routes
    """    
    
    df_wide = (df.groupby("schedule_gtfs_dataset_key", group_keys=False)
               .agg({
                   **{f"is_{c}": "sum" for c in route_typology_types}
               })
               .reset_index()
               .rename(columns = {
                   **{f"is_{c}": f"n_{c.replace('is_', '')}_routes" 
                      for c in route_typology_types}
               })
              )
    
    return df_wide


if __name__ == "__main__":
    
    from update_vars import analysis_date_list
    
    ROUTE_TYPOLOGY = GTFS_DATA_DICT.schedule_tables.route_typologies
    OPERATOR_EXPORT = GTFS_DATA_DICT.schedule_tables.operator_scheduled_stats
    OPERATOR_ROUTE_EXPORT = GTFS_DATA_DICT.schedule_tables.operator_routes
    
    for analysis_date in analysis_date_list:
        start = datetime.datetime.now()
        
        year = pd.to_datetime(analysis_date).year
        
        crosswalk = helpers.import_schedule_gtfs_key_organization_crosswalk(
            analysis_date
        )[["schedule_gtfs_dataset_key", 
           "name", "organization_source_record_id", "organization_name"]]
        
        route_typology = pd.read_parquet(
            f"{SCHED_GCS}{ROUTE_TYPOLOGY}_{year}.parquet"
        )
           
        operator_typology_counts = operator_typology_breakdown(route_typology)
    
        stats = schedule_stats_by_operator(
            analysis_date,
            group_cols = ["schedule_gtfs_dataset_key"]
        ).merge(
            operator_typology_counts,
            on = "schedule_gtfs_dataset_key",
            how = "inner"
        ).merge(
            crosswalk,
            on = "schedule_gtfs_dataset_key",
            how = "inner"
        )
        
        stats.to_parquet(
            f"{SCHED_GCS}{OPERATOR_EXPORT}_{analysis_date}.parquet"
        )
        
        # route typology is by route, but there are some rows that are duplicated
        # because of differences in route_long_name, route_short_name
        route_typology_grouped = (
            route_typology
            .groupby(["schedule_gtfs_dataset_key", "route_id"])
            .agg({**{f"is_{c}": "max" for c in route_typology_types}})
            .reset_index()
        )
        
        route_gdf = longest_shape_by_route(
            analysis_date
        ).merge(
            route_typology_grouped,
            on = ["schedule_gtfs_dataset_key", "route_id"],
            how = "left"
        ).merge(
            crosswalk,
            on = "schedule_gtfs_dataset_key",
            how = "inner"
        )

        utils.geoparquet_gcs_export(
            route_gdf,
            SCHED_GCS,
            f"{OPERATOR_ROUTE_EXPORT}_{analysis_date}"
        )
        
        end = datetime.datetime.now()
        print(f"operator stats for {analysis_date}: {end - start}")
