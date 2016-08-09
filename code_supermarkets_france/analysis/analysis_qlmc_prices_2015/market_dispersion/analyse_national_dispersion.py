#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import add_to_path
from add_to_path import *
import os, sys
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt
import timeit

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

path_built_csv = os.path.join(path_data,
                              'data_supermarkets',
                              'data_built',
                              'data_qlmc_2015',
                              'data_csv_201503')

# ##########
# LOAD DATA
# ##########

df_prices = pd.read_csv(os.path.join(path_built_csv,
                                     'df_res_ln_prices.csv'),
                        encoding = 'utf-8')

# overwrite store_chain
ls_replace_chains = [['HYPER U', 'SUPER U'],
                     ['U EXPRESS', 'SUPER U'],
                     ['HYPER CASINO', 'CASINO'],
                     ["LES HALLES D'AUCHAN", 'AUCHAN']]
for old_chain, new_chain in ls_replace_chains:
  df_prices.loc[df_prices['store_chain'] == old_chain,
                'store_chain'] = new_chain

ls_prod_cols = ['section', 'family', 'product']
df_prices['nb_obs'] = df_prices.groupby(ls_prod_cols)['price'].transform(len)
df_prices['ln_dev'] = np.log(df_prices['price'] /\
                        df_prices.groupby(ls_prod_cols)['price'].transform('mean'))
df_prices['ln_res'] = df_prices['ln_price'] - df_prices['ln_price_hat']

# ####################
# NATIONAL DISPERSION
# ####################

# - filter on nb obs
# - by section / family / product
# - by chain... elsewhere?
# - output: overview of product distributions
# - output: overview of distributions at section level
# - output: graph distributions?

df_prod_disp =\
  df_prices[ls_prod_cols + ['ln_dev', 'ln_res']]\
           [df_prices['nb_obs'] >= 50].groupby(ls_prod_cols)\
                                      .agg([lambda x: x.quantile(0.75) -\
                                                      x.quantile(0.25),
                                            'std',
                                            len])
df_prod_disp.columns = ['iqr_ln_dev', 'std_ln_dev',
                        'iqr_ln_res', 'std_ln_res',
                        'len_ls_dev', 'len_ls_res']
df_prod_disp.reset_index(inplace = True, drop = False)
df_su_prod_disp = df_prod_disp.groupby('section').agg('mean')
df_su_prod_disp['len'] = df_prod_disp.groupby('section').agg(len)['iqr_ln_dev']
print(df_su_prod_disp.to_string())

df_section_disp =\
  df_prices[['section', 'ln_dev', 'ln_res']]\
           [df_prices['nb_obs'] >= 50].groupby('section')\
                                      .agg([lambda x: x.quantile(0.75) -\
                                                      x.quantile(0.25),
                                            'std',
                                            len])

print()
print(df_section_disp.to_string())
