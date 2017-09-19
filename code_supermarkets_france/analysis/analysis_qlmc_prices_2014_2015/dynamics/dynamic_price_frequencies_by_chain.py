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

path_built = os.path.join(path_data, 'data_supermarkets', 'data_built')
path_built_csv = os.path.join(path_built, 'data_qlmc_2014_2015', 'data_csv')

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# ###########
# LOAD DATA
# ###########

ls_periods = ['201405', '201409']
period = ls_periods[0]
df_qlmc = pd.read_csv(os.path.join(path_built_csv, 'df_qlmc_{:s}.csv'.format(period)),
                      dtype = {'ean' : str,
                               'id_lsa' : str}, # to update soon
                      encoding = 'utf-8')

# store chain harmonization per qlmc
ls_replace_chains = [['HYPER CASINO', 'CASINO'],
                     ['HYPER U', 'SUPER U'],
                     ['U EXPRESS', 'SUPER U'],
                     ["LES HALLES D'AUCHAN", 'AUCHAN'],
                     ['INTERMARCHE SUPER', 'INTERMARCHE'],
                     ['INTERMARCHE HYPER', 'INTERMARCHE'], # any?
                     ['MARKET', 'CARREFOUR MARKET'],
                     ['CENTRE E.LECLERC', 'LECLERC']]

for old_chain, new_chain in ls_replace_chains:
  df_qlmc.loc[df_qlmc['store_chain'] == old_chain,
              'store_chain'] = new_chain
# does not chge much to include only super-u or hyper-u

ls_prod_cols = ['ean', 'product']
ls_store_cols = ['id_lsa', 'store_name']

# Robustness check: 2000 most detained products only
se_prod_vc = df_qlmc[ls_prod_cols].groupby(ls_prod_cols).agg(len)
ls_keep_products = [x[-1] for x in list(se_prod_vc[0:3000].index)]
df_qlmc = df_qlmc[df_qlmc[ls_prod_cols[-1]].isin(ls_keep_products)]

# #############################################
# PRICE DISTRIBUTION PER CHAIN FOR TOP PRODUCTS
# #############################################

PD = PriceDispersion()

nb_obs_min = 40 # Product must be observed at X stores at least
pct_min = 0.33 # Ref price is share by X% of stores only (else no ref)

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

dict_df_chain_product_stats = {}
dict_df_chain_store_desc = {}

