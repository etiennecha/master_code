#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
import os
import json
from datetime import date, timedelta
import datetime
import numpy as np
import pprint
import itertools
import pandas as pd
import matplotlib.pyplot as plt

path_built = os.path.join(path_data,
                          u'data_supermarkets',
                          u'data_built',
                          u'data_drive',
                          u'data_auchan')

path_built_csv = os.path.join(path_built,
                              u'data_csv')

# #########
# LOAD DATA
# #########

dict_df_velizy = {}
for x in ['master', 'prices', 'products']:
  ls_parse_dates = []
  if x in ['master', 'prices']:
    ls_parse_dates = ['date']
  dict_df_velizy['df_{:s}'.format(x)] =\
      pd.read_csv(os.path.join(path_built_csv,
                               'df_{:s}_auchan_velizy_2012-13.csv'.format(x)),
                  parse_dates = ls_parse_dates,
                  dtype = {'available' : str,
                           'pictos' : str,
                           'promo' : str,
                           'promo_vignette' : str},
                  encoding = 'utf-8')

df_master_velizy = dict_df_velizy['df_master']
df_prices_velizy = dict_df_velizy['df_prices']
df_products_velizy = dict_df_velizy['df_products']

dict_df_2013 = {}
for x in ['master', 'prices', 'products']:
  ls_parse_dates = []
  if x in ['master', 'prices']:
    ls_parse_dates = ['date']
  dict_df_2013['df_{:s}'.format(x)] =\
      pd.read_csv(os.path.join(path_built_csv,
                               'df_{:s}_auchan_2013.csv'.format(x)),
                  parse_dates = ls_parse_dates,
                  dtype = {'available' : str,
                           'pictos' : str,
                           'promo' : str,
                           'promo_vignette' : str},
                  encoding = 'utf-8')

df_master = dict_df_2013['df_master']
df_prices = dict_df_2013['df_prices']
df_products = dict_df_2013['df_products']

# #############
# OVERVIEW DATA
# #############

# todo: check duplicate stories
