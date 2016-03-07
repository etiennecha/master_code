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

path_built_csv = os.path.join(path_data,
                              'data_supermarkets',
                              'data_built',
                              'data_qlmc_2015',
                              'data_csv_201503')

path_lsa_csv = os.path.join(path_data,
                            'data_supermarkets',
                            'data_built',
                            'data_lsa',
                            'data_csv')

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# #######################
# LOAD DF QLMC
# #######################

# LOAD DF PRICES
df_prices = pd.read_csv(os.path.join(path_built_csv,
                                     'df_prices.csv'),
                        encoding = 'utf-8')

# LOAD DF STORES (INCLUDING LSA INFO)
df_stores = pd.read_csv(os.path.join(path_built_csv,
                                     'df_stores_final.csv'),
                        dtype = {'c_insee' : str,
                                 'id_lsa' : str},
                        encoding = 'utf-8')

df_lsa = pd.read_csv(os.path.join(path_lsa_csv,
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
                     encoding = 'utf-8')

df_stores = pd.merge(df_stores,
                     df_lsa[['id_lsa', 'enseigne_alt', 'groupe', 'surface']],
                     on = 'id_lsa',
                     how = 'left')

# BUILD DF QLMC WITH PRICE AND STORE INFO
df_prices.drop(['store_chain'], axis = 1, inplace = True) # in df_stores too...
df_qlmc = pd.merge(df_prices,
                   df_stores,
                   left_on = 'store_id',
                   right_on = 'store_id',
                   how = 'left')
df_qlmc = df_qlmc[~df_qlmc['id_lsa'].isnull()]

# Avoid error msg on condition number
df_qlmc['surface'] = df_qlmc['surface'].apply(lambda x: x/1000.0)
# df_qlmc_prod['ac_hhi'] = df_qlmc_prod['ac_hhi'] * 10000
# Try with log of price (semi elasticity)
df_qlmc['ln_price'] = np.log(df_qlmc['price'])
# Control for dpt (region?)
df_qlmc['dpt'] = df_qlmc['c_insee'].str.slice(stop = 2)

# #############################################
# PRICE DISTRIBUTION PER CHAIN FOR TOP PRODUCTS
# #############################################

def nb_obs(se_prices):
  return len(se_prices)

def price_1(se_prices):
  return se_prices.value_counts().index[0]

def price_1_freq(se_prices):
  return se_prices.value_counts().iloc[0] / float(len(se_prices))

def price_2(se_prices):
  if len(se_prices.value_counts()) > 1:
    return se_prices.value_counts().index[1]
  else:
    return np.nan

def price_2_freq(se_prices):
  if len(se_prices.value_counts()) > 1:
    return se_prices.value_counts().iloc[1] / float(len(se_prices))
  else:
    return 0

se_prod = df_qlmc.groupby(['section', 'family', 'product']).agg('size')
se_prod.sort(ascending = False, inplace = True)

ls_loop_rcs = ['CENTRE E.LECLERC',
               'INTERMARCHE SUPER',
               'CARREFOUR MARKET',
               'AUCHAN',
               'HYPER U',
               'INTERMARCHE HYPER',
               'CORA',
               'CARREFOUR',
               'GEANT CASINO']

dict_ls_se_desc = {'nb_stores_by_prod' : [],
                   'freq_prods' : [],
                   'nb_prods_by_store' : [],
                   'no_ref' : [],
                   'freq_stores' : []}

dict_df_chain_store_desc = {}

for retail_chain in ls_loop_rcs:
  print()
  print(u'-'*60)
  print(retail_chain)

  nb_obs_min = 50 # Product must be observed at X stores at least
  pct_min = 0.33
  
  print()
  print('Stats des on ref prices for {:s} :'.format(retail_chain))
  
  # How close stores are to reference price
  df_sub = df_qlmc[(df_qlmc['enseigne_alt'] == retail_chain)]
  # All brands together: few prods with ref price (restrict store size?)
  #df_sub = df_qlmc[(df_qlmc['period'] == per_ind)]
  
  # Check duplicates at store level
  ls_sub_dup_cols = ['section', 'family', 'product', 'id_lsa']
  df_sub_dup = df_sub[(df_sub.duplicated(ls_sub_dup_cols, take_last = True)) |\
                      (df_sub.duplicated(ls_sub_dup_cols, take_last = False))]
  # Make sure no duplicate
  df_sub = df_sub.drop_duplicates(ls_sub_dup_cols)
  
  # Build df with product most common prices
  df_sub_products =  df_sub[['section', 'family', 'product', 'price']]\
                       .groupby(['section', 'family', 'product'])\
                       .agg([nb_obs,
                             price_1,
                             price_1_freq,
                             price_2,
                             price_2_freq])['price']
  
  df_sub_products['price_12_freq'] =\
    df_sub_products[['price_1_freq', 'price_2_freq']].sum(axis = 1)
  
  # Keep only products observed at enough stores
  df_enough_obs = df_sub_products[(df_sub_products['nb_obs'] >= nb_obs_min)]
  df_ref_price = df_sub_products[(df_sub_products['nb_obs'] >= nb_obs_min) &\
                                 (df_sub_products['price_1_freq'] >= pct_min)]
  
  
  if len(df_enough_obs) > 0:
    
    print(u'Overview at product level')
    print(df_enough_obs.describe())
    
    df_enough_obs_desc = df_enough_obs.describe()
    dict_ls_se_desc['nb_stores_by_prod'].append(df_enough_obs_desc['nb_obs'])
    dict_ls_se_desc['freq_prods'].append(df_enough_obs_desc['price_1_freq'])

    print(u'Nb prod w/ >= {:d} obs: {:d}'.format(\
            nb_obs_min, len(df_enough_obs)))
    
    print(u'Nb prod w/ >= {:d} obs and ref price (33%+): {:d} ({:.0f}%)'.format(\
            nb_obs_min,
            len(df_ref_price), 
            len(df_ref_price) / float(len(df_enough_obs)) * 100))
    
    df_enough_obs.reset_index(drop = False, inplace = True)
    
    df_sub = pd.merge(df_sub,
                      df_enough_obs,
                      on = ['section', 'family', 'product'],
                      how = 'left')
    
    # Build df stores accounting for match with ref prices
    
    ## With dummy
    #df_sub['ref_price_dum'] = 0
    #df_sub.loc[df_sub['price'] == df_sub['price_1'],
    #           'ref_price_dum'] = 1
    ## Pbm Store can be slightly diff from id_lsa but...
    #df_ref = df_sub[['store', 'ref_price_dum']]\
    #           .groupby('store').agg([np.size,
    #                                    sum])
    #print df_ref[0:20].to_string()
    
    df_sub['ref_price'] = 'diff'
    df_sub.loc[df_sub['price'] == df_sub['price_1'],
               'ref_price'] = 'price_1'
    df_sub.loc[(df_sub['price'] != df_sub['price_1']) &\
               (df_sub['price'] == df_sub['price_2']),
               'ref_price'] = 'price_2'
    df_sub.loc[(df_sub['price_1_freq'] <= pct_min),
               'ref_price'] = 'no_ref'
    #df_sub.loc[df_sub['nb_obs'] < nb_obs_min,
    #           'ref_price'] = 'insuff'
    
    df_ref = pd.pivot_table(data = df_sub[['store_id', 'ref_price']],
                            index = 'store_id',
                            columns = 'ref_price',
                            aggfunc = len,
                            fill_value = 0).astype(int)
    
    try:
      # drop if not enough data (but should report ?)
      se_nb_tot_obs = df_ref.sum(axis = 1).astype(int)
      #se_insuff = df_ref['insuff'] / df_ref.sum(axis = 1)
      #df_ref.drop(labels = ['insuff'], axis = 1, inplace = True)
      
      df_ref_pct = df_ref.apply(lambda x: x / x.sum(), axis = 1)
      df_ref_pct['nb_obs'] = df_ref.sum(axis = 1).astype(int)
      df_ref_pct['nb_tot_obs'] = se_nb_tot_obs
      #df_ref_pct['insuff'] = se_insuff
      if 'no_ref' not in df_ref_pct.columns:
        df_ref_pct['no_ref'] = 0
      
      #print()
      #print(u'Overview ref prices:')
      #print(df_ref.to_string())
      
      print()
      print(u'Overview at store level:')
      print(df_ref_pct[['nb_tot_obs', # 'insuff',
                        'nb_obs',
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
      dict_df_chain_store_desc[retail_chain] = df_ref_pct

    except:
      print()
      print(u'Not enough data to display store ref prices')
      for col in ['nb_prods_by_store', 'no_ref', 'freq_stores']:
        dict_ls_se_desc[col].append(None)
  else:
    for col in ['nb_prods_by_store', 'no_ref', 'freq_stores']:
      dict_ls_se_desc[col].append(None)

print()
print(df_qlmc['enseigne_alt'].value_counts())

dict_df_desc = {k: pd.concat(v, axis = 1, keys = ls_loop_rcs)\
                   for k, v in dict_ls_se_desc.items()}

dict_ens_alt_replace = {'CENTRE E.LECLERC' : 'LECLERC',
                        'INTERMARCHE SUPER' : 'ITM SUP',
                        'INTERMARCHE HYPER' : 'ITM HYP',
                        'CARREFOUR MARKET' : 'CAR. MARKET'}

dict_ds_desc = {k: v.rename(columns = dict_ens_alt_replace, inplace = True)\
                   for k,v in dict_df_desc.items()}

print()
print('Distributions of nb of prods by store and vice versa')
for x in ['nb_prods_by_store', 'nb_stores_by_prod']:
  print()
  print(x)
  print(dict_df_desc[x].to_string(float_format = '{:,.0f}'.format))

print()
print('freq_prods: frequency of the most common price')
print('no_ref: percentage of products in store with no brand ref price (33%...)')
print('freq_stores: percentage of products in store which follow brand ref price')
for x in ['freq_prods', 'no_ref', 'freq_stores']:
  print()
  print(x)
  print(dict_df_desc[x].to_string(float_format = '{:,.2f}'.format))

print()
print('Check price stats by chain at store level')

for x in ['CENTRE E.LECLERC', 'AUCHAN', 'CARREFOUR', 'GEANT CASINO']:
  print()
  print(dict_df_chain_store_desc[x][0:20].to_string())
