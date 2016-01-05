#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
from generic_competition import *
from functions_string import *
from BeautifulSoup import BeautifulSoup
import copy
import collections

path_dir_scraped = os.path.join(path_data,
                                u'data_gasoline',
                                u'data_built',
                                u'data_scraped_2011_2014')

path_dir_scraped_csv = os.path.join(path_dir_scraped,
                                    'data_csv')

path_dir_scraped_json = os.path.join(path_dir_scraped,
                                     'data_json')

path_dir_zagaz = os.path.join(path_data,
                              u'data_gasoline',
                              u'data_built',
                              u'data_zagaz')

path_dir_zagaz_csv = os.path.join(path_dir_zagaz, 'data_csv')

path_dir_match_insee = os.path.join(path_data,
                                    u'data_insee',
                                    u'match_insee_codes')

path_dir_insee_extracts = os.path.join(path_data,
                                       u'data_insee',
                                       u'data_extracts')

# ################
# LOAD DF ZAGAZ
# ################

df_zagaz = pd.read_csv(os.path.join(path_dir_zagaz_csv,
                                    'df_zagaz_stations.csv'),
                       encoding='utf-8',
                       dtype = {'id_zagaz' : str,
                                'zip' : str,
                                'ci_1' : str,
                                'ci_ardt_1' : str})
df_zagaz.set_index('id_zagaz', inplace = True)

dict_brands = dec_json(os.path.join(path_data,
                                    'data_gasoline',
                                    'data_source',
                                    'data_other',
                                    'dict_brands.json'))

# update with zagaz
dict_brands_update = {'OIL' : [u'INDEPENDANT', u'INDEPENDANT', u'IND'],
                      'TEXACO' : [u'INDEPENDANT', u'INDEPENDANT', u'IND'],
                      'ENI' : [u'AGIP', u'AGIP', u'OIL'],
                      'IDS': [u'INDEPENDANT', u'INDEPENDANT', u'IND'],
                      '8 A HUIT' : [u'HUIT_A_HUIT', u'CARREFOUR', u'SUP'],
                      'AS 24' : [u'INDEPENDANT', u'INDEPENDANT', u'IND'],
                      'AS24' : [u'INDEPENDANT', u'INDEPENDANT', u'IND'],
                      'SPAR' : [u'CASINO', u'CASINO', u'SUP'],
                      'ANTARGAZ' : [u'INDEPENDANT', u'INDEPENDANT', u'IND'],
                      'DIVERS' : [u'INDEPENDANT', u'INDEPENDANT', u'IND'],
                      'MATCH' : [u'CORA', u'CORA', u'SUP'],
                      'PRIMAGAZ' : [u'INDEPENDANT', u'INDEPENDANT', u'IND']}
dict_brands.update(dict_brands_update)

# NORMALIZATION FOR MATCHING
dict_brands_std = {v[0]: v[1:] for k,v in dict_brands.items()}
dict_brands_norm = {u'SHOPI': [u'CARREFOUR', u'GMS'],
                    u'CARREFOUR_CONTACT': [u'CARREFOUR', u'GMS'],
                    u'ECOMARCHE' : [u'MOUSQUETAIRES', u'GMS'],
                    u'INTERMARCHE_CONTACT' : [u'MOUSQUETAIRES', u'GMS'],
                    u'INTERMARCHE' : [u'MOUSQUETAIRES', u'GMS'],
                    u'ESSO_EXPRESS' : [u'ESSO', u'OIL']}
dict_brands_std.update(dict_brands_norm)

df_zagaz['brand_std_last'] = df_zagaz['brand_std_2013']
df_zagaz.loc[df_zagaz['brand_std_last'].isnull(),
             'brand_std_last'] = df_zagaz['brand_std_2012']

df_zagaz['brand_std_last'] = df_zagaz['brand_std_last'].apply(\
                               lambda x: dict_brands_std.get(x, [None, None])[0])

# ################
# LOAD DF GOUV
# ################

