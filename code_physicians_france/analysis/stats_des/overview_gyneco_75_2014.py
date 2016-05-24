#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_ameli import *
import re
import time
from collections import Counter
import pprint
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import statsmodels as sm
import statsmodels.formula.api as smf

path_built_ameli = os.path.join(path_data,
                                u'data_ameli',
                                u'data_built')

path_built_csv= os.path.join(path_built_ameli, 'data_csv')
path_built_json = os.path.join(path_built_ameli, u'data_json')

pd.set_option('float_format', '{:,.0f}'.format)

# LOAD DATA

df_physicians = pd.read_csv(os.path.join(path_built_csv,
                                         'df_gyneco_75_2014.csv'),
                            encoding = 'utf-8')

# temp fix (move)
df_physicians.loc[df_physicians['id_physician'] == 'B7c1kzs5ODu0',
                  'convention'] = u'1 DPD'

df_physicians_bu = df_physicians.copy()
df_physicians = df_physicians[df_physicians['status'] != u'Hopital L']

df_physicians.rename(columns = {'consultation' : 'c_base'},
                     inplace = True)

# STATS DES

ls_rows_c_postal = []
for c_postal in df_physicians['zip'].unique():
  df_c_postal = df_physicians[df_physicians['zip'] == c_postal]
  df_s1 = df_c_postal[df_c_postal['convention'].str.contains('1')]
  df_s2 = df_c_postal[df_c_postal['convention'].str.contains('2')]
  ls_rows_c_postal.append([c_postal,
                      len(df_c_postal),
                      len(df_s1),
                      len(df_s2),
                      len(df_s2[~df_s2['c_base'].isnull()]),
                      df_s2['c_base'].mean(),
                      df_s2['c_base'].std(),
                      df_s2['c_base'].median()])

df_su_c_postal = pd.DataFrame(ls_rows_c_postal,
                         columns = ['Zip',
                                    'Nb physicians',
                                    'Nb sector 1',
                                    'Nb sector 2',
                                    'Nb prices',
                                    'Mean price',
                                    'Std price',
                                    'Median price'])

print u'Stats des on Gynecos in Paris'
print u'Prices are for sector 2 only (others: 28e)'
df_su_c_postal.sort('Nb physicians', ascending = False)
print df_su_c_postal.to_string()
