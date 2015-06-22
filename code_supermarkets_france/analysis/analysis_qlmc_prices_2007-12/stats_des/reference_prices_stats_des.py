#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

path_dir_qlmc = os.path.join(path_data, 'data_qlmc')
path_dir_built_csv = os.path.join(path_dir_qlmc, 'data_built' , 'data_csv')
#path_dir_built_hdf5 = os.path.join(path_dir_qlmc, 'data_built', 'data_hdf5')

pd.set_option('float_format', '{:,.2f}'.format)

# #######################
# BUILD DF QLMC
# ####################### 

# LOAD DF PRICES
print u'Loading qlmc prices'
# date parsing slow... better if specified format?
df_qlmc = pd.read_csv(os.path.join(path_dir_built_csv,
                                   'df_qlmc_prices.csv'),
                      encoding = 'utf-8')

# LOAD DF STORES
print u'Loading qlmc stores (inc. LSA id)'
df_stores = pd.read_csv(os.path.join(path_dir_built_csv,
                                     'df_qlmc_stores.csv'),
                        dtype = {'id_lsa': str,
                                 'INSE_ZIP' : str,
                                 'INSEE_Dpt' : str,
                                 'INSEE_Code' : str,
                                 'QLMC_Dpt' : str},
                        encoding = 'UTF-8')
df_stores['Magasin'] = df_stores['Enseigne'] + u' ' + df_stores['Commune']
df_stores = df_stores[['P', 'Magasin', 'Enseigne', 'id_lsa',
                       'INSEE_Code', 'INSEE_Commune']]

df_stores.rename(columns = {'Enseigne' : 'Enseigne_QLMC'},
                 inplace = True)

# LOAD DF LSA
df_lsa = pd.read_csv(os.path.join(path_dir_built_csv,
                                  'df_lsa_active_fm_hsx.csv'),
                     dtype = {u'Ident': str,
                              u'Code INSEE' : str,
                              u'Code INSEE ardt' : str,
                              u'N°Siren' : str,
                              u'N°Siret' : str},
                     parse_dates = [u'DATE ouv', u'DATE ferm', u'DATE réouv',
                                    u'DATE chg enseigne', u'DATE chgt surf'],
                     encoding = 'UTF-8')

df_lsa.rename(columns = {u'Ident': 'id_lsa',
                         u'Surf Vente' : 'Surface',
                         u'Nbr de caisses' : u'Nb_checkouts',
                         u'Nbr emp' : 'Nb_emp',
                         u'Nbr parking' : 'Nb_parking',
                         u'Intégré / Indépendant' : u'Indpt'},
               inplace = True)

df_stores = pd.merge(df_stores,
                     df_lsa,
                     on = 'id_lsa',
                     how = 'left')

df_qlmc = pd.merge(df_qlmc,
                   df_stores,
                   on = ['P', 'Magasin'],
                   how = 'left')

# high memory usage..

# get rid of no id_lsa match
df_qlmc = df_qlmc[~df_qlmc['id_lsa'].isnull()]
# get rid of closed (so far but should accomodate later)
df_qlmc = df_qlmc[~df_qlmc['Enseigne_alt'].isnull()]

# Avoid error msg on condition number
df_qlmc['Surface'] = df_qlmc['Surface'].apply(lambda x: x/1000.0)
# df_qlmc_prod['ac_hhi'] = df_qlmc_prod['ac_hhi'] * 10000
# Try with log of price (semi elasticity)
df_qlmc['ln_Prix'] = np.log(df_qlmc['Prix'])
# Control for dpt (region?)
df_qlmc['Dpt'] = df_qlmc['INSEE_Code'].str.slice(stop = 2)

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

se_prod = df_qlmc.groupby(['Rayon', 'Famille', 'Produit']).agg('size')
se_prod.sort(ascending = False, inplace = True)

# retail_chain = 'CARREFOUR'
retail_chain = 'CARREFOUR' # 'GEANT CASINO'
nb_obs_min = 10
pct_min = 0.33

print '\nStats des on ref prices for {:s} :'.format(retail_chain)

