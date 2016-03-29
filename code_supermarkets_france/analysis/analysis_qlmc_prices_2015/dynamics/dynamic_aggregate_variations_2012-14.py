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
path_built_200712_excel = os.path.join(path_built_200712,
                                       'data_excel')

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
#                    [ls_pct_var_cols].describe().to_string())

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

# ###################################
# CHECK PRODUCTS 2007-12 VS. 2014-15
# ###################################

df_qlmc_0712['product'] = df_qlmc_0712['product_brand'].str.upper() + ' '\
                            + df_qlmc_0712['product_name'].str.upper() + ' '\
                            + df_qlmc_0712['product_format'].str.upper()

df_qlmc_2012 = df_qlmc_0712[df_qlmc_0712['period'] == 12].copy()

ls_prod_cols = ['section', 'family' , 'product'] # ['product']
df_mp_2012 = df_qlmc_2012.groupby(ls_prod_cols).agg([len, 'mean'])['price']
df_mp_2012.reset_index(drop = False, inplace = True)

df_mp_2014 = df_qlmc_1415.groupby(ls_prod_cols + ['ean']).agg([len, 'mean'])['price_0']
df_mp_2014.reset_index(drop = False, inplace = True)

df_ic = pd.merge(df_mp_2012,
                 df_mp_2014,
                 on = ['product'], # not same section / family
                 how = 'inner')

## todo: some reconciliations
## main brands (Coca, Herta, Fleury Michon, Elle & Vire, Danone etc.)
## chge display wide column
## sort on price
## reconcile EAN (2014) with product name (2012)
#
#pd.set_option('display.max_colwidth', 200)
#
#ls_brands = ['Herta',
#             'Fleury Michon',
#             'President',
#             'Coca',
#             'Panzani',
#             'Harry',
#             'Bonduelle',
#             'Elle & Vire',
#             'Cristaline',
#             'Activia',
#             'La laitiere',
#             'Nestle',
#             'Pasquier',
#             'Amora',
#             'Lustucru',
#             'Danette',
#             'Bonne maman',
#             'Knorr',
#             'Kinder',
#             'Andros',
#             'Danone',
#             'Tropicana',
#             'Heineken',
#             'Kronenbourg',
#             'Ricard',
#             'Campbell',
#             'Ballantine',
#             'Grants']
#
#for brand in ls_brands:
#  print()
#  print(brand)
#
#  print()
#  print('Products in 2012 for brand', brand)
#  df_brand_2012 = df_mp_2012[df_mp_2012['product'].str.contains(brand, case = False)].copy()
#  df_brand_2012.sort('mean', ascending = False, inplace = True)
#  print(df_brand_2012.to_string())
#  
#  print()
#  print('Products in 2014 for brand', brand)
#  df_brand_2014 = df_mp_2014[df_mp_2014['product'].str.contains(brand, case = False)].copy()
#  df_brand_2014.sort('mean', ascending = False, inplace = True)
#  print(df_brand_2014.to_string())

# ############################
# COMPARE 2012 TO 2014
# ############################

# todo import 2012 EAN from excel file
df_ean_2012 = pd.read_excel(os.path.join(path_built_200712_excel,
                                         'QLMC_2012_product_ean.xls'),
                            sheetname = 'Feuil1')
df_ean_2012['ean'] = df_ean_2012['ean'].astype(str)
df_ean_2012.rename(columns = {'product_2012' : 'product'}, inplace = True)

df_qlmc_0712 = pd.merge(df_qlmc_0712,
                        df_ean_2012[['product', 'ean']],
                        on = ['product'],
                        how = 'inner')

# merge with 2014 on EAN (chain level compa + store level?)
df_qlmc_2012 = df_qlmc_0712[df_qlmc_0712['period'] == 12].copy()

ls_prod_cols_12 = ['ean'] # ['product']
# caution: need to use 'mean' and not np.mean to avoid np.nan
df_mcp_2012 = df_qlmc_2012.groupby(['store_chain_alt', 'ean']).agg([len, 'mean'])['price']
df_mcp_2012.reset_index(drop = False, inplace = True)

df_mcp_2012.loc[df_mcp_2012['store_chain_alt'] == 'CHAMPION',
                'store_chain_alt'] = 'CARREFOUR MARKET'
df_mcp_2012.rename(columns = {'store_chain_alt' : 'store_chain'}, inplace = True)

ls_prod_cols_14 = ['ean', 'section', 'family', 'product']
df_mcp_2014 = df_qlmc_1415.groupby(['store_chain'] +\
                                   ls_prod_cols_14).agg([len, 'mean'])['price_0']
df_mcp_2014.reset_index(drop = False, inplace = True)

df_mcp_comp = pd.merge(df_mcp_2012,
                       df_mcp_2014,
                       on = ['store_chain', 'ean'],
                       how = 'inner',
                       suffixes = ('_12', '_14'))

df_mcp_comp = df_mcp_comp[(~df_mcp_comp['mean_12'].isnull()) &\
                          (~df_mcp_comp['mean_14'].isnull())]

df_mcp_comp = df_mcp_comp[(df_mcp_comp['len_12'] >= 20) &\
                          (df_mcp_comp['len_14'] >= 20)]

df_mcp_comp['var'] = (df_mcp_comp['mean_14'] / df_mcp_comp['mean_12'] - 1) * 100

for chain in df_mcp_comp['store_chain'].unique():
  print()
  print(chain)
  df_chain_comp = df_mcp_comp[df_mcp_comp['store_chain'] == chain]
  print(df_chain_comp.describe())
  print((df_chain_comp['mean_14'].sum() / df_chain_comp['mean_12'].sum() - 1) * 100)

df_chain_comp = df_mcp_comp[df_mcp_comp['store_chain'] == 'LECLERC'].copy()
df_chain_comp.sort('var', ascending = True, inplace = True)
print()
print(df_chain_comp.to_string())
