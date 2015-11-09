#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *

path_built = os.path.join(path_data,
                              'data_supermarkets',
                              'data_built',
                              'data_lsa')

path_built_csv = os.path.join(path_built,
                              'data_csv')

path_built_json = os.path.join(path_built,
                               'data_json')

path_dir_insee_extracts = os.path.join(path_data,
                                       'data_insee',
                                       'data_extracts')

# ###############
# LOAD DATA
# ###############

# LOAD DF LSA

df_lsa = pd.read_csv(os.path.join(path_built_csv,
                                  'df_lsa_active.csv'),
                     dtype = {u'id_lsa' : str,
                              u'c_insee' : str,
                              u'c_insee_ardt' : str,
                              u'c_postal' : str,
                              u'c_siren' : str,
                              u'c_nic' : str,
                              u'c_siret' : str},
                     parse_dates = [u'date_ouv', u'date_fer', u'date_reouv',
                                    u'date_chg_enseigne', u'date_chg_surface'],
                     encoding = 'UTF-8')

df_lsa = df_lsa[(~df_lsa['latitude'].isnull()) &
                (~df_lsa['longitude'].isnull())]

df_lsa.rename(columns = {'latitude' : 'lat',
                         'longitude' : 'lng'},
              inplace = True)

df_lsa.set_index('id_lsa', inplace = True)

# LOAD JSON CLOSE

dict_ls_close = dec_json(os.path.join(path_built_json,
                                      'dict_ls_close.json'))
ls_close_pairs = dec_json(os.path.join(path_built_json,
                                      'ls_close_pairs.json'))

# ################################
# GET COMPETITORS FROM NEIGHBOURS
# ################################

ls_comp_pairs = [(id_lsa, id_close, dist) for (id_lsa, id_close, dist) in ls_close_pairs\
                   if df_lsa.ix[id_close]['groupe'] != df_lsa.ix[id_lsa]['groupe']]

dict_ls_comp = {}
for id_lsa, ls_close in dict_ls_close.items():
  ls_comp = [(id_close, dist) for (id_close, dist) in ls_close\
               if df_lsa.ix[id_close]['groupe'] != df_lsa.ix[id_lsa]['groupe']]
  dict_ls_comp[id_lsa] = ls_comp

enc_json(ls_comp_pairs, os.path.join(path_dir_built_json,
                                      'ls_comp_pairs.json'))

enc_json(dict_ls_comp, os.path.join(path_dir_built_json,
                                     'dict_ls_comp.json'))

print u'\nFound and saved {:d} pairs of competitors'.format(len(ls_comp_pairs))
print u'\nFound and saved competitors for {:d} stations'.format(len(dict_ls_comp))

# ########################
# MARKETS AROUND STATIONS
# ########################

# todo: integrate possibility to drop stations

# NB COMP BASED ON RADIUS

dict_ls_comp = dec_json(os.path.join(path_dir_built_json,
                                     'dict_ls_comp.json'))
# dict_ls_comp = {k: sorted(v, key=lambda tup: tup[1]) for k,v in dict_ls_comp.items()}

ls_max_dist = [5, 4, 3, 2, 1]
# ls_max_dist.sort(reverse = True) # decreasing order
ls_rows_nb_around = []
for id_lsa in df_lsa.index:
  station_group = df_lsa.ix[id_lsa]['groupe']
  ls_close = dict_ls_close.get(id_lsa, None)
  if ls_close is not None:
    ls_nb_comp, ls_nb_same = [], []
    for max_dist in ls_max_dist:
      ls_comp = [close for close in ls_close if (close[1] <= max_dist) and\
                      df_lsa.ix[close[0]]['groupe'] != station_group]
      ls_same = [close for close in ls_close if (close[1] <= max_dist) and\
                     df_lsa.ix[close[0]]['groupe'] == station_group]
      ls_nb_comp.append(len(ls_comp))
      ls_nb_same.append(len(ls_same))
    row_nb_around = ls_nb_comp + ls_nb_same
  else:
    row_nb_around = [np.nan for i in range(len(ls_max_dist) *2)]
  ls_rows_nb_around.append(row_nb_around)
