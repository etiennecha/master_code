#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
from functions_maps import *
from mpl_toolkits.basemap import Basemap
from shapely.geometry import Point, Polygon, MultiPoint, MultiPolygon, shape
from shapely.prepared import prep
from descartes import PolygonPatch
from matplotlib.text import TextPath

path_dir_built = os.path.join(path_data,
                              'data_gasoline',
                              'data_built',
                              'data_scraped_2011_2014')
path_dir_built_json = os.path.join(path_dir_built, 'data_json')
path_dir_built_csv = os.path.join(path_dir_built, u'data_csv')
path_dir_built_graphs = os.path.join(path_dir_built, u'data_graphs')

path_dir_built_dis = os.path.join(path_data,
                                  u'data_gasoline',
                                  u'data_built',
                                  u'data_dispersion')
path_dir_built_dis_csv = os.path.join(path_dir_built_dis, u'data_csv')
path_dir_built_dis_json = os.path.join(path_dir_built_dis, u'data_json')

path_dir_insee_extracts = os.path.join(path_data,
                                       'data_insee',
                                       'data_extracts')


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
# Get rid of highway (gps too unreliable so far + require diff treatment)
df_info = df_info[df_info['highway'] != 1]

# LOAD PRICES (only for stats des...)
df_prices_ht = pd.read_csv(os.path.join(path_dir_built_csv,
                                        'df_prices_ht_final.csv'),
                           parse_dates = ['date'])
df_prices_ht.set_index('date', inplace = True)

df_prices_ttc = pd.read_csv(os.path.join(path_dir_built_csv,
                                         'df_prices_ttc_final.csv'),
                            parse_dates = ['date'])
df_prices_ttc.set_index('date', inplace = True)

# LOAD JSON CLOSE

dict_ls_close = dec_json(os.path.join(path_dir_built_json,
                                      'dict_ls_close.json'))
ls_close_pairs = dec_json(os.path.join(path_dir_built_json,
                                      'ls_close_pairs.json'))

# COMPETITORS
ls_comp_pairs = dec_json(os.path.join(path_dir_built_json,
                                      'ls_comp_pairs.json'))

dict_ls_comp = dec_json(os.path.join(path_dir_built_json,
                                     'dict_ls_comp.json'))

# NB BASED ON INSEE AREAS
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
df_area_nb = df_info[ls_areas].copy()
df_area_nb.reset_index(inplace = True) # index used to add data by area
for area in ls_areas:
  se_area = df_info[area].value_counts()
  df_area_nb.set_index(area, inplace = True)
  df_area_nb['nb_%s' %area] = se_area
df_area_nb.set_index('id_station', inplace = True)

# NB SAME GROUP IN INSEE AREAS
ls_areas = ['ci_1', 'AU2010', 'UU2010', 'BV']
df_area_same = df_info[['group'] + ls_areas].copy()
ls_groups = df_info['group'][~(df_info['group'].isnull())].unique()
for group_name in ls_groups:
  df_group = df_info[df_info['group'] == group_name]
  for area in ls_areas:
    se_group_area = df_group[area].value_counts()
    df_area_same.reset_index(inplace = True)
    df_area_same.set_index(area, inplace = True)
    df_area_same.loc[df_area_same['group'] == group_name,
                     'nb_s_%s' %area] = se_group_area
df_area_same.set_index('id_station', inplace = True)
df_area_same = df_area_same[['nb_s_%s' %area for area in ls_areas]]

# MARKETS ON THEIR OWN
ls_dict_markets = dec_json(os.path.join(path_dir_built_json,
                                        'ls_dict_stable_markets.json'))

ls_robust_markets = dec_json(os.path.join(path_dir_built_json,
                                          'ls_robust_stable_markets.json'))
dict_robust_markets = {}
for x in ls_robust_markets:
  dict_robust_markets.setdefault(len(x), []).append(x)

# DF PAIRS
ls_dtype_temp = ['id', 'ci_ardt_1']
dict_dtype = dict([('%s_1' %x, str) for x in ls_dtype_temp] +\
                  [('%s_2' %x, str) for x in ls_dtype_temp])
df_pairs = pd.read_csv(os.path.join(path_dir_built_dis_csv,
                                    'df_pair_final.csv'),
              encoding = 'utf-8',
              dtype = dict_dtype)

# basic pair filter (insufficient obs, biased rr measure)
df_pairs = df_pairs[(~((df_pairs['nb_spread'] < 90) &\
                       (df_pairs['nb_ctd_both'] < 90))) &
                    (~(df_pairs['nrr_max'] > 60))]

# ###########
# FIND MARKET
# ###########

ls_market_ids = [u'48100001', u'48100002', u'48100003', u'48100004']

print('Marvejols:')
print(df_info.ix[ls_market_ids][['brand_0', 'brand_1', 'day_1', 'lat', 'lng']])

plt.rcParams['figure.figsize'] = 16, 6

ls_loop = [(df_info.ix[id_station]['brand_0'],
            df_prices_ttc[id_station]) for id_station in ls_market_ids]

str_date_beg, str_date_end = '2011-12-01', '2012-11-30'

fig = plt.figure()
ax1 = fig.add_subplot(111)
ls_l = []
for (label, se_temp), ls, alpha in zip(ls_loop,
                                       ['-', '-', '--', ':'],
                                       [1, 0.4, 1, 1]):
  ls_l.append(ax1.plot(se_temp.ix[str_date_beg: str_date_end].index,
                       se_temp.ix[str_date_beg: str_date_end].values,
                       c = 'k', ls = ls, alpha = alpha,
                       label = label))
lns = [x[0] for x in ls_l]
labs = [l.get_label() for l in lns]
#ax1.set_ylim(0, 50.0)
ax1.legend(lns, labs, loc=0, labelspacing = 0.3)
ax1.grid()
# Show ticks only on left and bottom axis, out of graph
ax1.yaxis.set_ticks_position('left')
ax1.xaxis.set_ticks_position('bottom')
ax1.get_yaxis().set_tick_params(which='both', direction='out')
ax1.get_xaxis().set_tick_params(which='both', direction='out')
plt.xlim(str_date_beg, str_date_end)
plt.xlabel('')
plt.ylabel('Retail diesel price (euro/liter)')
plt.tight_layout()
plt.savefig(os.path.join(path_dir_built_graphs,
                         'case_study',
                         'case_study_marvejols_prices.png'),
            bbox_inches='tight')
plt.close()
