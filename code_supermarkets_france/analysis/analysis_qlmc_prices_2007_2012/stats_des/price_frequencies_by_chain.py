#!/usr/bin/env python
# -*- coding: utf-8 -*- 

from __future__ import print_function
import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

pd.set_option('float_format', '{:,.2f}'.format)

path_built_csv = os.path.join(path_data, 'data_supermarkets', 'data_built',
                              'data_qlmc_2007_2012', 'data_csv')

# #######################
# LOAD DATA
# #######################

# LOAD DF QLMC
df_qlmc = pd.read_csv(os.path.join(path_built_csv, 'df_qlmc.csv'),
                      parse_dates = ['date'],
                      dayfirst = True,
                      infer_datetime_format = True,
                      encoding = 'utf-8')

# Fix Store_Chain for prelim stats des
ls_sc_drop = ['CARREFOUR CITY',
              'CARREFOUR CONTACT',
              'CARREFOUR PLANET',
              'GEANT DISCOUNT',
              'HYPER CHAMPION',
              'INTERMARCHE HYPER',
              'LECLERC EXPRESS',
              'MARCHE U',
              'U EXPRESS']

df_qlmc = df_qlmc[~df_qlmc['store_chain'].isin(ls_sc_drop)]

ls_sc_replace = [('CENTRE E. LECLERC', 'LECLERC'),
                 ('CENTRE LECLERC', 'LECLERC'),
                 ('E. LECLERC', 'LECLERC'),
                 ('E.LECLERC', 'LECLERC'),
                 ('SYSTEME U', 'SUPER U'),
                 ('GEANT', 'GEANT CASINO'),
                 ('CHAMPION', 'CARREFOUR MARKET'),
                 ('INTERMARCHE SUPER', 'INTERMARCHE'),
                 ('HYPER U', 'SUPER U')]
for sc_old, sc_new in ls_sc_replace:
  df_qlmc.loc[df_qlmc['store_chain'] == sc_old,
              'store_chain'] = sc_new

# #############################################
# PRICE DISTRIBUTION PER CHAIN FOR TOP PRODUCTS
# #############################################

PD = PriceDispersion()

ls_prod_cols = ['section', 'family', 'product']

store_chain = 'CARREFOUR' # 'CENTRE E.LECLERC'
nb_obs_min = 20 # Product must be observed at X stores at least
pct_min = 0.33

ls_loop_scs = ['AUCHAN',
               'CARREFOUR',
               'CARREFOUR MARKET',
               'GEANT CASINO', # no CASINO
               'CORA',
               'INTERMARCHE',
               'LECLERC',
               'SUPER U']

ls_dict_df_desc = []
ls_dict_df_chain_product_stats = []
ls_dict_df_chain_store_desc = []

