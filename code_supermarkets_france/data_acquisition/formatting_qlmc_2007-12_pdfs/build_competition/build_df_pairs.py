#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
import numpy as np
import pandas as pd

path_built = os.path.join(path_data,
                          'data_supermarkets',
                          'data_built',
                          'data_qlmc_2007-12')

path_built_csv = os.path.join(path_built,
                              'data_csv')

path_built_json = os.path.join(path_built,
                               'data_json')

path_built_lsa = os.path.join(path_data,
                                  'data_supermarkets',
                                  'data_built',
                                  'data_lsa')

path_built_csv_lsa = os.path.join(path_built_lsa,
                                  'data_csv')

# ################
# LOAD STORE DATA
##################

df_stores = pd.read_csv(os.path.join(path_built_csv,
                                     'df_stores.csv'),
                         encoding='utf-8')

df_lsa = pd.read_csv(os.path.join(path_built_csv_lsa,
                                  'df_lsa.csv'),
                     dtype = {u'C_INSEE' : str,
                              u'C_INSEE_Ardt' : str,
                              u'C_Postal' : str,
                              u'SIREN' : str,
                              u'NIC' : str,
                              u'SIRET' : str},
                     parse_dates = [u'Date_Ouv', u'Date_Fer', u'Date_Reouv',
                                    u'Date_Chg_Enseigne', u'Date_Chg_Surface'],
                     encoding = 'UTF-8')

# MERGE
df_stores = pd.merge(df_lsa[['Ident', 'Latitude', 'Longitude', 'Enseigne_Alt', 'Groupe']],
                     df_stores,
                     left_on = 'Ident',
                     right_on = 'id_lsa',
                     how = 'right')

df_stores.sort(['Period', 'Store'],
               ascending = True,
               inplace = True)

# drop stores non identified i.e. w/ no id_lsa
df_stores = df_stores[~df_stores['id_lsa'].isnull()]
# check no duplicate (period, lsa_id) => should not be...
print u'\nCheck no duplicates (should be empty):'
print df_stores[df_stores.duplicated(['Period', 'id_lsa'])]
# drop in case there are...
df_stores = df_stores.drop_duplicates(['Period', 'id_lsa'])

# #####################
# GET CLOSE STORE PAIRS
# #####################

print '\nGetting list of qlmc close pairs:'
ls_close_pairs  = []
for Period in df_stores['Period'].drop_duplicates():
  df_stores_per = df_stores[df_stores['Period'] == Period]
  for row_i, row in df_stores_per.iterrows():
    ident, lat, lng = row[['Ident', 'Latitude', 'Longitude']].values
    # want list of unique pairs
    df_temp = df_stores_per.ix[row_i:][1:].copy() # [1:] to avoid itself
    df_temp['lat_temp'] = lat
    df_temp['lng_temp'] = lng
    df_temp['dist'] = compute_distance_ar(df_temp['Latitude'],
                                          df_temp['Longitude'],
                                          df_temp['lat_temp'],
                                          df_temp['lng_temp'])
    ls_close = df_temp[df_temp['dist'] <= 25][['Ident', 'dist']].values.tolist()
    ls_close_pairs += [[int(Period), ident, ident_close, dist]\
                             for (ident_close, dist) in ls_close]

df_close_pairs = pd.DataFrame(ls_close_pairs,
                              columns = ['Period', 'id_lsa_0', 'id_lsa_1', 'dist'])

dict_close_pairs = {}
for Period, ident, ident_close, dist in ls_close_pairs:
  dict_close_pairs.setdefault(ident, []).append([Period, ident_close, dist])
  dict_close_pairs.setdefault(ident_close, []).append([Period, ident, dist])


# ################################
# ADD Store AND Store_Chain IN DF
# ################################

# todo: take Enseigne_Alt / Groupe at the right period
# suffix works only with redundant columns

df_stores = df_stores[['Period', 'Store', 'Store_Chain', 'Store_Municipality',
                       'id_lsa', 'Enseigne_Alt', 'Groupe']]
df_stores.columns = ['{:s}_0'.format(x) if x != 'Period' else x for x in df_stores.columns]

df_close_pairs = pd.merge(df_close_pairs,
                          df_stores,
                          on = ['Period', 'id_lsa_0'],
                          how = 'left')

df_stores.columns = [x.replace('0', '1') for x in df_stores.columns]

df_close_pairs = pd.merge(df_close_pairs,
                          df_stores,
                          on = ['Period', 'id_lsa_1'],
                          how = 'left')

# #############################################
# GET COMP STORE PAIRS & SAME CHAIN STORE PAIRS
# #############################################

df_comp_pairs = df_close_pairs[df_close_pairs['Groupe_0'] !=\
                               df_close_pairs['Groupe_1']]

df_same_pairs = df_close_pairs[df_close_pairs['Groupe_0'] ==\
                               df_close_pairs['Groupe_1']]

# May wish to add Surface

# #############
# OUTPUT
# #############

df_close_pairs.to_csv(os.path.join(path_built_csv,
                                   'df_close_store_pairs.csv'),
                      encoding = 'utf-8',
                      index = False)

df_comp_pairs.to_csv(os.path.join(path_built_csv,
                                  'df_comp_store_pairs.csv'),
                      encoding = 'utf-8',
                      index = False)

df_same_pairs.to_csv(os.path.join(path_built_csv,
                                  'df_same_chain_store_pairs.csv'),
                      encoding = 'utf-8',
                      index = False)

#enc_json(ls_close_pairs, os.path.join(path_dir_built_json,
#                                      'ls_close_pairs.json'))

#enc_json(dict_close_pairs, os.path.join(path_dir_built_json,
#                                 'dict_close_pairs.json'))
