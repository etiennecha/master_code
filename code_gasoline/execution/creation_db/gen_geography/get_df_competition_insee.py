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

# MARKETS BASED ON RADIUS
# todo: integrate possibility to drop stations

dict_ls_comp = dec_json(os.path.join(path_dir_built_json,
                                     'dict_ls_comp.json'))
dict_ls_comp = {k: sorted(v, key=lambda tup: tup[1]) for k,v in dict_ls_comp.items()}

ls_max_dist = [5, 4, 3, 2, 1] # Need decreasing order
ls_max_dist.sort(reverse = True)
ls_rows_comp = []
for id_station in df_info.index:
  ls_comp = dict_ls_comp.get(id_station, None)
  row_comp = []
  if ls_comp is not None:
    for max_dist in ls_max_dist:
      ls_comp = [comp for comp in ls_comp if comp[1] <= max_dist]
      row_comp.append(len(ls_comp))
  else:
    row_comp = [np.nan for i in ls_max_dist]
  ls_rows_comp.append(row_comp)
df_comp = pd.DataFrame(ls_rows_comp,
                       index = df_info.index,
                       columns = ['{:d}km'.format(i) for i in ls_max_dist])

# MARKETS BASED ON INSEE AREAS

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
ax = df_prices_ttc[dict_refined[3][1] + ['45240001', '45240002']].plot()
df_prices_ttc.mean(1).plot(ax=ax)
plt.show()