for per in range(13):
  df_qlmc_per = df_qlmc[df_qlmc['period'] == per]
  dict_ls_se_desc = {'nb_stores_by_prod' : [],
                     'freq_prods' : [],
                     'nb_prods_by_store' : [],
                     'no_ref' : [],
                     'freq_stores' : []}
  dict_df_chain_product_stats = {}
  dict_df_chain_store_desc = {}
  
  print()
  print(u'-'*80)
  print('Stats on chain prices for period:', per)

  for store_chain in ls_loop_scs:
    print()
    print(u'-'*60)
    print(store_chain)
    # Build df with product most common prices
    df_sub = df_qlmc_per[df_qlmc_per['store_chain'] == store_chain]
    # Make sure no duplicates at store level
    ls_sub_dup_cols = ls_prod_cols + ['id_lsa']
    df_sub_dup = df_sub[(df_sub.duplicated(ls_sub_dup_cols, take_last = True)) |\
                        (df_sub.duplicated(ls_sub_dup_cols, take_last = False))]
    df_sub = df_sub.drop_duplicates(ls_sub_dup_cols)
    # Build df with product most common prices
    df_sub_products =  df_sub[ls_prod_cols + ['price']]\
                         .groupby(ls_prod_cols)\
                         .agg([len,
                               'mean',
                               PD.kurtosis,
                               PD.skew,
                               PD.price_1,
                               PD.price_1_fq,
                               PD.price_2,
                               PD.price_2_fq])['price']
    df_sub_products.columns = [col.replace('PD.', '') for col in df_sub_products.columns]
    df_sub_products.rename(columns = {'len': 'nb_obs'}, inplace = True)
    df_sub_products['price_12_fq'] =\
      df_sub_products[['price_1_fq', 'price_2_fq']].sum(axis = 1)
    # Pbm with kurtosis and skew: div by 0 (only one price)
    # fix (a priori highly degenerate hence not normal)
    df_sub_products.loc[df_sub_products['kurtosis'].abs() >= 1000,
                        'kurtosis'] = np.nan
    df_sub_products.loc[df_sub_products['skew'].abs() >= 1000,
                        'skew'] = np.nan
    df_sub_products.reset_index(drop = False, inplace = True)
    # Keep only products observed at enough stores
    df_enough_obs = df_sub_products[(df_sub_products['nb_obs'] >= nb_obs_min)]
    df_ref_price = df_sub_products[(df_sub_products['nb_obs'] >= nb_obs_min) &\
                                   (df_sub_products['price_1_fq'] >= pct_min)]
    # Save chain product stats
    dict_df_chain_product_stats[store_chain] = df_enough_obs
    
    # Define ref prices and get stats from store viewpoint
    if len(df_enough_obs) >= 100:
      
      print()
      print(u'Overview at product level')
      print(df_enough_obs.describe().to_string())
      
      df_enough_obs_desc = df_enough_obs.describe()
      dict_ls_se_desc['nb_stores_by_prod'].append(df_enough_obs_desc['nb_obs'])
      dict_ls_se_desc['freq_prods'].append(df_enough_obs_desc['price_1_fq'])
      
      print()
      print(u'Nb prod w/ >= {:d} obs: {:d}'.format(\
              nb_obs_min,
              len(df_enough_obs)))
      
      print(u'Nb prod w/ >= {:d} obs and ref price (33%+): {:d} ({:.0f}%)'.format(\
              nb_obs_min,
              len(df_ref_price), 
              len(df_ref_price) / float(len(df_enough_obs)) * 100))
      
      df_sub = pd.merge(df_sub,
                        df_enough_obs,
                        on = ls_prod_cols,
                        how = 'left')
        
      # Build df stores accounting for match with ref prices
      df_sub['ref_price'] = 'diff'
      df_sub.loc[df_sub['price'] == df_sub['price_1'],
                 'ref_price'] = 'price_1'
      df_sub.loc[(df_sub['price'] != df_sub['price_1']) &\
                 (df_sub['price'] == df_sub['price_2']),
                 'ref_price'] = 'price_2'
      df_sub.loc[(df_sub['price_1_fq'] <= pct_min),
                 'ref_price'] = 'no_ref'
      
      df_ref = pd.pivot_table(data = df_sub[['store', 'ref_price']],
                              index = 'store',
                              columns = 'ref_price',
                              aggfunc = len,
                              fill_value = 0).astype(int)
      
      try:
        df_ref_pct = df_ref.apply(lambda x: x / x.sum(), axis = 1)
        df_ref_pct['nb_obs'] = df_ref.sum(axis = 1).astype(int)
        if 'no_ref' not in df_ref_pct.columns:
          df_ref_pct['no_ref'] = 0
        # keep only stores with enough procucts
        df_ref_pct = df_ref_pct[df_ref_pct['nb_obs'] >= 100]

        print()
        print(u'Overview at store level:')
        print(df_ref_pct[['nb_obs',
                          'no_ref',
                          'diff',
                          'price_1',
                          'price_2']].describe())

        df_ref_pct_desc = df_ref_pct.describe()
        dict_ls_se_desc['nb_prods_by_store'].append(df_ref_pct_desc['nb_obs'])
        dict_ls_se_desc['no_ref'].append(df_ref_pct_desc['no_ref'])
        dict_ls_se_desc['freq_stores'].append(df_ref_pct_desc['price_1'])
        
        # also save store stats for each chain
        df_ref_pct.sort('price_1', ascending = False, inplace = True)
        dict_df_chain_store_desc[store_chain] = df_ref_pct

      except:
        print()
        print(u'Not enough data to display store ref prices')
        for col in ['nb_prods_by_store', 'no_ref', 'freq_stores']:
          dict_ls_se_desc[col].append(None)
    else:
      for col in ['nb_stores_by_prod', 'freq_prods',
                  'nb_prods_by_store', 'no_ref', 'freq_stores']:
        dict_ls_se_desc[col].append(None)

  dict_df_desc = {k: pd.concat(v, axis = 1, keys = ls_loop_scs)\
                     for k, v in dict_ls_se_desc.items()}
  
  dict_ens_alt_replace = {'CENTRE E.LECLERC' : 'LECLERC',
                          'INTERMARCHE SUPER' : 'ITM SUP',
                          'INTERMARCHE HYPER' : 'ITM HYP',
                          'CARREFOUR MARKET' : 'CAR. MARKET',
                          'SIMPLY MARKET' : 'SIMPLY'}
  
  dict_df_desc = {k: v.rename(columns = dict_ens_alt_replace)\
                     for k,v in dict_df_desc.items()}

  ls_dict_df_desc.append(dict_df_desc)
  ls_dict_df_chain_product_stats.append(dict_df_chain_product_stats)
  ls_dict_df_chain_store_desc.append(dict_df_chain_store_desc)

ls_loop_scs[2] = 'CAR. MARKET' # adhoc fix..

# Freq prods across period for one chain
dict_su_chains = {}
for var in ['freq_prods', 'freq_stores']:
  dict_su_chains[var] = {}
  for store_chain in ls_loop_scs:
    ls_se_temp = []
    for per, dict_df_desc_per in enumerate(ls_dict_df_desc):
      ls_se_temp.append(dict_df_desc_per[var].get(store_chain))
    df_chain_temp = pd.concat(ls_se_temp,
                              axis = 1,
                              keys = range(13))
    dict_su_chains[var][store_chain] = df_chain_temp

for var in ['freq_prods', 'freq_stores']:
  print()
  print(var)
  for k,v in dict_su_chains[var].items():
    print()
    print(k)
    print(v.to_string())
