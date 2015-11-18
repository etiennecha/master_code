#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
import numpy as np
import pandas as pd

path_built = os.path.join(path_data,
                          'data_supermarkets',
                          'data_built',
                          'data_qlmc_2007-12')

path_built_csv = os.path.join(path_built,
                              'data_csv')

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# ###########
# LOAD DATA
# ###########

df_qlmc = pd.read_csv(os.path.join(path_built_csv,
                                   'df_qlmc.csv'),
                      parse_dates = ['date'],
                      encoding = 'utf-8')

df_stores = pd.read_csv(os.path.join(path_built_csv,
                                     'df_stores.csv'),
                        dtype = {'c_insee' : str,
                                 'id_lsa' : str},
                        encoding = 'utf-8')

df_pairs = pd.read_csv(os.path.join(path_built_csv,
                                     'df_close_store_pairs.csv'),
                        encoding = 'utf-8')

# todo: check mapping product vs. section/family (if not done?)
df_products = df_qlmc[['period', 'product', 'product_brand', 'product_name', 'product_format', 'section', 'family']].drop_duplicates()

# #####################
# ADD NB OBS BY PRODUCT
# #####################

ls_prod_cols = ['period', 'section', 'family', 'product']
se_prod_vc = df_qlmc[ls_prod_cols].groupby(ls_prod_cols).agg(len)
df_products.set_index(ls_prod_cols, inplace = True)
df_products['nb_obs'] = se_prod_vc
df_products.reset_index(drop = False, inplace = True)

# #######################
# BASKET COMPO BY SECTION
# #######################

# todo: add product mean price to have idea of value

df_products_p = df_products[df_products['period'] == 12].copy()
df_products_p.sort('nb_obs', ascending = False, inplace = True)

df_sections_p_rep = pd.concat([df_products_p['section'].value_counts(),
                               df_products_p['section'].value_counts(normalize = True) * 100],
                              axis = 1,
                              keys = ['Nb prod', 'Share (%)'])
print df_sections_p_rep.to_string(float_format = format_float_int)
