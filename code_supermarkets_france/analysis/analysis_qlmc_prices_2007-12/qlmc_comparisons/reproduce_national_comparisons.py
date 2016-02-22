#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import *
import os, sys
import numpy as np
import pandas as pd
import timeit

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

path_built = os.path.join(path_data,
                        'data_supermarkets',
                        'data_built',
                        'data_qlmc_2007-12')

path_built_csv = os.path.join(path_built,
                              'data_csv')

# ####################
# LOAD DATA
# ####################

df_qlmc = pd.read_csv(os.path.join(path_built_csv,
                                   'df_qlmc.csv'),
                      encoding = 'utf-8')

# harmonize store chains according to qlmc
df_qlmc['store_chain_alt'] = df_qlmc['store_chain']
ls_sc_replace = [('CENTRE E. LECLERC', 'LECLERC'),
                 ('CENTRE LECLERC', 'LECLERC'),
                 ('E. LECLERC', 'LECLERC'),
                 ('E.LECLERC', 'LECLERC'),
                 ('LECLERC EXPRESS', 'LECLERC'),
                 ('INTERMARCHE HYPER', 'INTERMARCHE'),
                 ('INTERMARCHE SUPER', 'INTERMARCHE'),
                 ('SUPER U', 'SYSTEME U'),
                 ('HYPER U', 'SYSTEME U'),
                 ('U EXPRESS', 'SYSTEME U'),
                 ('MARCHE U', 'SYSTEME U'),
                 ('CARREFOUR PLANET', 'CARREFOUR'),
                 ('GEANT CASINO', 'GEANT'),
                 ('GEANT DISCOUNT', 'GEANT'),
                 ('CARREFOUR MARKET', 'CHAMPION'),
                 ('HYPER CHAMPION', 'CHAMPION'),
                 ('CARREFOUR CITY', 'CHAMPION'),
                 ('CARREFOUR CONTACT', 'CHAMPION')]
for sc_old, sc_new in ls_sc_replace:
  df_qlmc.loc[df_qlmc['store_chain'] == sc_old,
              'store_chain_alt'] = sc_new

# #########################
# REPRODUCE QLMC COMPARISON
# #########################

ls_df_res = []
for i in range(0, 13):
  
  # Restrict to period
  print ''
  print 'Period {:d}'.format(i)
  df_qlmc_per = df_qlmc[df_qlmc['period'] == i]
  
  # Average price by product / chain
  ls_col_gb = ['store_chain_alt', 'section', 'family', 'product', 'price']
  df_chain_prod_prices = df_qlmc_per.groupby(ls_col_gb[:-1]).agg([len, np.mean])['price']
  
  # Compare two chains
  ls_some_chains = ['AUCHAN',
                    'CARREFOUR',
                    'CHAMPION',
                    'CORA',
                    'GEANT',
                    'INTERMARCHE',
                    'SYSTEME U']
  ls_compare_chains = [['LECLERC', chain] for chain in ls_some_chains]
  ls_res, ls_res_ind = [], []
  for chain_a, chain_b in ls_compare_chains:
    # chain_a, chain_b = 'CENTRE E.LECLERC', 'CARREFOUR'
    df_chain_a = df_chain_prod_prices.loc[(chain_a),:]
    df_chain_b = df_chain_prod_prices.loc[(chain_b),:]
    # print df_test.loc[(slice(None), u'CENTRE E.LECLERC'),:].to_string()
    
    df_duel = pd.merge(df_chain_a,
                       df_chain_b,
                       left_index = True,
                       right_index = True,
                       how = 'inner',
                       suffixes = (u'_{:s}'.format(chain_a), u'_{:s}'.format(chain_b)))
    
    # Nb obs required varies by chain (figure below for october..)
    # Min 16 for CORA, Max 21 for Carrefour Market, Intermarche and Systeme U
    # Leclerc: 20, Auchan 19, Carrefour 19, Geant 18
    
    df_duel_sub = df_duel[(df_duel['len_{:s}'.format(chain_a)] >= 15) &\
                          (df_duel['len_{:s}'.format(chain_b)] >= 15)].copy()
  
    if df_duel_sub.empty:
      print u'\nNot enough obs for:', chain_a, chain_b
    else:
      df_duel_sub['diff'] = df_duel_sub['mean_{:s}'.format(chain_b)] -\
                              df_duel_sub['mean_{:s}'.format(chain_a)]
      
      df_duel_sub['pct_diff'] = (df_duel_sub['mean_{:s}'.format(chain_b)] /\
                                  df_duel_sub['mean_{:s}'.format(chain_a)] - 1)*100
  
      res = (df_duel_sub['mean_{:s}'.format(chain_b)].mean().round(2) /\
               df_duel_sub['mean_{:s}'.format(chain_a)].mean().round(2) - 1) * 100
      
      # Save both nb stores of chain b and res
      ls_res.append([len(df_qlmc_per[df_qlmc_per['store_chain_alt'] ==\
                                       chain_b]['store'].unique()), res])
      ls_res_ind.append(chain_b)
      
      #print u'\nReplicated QLMC comparison: {:s} vs {:s}'.format(chain_a, chain_b)
      #print u'{:.1f}'.format(res)
  
      #percentiles = [0.1, 0.25, 0.5, 0.75, 0.9]
      #print df_duel_sub[['diff', 'pct_diff']].describe(percentiles = percentiles)
  
      ## Manipulate or assume consumer is somewhat informed
      #df_duel_sub.sort('diff', ascending = False, inplace = True)
      #df_duel_sub = df_duel_sub[len(df_duel_sub)/10:]
      #res = (df_duel_sub['mean_{:s}'.format(chain_b)].mean().round(2) /\
      #         df_duel_sub['mean_{:s}'.format(chain_a)].mean().round(2) - 1) * 100
      #print u'After manip against Leclerc: {:.1f}'.format(res)
  
  ##print df_duel[0:10].to_string()
  
  df_res = pd.DataFrame(ls_res,
                        index = ls_res_ind,
                        columns = ['Nb stores (my data)', 'vs. LEC (my data)'])
  df_res['vs. LEC (my data)'] =\
    df_res['vs. LEC (my data)'].apply(lambda x: u'{:.1f}%'.format(x))
  df_res.ix['LECLERC'] = [len(df_qlmc_per[df_qlmc_per['store_chain_alt'] ==\
                                'LECLERC']['store'].unique()), u'']
  
  ls_df_res.append(df_res)

  print df_res.to_string()
