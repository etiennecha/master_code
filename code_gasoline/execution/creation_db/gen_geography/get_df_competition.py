#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *

path_dir_built_paper = os.path.join(path_data, 'data_gasoline', 'data_built', 'data_paper')
path_dir_built_json = os.path.join(path_dir_built_paper, 'data_json')
path_dir_built_csv = os.path.join(path_dir_built_paper, u'data_csv')
path_dir_source = os.path.join(path_data, 'data_gasoline', 'data_source')
path_dir_insee_extracts = os.path.join(path_data, 'data_insee', 'data_extracts')

# ###############
# LOAD DATA
# ###############

# LOAD DF INFO AND PRICES

df_info = pd.read_csv(os.path.join(path_dir_built_csv,
                                   'df_station_info_final.csv'),
                      encoding = 'utf-8',
                      dtype = {'id_station' : str,
                               'adr_zip' : str,
                               'adr_dpt' : str,
                               'ci_1' : str,
                               'ci_ardt_1' :str,
                               'ci_2' : str,
                               'ci_ardt_2' : str,
                               'dpt' : str},
                      parse_dates = ['start', 'end', 'day_0', 'day_1', 'day_2'])
df_info.set_index('id_station', inplace = True)

# Get rid of highway
df_info = df_info[df_info['highway'] != 1]

df_prices_ht = pd.read_csv(os.path.join(path_dir_built_csv, 'df_prices_ht_final.csv'),
                        parse_dates = ['date'])
df_prices_ht.set_index('date', inplace = True)

df_prices_ttc = pd.read_csv(os.path.join(path_dir_built_csv, 'df_prices_ttc_final.csv'),
                        parse_dates = ['date'])
df_prices_ttc.set_index('date', inplace = True)

# LOAD JSON COMP FILES

dict_ls_comp = dec_json(os.path.join(path_dir_built_json,
                                    'dict_ls_comp.json'))
ls_comp_pairs = dec_json(os.path.join(path_dir_built_json,
                                     'ls_comp_pairs.json'))

# LOAD BRAND DICT

dict_brands = dec_json(os.path.join(path_dir_source,
                                    'data_other',
                                    'dict_brands.json'))
dict_std_brands = {v[0]: v for k, v in dict_brands.items()}

# ########################
# MARKETS AROUND STATIONS
# ########################

# todo: integrate possibility to drop stations

# NB COMP BASED ON RADIUS

dict_ls_comp = dec_json(os.path.join(path_dir_built_json,
                                     'dict_ls_comp.json'))
# dict_ls_comp = {k: sorted(v, key=lambda tup: tup[1]) for k,v in dict_ls_comp.items()}

ls_max_dist = [5, 4, 3, 2, 1] # Need decreasing order
ls_max_dist.sort(reverse = True)
ls_rows_nb_comp = []
for id_station in df_info.index:
  ls_comp = dict_ls_comp.get(id_station, None)
  row_nb_comp = []
  if ls_comp is not None:
    for max_dist in ls_max_dist:
      ls_comp = [comp for comp in ls_comp if comp[1] <= max_dist]
      row_nb_comp.append(len(ls_comp))
  else:
    row_nb_comp = [np.nan for i in ls_max_dist]
  ls_rows_nb_comp.append(row_nb_comp)
df_nb_comp = pd.DataFrame(ls_rows_nb_comp,
                       index = df_info.index,
                       columns = ['{:d}km'.format(i) for i in ls_max_dist])

# NB COMP BASED ON INSEE AREAS

df_insee_areas = pd.read_csv(os.path.join(path_dir_insee_extracts,
                                          'df_insee_areas.csv'),
                             dtype = {'CODGEO' : str,
                                      'AU2010': str,
                                      'UU2010': str,
                                      'BV' : str},
                             encoding = 'utf-8')

df_info = df_info.reset_index().merge(df_insee_areas[['CODGEO', 'AU2010', 'UU2010', 'BV']],
                                      left_on = 'ci_1', right_on = 'CODGEO',
                                      how = 'left').set_index('id_station')

