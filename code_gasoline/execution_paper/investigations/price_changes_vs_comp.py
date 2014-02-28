#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path_sub
from add_to_path_sub import path_data
from generic_master_price import *
from generic_master_info import *
from generic_competition import *
import time

path_dir_built_paper = os.path.join(path_data, 'data_gasoline', 'data_built', 'data_paper')

path_dir_built_json = os.path.join(path_dir_built_paper, 'data_json')
path_diesel_price = os.path.join(path_dir_built_json, 'master_price_diesel.json')
path_info = os.path.join(path_dir_built_json, 'master_info_diesel.json')
path_ls_ls_competitors = os.path.join(path_dir_built_json, 'ls_ls_competitors.json')
path_ls_tuple_competitors = os.path.join(path_dir_built_json, 'ls_tuple_competitors.json')

path_dir_source = os.path.join(path_data, 'data_gasoline', 'data_source')
path_dict_brands = os.path.join(path_dir_source, 'data_other', 'dict_brands.json')
path_csv_insee_data = os.path.join(path_dir_source, 'data_other', 'data_insee_extract.csv')

path_dir_insee = os.path.join(path_data, 'data_insee')
path_dict_dpts_regions = os.path.join(path_dir_insee, 'dpts_regions', 'dict_dpts_regions.json')

master_price = dec_json(path_diesel_price)
master_info = dec_json(path_info)
ls_ls_competitors = dec_json(path_ls_ls_competitors)
ls_tuple_competitors = dec_json(path_ls_tuple_competitors)
dict_brands = dec_json(path_dict_brands)
dict_dpts_regions = dec_json(path_dict_dpts_regions)

zero_threshold = np.float64(1e-10)
series = 'diesel_price'
km_bound = 5

master_np_prices = np.array(master_price[series], np.float64)

# PRICE CHANGES VS. COMPETITORS (MOVE ?)

start = time.clock()
ls_ls_comp_chges = []
for indiv_ind, ls_competitors in enumerate(ls_ls_competitors):
  if ls_competitors is not None:
    ls_comp_chges = []
    for competitor_id, distance in ls_competitors:
      if distance < km_bound:
        competitor_ind = master_price['ids'].index(competitor_id)
        ls_chge_results = get_stats_two_firm_price_chges(master_np_prices[indiv_ind, :],
                                                         master_np_prices[competitor_ind, :])
        ls_comp_chges.append([master_price['ids'][indiv_ind],
                              competitor_id,
                              distance] + ls_chge_results)
    ls_ls_comp_chges.append(ls_comp_chges)
  else:
    ls_ls_comp_chges.append(None)
print 'Price chges vs. competitors:',  time.clock() - start

# Over X% changes the same day(test also before/after)
# TODO: check if same brand + margin (+stability over time) + reciprocity?
ls_all_comp_chges = [comp_chges for ls_comp_chges in ls_ls_comp_chges for comp_chges in ls_comp_chges]
ls_columns = ['id_1', 'id_2', 'distance', 'nb_chge_1', 'nb_chge_2', 'sim', 'before', 'after']
df_comp_chges = pd.DataFrame(ls_all_comp_chges, columns = ls_columns)

df_comp_chges['nb_chge_min'] = df_comp_chges[['nb_chge_1', 'nb_chge_2']].min(axis=1)

df_comp_chges['pct_sim_1'] = df_comp_chges['sim'] / df_comp_chges['nb_chge_1']
df_comp_chges['pct_sim_2'] = df_comp_chges['sim'] / df_comp_chges['nb_chge_2']
df_comp_chges['pct_sim'] = df_comp_chges[['pct_sim_1', 'pct_sim_2']].max(axis=1)
df_comp_chges['pct_sim'] = df_comp_chges['pct_sim'][df_comp_chges['nb_chge_min'] > 30]

n, bins, patches = plt.hist(df_comp_chges['pct_sim'][~pd.isnull(df_comp_chges['pct_sim'])], 30)
plt.show()

df_comp_chges['pct_close_1'] = df_comp_chges[['sim', 'before', 'after']].sum(axis = 1) /\
                                 df_comp_chges['nb_chge_1']
df_comp_chges['pct_close_2'] = df_comp_chges[['sim', 'before', 'after']].sum(axis = 1) /\
                                 df_comp_chges['nb_chge_2']
df_comp_chges['pct_close'] = df_comp_chges['pct_close'][df_comp_chges['nb_chge_min'] > 30]

# TODO: how many have no competitors based on distance / on this criteria
# TODO: how many recursions: too big markets? have to refine? which are excluded?
# TODO: draw map with links between stations within market
# TODO: is pandas suitable for query: how many days do two stations chge prices together?
# TODO: yes a priori but is it fast? (what about group?) Do I want to work on day indexes?
