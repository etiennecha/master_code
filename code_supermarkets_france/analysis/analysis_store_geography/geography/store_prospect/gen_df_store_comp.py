#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
from functions_geocoding import *

path_built = os.path.join(path_data,
                          'data_supermarkets',
                          'data_built',
                          'data_lsa')

path_built_csv = os.path.join(path_built,
                              'data_csv')
path_built_json = os.path.join(path_built,
                               'data_json')

pd.set_option('float_format', '{:10,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# ##############
# LOAD LSA data
# ##############

df_lsa = pd.read_csv(os.path.join(path_built_csv,
                                  'df_lsa_active_hsx.csv'),
                     dtype = {u'c_insee' : str,
                              u'c_insee_ardt' : str,
                              u'c_postal' : str,
                              u'c_siren' : str,
                              u'c_nic' : str,
                              u'c_siret' : str},
                     parse_dates = [u'date_ouv', u'date_fer', u'date_reouv',
                                    u'date_chg_enseigne', u'date_chg_surface'],
                     encoding = 'utf-8')

df_lsa = df_lsa[(~pd.isnull(df_lsa['latitude'])) &\
                (~pd.isnull(df_lsa['longitude']))].copy()

lsd0 = [u'enseigne',
        u'adresse1',
        u'c_postal',
        u'ville'] #, u'latitude', u'longitude']

# Type restriction
ls_h_and_s = [[['H'], ['H'], 25, 'H_v_H'],
              [['H'], ['H', 'X', 'S'], 25, 'H_v_all'],
              [['S'], ['H', 'X', 'S'], 10, 'S_v_all'],
              [['H', 'S'], ['H', 'X', 'S'], 10, 'HS_v_all_10km'],
              [['H', 'S'], ['H', 'X', 'S'], 20, 'HS_v_all_20km']]

dict_df_comp = {}
for type_store, type_comp, dist_comp, title in ls_h_and_s:
  df_lsa_type = df_lsa[(df_lsa['type_alt'].isin(type_store))].copy()
  
  # Competitors for one store
  
  ls_rows_des_comp = []
  for row_ind, row in df_lsa_type.iterrows():
    ## could actually keep reference store since using groupe surface only
    #df_lsa_sub_temp = df_lsa_sub[df_lsa_sub.index != row_ind].copy()
    df_lsa_sub_temp = df_lsa[df_lsa['type_alt'].isin(type_comp)].copy()
    df_lsa_sub_temp['lat'] = row['latitude']
    df_lsa_sub_temp['lng'] = row['longitude']
    df_lsa_sub_temp['dist'] = compute_distance_ar(df_lsa_sub_temp['latitude'],
                                                  df_lsa_sub_temp['longitude'],
                                                  df_lsa_sub_temp['lat'],
                                                  df_lsa_sub_temp['lng'])
    
    # CONTINUOUS
    df_lsa_sub_temp['wgtd_surface'] = np.exp(-df_lsa_sub_temp['dist']/10) *\
                                          df_lsa_sub_temp['surface']
    df_lsa_sub_temp_groupe = df_lsa_sub_temp[df_lsa_sub_temp['groupe'] == row['groupe']].copy()
    df_lsa_sub_temp_comp = df_lsa_sub_temp[df_lsa_sub_temp['groupe'] != row['groupe']].copy()
    
    # distance to closest comp / closest same groupe
    dist_cl_groupe =\
      df_lsa_sub_temp_groupe[df_lsa_sub_temp_groupe.index != row_ind]['dist'].min()
    dist_cl_comp = df_lsa_sub_temp_comp['dist'].min()

    # HHI (see below: not working if None group)
    store_share = row['surface'] / df_lsa_sub_temp['wgtd_surface'].sum()
    groupe_share = df_lsa_sub_temp_groupe['wgtd_surface'].sum() /\
                      df_lsa_sub_temp['wgtd_surface'].sum()
    df_hhi = df_lsa_sub_temp[['groupe',
                              'wgtd_surface']].groupby('groupe').agg([sum])['wgtd_surface']
    df_hhi['market_share'] = df_hhi['sum'] / df_hhi['sum'].sum()
    hhi = (df_hhi['market_share']**2).sum()
  
    # WITHIN RADIUS
    df_lsa_market = df_lsa_sub_temp[df_lsa_sub_temp['dist'] <= dist_comp].copy()
    df_lsa_market_groupe = df_lsa_market[df_lsa_market['groupe'] == row['groupe']].copy()
    df_lsa_market_comp = df_lsa_market[df_lsa_market['groupe'] != row['groupe']].copy()
    
    ac_nb_stores = len(df_lsa_market) - 1 # exclude reference store (even if no group)
    ac_nb_chains = len(df_lsa_market['groupe'].unique())
    ac_nb_comp = len(df_lsa_market_comp) # reference store already excluded (even if no group)

    ac_store_share = row['surface'] / df_lsa_market['surface'].sum()
    ac_groupe_share = df_lsa_market_groupe['surface'].sum() /\
                        df_lsa_market['surface'].sum()
    # HHI (see below: not working if None group)
    df_hhi = df_lsa_market[['groupe',
                            'surface']].groupby('groupe').agg([sum])['surface']
    df_hhi['market_share'] = df_hhi['sum'] / df_hhi['sum'].sum()
    ac_hhi = (df_hhi['market_share']**2).sum()
  
    ls_rows_des_comp.append((row_ind, dist_cl_groupe, dist_cl_comp,
                             store_share, groupe_share, hhi,
                             ac_nb_stores, ac_nb_chains, ac_nb_comp,
                             ac_store_share, ac_groupe_share, ac_hhi))
  
  df_des_comp = pd.DataFrame(ls_rows_des_comp,
                             columns = ['index', 'dist_cl_groupe', 'dist_cl_comp',
                                        'store_share', 'group_share', 'hhi',
                                        'ac_nb_stores', 'ac_nb_chains', 'ac_nb_comp',
                                        'ac_store_share', 'ac_group_share', 'ac_hhi'])
  df_des_comp.set_index('index', inplace = True)
  
  df_lsa_type = pd.merge(df_lsa_type,
                         df_des_comp,
                         how = 'left',
                         left_index = True,
                         right_index = True)
  
  df_lsa_type.sort(['c_insee_ardt', 'enseigne'], inplace = True)
  
  ls_comp_cols = ['dist_cl_comp', 'dist_cl_groupe',
                  'ac_nb_stores', 'ac_nb_chains', 'ac_nb_comp',
                  'ac_store_share', 'store_share',
                  'ac_group_share', 'group_share',
                  'ac_hhi', 'hhi']

  ls_disp_lsa_comp = lsd0 + ls_comp_cols

  print u'\n', title
  print df_lsa_type[ls_disp_lsa_comp][0:20].to_string()
  
  dict_df_comp[title] = df_lsa_type

  df_lsa_type[['id_lsa'] + ls_comp_cols]\
    .to_csv(os.path.join(path_built_csv,
                         '201407_competition',
                         'df_store_prospect_comp_%s.csv' %title),
            encoding = 'utf-8',
            float_format ='%.3f',
            index = False)

df_hs_1025 = pd.concat([dict_df_comp['H_v_all'],
                        dict_df_comp['S_v_all']],
                        axis = 0)

df_hs_1025[['id_lsa'] + ls_comp_cols]\
  .to_csv(os.path.join(path_built_csv,
                       '201407_competition',
                       'df_store_prospect_comp_HS_v_all_1025km.csv'),
          encoding = 'utf-8',
          float_format ='%.3f',
          index = False)

# Caution: dist_cl_groupe for small groups: very high
# Remedy(?): erase if Groupe != Groupe_Alt

## Caution: None is ignored by groupby
## Hence if None: need to replace w/ unique entries to compute HHI
#df_mkt = pd.DataFrame([['Carrouf', 100],
#                       ['Leclerc',  50],
#                       [None     ,  11],
#                       [None     ,   3]], columns = ['Groupe', 'Surface'])
#df_hhi_test = df_mkt[['Groupe', 'Surface']].groupby('Groupe').agg([sum])['Surface']
#df_hhi_test['market_share'] = df_hhi_test['sum'] / df_hhi_test['sum'].sum()
#print df_hhi_test.to_string()
