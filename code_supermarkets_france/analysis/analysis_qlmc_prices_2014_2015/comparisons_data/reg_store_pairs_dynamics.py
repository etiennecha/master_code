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

# user store chars from March 2015
path_built_201503_csv = os.path.join(path_built_2015,
                                     'data_csv_201503')

path_built_lsa_csv = os.path.join(path_data,
                                  'data_supermarkets',
                                  'data_built',
                                  'data_lsa',
                                  'data_csv')

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

df_stores = pd.read_csv(os.path.join(path_built_201503_csv,
                                     'df_stores_final.csv'),
                        dtype = {'id_lsa' : str,
                                 'c_insee' : str},
                        encoding = 'utf-8')

df_lsa = pd.read_csv(os.path.join(path_built_lsa_csv,
                                  'df_lsa_active_hsx.csv'),
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

df_store_markets = pd.read_csv(os.path.join(path_built_lsa_csv,
                                            '201407_competition',
                                            'df_store_market_chars.csv'),
                               dtype = {'id_lsa' : str},
                               encoding = 'utf-8')

ls_lsa_cols = ['type_alt', 'region', 'surface',
               'nb_caisses', 'nb_pompes', 'drive']

df_store_chars = pd.merge(df_lsa[['id_lsa'] + ls_lsa_cols],
                          df_store_markets,
                          on = 'id_lsa',
                          how = 'left')

df_stores = pd.merge(df_stores,
                     df_store_chars,
                     on = 'id_lsa',
                     how = 'left')

for col in ['surface',
            'hhi_1025km', 'ac_hhi_1025km',
            'UU_med_rev', 'AU_med_rev', 'CO_med_rev',
            'AU_pop', 'UU_pop', 'CO_pop',
            'pop_cont_10', 'pop_ac_10km', 'pop_ac_20km']:
  df_stores['ln_{:s}'.format(col)] = np.log(df_stores[col])

# avoid error msg on condition number (regressions)
for col_var in ['AU_med_rev', 'UU_med_rev', 'CO_med_rev',
                'demand_cont_10', 'surface']:
  df_stores[col_var] = df_stores[col_var].apply(lambda x: x/1000.0)
df_stores['hhi'] = df_stores['hhi_1025km'] 

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

ls_ev = ['hhi', 'demand_cont_10', 'CO_med_rev']
str_ev = " + ".join(ls_ev)
df_compa = pd.merge(df_pairs,
                     df_stores[['id_lsa'] + ls_ev],
                     left_on = 'id_lsa_A',
                     right_on = 'id_lsa',
                     how = 'left')

# abs value for differentiation
df_pairs['abs_pct_agg_compa_0'] = np.abs(df_pairs['pct_agg_compa_0'])
df_pairs['abs_pct_agg_compa_2'] = np.abs(df_pairs['pct_agg_compa_2'])


# subsample based on differentiation
df_compa = df_compa[(df_compa['pct_agg_compa_0'].abs() <= 2) |\
                    (df_compa['pct_agg_compa_2'].abs() <= 2)]

## check without carrefour
#df_compa = df_compa[(df_compa['groupe_0'] != 'CARREFOUR') &\
#                    (df_compa['groupe_1'] != 'CARREFOUR')]

for rr_var in ['pct_rr', 'pct_prod_rr_0', 'pct_prod_rr_2']:
  dict_res = {}
  print()
  print('='*50)
  print('='*50)
  print(rr_var)
  for d_dist, dist_var, dist_max in [['d_dist_5', 'dist', 10],
                                     ['d_gg_dur_12', 'gg_dur', 20]]:
    
    formula = '{:s} ~ {:s}'.format(rr_var, d_dist) + '+ {:s}'.format(str_ev)
    
    ols_res = smf.ols(formula,
                      data = df_compa).fit()
    #print()
    #print(ols_res.summary())
    
    ls_res = []
    ls_quantiles = [0.25, 0.5, 0.75] # use 0.7501 if issue
    for quantile in ls_quantiles:
      #print()
      #print(quantile)
      #print(smf.quantreg('pct_rr~d_dist_5', data = df_repro_compa).fit(quantile).summary())
      ls_res.append(smf.quantreg(formula,
                                 data = df_compa[~df_compa[d_dist].isnull()]).fit(quantile))
      
    su = summary_col([ols_res] + ls_res,
                     stars=True,
                     float_format='%0.2f',
                     model_names=['OLS'] + [u'Q{:2.0f}'.format(quantile*100)\
                                             for quantile in ls_quantiles],
                     info_dict={'N':lambda x: "{0:d}".format(int(x.nobs)),
                                'R2':lambda x: "{:.2f}".format(x.rsquared)})

    print()
    print(u'Variable for close distance:', d_dist)
    print(su)
