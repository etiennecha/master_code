#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
from functions_geocoding import *

path_dir_qlmc = os.path.join(path_data, 'data_qlmc')
path_dir_built_csv = os.path.join(path_dir_qlmc, 'data_built' , 'data_csv')
path_dir_built_png = os.path.join(path_dir_qlmc, 'data_built' , 'data_png')
path_dir_built_json = os.path.join(path_dir_qlmc, 'data_built' , 'data_json_qlmc')

pd.set_option('float_format', '{:10,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# ##############
# LOAD LSA data
# ##############

df_lsa = pd.read_csv(os.path.join(path_dir_built_csv,
                                  'df_lsa_active_fm_hsx.csv'),
                     dtype = {u'Code INSEE' : str,
                              u'Code INSEE ardt' : str,
                              u'N°Siren' : str,
                              u'N°Siret' : str},
                     parse_dates = [u'DATE ouv', u'DATE ferm', u'DATE réouv',
                                    u'DATE chg enseigne', u'DATE chgt surf'],
                     encoding = 'UTF-8')
df_lsa = df_lsa[(~pd.isnull(df_lsa['Latitude'])) &\
                (~pd.isnull(df_lsa['Longitude']))].copy()

ls_disp_lsa = [u'Enseigne',
               u'ADRESSE1',
               u'Code postal',
               u'Ville'] # u'Latitude', u'Longitude']

# Type restriction
ls_h_and_s = [['H', ['H'], 25, 'H_v_H'],
              ['H', ['H', 'X', 'S'], 25, 'H_v_all'],
              ['S', ['H', 'X', 'S'], 10, 'S_v_all']]

for type_store, type_comp, dist_comp, title in ls_h_and_s:
  df_lsa_type = df_lsa[df_lsa['Type_alt'] == type_store].copy()
  
  # Competitors for one store
  
  ls_rows_des_comp = []
  for row_ind, row in df_lsa_type.iterrows():
    ## could actually keep reference store since using groupe surface only
    #df_lsa_sub_temp = df_lsa_sub[df_lsa_sub.index != row_ind].copy()
    df_lsa_sub_temp = df_lsa[df_lsa['Type_alt'].isin(type_comp)].copy()
    df_lsa_sub_temp['lat'] = row['Latitude']
    df_lsa_sub_temp['lng'] = row['Longitude']
    df_lsa_sub_temp['dist'] = compute_distance_ar(df_lsa_sub_temp['Latitude'],
                                                  df_lsa_sub_temp['Longitude'],
                                                  df_lsa_sub_temp['lat'],
                                                  df_lsa_sub_temp['lng'])
    
    # CONTINUOUS
    df_lsa_sub_temp['Wgt Surf Vente'] = np.exp(-df_lsa_sub_temp['dist']/10) *\
                                          df_lsa_sub_temp['Surf Vente']
    df_lsa_sub_temp_groupe = df_lsa_sub_temp[df_lsa_sub_temp['Groupe'] == row['Groupe']].copy()
    df_lsa_sub_temp_comp = df_lsa_sub_temp[df_lsa_sub_temp['Groupe'] != row['Groupe']].copy()
    
    store_share = row['Surf Vente'] / df_lsa_sub_temp['Wgt Surf Vente'].sum()
    groupe_share = df_lsa_sub_temp_groupe['Wgt Surf Vente'].sum() /\
                      df_lsa_sub_temp['Wgt Surf Vente'].sum()
    # HHI (see below: not working if None group)
    df_hhi = df_lsa_sub_temp[['Groupe',
                              'Wgt Surf Vente']].groupby('Groupe').agg([sum])['Wgt Surf Vente']
    df_hhi['market_share'] = df_hhi['sum'] / df_hhi['sum'].sum()
    hhi = (df_hhi['market_share']**2).sum()
  
    # WITHIN RADIUS
    df_lsa_market = df_lsa_sub_temp[df_lsa_sub_temp['dist'] <= dist_comp].copy()
    df_lsa_market_groupe = df_lsa_market[df_lsa_market['Groupe'] == row['Groupe']].copy()
    df_lsa_market_comp = df_lsa_market[df_lsa_market['Groupe'] != row['Groupe']].copy()
    
    ac_nb_stores = len(df_lsa_market) - 1 # exclude reference store (even if no group)
    ac_nb_chains = len(df_lsa_market['Groupe'].unique())
    ac_nb_comp = len(df_lsa_market_comp) # reference store already excluded (even if no group)

    ac_store_share = row['Surf Vente'] / df_lsa_market['Surf Vente'].sum()
    ac_groupe_share = df_lsa_market_groupe['Surf Vente'].sum() /\
                        df_lsa_market['Surf Vente'].sum()
    # HHI (see below: not working if None group)
    df_hhi = df_lsa_market[['Groupe',
                            'Surf Vente']].groupby('Groupe').agg([sum])['Surf Vente']
    df_hhi['market_share'] = df_hhi['sum'] / df_hhi['sum'].sum()
    ac_hhi = (df_hhi['market_share']**2).sum()
  
    ls_rows_des_comp.append((row_ind, store_share, groupe_share, hhi,
                             ac_nb_stores, ac_nb_chains, ac_nb_comp,
                             ac_store_share, ac_groupe_share, ac_hhi))
  
  df_des_comp = pd.DataFrame(ls_rows_des_comp,
                              columns = ['index', 'store_share', 'group_share', 'hhi',
                                        'ac_nb_stores', 'ac_nb_chains', 'ac_nb_comp',
                                        'ac_store_share', 'ac_group_share', 'ac_hhi'])
  df_des_comp.set_index('index', inplace = True)
  
  df_lsa_type = pd.merge(df_lsa_type,
                         df_des_comp,
                         how = 'left',
                         left_index = True,
                         right_index = True)
  
  df_lsa_type.sort(['Code INSEE ardt', 'Enseigne'], inplace = True)
  
  ls_disp_lsa_comp = ls_disp_lsa + ['ac_nb_stores', 'ac_nb_chains', 'ac_nb_comp',
                                    'ac_store_share', 'store_share',
                                    'ac_group_share', 'group_share',
                                    'ac_hhi', 'hhi']

  print u'\n', title
  print df_lsa_type[ls_disp_lsa_comp][0:20].to_string()
  
  # temp: avoid error with dates before 1900 and strftime (when outputing to csv)
  df_lsa_type.loc[df_lsa_type[u'DATE ouv'] <= '1900', 'DATE ouv'] =\
     pd.to_datetime('1900/01/01', format = '%Y/%m/%d')

  df_lsa_type.to_csv(os.path.join(path_dir_built_csv,
                                  'df_eval_comp%s.csv' %title),
                     encoding = 'latin-1',
                     float_format ='%.3f',
                     date_format='%Y%m%d',
                     index = False)

## Test GroupBy with None => Caution, None ignored in groupby
## Hence need to fill with unique entries if None to get it working properly
#df_mkt = pd.DataFrame([['Carrouf', 100],
#                       ['Leclerc',  50],
#                       [None     ,  11],
#                       [None     ,   3]], columns = ['Groupe', 'Surf Vente'])
#df_hhi_test = df_mkt[['Groupe', 'Surf Vente']].groupby('Groupe').agg([sum])['Surf Vente']
#df_hhi_test['market_share'] = df_hhi_test['sum'] / df_hhi_test['sum'].sum()
#print df_hhi_test.to_string()
