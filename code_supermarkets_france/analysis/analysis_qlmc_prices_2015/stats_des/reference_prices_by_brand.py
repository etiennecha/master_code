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

# store chain harmonization per qlmc
ls_replace_chains = [['HYPER CASINO', 'CASINO'],
                     ['HYPER U', 'SUPER U'],
                     ['U EXPRESS', 'SUPER U'],
                     ["LES HALLES D'AUCHAN", 'AUCHAN']]
for old_chain, new_chain in ls_replace_chains:
  df_prices.loc[df_prices['store_chain'] == old_chain,
                'store_chain'] = new_chain
# does not chge much to include only super-u or hyper-u

# adhoc fixes
ls_suspicious_prods = [u'VIVA LAIT TGV 1/2 ÉCRÉMÉ VIVA BP 6X50CL']
df_prices = df_prices[~df_prices['product'].isin(ls_suspicious_prods)]
df_prices['product'] =\
  df_prices['product'].apply(lambda x: x.replace(u'\x8c', u'OE'))

df_qlmc = df_prices

# Robustness check: 2000 most detained products only
ls_prod_cols = ['section', 'family', 'product']
se_prod_vc = df_prices[ls_prod_cols].groupby(ls_prod_cols).agg(len)
ls_keep_products = [x[-1] for x in list(se_prod_vc[0:3000].index)]
df_qlmc = df_qlmc[df_qlmc['product'].isin(ls_keep_products)]

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

nb_obs_min = 40 # Product must be observed at X stores at least
pct_min = 0.33

ls_loop_rcs = ['AUCHAN',
               'CARREFOUR',
               'CARREFOUR MARKET',
               'GEANT CASINO',
               'CASINO',
               'CORA',
               'INTERMARCHE',
               'LECLERC',
               'SIMPLY MARKET',
               'SUPER U']

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

  print()
  print('Stats des on ref prices for {:s} :'.format(retail_chain))
  # Build df with product most common prices
  df_sub = df_qlmc[(df_qlmc['store_chain'] == retail_chain)]
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
  
  if len(df_enough_obs) >= 100:
    
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
      dict_df_chain_store_desc[retail_chain] = df_ref_pct

    except:
      print()
      print(u'Not enough data to display store ref prices')
      for col in ['nb_prods_by_store', 'no_ref', 'freq_stores']:
        dict_ls_se_desc[col].append(None)
  else:
    for col in ['nb_stores_by_prod', 'freq_prods',
                'nb_prods_by_store', 'no_ref', 'freq_stores']:
      dict_ls_se_desc[col].append(None)

dict_df_desc = {k: pd.concat(v, axis = 1, keys = ls_loop_rcs)\
                   for k, v in dict_ls_se_desc.items()}

dict_ens_alt_replace = {'CENTRE E.LECLERC' : 'LECLERC',
                        'INTERMARCHE SUPER' : 'ITM SUP',
                        'INTERMARCHE HYPER' : 'ITM HYP',
                        'CARREFOUR MARKET' : 'CAR. MARKET',
                        'SIMPLY MARKET' : 'SIMPLY'}

dict_df_desc = {k: v.rename(columns = dict_ens_alt_replace)\
                   for k,v in dict_df_desc.items()}

print()
print('freq_prods: frequency of the most common price')
print('no_ref: percentage of products in store with no brand ref price (33%...)')
print('freq_stores: percentage of products in store which follow brand ref price')

lsd_su = ['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max']
for x in ['nb_prods_by_store', 'nb_stores_by_prod', 'freq_prods', 'no_ref', 'freq_stores']:
  print()
  print(x)
  print(dict_df_desc[x].ix[lsd_su].T.to_string(float_format = '{:,.2f}'.format))

#print()
#print('Check price stats by chain at store level')
#for x in ['CENTRE E.LECLERC', 'AUCHAN', 'CARREFOUR', 'GEANT CASINO']:
#  print()
#  print(dict_df_chain_store_desc[x][0:20].to_string())

# check ITM and LECLERC: freq_stores == 1 !!! which ones?

df_chain_store_su = dict_df_chain_store_desc['SUPER U'].copy()
df_chain_store_su.sort('price_1', ascending = False, inplace = True)
