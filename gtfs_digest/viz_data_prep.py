import pandas as pd

route_direction_cols_for_viz = [
    "direction_id",
    "time_period",
    "avg_scheduled_service_minutes",
    "n_scheduled_trips",
    'n_vp_trips',
    "service_date",
    "recent_combined_name",
    "route_primary_direction",
    "minutes_atleast1_vp", 
    "minutes_atleast2_vp",
    "is_early",
    "is_ontime",
    "is_late",
    "vp_per_minute",
    "pct_in_shape",
    "pct_sched_journey_atleast1_vp",
    "pct_sched_journey_atleast2_vp",
    "rt_sched_journey_ratio",
    "speed_mph",
    "portfolio_organization_name",
    "headway_in_minutes",
    "sched_rt_category", # added this
    'avg_stop_miles'
]

readable_col_names = {
    "direction_id": "Direction (0/1)",
    "time_period": "Period",
    "avg_scheduled_service_minutes": "Average Scheduled Service (trip minutes)",
    "n_scheduled_trips": "# Scheduled Trips",
    'n_vp_trips': "# Realtime Trips",
    "service_date": "Date",
    "recent_combined_name": "Route",
    "route_primary_direction": "Direction",
    "minutes_atleast1_vp": "# Minutes with 1+ VP per Minute",
    "minutes_atleast2_vp": "# Minutes with 2+ VP per Minute",
    "is_early": "# Early Arrival Trips",
    "is_ontime": "# On-Time Trips",
    "is_late": "# Late Trips",
    "vp_per_minute": "Average VP per Minute",
    "pct_in_shape": "% VP within Scheduled Shape",
    "pct_sched_journey_atleast1_vp": "% Scheduled Trip w/ 1+ VP/Minute",
    "pct_sched_journey_atleast2_vp": "% Scheduled Trip w/ 2+ VP/Minute",
    "rt_sched_journey_ratio": "Realtime versus Scheduled Service Ratio",
    "speed_mph": "Speed (MPH)",
    "portfolio_organization_name": "Portfolio Organization Name",
    "headway_in_minutes": "Headway (Minutes)",
    'avg_stop_miles':"Average Stop Distance (Miles)",
    "sched_rt_category":"GTFS Availability",
}


def data_wrangling_for_visualizing(
    df, 
    subset, 
    readable_col_names
):
    """
    Depending on how much this is used, some stuff
    might be moved outside to be variables borrowed elsewhere.
    remove the args subset, readable_col_names, just leave here to use in notebook
    """
    
    # create new columns
    df = df.assign(
        headway_in_minutes = 60 / df.frequency
    ).round(0)
    
    # these show up as floats but should be integers
    # also these aren't kept...
    route_typology_cols = [
        f"is_{c}" for c in 
        ["express", "rapid",
         "ferry", "rail", "coverage",
         "local", "downtown_local"]
    ]
    
    float_cols = [c for c in df.select_dtypes(include=["float"]).columns 
                     if c not in route_typology_cols and "pct" not in c]
    
    df[float_cols] = df[float_cols].round(2)
    

    pct_cols = [c for c in df.columns if "pct" in c]
    df[pct_cols] = df[pct_cols].round(0) * 100

    df2 = df.assign(
        time_period = df.time_period.astype(str).str.replace("_", " ").str.title()
    )[subset].query(
        'sched_rt_category == "schedule_and_vp"'
    ).rename(
        columns = readable_col_names
    ).reset_index(drop=True)

    return df2