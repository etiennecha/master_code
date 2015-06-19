## analysis_store_geography

----------

### overview

- describe_stores_lsa : partially redundant with files which formats the excel lsa file for qlmc (todo: keep only stats des)
- draw_maps : loads geofla dpt and commune (todo: create class to import?) and lsa data. Outputs maps accounting for competition at commune level (ok but move to dedicated data file)
-  draw_maps_group_history : loads geofla dpt and commune (same remark as before) and lsa data (check redundancy in data treatment with previous script). Outputs map accounting for group history (ok but move to dedicated data file)
-  draw_map_nb_stores : loads geofla dpt and commune (same remark as before) and lsa data (check redundancy in data treatment with previous script). Outputs map with nb stores and store surface by insee area (ok but move to dedicated data file)

Overall: refactor to get rid of repetitions, redefine output locations and give structure (e.g. by variable and by insee area). Keep only stats des (should not include HHI, nb of competitors etc), description of data (no latex output either).

### report

- ta_insee_areas : stats des on store locations vs. population (todo: include in overview)
- ta_region_comp : share of surface by region by group, share of group by region, CRN and HHI at region level
- ta_region_cr_hhi : seems redundant but using variable Groupe (instead of Groupe_alt) so probably wrong (todo: check and delete)
- ta_retail_groups : overview of retail group (chain?) store characteristics
- ta_variables : overview of store variables (very first overview...)

Overall: rethink distinction between report and overview. Not sure there should be two files... maybe rather subfiles... and flexibility for output format? Also, what if want to get all tables/maps for a different date (i.e. say lsa file and/or possibly different insee classifications)

### geography

- draw_map_retail_group_surfaces : loads geofla dpt and commune (same remark as before) and lsa data. Outputs maps of store surface at municipality level by retail group
- draw_map_surfaces : loads geofla commune and computes competition variables, gini, entropy etc. (no map!)
- get_df_entropy_decomposition : computes entropy within and inter regions
- get_df_retail_group_market_shares : loads geofla commune and formats its. Comptes surface available to each municipality by chain (continuous) and then market share of groups in each municipality (drop?)
- get_df_retail_group_market_shares : loads geofla commune and formats its.  Computes retail group market shares in each municipality
- get_df_retail_group_surfaces : loads geofla commune and formats its.  Computes retail group surfaces in each municipality (drop?)
- get_df_store_type_surface : loads geofla commune and formats its.   Computes surfae vailable by store type
- get_df_surface : same as draw_map_surfaces(?) most advanced in terms of competition description?
- interact_insee_data : loads insee area data. Analysis of store surface vs. population and its characteristics

### eva_autoconc_1

- example_geography : loads geofla com.. only for home to query local osrm dist server for distance
- gen_df_autconc_and_continuous_H_and_S : computes store and group market shares and hhi with continuous distance discounting or simple radius
- gen df_demand_H_and_S : loads geogla com, computes pop for each store based on continuous distance discounting or simple radius
- gen df_hhi_municipalities: loads geofla com, computes hhi from municipality viewpoints
- get_map_example: draws a map with stores and osm tiles
- get_ta_autconc_and_continuous_H_and_S: stats des on dfs previously obtained to describe competition (and demand?) taking into account population
