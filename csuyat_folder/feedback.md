# Feedback for Christian 

## Exercise 1
* Use `git mv` to change the path of where your current exercises in progress and future exercises live. Use `csuyat_folder` and not `csuyat_folder/python`.    
   * `YOURNAME_exercise1` can be interpreted as `christian_exercise1`...not literally as `CHRISTIAN_exercise1`
* Functions within scripts are imported if they are in the same directory. It is brittle to have too many nested folders for simpler projects.
   * Most folders within `data-analyses` follow this, except for larger projects like `rt_segment_speeds` and `dla`
   * For more complex projects, nested directories are used, but only in conjunction with installable packages.
* When submitting a finished exercise, use `Kernel > Restart Kernel and Run ALl Cells` to show a fresh run of code with outputs.

## Exercise 2
* Left join keeps all rows that show up in the left df, whether or not the right df has it.
   * If the right df has it, those columns will be populated. 
   * If the right df does not have those rows, those columns will be filled with NaNs / missing values. NaNs = not a number.
   * In this exercise, if there were 100 agencies in the left df, and 90 agencies in the right df:
      * A left merge would leave you with 100 agencies in your merged df. Those 10 agencies not present in the right df would have their `vehicles` columns populated with NaNs.
      * An inner merge would leave you with 90 agencies in your merged df. These are the 90 agencies are found in the left and the right dfs.
   * There are use cases for having a left merge or an inner merge. Sometimes you want agencies with complete information. Other times you want all the agencies to show up in your results and you want to present how many agencies have missing info.
* Modify this cell to another column that isn't categorical. 
    ```
    merge2.groupby('State').TOS.agg(['count', 'nunique', 'min']).head()    
    ```
   * Use `df.dtypes` to check what data types are. 
   * `TOS` = type of service, and it has 2 unique values, DO and PT (directly operated). `min(TOS) = DO` isn't that interpretable, since the min of a string is just the first one that appears in the alphabet.
* Add a line of code to rename columns where the new line character is cleaned up. Ex: `Population\n` becomes `Population` without the new line character.
* Do the challenge portion and provide not only aggregate stats for `service_vehicles`, but also `per capita service vehicles`. Plot these 2 charts side-by-side.

