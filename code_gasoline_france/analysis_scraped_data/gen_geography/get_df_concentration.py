#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *

path_dir_built_scraped = os.path.join(path_data,
                                    'data_gasoline',
                                    'data_built',
                                    'data_scraped_2011_2014')

path_dir_built_json = os.path.join(path_dir_built_scraped, 'data_json')
path_dir_built_csv = os.path.join(path_dir_built_scraped, u'data_csv')

path_dir_source = os.path.join(path_data, 'data_gasoline', 'data_source')
path_dir_insee_extracts = os.path.join(path_data, 'data_insee', 'data_extracts')

pd.set_option('float_format', '{:,.2f}'.format)

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
#ls_close_pairs = dec_json(os.path.join(path_dir_built_json,
#                                      'ls_close_pairs.json'))

# ################################
# MARKETS AROUND STATIONS
# ################################

# Caution: need to check group and independent (small groups?)
df_info.loc[df_info['group'].isnull(),
            'group'] = 'INDEPENDANT'

# RADIUS (3km for now)

ls_rows = []
for id_station, ls_close in dict_ls_close.items():
  ls_comp = [(id_station, 0, df_info.ix[id_station]['group'])] +\
            [(id_close, dist, df_info.ix[id_close]['group'])\
               for (id_close, dist) in ls_close if dist <= 3]
  df_comp = pd.DataFrame(ls_comp, columns = ['id', 'distance', 'group'])
  se_group_nb = df_comp['group'].value_counts()
  se_group_ms = se_group_nb.astype(float) * 100 / se_group_nb.sum()
  ls_rows.append((id_station, se_group_nb, se_group_ms))

df_ms = pd.concat([row[2] for row in ls_rows], keys = [row[0] for row in ls_rows], axis = 1).T
df_ms.fillna(0, inplace = True)
df_ms['HHI'] = df_ms.apply(lambda x: (x**2).sum(), axis = 1)

# pbm cannot take into account independent market shares properly
# build df with nb of stores of each brand
# treat independent column specifically

df_nb = pd.concat([row[1] for row in ls_rows], keys = [row[0] for row in ls_rows], axis = 1).T
df_nb.fillna(0, inplace = True)

ls_chains = list(df_nb.columns)
ls_chains.remove('INDEPENDANT')
df_nb['HHI'] = df_nb.apply(lambda x: ((x[ls_chains] * 100 / x.sum())**2).sum() +\
                                     ((100 / x.sum())**2) * x['INDEPENDANT'],  axis = 1)

# DISTANCE WEIGHTING (todo but much slower)

# ############
# INSEE AREAS
# ############

df_insee_areas = pd.read_csv(os.path.join(path_dir_insee_extracts,
                                          'df_insee_areas.csv'),
                             dtype = {'CODGEO' : str,
                                      'UU2010' : str,
                                      'AU2010' : str,
                                      'BV2010' : str},
                             encoding = 'UTF-8')

df_info.reset_index(inplace = True)
df_info = pd.merge(df_info,
                   df_insee_areas,
                   left_on = 'ci_ardt_1',
                   right_on = 'CODGEO',
                   how = 'left')
#df_info.set_index('id_station', inplace = True)

area_field, area_lib = 'AU2010', 'LIBAU2010'
#area_field, area_lib = 'UU2010', 'LIBUU2010'
#area_field, area_lib = 'BV', 'LIBBV'

ls_se_area_nb = []
for area in df_info[area_field].unique():
  se_area_nb = df_info[df_info[area_field] == area]['group'].value_counts()
  ls_se_area_nb.append((area, se_area_nb))
df_area_nb = pd.concat([row[1] for row in ls_se_area_nb],
                       keys = [row[0] for row in ls_se_area_nb], axis = 1).T
df_area_nb.fillna(0, inplace = True)
df_area_nb['HHI'] = df_area_nb.apply(lambda x: ((x[ls_chains] * 100 / x.sum())**2).sum() +\
                                               ((100 / x.sum())**2) * x['INDEPENDANT'],
                                     axis = 1)

df_info = pd.merge(df_info,
                   df_area_nb[['HHI']],
                   left_on = area_field,
                   right_index = True,
                   how = 'left')
df_info.set_index('id_station', inplace = True)

# ################################
# STABLE MARKETS
# ################################

ls_robust_markets = dec_json(os.path.join(path_dir_built_json,
                                          'ls_robust_stable_markets.json'))

ls_rows_robust = []
for ls_market_ids in ls_robust_markets:
  ls_robust_ids = [(id_station, df_info.ix[id_station]['group'])\
                        for id_station in ls_market_ids]
  df_robust = pd.DataFrame(ls_robust_ids, columns = ['id', 'group'])
  se_robust_nb = df_robust['group'].value_counts()
  ls_rows_robust.append((id_station, se_robust_nb))

df_robust_nb = pd.concat([row[1] for row in ls_rows_robust],
                         keys = [row[0] for row in ls_rows_robust], axis = 1).T
df_robust_nb.fillna(0, inplace = True)

ls_chains = list(df_robust_nb.columns)
if 'INDEPENDANT' in ls_chains:
  ls_chains.remove('INDEPENDANT')
df_robust_nb['HHI'] =\
  df_robust_nb.apply(lambda x: ((x[ls_chains] * 100 / x.sum())**2).sum() +\
                               ((100 / x.sum())**2) * x['INDEPENDANT'],  axis = 1)

print u'\nOverview HHI robust markets'
print df_robust_nb['HHI'].describe()

# Can combine HHI within INSEE area & stable markets to find high concentration
# or around stations instead of stable markets
# How to take demand into account? (station network density?)
# pop/station? threshold? nb of supermarkets plays a role?
