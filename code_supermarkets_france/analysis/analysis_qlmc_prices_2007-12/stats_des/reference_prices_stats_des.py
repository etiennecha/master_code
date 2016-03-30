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

path_built = os.path.join(path_data,
                          'data_supermarkets',
                          'data_built',
                          'data_qlmc_2007-12')

path_built_csv = os.path.join(path_built,
                              'data_csv')

pd.set_option('float_format', '{:,.2f}'.format)

# #######################
# LOAD DATA
# #######################

# LOAD DF QLMC
df_qlmc = pd.read_csv(os.path.join(path_built_csv,
                                   'df_qlmc.csv'),
                      parse_dates = ['date'],
                      dayfirst = True,
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
                 ('CHAMPION', 'CARREFOUR MARKET')]
for sc_old, sc_new in ls_sc_replace:
  df_qlmc.loc[df_qlmc['store_chain'] == sc_old,
              'store_chain'] = sc_new

# #############################################
# PRICE DISTRIBUTION PER CHAIN FOR TOP PRODUCTS
# #############################################

PD = PriceDispersion()

se_prod = df_qlmc.groupby(['section', 'family', 'product']).agg('size')
se_prod.sort(ascending = False, inplace = True)

store_chain = 'CARREFOUR' # 'CENTRE E.LECLERC'
nb_obs_min = 20 # Product must be observed at X stores at least
pct_min = 0.33

print('Stats des on ref prices for {:s} :'.format(store_chain))

for per_ind in range(13):
  print()
  print(u'-'*80)
  print(u'Period {:d}'.format(per_ind))
  # How close stores are to reference price
  df_sub = df_qlmc[(df_qlmc['period'] == per_ind) &\
                   (df_qlmc['store_chain'] == store_chain)]
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
  # kurtosis and skew: div by 0 (only one price)
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

  if len(df_enough_obs) > 0:
   
    print()
    print(u'Overview at product level')
    print(df_enough_obs.describe().to_string())
    
    print(u'Nb prod w/ >= {:d} obs: {:d}'.format(\
            nb_obs_min, len(df_enough_obs)))
    
    print(u'Nb prod w/ >= {:d} obs and ref price (0.33): {:d}'.format(\
            nb_obs_min, len(df_ref_price)))
                
    print(u'Pct prod w/ >= 20 obs and ref price (0.33): {:.2f}'.format(\
            nb_obs_min, len(df_ref_price) / float(len(df_enough_obs))))
    
    df_sub = pd.merge(df_sub,
                      df_enough_obs,
                      on = ['section', 'family', 'product'],
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
      # drop if not enough data (but should report ?)
      se_nb_tot_obs = df_ref.sum(axis = 1).astype(int)
      #se_insuff = df_ref['insuff'] / df_ref.sum(axis = 1)
      #df_ref.drop(labels = ['insuff'], axis = 1, inplace = True)
      
      df_ref_pct = df_ref.apply(lambda x: x / x.sum(), axis = 1)
      df_ref_pct['nb_obs'] = df_ref.sum(axis = 1).astype(int)
      df_ref_pct['nb_tot_obs'] = se_nb_tot_obs
      #df_ref_pct['insuff'] = se_insuff
      
      #print u'\nOverview ref prices:'
      #print df_ref.to_string()
     
      print()
      print(u'Overview at store level:')
      print(df_ref_pct[['nb_tot_obs', # 'insuff',
                        'nb_obs',
                        'no_ref',
                        'diff',
                        'price_1',
                        'price_2']].describe().to_string())
    except:
      print(u'Not enough data to display store ref prices')

# print df_qlmc['Enseigne_alt'].value_counts()