ls_areas = ['ci_1', 'AU2010', 'UU2010', 'BV']
# todo: apply further restrictions?
df_area = df_info[ls_areas][df_info['highway'] != 1].copy()
df_area.reset_index(inplace = True) # index used to add data by area
for area in ls_areas:
  se_area = df_info[area].value_counts()
  df_area.set_index(area, inplace = True)
  df_area['M_%s' %area] = se_area
df_area.set_index('id_station', inplace = True)

# CLOSEST COMP, CLOSEST SUPERMARKET (move to get distances?)

df_distances = pd.read_csv(os.path.join(path_dir_built_csv,
                                        'df_distances.csv'),
                           dtype = {'id_station' : str},
                           encoding = 'utf-8')
df_distances.set_index('id_station', inplace = True)
## need to add first and last to complete index/columns
#df_distances.ix['10000001'] = np.nan
#df_distances['9700001'] = np.nan

ls_ids_dist_sup = [id_station for id_station in df_info.index\
                     if (dict_std_brands.get(df_info.ix[id_station]['brand_0'])[2] == 'SUP') and\
                        (id_station in df_distances.columns)]

ls_rows_clc = []
for id_station in df_info.index:
  if id_station in df_distances.columns:
    se_dist = pd.concat([df_distances[id_station][~pd.isnull(df_distances[id_station])],
                         df_distances.ix[id_station][~pd.isnull(df_distances.ix[id_station])]])
    se_dist_sup = se_dist[ls_ids_dist_sup]
    ls_rows_clc.append([se_dist.min(), se_dist_sup.min()])
  else:
    ls_rows_clc.append([np.nan, np.nan])
df_clc = pd.DataFrame(ls_rows_clc,
                      index = df_info.index,
                      columns = ['dist_cl', 'dist_cl_sup'])

# MERGE AND OUTPUT

df_comp = pd.merge(df_nb_comp, df_area, left_index = True, right_index = True)
df_comp = pd.merge(df_comp, df_clc, left_index = True, right_index = True)

# #####################
# MARKETS ON THEIR OWN
# #####################

# CLOSED MARKETS BASED ON RADIUS

ls_dict_markets = []
for distance in [3, 4, 5]:
  print '\nMarkets with distance', distance
  ls_markets = []
  for k,v in dict_ls_comp.items():
    ls_comp_ids = [x[0] for x in v if x[1] <= distance]
    if ls_comp_ids:
      ls_markets.append([k] + ls_comp_ids)
  dict_market_ind = {ls_ids[0]: i for i, ls_ids in enumerate(ls_markets)}
  # todo: keep centers of market and periphery?
  ls_closed_markets = []
  for market in ls_markets:
    dum_closed_market = True
    for indiv_id in market[1:]:
      if any(comp_id not in market for comp_id in ls_markets[dict_market_ind[indiv_id]]):
        dum_closed_market = False
        break
    market = sorted(market)
    if dum_closed_market == True and market not in ls_closed_markets:
      ls_closed_markets.append(market)
  # Dict: markets by nb of competitors
  dict_market_size = {}
  for market in ls_closed_markets:
  	dict_market_size.setdefault(len(market), []).append(market)
  for k,v in dict_market_size.items():
  	print k, len(v)
  ls_dict_markets.append(dict_market_size)
# output?

# MOST STABLE MARKETS

print '\nMarkets robust to distance vars'
dict_refined, dict_rejected = {}, {}
for market_size, ls_markets in ls_dict_markets[0].items():
  for market in ls_markets:
    if all((market_size in dict_market) and (market in dict_market[market_size])\
             for dict_market in ls_dict_markets[1:]):
      dict_refined.setdefault(market_size, []).append(market)
    else:
      dict_rejected.setdefault(market_size, []).append(market)
for k, v in dict_refined.items():
  print k, len(v)

ls_ls_stable_markets = [x for k,v in dict_refined.items() for x in v]
# enc_json(ls_ls_markets, os.path.join(path_dir_built_json, 'ls_ls_markets.json'))

# STATS DES

# have a look (tacit collusion?)
ax = df_prices_ttc[[u'41700003', u'41700004', u'41700006'] + ['45240001', '45240002']].plot()
df_prices_ttc.mean(1).plot(ax=ax)
plt.show()

ax = df_prices_ttc[[u'73300001', u'73300002', u'73300004']].plot()
plt.show()