for per_ind in range(13):
  print u'\n' + '-'*80
  print u'Period {:d}'.format(per_ind)
  # How close stores are to reference price
  df_sub = df_qlmc[(df_qlmc['P'] == per_ind) &\
                   (df_qlmc['Enseigne_alt'] == retail_chain)]
  
  # Check duplicates at store level
  ls_sub_dup_cols = ['Rayon', 'Famille', 'Produit', 'id_lsa']
  df_sub_dup = df_sub[(df_sub.duplicated(ls_sub_dup_cols, take_last = True)) |\
                      (df_sub.duplicated(ls_sub_dup_cols, take_last = False))]
  # Make sure no duplicate
  df_sub = df_sub.drop_duplicates(ls_sub_dup_cols)
  
  # Build df with product most common prices
  df_sub_products =  df_sub[['Rayon', 'Famille', 'Produit', 'Prix']]\
                       .groupby(['Rayon', 'Famille', 'Produit'])\
                       .agg([nb_obs,
                             price_1,
                             price_1_freq,
                             price_2,
                             price_2_freq])['Prix']
  
  df_sub_products['price_12_freq'] =\
    df_sub_products[['price_1_freq', 'price_2_freq']].sum(axis = 1)
  
  print u'\nOverview products:'
  print df_sub_products.describe()
  
  df_enough_obs = df_sub_products[(df_sub_products['nb_obs'] >= nb_obs_min)]
  df_ref_price = df_sub_products[(df_sub_products['nb_obs'] >= nb_obs_min) &\
                                 (df_sub_products['price_1_freq'] >= pct_min)]

  if len(df_enough_obs) > 0:
    
    print u'Nb prod w/ >= {:d} obs: {:d}'.format(\
            nb_obs_min, len(df_enough_obs))
    
    print u'Nb prod w/ >= {:d} obs and no ref price (0.33): {:d}'.format(\
            nb_obs_min, len(df_ref_price))
                
    print u'Pct prod w/ >= 20 obs and no ref price (0.33): {:.2f}'.format(\
            nb_obs_min, len(df_ref_price) / float(len(df_enough_obs)))
    
    df_sub_products.reset_index(drop = False, inplace = True)
    
    df_sub = pd.merge(df_sub,
                      df_sub_products,
                      on = ['Rayon', 'Famille', 'Produit'],
                      how = 'left')
    
    # Build df stores accounting for match with ref prices
    
    ## With dummy
    #df_sub['ref_price_dum'] = 0
    #df_sub.loc[df_sub['Prix'] == df_sub['price_1'],
    #           'ref_price_dum'] = 1
    ## Pbm Magasin can be slightly diff from id_lsa but...
    #df_ref = df_sub[['Magasin', 'ref_price_dum']]\
    #           .groupby('Magasin').agg([np.size,
    #                                    sum])
    #print df_ref[0:20].to_string()
    
    df_sub['ref_price'] = 'diff'
    df_sub.loc[df_sub['Prix'] == df_sub['price_1'],
               'ref_price'] = 'price_1'
    df_sub.loc[(df_sub['Prix'] != df_sub['price_1']) &\
               (df_sub['Prix'] == df_sub['price_2']),
               'ref_price'] = 'price_2'
    df_sub.loc[(df_sub['price_1_freq'] <= pct_min),
               'ref_price'] = 'no_ref'
    df_sub.loc[df_sub['nb_obs'] <= nb_obs_min,
               'ref_price'] = 'insuff'
    
    df_ref = pd.pivot_table(data = df_sub[['Magasin', 'ref_price']],
                            index = 'Magasin',
                            columns = 'ref_price',
                            aggfunc = len,
                            fill_value = 0).astype(int)
    
    try:
      # drop if not enough data (but should report ?)
      se_nb_tot_obs = df_ref.sum(axis = 1).astype(int)
      se_insuff = df_ref['insuff'] / df_ref.sum(axis = 1)
      df_ref.drop(labels = ['insuff'], axis = 1, inplace = True)
      
      df_ref_pct = df_ref.apply(lambda x: x / x.sum(), axis = 1)
      df_ref_pct['nb_obs'] = df_ref.sum(axis = 1).astype(int)
      df_ref_pct['nb_tot_obs'] = se_nb_tot_obs
      df_ref_pct['insuff'] = se_insuff
      
      #print u'\nOverview ref prices:'
      #print df_ref.to_string()
      
      print u'\nOverview ref prices:'
      print df_ref_pct[['nb_tot_obs',
                        'insuff',
                        'nb_obs',
                        'no_ref',
                        'diff',
                        'price_1',
                        'price_2']].describe()
    except:
      print u'\nNot enough data to display store ref prices'

# print df_qlmc['Enseigne_alt'].value_counts()
