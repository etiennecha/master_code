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
                                         'df_ophtalmo_suburb_2014.csv'),
                            encoding = 'utf-8')

# temp fix (move)
df_physicians.loc[df_physicians['id_physician'] == 'CbA1kjEyODC3',
                  'convention'] = u'1 DPD'

df_physicians_bu = df_physicians.copy()
df_physicians = df_physicians[df_physicians['status'] != u'Hopital L']

## Add base price when only min and max provided
#df_physicians.loc[(df_physicians['c_base'].isnull()) &\
#                  (~df_physicians['c_min'].isnull()),
#                  'c_base'] =\
#  df_physicians[['c_min', 'c_max']][(df_physicians['c_base'].isnull()) &\
#                                    (~df_physicians['c_min'].isnull())].mean(axis = 1)

# STATS DES

ls_rows_dpt = []
for dpt in df_physicians['dpt'].unique():
  df_dpt = df_physicians[df_physicians['dpt'] == dpt]
  df_s1 = df_dpt[df_dpt['convention'].str.contains('1')]
  df_s2 = df_dpt[df_dpt['convention'].str.contains('2')]
  ls_rows_dpt.append([dpt,
                      len(df_dpt),
                      len(df_s1),
                      len(df_s2),
                      len(df_s2[~df_s2['c_base'].isnull()]),
                      df_s2['c_base'].mean(),
                      df_s2['c_base'].std(),
                      df_s2['c_base'].median()])

df_su_dpt = pd.DataFrame(ls_rows_dpt,
                         columns = ['Dpt',
                                    'Nb physicians',
                                    'Nb sector 1',
                                    'Nb sector 2',
                                    'Nb prices',
                                    'Mean price',
                                    'Std price',
                                    'Median price'])

print u'Stats des on Ophthalmologists around Paris'
print u'Prices are for sector 2 only (others: 28e)'
print df_su_dpt.to_string()

## todo: GEOCODING (?), LOAD INSEE DATA + INTEGRATE WITH OTHER PHYSICIAN DATA
## todo: PUT FOLLOWING IN ANOTHER SCRIPT (AND LOAD DF PHYSICIANS)
## FIX ADDRESSES FOR GEOCODING (ZIP CODE CEDEX)
#df_physicians['zip_city'][df_physicians['zip_city'].str.contains('CEDEX')]
# todo: check also bis (e.g. "27B") and ter (same pattern)