df_info = pd.read_csv(os.path.join(path_dir_scraped_csv,
                                   'df_station_info_final.csv'),
                              encoding = 'utf-8',
                              dtype = {'id_station' : str,
                                       'adr_zip' : str,
                                       'adr_dpt' : str,
                                       'ci_1' : str,
                                       'ci_ardt_1' :str,
                                       'ci_2' : str,
                                       'ci_ardt_2' : str,
                                       'dpt' : str})
df_info.set_index('id_station', inplace = True)

for field_brand in ['brand_0', 'brand_1',  'brand_2']:
  df_info[field_brand] = df_info[field_brand].apply(\
                              lambda x: dict_brands_std.get(x, [None, None])[0])

# #############
# LOAD MATCH
# #############

df_zagaz_match = pd.read_csv(os.path.join(path_dir_zagaz_csv,
                                          'df_zagaz_stations_match_1.csv'),
                             dtype = {'zag_id' : str,
                                      'gov_id' : str,
                                      'ci' : 'str'},
                             encoding = 'UTF-8')
# Need unicity of gov_id
df_zagaz_match.set_index('gov_id', inplace = True)

df_info = pd.merge(df_info,
                   df_zagaz_match[['zag_id', 'quality', 'dist']],
                   left_index = True,
                   right_index = True,
                   how = 'left')

## Inspect => pbm: clearly large cities... do some by hand in csv
#print df_info[['name', 'adr_street', 'adr_city', 'brand_0']]\
#             [df_info['zag_id'].isnull()][0:100].to_string()
#print df_info['ci_1'][df_info['zag_id'].isnull()].value_counts()[0:10]
#print df_info['ci_1'][df_info['zag_id'].isnull()].value_counts()[0:20]

df_nomatch = df_info[df_info['zag_id'].isnull()].copy()
## Temp: check why here (fully empty: can drop?)
#df_nomatch = df_nomatch[df_nomatch.index != '34500021']
df_nomatch['nb_ci'] = df_nomatch.groupby('ci_1')['ci_1'].transform(len)
df_nomatch.sort(['nb_ci', 'brand_0'], ascending = False, inplace = True)


df_fix = pd.read_csv(os.path.join(path_dir_zagaz_csv,
                                  'fix_matching.csv'),
                               sep = ';',
                               dtype = {'id_station' : str,
                                        'fixed_zag_id' : str},
                               encoding = 'latin-1')

# print len(df_fix[~df_fix['fixed_zag_id'].isnull()])

# check for conflicts with current match file
ls_conflicts = []
for zag_id in df_fix['fixed_zag_id'].values:
  if zag_id in df_info['zag_id'].values:
    ls_conflicts.append(zag_id)

lsdm = ['name', 'adr_street', 'adr_city', 'adr_zip',
        'ci_1', 'brand_0', 'brand_1', 'zag_id']

print u'\nConflicts: from original matching:'
print df_info[lsdm][df_info['zag_id'].isin(ls_conflicts)].to_string()

print u'\nConflicts: matching by hand:'
print df_fix[lsdm[:-1] + ['fixed_zag_id']]\
            [df_fix['fixed_zag_id'].isin(ls_conflicts)].to_string()

print u'\nConflicts: zagaz:'
print df_zagaz.ix[ls_conflicts]\
                 [['name', 'street', 'zip', 'municipality',
                   'ci', 'brand_2012', 'brand_2013']].to_string()


## todo: update so previous info is saved
#
#lsdnm = ['name', 'adr_street', 'adr_city', 'adr_zip',
#        'ci_1', 'brand_0', 'brand_1', 'nb_ci']
#df_nomatch[lsdnm].to_csv(os.path.join(path_dir_zagaz_csv,
#                                     'fix_matching.csv'),
#                         index_label = 'id_station',
#                         encoding = 'latin-1',
#                         sep = ';',
#                         quoting = 1) # no impact, cannot have trailing 0s
