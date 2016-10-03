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
from statsmodels.iolib.summary2 import summary_col

path_built_2015 = os.path.join(path_data,
                               'data_supermarkets',
                               'data_built',
                               'data_qlmc_2015')
path_built_201415_csv = os.path.join(path_built_2015,
                                     'data_csv_2014-2015')
path_built_201415_json = os.path.join(path_built_2015,
                                     'data_json_2014-2015')

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# ###########
# LOAD DATA
# ###########

df_qlmc = pd.read_csv(os.path.join(path_built_201415_csv,
                                   'df_qlmc_2014-2015.csv'),
                      dtype = {'ean' : str,
                               'id_lsa' : str},
                      encoding = 'utf-8')

df_comp_pairs = pd.read_csv(os.path.join(path_built_201415_csv,
                                         'df_comp_store_pairs_final.csv'),
                            dtype = {'id_lsa_0' : str,
                                     'id_lsa_1' : str},
                            encoding = 'utf-8')

df_comp_pairs.rename(columns = {'gg_dist_val' : 'gg_dist',
                                'gg_dur_val' : 'gg_dur'},
                inplace = True)
df_comp_pairs.drop(['gg_dist_txt', 'gg_dur_txt', 'dist'], axis = 1, inplace = True)

df_pairs = pd.read_csv(os.path.join(path_built_201415_csv,
                                    'df_pair_dispersion_dynamic.csv'),
                       encoding = 'utf-8',
                       dtype = {'id_lsa_A' : str,
                                'id_lsa_B' : str})

# merge to get distance
df_pairs = pd.merge(df_pairs,
                    df_comp_pairs,
                    left_on = ['id_lsa_A', 'id_lsa_B'],
                    right_on = ['id_lsa_0', 'id_lsa_1'],
                    how = 'left')

# enrich distance variables
print()
print(df_pairs[['dist', 'gg_dist', 'gg_dur']].describe())

for dist in [5, 10, 12]:
  for dist_col in ['dist', 'gg_dist', 'gg_dur']:
    df_pairs['d_{:s}_{:d}'.format(dist_col, dist)] = np.nan
    df_pairs.loc[df_pairs[dist_col] <= dist,
                       'd_{:s}_{:d}'.format(dist_col, dist)] = 1
    df_pairs.loc[df_pairs[dist_col] > dist,
                       'd_{:s}_{:d}'.format(dist_col, dist)] = 0

# abs value for differentiation
df_pairs['abs_pct_agg_compa_0'] = np.abs(df_pairs['pct_agg_compa_0'])
df_pairs['abs_pct_agg_compa_2'] = np.abs(df_pairs['pct_agg_compa_2'])

# subsample based on differentiation
df_compa = df_pairs[(df_pairs['pct_agg_compa_0'].abs() <= 2) |\
                    (df_pairs['pct_agg_compa_2'].abs() <= 2)]

# check without carrefour
df_compa = df_compa[(df_compa['groupe_0'] != 'CARREFOUR') &\
                    (df_compa['groupe_1'] != 'CARRFOUR')]

for rr_var in ['pct_rr', 'pct_prod_rr_0', 'pct_prod_rr_2']:
  dict_res = {}
  for d_dist, dist_var, dist_max in [['d_dist_5', 'dist', 10],
                                     ['d_gg_dur_12', 'gg_dur', 20]]:
    
    print()
    print(u'-'*30)
    print(u'Variable for close distance:', d_dist)
    
    # NO CONTROL
    ols_res = smf.ols('{:s} ~ {:s}'.format(rr_var, d_dist),
                      data = df_compa).fit()
    #print()
    #print(ols_res.summary())
    
    ls_res = []
    ls_quantiles = [0.25, 0.5, 0.75] # use 0.7501 if issue
    for quantile in ls_quantiles:
      #print()
      #print(quantile)
      #print(smf.quantreg('pct_rr~d_dist_5', data = df_repro_compa).fit(quantile).summary())
      ls_res.append(smf.quantreg('pct_rr ~ {:s}'.format(d_dist),
                                 data = df_compa[~df_compa[d_dist].isnull()]).fit(quantile))
      
    print(summary_col([ols_res] + ls_res,
                      stars=True,
                      float_format='%0.2f',
                      model_names=['OLS'] + [u'Q{:2.0f}'.format(quantile*100) for quantile in ls_quantiles],
                      info_dict={'N':lambda x: "{0:d}".format(int(x.nobs)),
                                 'R2':lambda x: "{:.2f}".format(x.rsquared)}))