for retail_chain in ls_loop_rcs:
  print()
  print(u'-'*60)
  print(retail_chain)

  print()
  print('Stats des on ref prices for {:s} :'.format(retail_chain))
  # Build df with product most common prices
  df_sub = df_qlmc[(df_qlmc['store_chain'] == retail_chain)]
  df_sub_products =  (df_sub[ls_prod_cols + ['price']]
                        .groupby(ls_prod_cols)
                        .agg([len,
                              'mean',
                              PD.kurtosis,
                              PD.skew,
                              PD.price_1,
                              PD.price_1_fq,
                              PD.price_2,
                              PD.price_2_fq])['price'])
  df_sub_products.columns = [col.replace('PD.', '') for col in df_sub_products.columns]
  df_sub_products.rename(columns = {'len': 'nb_obs'}, inplace = True)
  df_sub_products['price_12_fq'] = df_sub_products[['price_1_fq', 'price_2_fq']].sum(axis = 1)
  # kurtosis and skew: div by 0 (only one price)
  # fix (a priori highly degenerate hence not normal)
  df_sub_products.loc[df_sub_products['kurtosis'].abs() >= 1000,
                      'kurtosis'] = np.nan
  df_sub_products.loc[df_sub_products['skew'].abs() >= 1000,
                      'skew'] = np.nan
  df_sub_products.reset_index(drop = False, inplace = True)
  
  # Keep only products observed at enough stores
  df_enough_obs = df_sub_products[(df_sub_products['nb_obs'] >= nb_obs_min)]
  df_ref_price = (df_sub_products[(df_sub_products['nb_obs'] >= nb_obs_min) &
                                  (df_sub_products['price_1_fq'] >= pct_min)])
  dict_df_chain_product_stats[retail_chain] = df_enough_obs
  
  if len(df_enough_obs) >= 100:
    
    print(u'Overview at product level')
    print(df_enough_obs.describe().to_string())
    
    df_enough_obs_desc = df_enough_obs.describe()
    dict_ls_se_desc['nb_stores_by_prod'].append(df_enough_obs_desc['nb_obs'])
    dict_ls_se_desc['freq_prods'].append(df_enough_obs_desc['price_1_fq'])

    print(u'Nb prod w/ >= {:d} obs: {:d}'.format(
            nb_obs_min,
            len(df_enough_obs)))
    
    print(u'Nb prod w/ >= {:d} obs and ref price (33%+): {:d} ({:.0f}%)'.format(
            nb_obs_min,
            len(df_ref_price), 
            len(df_ref_price) / float(len(df_enough_obs)) * 100))
    
    # df_enough_obs.reset_index(drop = False, inplace = True)
    
    df_sub = pd.merge(df_sub,
                      df_enough_obs,
                      on = ls_prod_cols,
                      how = 'left')
    
    # Build df stores accounting for match with ref prices
    df_sub['ref_price'] = 'diff'
    df_sub.loc[df_sub['price'] == df_sub['price_1'], 'ref_price'] = 'price_1'
    df_sub.loc[(df_sub['price'] != df_sub['price_1']) &
               (df_sub['price'] == df_sub['price_2']), 'ref_price'] = 'price_2'
    df_sub.loc[(df_sub['price_1_fq'] <= pct_min), 'ref_price'] = 'no_ref'
    
    df_ref = pd.pivot_table(data = df_sub[ls_store_cols + ['ref_price']],
                            index = ls_store_cols,
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
      df_ref_pct.sort_values('price_1', ascending = False, inplace = True)
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

dict_df_desc = {k: v.rename(columns = dict_ens_alt_replace) for k,v in dict_df_desc.items()}

# ###########################
# STATS DES BY RETAIL CHAIN
# ###########################

print()
print(u'-'*60)
print(u'Stats by retail chain')
print()
print(u'freq_prods: frequency of the most common price')
print(u'no_ref: percentage of products in store with no brand ref price (33%...)')
print(u'freq_stores: percentage of products in store which follow brand ref price')

lsd_su = ['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max']
for x in ['nb_prods_by_store', 'nb_stores_by_prod', 'no_ref', 'freq_prods', 'freq_stores']:
  print()
  print(x)
  print(dict_df_desc[x].ix[lsd_su].T.to_string(float_format = '{:,.2f}'.format))

#print()
#print('Check price stats by chain at store level')
#for x in ['CENTRE E.LECLERC', 'AUCHAN', 'CARREFOUR', 'GEANT CASINO']:
#  print()
#  print(dict_df_chain_store_desc[x][0:20].to_string())

# check ITM and LECLERC: freq_stores == 1 !!! which ones?

df_chain_store_su = dict_df_chain_store_desc['CARREFOUR'].copy()
df_chain_store_su.sort('price_1', ascending = False, inplace = True)

# ##############################################
# CHECK PRODUCT WITH TOP CONCENTRATION BY CHAIN
# #############################################

print()
print(u'-'*60)
print(u'Inspace products with most concentrated prices per chain')
for chain in dict_df_chain_product_stats.keys():
  df_chain = dict_df_chain_product_stats[chain].copy()
  print()
  print(chain)
  df_chain.sort('price_1_fq', ascending = False, inplace = True)
  print(df_chain[0:20].to_string())

# ############################################
# COMPARE LECLERC AND GEANT CASINO REF PRICES
# ############################################

df_gc = dict_df_chain_product_stats['GEANT CASINO'].copy()
df_lec = dict_df_chain_product_stats['LECLERC'].copy()

df_compa = pd.merge(df_gc,
                    df_lec,
                    on = ls_prod_cols,
                    suffixes = ('_gc', '_lec'),
                    how = 'inner')
df_compa['diff'] = df_compa['price_1_gc'] - df_compa['price_1_lec']
df_compa['diff_pct'] = ((df_compa['price_1_gc'] - df_compa['price_1_lec'])
                           * 100 / df_compa['price_1_lec'])

lsd_compa = ls_prod_cols + ['price_1_gc', 'price_1_lec',
                            'price_1_fq_gc', 'price_1_fq_lec',
                            'diff', 'diff_pct']

print()
print(u'-'*60)
print(u'Compare Leclerc and Geant Casino baseline prices')
print()
print()
print(df_compa[lsd_compa].describe().to_string())

print()
print(df_compa[df_compa['price_1_fq_lec'] >= 0.33][lsd_compa].describe().to_string())

print()
print(u'Pct draws: {:.2f}'.format(len(df_compa[(df_compa['diff'].abs() <= 10e-4)]) /
                                  float(len(df_compa))* 100))
print(u'Pct LEC wins: {:.2f}'.format(len(df_compa[(df_compa['diff'] > 10e-4)]) /
                                  float(len(df_compa))* 100))
print(u'Pct GC wins: {:.2f}'.format(len(df_compa[(df_compa['diff'] < -10e-4)]) /
                                  float(len(df_compa))* 100))

# todo: compare in both periods (and third i.e. 2015 if possible)

# ############################################
# OUTPUT
# ############################################

ls_df_chain_products = []
for chain in dict_df_chain_product_stats.keys():
  df_chain_products = dict_df_chain_product_stats[chain].copy()
  df_chain_products['store_chain'] = chain
  ls_df_chain_products.append(df_chain_products)
df_chain_products = pd.concat(ls_df_chain_products)
# dunno how to solve cleanly ('index' appears at concat step)
df_chain_products.drop('index', axis = 1, inplace = True)

ls_df_chain_stores = []
for chain in dict_df_chain_store_desc.keys():
  df_chain_stores = dict_df_chain_store_desc[chain].copy()
  df_chain_stores['store_chain'] = chain
  ls_df_chain_stores.append(df_chain_stores)
df_chain_stores = pd.concat(ls_df_chain_stores)
df_chain_stores.reset_index(drop = False, inplace = True)

df_chain_products.to_csv(os.path.join(path_built_csv,
                                      'df_chain_product_price_freq_{:s}.csv'.format(period)),
  encoding = 'utf-8',
  float_format='%.3f',
  index = False)

df_chain_stores.to_csv(os.path.join(path_built_csv,
                                    'df_chain_store_price_freq_{:s}.csv'.format(period)),
  encoding = 'utf-8',
  float_format='%.3f',
  index = False)