df_nb_comp = pd.DataFrame(ls_rows_nb_around,
                       index = df_lsa.index,
                       columns = ['nb_c_{:d}km'.format(i) for i in ls_max_dist] +\
                                 ['nb_s_{:d}km'.format(i) for i in ls_max_dist])

# NB BASED ON INSEE AREAS

df_insee_areas = pd.read_csv(os.path.join(path_dir_insee_extracts,
                                          'df_insee_areas.csv'),
                             dtype = {'CODGEO' : str,
                                      'AU2010': str,
                                      'UU2010': str,
                                      'BV' : str},
                             encoding = 'utf-8')

df_lsa = df_lsa.reset_index().merge(df_insee_areas[['CODGEO', 'AU2010', 'UU2010', 'BV']],
                                      left_on = 'ci_1', right_on = 'CODGEO',
                                      how = 'left').set_index('id_lsa')

ls_areas = ['ci_1', 'AU2010', 'UU2010', 'BV']
df_area_nb = df_lsa[ls_areas].copy()
df_area_nb.reset_index(inplace = True) # index used to add data by area
for area in ls_areas:
  se_area = df_lsa[area].value_counts()
  df_area_nb.set_index(area, inplace = True)
  df_area_nb['nb_%s' %area] = se_area
df_area_nb.set_index('id_lsa', inplace = True)

# NB SAME GROUP IN INSEE AREAS

ls_areas = ['ci_1', 'AU2010', 'UU2010', 'BV']
df_area_same = df_lsa[['groupe'] + ls_areas].copy()
ls_groups = df_lsa['groupe'][~(df_lsa['groupe'].isnull())].unique()
for group_name in ls_groups:
  df_group = df_lsa[df_lsa['groupe'] == group_name]
  for area in ls_areas:
    se_group_area = df_group[area].value_counts()
    df_area_same.reset_index(inplace = True)
    df_area_same.set_index(area, inplace = True)
    df_area_same.loc[df_area_same['groupe'] == group_name,
                     'nb_s_%s' %area] = se_group_area
df_area_same.set_index('id_lsa', inplace = True)
df_area_same = df_area_same[['nb_s_%s' %area for area in ls_areas]]

# CLOSEST COMP, CLOSEST SUPERMARKET (move to get distances?)

df_distances = pd.read_csv(os.path.join(path_dir_built_csv,
                                        'df_distances.csv'),
                           dtype = {'id_lsa' : str},
                           encoding = 'utf-8')
df_distances.set_index('id_lsa', inplace = True)

# old method not taking into account retail group
dict_rgp_ids = {rgp: list(df_lsa.index[df_lsa['groupe'] == rgp])\
                  for rgp in df_lsa['groupe'].unique()}

dict_diff_rgp_ids = {rgp: list(df_lsa.index[df_lsa['groupe'] != rgp])\
                       for rgp in df_lsa['groupe'].unique()}

dict_diff_rgp_sup_ids = {rgp: list(df_lsa.index[(df_lsa['groupe'] != rgp) &\
                                                 (df_lsa['group_type'] == 'SUP')])\
                           for rgp in df_lsa['groupe'].unique()}

ls_rows_clc = []
for id_lsa in df_lsa.index:
  if id_lsa in df_distances.columns:
    group_station = df_lsa.ix[id_lsa]['groupe']
    se_dist = pd.concat([df_distances[id_lsa][~pd.isnull(df_distances[id_lsa])],
                         df_distances.ix[id_lsa][~pd.isnull(df_distances.ix[id_lsa])]])
    ls_rows_clc.append([se_dist[dict_rgp_ids[group_station]].min(),
                        se_dist[dict_diff_rgp_ids[group_station]].min(),
                        se_dist[dict_diff_rgp_sup_ids[group_station]].min()])
  else:
    ls_rows_clc.append([np.nan, np.nan, np.nan])
