#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import *
import os, sys
import httplib
import urllib, urllib2
from bs4 import BeautifulSoup
import re
import json
import pandas as pd
from functions_generic_qlmc import *
import numpy as np

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

path_qlmc_scraped = os.path.join(path_data,
                                  'data_qlmc',
                                  'data_source',
                                  'data_scraped')

path_csv = os.path.join(path_data,
                        'data_qlmc',
                        'data_built',
                        'data_csv')

df_stores = pd.read_csv(os.path.join(path_csv,
                                     'qlmc_scraped',
                                     'df_stores.csv'))

df_comp = pd.read_csv(os.path.join(path_csv,
                                   'qlmc_scraped',
                                   'df_competitors.csv'))

df_france = pd.read_csv(os.path.join(path_csv,
                                     'qlmc_scraped',
                                     'df_france.csv'))

# Based on group of ids... build df with stores as columns (inner join to start with)

# CORSE

# TEMP: define market (INSEE and LSA matching not performed so far)
ls_corse_ids = ['centre-e-leclerc-corbara',
                 'centre-e-leclerc-ajaccio-rte-d-alata',
                 'centre-e-leclerc-ajaccio-prince-imperial',
                 'centre-e-leclerc-porto-vecchio',
                 'centre-e-leclerc-ghisonaccia',
                 'centre-e-leclerc-aleria',
                 'centre-e-leclerc-san-giuliano',
                 'centre-e-leclerc-oletta',
                 'leclerc-express-borgo',
                 'centre-e-leclerc-bastia']

# TEMP: keep only stores present in data
ls_collected_store_ids = df_france['store_id'].unique().tolist()
ls_market_ids = [store_id for store_id in ls_corse_ids\
                   if store_id in ls_collected_store_ids]

# Merge store prices (inner for now... but intersection quickly reduces)
df_market = df_france[df_france['store_id'] == ls_market_ids[0]][['family', 'subfamily', 'product' ,'price']]
for store_id in ls_market_ids[1:]:
  df_market = pd.merge(df_market,
                       df_france[df_france['store_id'] == store_id][['product', 'price']],
                       on = 'product',
                       suffixes = ('', '_{:s}'.format(store_id)),
                       how = 'inner')
df_market.rename(columns = {'price' : 'price_{:s}'.format(ls_market_ids[0])}, inplace = True)

df_market_pr = df_market.drop(['subfamily', 'family'], axis = 1)
df_market_pr.set_index('product', inplace = True)
df_market_pr = df_market_pr.T

se_sum = df_market_pr.sum(1)
print se_sum.to_string()

df_market_su = df_market_pr.describe().T
df_market_su['spread'] = df_market_su['max'] - df_market_su['min']
df_market_su['gfs'] = df_market_su['mean'] - df_market_su['min']
df_market_su['cv'] = df_market_su['std'] / df_market_su['mean']

# Compare leclerc stores which offer those same products in mainland France
# (efficient? better ways to do? => simple reg?)
# (dispersion in mainland france btw?)

# FRANCE MAINLAND (pbm: not same products... how many left?)

ls_france_ids = df_stores[(df_stores['store_chain'] == 'LEC') &\
                          (~df_stores['store_id'].isin(ls_market_ids))]\
                    ['store_id'].unique().tolist()

ls_market_2_ids = [store_id for store_id in ls_france_ids\
                     if store_id in ls_collected_store_ids]

df_market_2 = df_france[df_france['store_id'] == ls_market_2_ids[0]][['family', 'subfamily', 'product' ,'price']]
for store_id in ls_market_2_ids[1:]:
  df_market_2 = pd.merge(df_market_2,
                       df_france[df_france['store_id'] == store_id][['product', 'price']],
                       on = 'product',
                       suffixes = ('', '_{:s}'.format(store_id)),
                       how = 'inner')
df_market_2.rename(columns = {'price' : 'price_{:s}'.format(ls_market_2_ids[0])}, inplace = True)

df_market_2_pr = df_market_2.drop(['subfamily', 'family'], axis = 1)
df_market_2_pr.set_index('product', inplace = True)
df_market_2_pr = df_market_2_pr.T

se_sum_2 = df_market_2_pr.sum(1)
print se_sum_2.to_string()

df_market_2_su = df_market_2_pr.describe().T
df_market_2_su['spread'] = df_market_2_su['max'] - df_market_2_su['min']
df_market_2_su['gfs'] = df_market_2_su['mean'] - df_market_2_su['min']
df_market_2_su['cv'] = df_market_2_su['std'] / df_market_2_su['mean']
