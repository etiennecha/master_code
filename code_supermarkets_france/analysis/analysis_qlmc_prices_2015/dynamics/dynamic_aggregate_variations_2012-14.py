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

path_built_200712 = os.path.join(path_data,
                                 'data_supermarkets',
                                 'data_built',
                                 'data_qlmc_2007-12')

path_built_200712_csv = os.path.join(path_built_200712,
                                     'data_csv')

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

df_qlmc_0712 = pd.read_csv(os.path.join(path_built_200712_csv,
                                        'df_qlmc.csv'),
                           encoding = 'utf-8',
                           parse_dates = ['date'])

# harmonize store chains according to qlmc
df_qlmc_0712['store_chain_alt'] = df_qlmc_0712['store_chain']
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
  df_qlmc_0712.loc[df_qlmc_0712['store_chain'] == sc_old,
              'store_chain_alt'] = sc_new

df_qlmc_1415 = pd.read_csv(os.path.join(path_built_201415_csv,
                                        'df_qlmc_2014-2015.csv'),
                           dtype = {'ean' : str,
                                    'id_lsa' : str},
                           encoding = 'utf-8')

#ls_tup_pers = [('0', '1'), ('1', '2'), ('0', '2')]
#for tup_per in ls_tup_pers:
#  df_qlmc_1415['pct_var_{:s}{:s}'.format(*tup_per)] =\
#    df_qlmc_1415['price_{:s}'.format(tup_per[1])] /\
#      df_qlmc_1415['price_{:s}'.format(tup_per[0])] - 1
#
#ls_pct_var_cols = ['pct_var_{:s}{:s}'.format(*tup_per)\
#                      for tup_per in ls_tup_pers]
#
#for chain in ['LECLERC', 'GEANT CASINO', 'CARREFOUR']:
#  print()
#  print(chain)
#  print(df_qlmc_1415[df_qlmc_1415['store_chain'] == chain]\
               [ls_pct_var_cols].describe().to_string())

# All periods observed? 670 stores with 158 to 1599 obs
df_full = df_qlmc_1415[(~df_qlmc_1415['price_0'].isnull()) &\
                       (~df_qlmc_1415['price_1'].isnull()) &\
                       (~df_qlmc_1415['price_2'].isnull())]

# Could also consider 0 to 2
df_02 = df_qlmc_1415[(~df_qlmc_1415['price_0'].isnull()) &\
                     (~df_qlmc_1415['price_2'].isnull())]

# Check indiv price vars for suspicious changes
# Quite a few pbms to fix... should check price distributions in static
# print(df_02[df_02['store_chain'] == 'INTERMARCHE']['pct_var_02'].describe())
# print(df_full[df_full['pct_var_01'] > 1].to_string())

# ############################
# COMPARE 2007-12 vs. 2014-15
# ############################

df_qlmc_2012 = df_qlmc_0712[df_qlmc_0712['period'] == 12]
df_qlmc_0712['product'] = df_qlmc_0712['product_brand'].str.upper() + ' '\
                            + df_qlmc_0712['product_name'].str.upper() + ' '\
                            + df_qlmc_0712['product_format'].str.upper()

ls_prod_cols = ['section', 'family' , 'product'] # ['product']
df_mp_2012 = df_qlmc_0712.groupby(ls_prod_cols).agg([len, np.mean])['price']
df_mp_2012.reset_index(drop = False, inplace = True)

df_mp_2014 = df_qlmc_1415.groupby(ls_prod_cols).agg([len, np.mean])['price_0']
df_mp_2014.reset_index(drop = False, inplace = True)

df_ic = pd.merge(df_mp_2012,
                 df_mp_2014,
                 on = ['product'],
                 how = 'inner')

# todo: some reconciliations
# main brands (Coca, Herta, Fleury Michon, Elle & Vire, Danone etc.)
# chge display wide column
# sort on price
# reconcile EAN (2014) with product name (2012)