df_clc = pd.DataFrame(ls_rows_clc,
                      index = df_lsa.index,
                      columns = ['dist_s', 'dist_c', 'dist_c_sup'])

# MERGE AND OUTPUT

df_comp = pd.merge(df_nb_comp, df_area_nb, left_index = True, right_index = True)
df_comp = pd.merge(df_comp, df_area_same, left_index = True, right_index = True)
df_comp = pd.merge(df_comp, df_clc, left_index = True, right_index = True)

# fix stations with no group
# counted in nb_AU2010 (e.g.) but not in nb_c
len(df_comp[(~df_comp['nb_UU2010'].isnull()) & (df_comp['nb_s_UU2010'].isnull())])
for area in ['ci_1', 'AU2010', 'UU2010', 'BV']:
  df_comp.loc[(df_comp['nb_s_%s' %area].isnull()) &\
              (~df_comp['nb_%s' %area].isnull()),
              'nb_s_%s' %area] = 1

df_comp.to_csv(os.path.join(path_dir_built_csv,
                            'df_comp.csv'),
               encoding = 'utf-8',
               index_label = 'id_lsa',
               float_format= '%.2f')

## #####################
## MARKETS ON THEIR OWN
## #####################
#
## CLOSED MARKETS BASED ON RADIUS
#
#ls_dict_markets = []
#for distance in [3, 4, 5]:
#  print '\nMarkets with distance', distance
#  ls_markets = []
#  for k,v in dict_ls_close.items():
#    ls_close_ids = [x[0] for x in v if x[1] <= distance]
#    if ls_close_ids:
#      ls_markets.append([k] + ls_close_ids)
#  dict_market_ind = {ls_ids[0]: i for i, ls_ids in enumerate(ls_markets)}
#  # todo: keep centers of market and periphery?
#  ls_closed_markets = []
#  for market in ls_markets:
#    dum_closed_market = True
#    for indiv_id in market[1:]:
#      if any(close_id not in market for close_id in ls_markets[dict_market_ind[indiv_id]]):
#        dum_closed_market = False
#        break
#    market = sorted(market)
#    if dum_closed_market == True and market not in ls_closed_markets:
#      ls_closed_markets.append(market)
#  # Dict: markets by nb of competitors
#  dict_market_size = {}
#  for market in ls_closed_markets:
#  	dict_market_size.setdefault(len(market), []).append(market)
#  for k,v in dict_market_size.items():
#  	print k, len(v)
#  ls_dict_markets.append(dict_market_size)
#
#enc_json(ls_dict_markets,
#         os.path.join(path_dir_built_json,
#                      'ls_dict_stable_markets.json'))
#
## MOST ROBUST MARKETS
#
#print '\nMarkets robust to distance vars'
#dict_refined, dict_rejected = {}, {}
#for market_size, ls_markets in ls_dict_markets[0].items():
#  for market in ls_markets:
#    if all((market_size in dict_market) and (market in dict_market[market_size])\
#             for dict_market in ls_dict_markets[1:]):
#      dict_refined.setdefault(market_size, []).append(market)
#    else:
#      dict_rejected.setdefault(market_size, []).append(market)
#for k, v in dict_refined.items():
#  print k, len(v)
#
#ls_robust_markets = [x for k,v in dict_refined.items() for x in v]
#
#enc_json(ls_robust_markets,
#         os.path.join(path_dir_built_json,
#                      'ls_robust_stable_markets.json'))
#
## STATS DES
#
## have a look (tacit collusion?)
#ax = df_prices_ttc[[u'41700003', u'41700004', u'41700006'] +\
#                   ['45240001', '45240002']].plot()
#df_prices_ttc.mean(1).plot(ax=ax)
#plt.show()
#
#ax = df_prices_ttc[[u'73300001', u'73300002', u'73300004']].plot()
#plt.show()