## Exercise 3
* The rows do differ outside of the `subset_cols` you've defined. For `mode = MB (bus)`, the 2 rows left for LA Metro are probably for `TOS = DO or PT` (directly operated or contracted out purchased transportation). 
* [NTD Glossary](https://www.transit.dot.gov/ntd/national-transit-database-ntd-glossary)
* When deciding whether to aggregate or deal with duplicates by dropping, it depends on the research question.
   * If you wanted to focus on directly operated bus service, it's possible to filter down to the point where you no longer have duplicates.
   * If you wanted to compare agencies, aggregation is usually the way to go. 
* Fix the dictionary for mapping `Mode` values. 
   * Check whether the `and` worked by comparing `df.mode_cat.value_counts()` with `df.mode_cat.value_counts(dropna=False)`
   * If there are unmapped modes, write out the dictionary in long form:
      ```
      mode_fill = {
          "HR": "Rail",
          "SR": "Rail",
          "AR": "Rail",
          "LR": "Light Rail"
      }
      ```
* Looping: `for c in some_list:` is how loops start. `c` is the variable that is injected into the later lines.
   * By convention, it's usually something related to what that variable means. `c` here is column. You can also use `for col in df.columns:` for something readable.
   * Within each loop, `c` is replaced by the variable.
   * When the loop goes through the first time, `c = Agency_VOMS`. The second time, `c = Mode_VOMS`
      * `df.Agency_VOMS = df.Agency_VOMS.str.replace(',', '').fillna('0').astype({"Agency_VOMS": int})`
      * `df.Mode_VOMS = df.Mode_VOMS.str.replace(',', '').fillna('0').astype({"Mode_VOMS": int})`
* Alternatively, for weighted averages, you can simply take the `sum(operating_expenses)` and `sum(vehicle_miles)` by state.
   * Then, your df with 5 rows (5 states), you can add a new column calculating state-level operating expenses per mile by dividing the 2 summation columns.
   * `df["operating_cost_per_mi"] = df.total_operating_expenses.divide(df.vehicle_miles)` or `df.total_operating_expenses / df.total_vehicle_miles`
* To show `altair` chart, first use the function to make the chart: `chart = make_bar_chart()`, followed by `chart` to print it, not `chart.show()`

## Exercise 4
* Challenge question: why does `stops_2229 = stops_ptg.assign(geometry=stops_ptg.geometry.to_crs('EPSG:2229'))` show results of area = 0 for all the rows?
   * Do points have area?
   * Do lines have area? 
   * Area can only be calculated for polygons. Lines and points do not have area, so if you try to calculate it, it will always return 0.
   * Lines have lengths, and so do polygons (circumference)! Points do not have length, so if you try to calculate length on a point, you'll also return 0.
* Diving into the swapping which df to put on the left, county or stops.
   * What is the active geometry column name and what does it reflect? Is it the left or right gdf's geometry?
   * It matters which column you're interested in attaching attributes to / wanting to aggregate. If you want to count how many stops are in a county, you first want to attach the county for each stop.
   * When you keep stops on the left, it's because you want to keep stop (point) geometry for plotting, and each dot on a map should be colored according to the county name. Most of the time you want points on the left.
   * If you want to keep county on the left and plot county boundaries, you can keep county (polygon) geometry on the left.
   * Most of the time, for point-in-polygon questions, like, which polygon does this point fall into, you want the point gdf on the left.
* Do the sq ft calculation on the county gdf, not the stops. Keep only 1 row for each county, and add the column for `county_sq_ft`, then another column converting `county_sq_ft` to `county_sq_mi`. 
   * When you have your results for the county, merge it onto your groupby results here: `stop_count = geojoin_stp_cnty.groupby('COUNTY_NAME')['stop_id'].count().reset_index()
)`. `stop_count` will then contain the number of stops as well as county polygon geometry, sq_ft, sq_mi, and a new column with stops_per_sq_mi.

## Exercise 5
* When we interact with the warehouse, we use `siuba` to query it. Without `collect()`, it returns a `siuba.LazyTbl`, which is a view of the warehouse table, but not a df. To materialize it as a df that we can interact with, we always call `collect()`. 
   * Side note: querying the warehouse does cost money. For our use cases, it's not a big deal, since we're always querying a single day and whatnot. But, querying it, calling `collect`, and saving it as a parquet in our GCS bucket is one way we can reuse the large table over and over without worrying about querying costs.
* This merge is killing the kernel because it's not merged on the right columns. This is likely why there are 30k unique rows of stops, but it's ballooned up to 700k.
   * `stops` and `stop_counts` are both stop-level data, which means a row is uniquely represented by `feed_key` and `stop_id`. Include those in the merge, and it won't kill the kernel.
   * By not including them, and only merging on `feed_key`, it's creating a very large many to many merge, where each stop for an operator is attached every other stop for that operator.
   * This is where looking at what makes a row unique `len(df)` vs `df.feed_key.nunique` will show that only a handful of feeds are present, but each feed/operator serves many stops.
    
    ```
    stop_stpcnt = pd.merge(stops, stop_counts, on = 'feed_key', how ='left')
    
    # Use this instead:
    stop_stpcnt = pd.merge(
        stops,
        stop_counts,
        on = ["feed_key", "stop_id"],
        how = "left",
        validate = "1:1"
    )
    ```   
* Instead of this: `ca_county.plot('centroid')`, which actually just plots the values within the column `centroid`, do this: `ca_county.set_geometry("centroid").plot()`...and the results should show points instead of polygons.
* [altair example charts](https://altair-viz.github.io/gallery/index.html)
* use `altair` for `stop_by_op.plot.bar(x='name', y='nunique_stops')` and use the `styleguide`. See this [function to apply the styleguide on your chart object](https://github.com/cal-itp/data-analyses/blob/main/_shared_utils/shared_utils/styleguide.py#L245C5-L251)
   * see below for what's listed after the colon: N (nominal), O (ordinal), Q (quantity), T (time)
   * nominal = categorical
   * ordinal = ordered categorical (sorted alphabetically by default)
   * quantity = numeric, and you can do `sum("nunique_stops")` or `count()` or `mean()` on the column
   * time = datetime columns, because you can actually have it do datetime operations like `month(date)` or `year(date)`
  ```
  chart = (alt.Chart(stop_by_op)
          .mark_bar()
          .encode(
 
              x=alt.X("name:N", title = "Transit Operator"),
              y=alt.Y("nunique_stops:Q", title = "# unique stops"),
              # the column you want the color to be based on
              # if not specified, it's the same color for every bar
              color = alt.Color("name:N"), 
          )
          )
          
   styleguide.preset_chart_config(chart)
  ```

## Exercise 6
* Be careful of naming things with names already used. `sjoin = gpd.sjoin()` is not a good idea because you're using a name that's already used by `geopandas`. Try to stay away from names already used in certain packages. There are certain words you shouldn't use for objects, like `min`, `max`, etc because those are already have meanings associated with it. 
   * Don't call a df this way: `max = df.groupby(x_col).agg(y_col: "max").reset_index()` because `max` is a name already taken.
* For sjoins, if you're ever not sure of the CRS and forgot to change it, projecting it on-the-fly also works:
    ```
    sjoin = gpd.sjoin(
        county2229.to_crs("EPSG:2229"), 
        stops_ptg.to_crs("EPSG:2229"), 
        how='inner',
        predicate='intersects'
    )
    ```
* Your spatial join puts county on the left, so that's the geometry it reflects. But, the number of rows reflects each stop. Plotting this will be extremely intensive because it's trying to plot a polygon for each stop.
   * Either: aggregate stops to get a count of stops by county, and then each county's polygon is associated with 1 aggregate metric
   * Or: put stops on the left, and plot the points, but you can color it by county. `gdf.explore("COUNTY_NAME")`
* `transform` can be used when you want to calculate a column based on a grouping, or apply a custom function to a grouping. You'd want to use it if you're trying to make several new columns, but need to use different kinds of groupbys to get those values.
   ```
   df = df.assign(
       # this creates a column called 'state' and it fills every value with "CA"
       state = "CA",
       number_of_operators = df.groupby("COUNTY_NAME")["feed_key"].transform("nunique"),
       number_of_stops = df.groupby("feed_key").stop_id.transform("count"),
   )
   ```
* You usually want to have a return statement in your function. 
    ```
    def plot_bar(df,x_col, y_col):
        return df.plot.bar(x=x_col, y=y_col)
    ```

## Exercise 7
* Looking at your [commit history](https://github.com/cal-itp/data-analyses/compare/main...csuyat_work2), reusing a lot of the same commit messages ultimately won't be too useful. Try to describe what the commit is doing. 
   * Ex: "exercise 7, add sjoin section", "ex8 get dissolve for shn"
   * This is the `main` branch's [commit history](https://github.com/cal-itp/data-analyses/commits/main)...and finding a relevant commit where something happens relies on a concise, yet descriptive message.
* Print and display statements can be mixed. Also, you can use as many as you'd like. Think about what makes sense to save as an object like `results`. 
   * [last cell in this notebook](https://github.com/cal-itp/data-analyses/blob/main/bus_service_increase/competitive-routes.ipynb)...a link was saved out as an object, then used in a caption.
   * An example of writing out a [longer caption with some formatting](https://github.com/CityOfLosAngeles/covid19-indicators/blob/master/processing_utils/us_county_utils.py#L206-L216)
    
    ```
    # An example of mixing print statements with commas with 
    # single print statements with display statements
    
    def gdf_ptg_info(a):
        print(a.geometry.x.iloc[0], a.geometry.y.iloc[0])
        print(a.geometry.name)
        print(f"second row: {a.geometry.iloc[2]}")
        display(a.head(2))
    ```
    
* It is possible to chain functions, and this is how you'd get it to work. You would project the geometry on-the-fly and draw the buffer, and get that new column to stick. 
   
   ```
   stops_test = stops.assign(
       geometry_buffered = stops.geometry.to_crs("EPSG:3310").buffer(50),
       geometry = stops.geometry.to_crs("ESPG:3310") #if you didn't already get the projection to stick in geometry, you can do it within the assign
   )
   ```
* These docs...we should add this to our own docs reference: https://pygis.io/docs/e_vector_overlay.html
* Watch [video](https://www.youtube.com/watch?v=QBVv7h2Jhvo) that gives diagrams of clipping vs overlay
* In addition to looking at what's in `s2` from your left sjoin, you can look at it with a map. For stops that do fall in CA boundaries, what values are populated in the column `state`? For stops that do not fall in CA boundaries, what values are populated in `state`? Compare that with `s2.explore("state")` and see how the colors change based on whether they are in CA or outside.
    ```
    s2 = gpd.sjoin(
        amtrak_stops.to_crs("EPSG:2229"),
        ca2.to_crs("EPSG:2229"),
        how = "left",
        predicate = "intersects"
    )
    ```
* Note that the right sjoin uses geometry from the right df. Compare what the df looks like with what's being plotted. What shows up in the geometry column, and is that value consistent through all 116 rows of the df? 
    ```
    s3 = gpd.sjoin(
        amtrak_stops.to_crs("EPSG:2229"),
        ca2.to_crs("EPSG:2229"),
        how = "right",
        predicate = "intersects"
    )
    ```

## Exercise 8
* Markdown cell formatting: if the preview doesn't show the newline the way you want, simply add `<br>` for break right at the beginning of that line. 
* When we use gdfs that come from ESRI, there's always these columns: `Shape_Area` and/or `Shape_Length` and/or `OBJECTID`. Usually, we don't need these. Your dissolve doesn't need to include `Shape_Area`, because you won't be really sure what units those are in, and it's better to calculate your own `geometry.area` in the projected CRS of your choice.
* Before you get started on categorizing rail routes, make sure to check for duplicates against this subset of columns: `org_id, agency, route_id`. In the display you have, the first 2 rows look similar, and they simply differ on `shape_id`.
   * shape is a variation of the route path. A route can have 2 shapes, one in each direction, or short vs long routes. 
   * Get rid of duplicates by keeping the longest shape_id for each route. Use `gdf.geometry.length` to compare lengths, and do a groupby/transform/max for the route to find which one row has the longest. The longest route has the most chance of getting close to the SHN. 
   * If there are still duplicates, handle it by sorting on `shape_id` and keeping the one first alphabetically. Use chaining to accomplish the sorting/drop duplicates. `df.sort_values(['org_id', 'route_id', 'shape_id'], ascending=[True, True, True].drop_duplicates(subset=some_col_list)`
   * This ensures that 2 people who are handling the df can reproduce the same result, even if the row order was scrambled. You want to use a heuristic that can be replicated (alphabetical, length, etc) 
* Buffer by 0.25 mile around SHN, not rail routes. 
   * This gives you a cleaner overlay result.
   * Each rail route would be split by the portion within 0.25 mile and outside the 0.25 mile.
* To categorize each rail route into one of the 3 categories, you want to create two tables that can be combined: 

**Table 1: Route Characteristics before overlay**
| name    | route | route_length|     
|---------|---------|-----------|
| Amtrak  | Route1  | 25 miles  |      
| Amtrak  | Route2  | 10 miles  |    
 
**Table 2: Overlay/Intersection Results**
| name    | route   | overlay_length|     
|---------|---------|-------------|
| Amtrak  | Route1  | 12.5 miles  |      
| Amtrak  | Route2  | 4 miles     | 

**Put Together** 
| name    | route | pct_near_SHN  |     
|---------|---------|-------------|
| Amtrak  | Route1  | 0.50        |      
| Amtrak  | Route2  | 0.4         |  
 
 
* Once you handle duplicates, do an overlay with `intersection`. Do post processing on table 2 to get it to route level, if it's not. Each route should be 1 row. 
* Rail routes that are never within 0.25 mi of SHN:
   * Instead of using use overlay `symmetric difference`, which isn't exactly what you want, you can use an overlay `intersects`. If a route does go near the SHN, the overlay results will produce 1 row for the portion inside the buffered area and 1 row for the portion outside the buffered area.
* Your methodology looks ok and the final results look roughly correct to me! But, I would just adjust 2 of the steps to be a tighter methodology:
   * Handle duplicates in rail routes, no multiple shape_ids present, each row should represent one route `org_id, route_id` combination.
   * Switch the buffering to occur on SHN
   * Continue using the same methodology related to `overlay_dissolve.geom_len / overlay_dissolve.rail_len)*100)` and using a function to categorize each route.
* All in all, valiant effort!

## Exercise 9
* `stops` should be read in with `gpd.read_parquet`, not `pd.read_parquet`. The hint is that there is a `geometry` column that looks like gibberish. If you read it in with `geopandas`, it'll look normal.
* Be careful whether you use `set_crs` or `to_crs`. Here: `stops2 = gpd.GeoDataFrame(stops2).set_geometry('pt_geom').set_crs('EPSG:2229')`, instead of setting the CRS right away, you should check whether it is set already. If `stops2.crs is None`, then the CRS should be set to `EPSG:4326` first, based on the format (-118, 34).  * Following setting the correct CRS, you should use `to_crs` here: 
    ```
    def makegdf(df, geom):
        gdf = gpd.GeoDataFrame(df).set_geometry(geom).set_crs('EPSG:2229')

        return gdf 
    ```
* If you read in `stops` with `geopandas`, the CRS would already be set, and you can skip over creating your own geometry column, and simply project it to `EPSG:2229`. (This is what you did with the `highways` dataset). 
* When you set the CRS (incorrectly) to `EPSG:2229` when it is **actually** `EPSG:4326`, you'll get funky results like distance being in decimal degrees (0.0000, 0.00001, etc). That's a hint to go to an earlier step to fix it. You are expecting distances in feet, so it'd be reasonable for first and last stops to be more than 0 ft apart, unless every single route ran in a circulator/loop.
* When creating your trip-level df with the straight line distance between first and last stop, `trip_distance`, I would instead go back to these 2 gdfs, merge first, then find the distance: 
    ```
    # before this, make sure any trip-level aggregation is done with feed_key and trip_id
    testpv = gdfmin.merge(
        gdfmax,
        on=['feed_key', 'trip_id'],
        how='inner'
    )
    
    testpv = testpv.assign(
        distance = testpv.first_stop_geom.distance(testpv.last_stop_geom)
    )
    ```
    * I noticed a warning that the indices of the geoseries are different. That tells me either `gdfmin` or `gdfmax` is longer (perhaps due to the `how='left'`)? If they're of different lengths, the first row of one series is having its distance calculated against the first row of the other series, but you have no guarantee that these 2 rows actually refer to the same trip. Merging first, then calculating the distance after ensures you're lining up the columns correctly, so distance is being calculated between the first/last stop of the same trip.
* Good job on the distance from every stop to the interstate.
   * Following this, I'm looking for a `groupby/agg` at the trip-level to find the minimum distance, across all stops present, for a given trip. Take that value and merge it back onto your trip results with distance between first/last stop.
* Your final output contains duplicate rows (because the merges were done for the trip-stop), but outputs should be per trip (feed_key, trip_id), not (feed_key, trip_id, stop_id, stop_key).