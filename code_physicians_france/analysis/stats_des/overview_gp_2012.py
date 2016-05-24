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
                                         'df_gp_2012.csv'),
                            dtype = {'zip' : str,
                                     'CODGEO' : str},
                            encoding = 'utf-8')

df_physicians['dpt'] = df_physicians['zip'].apply(lambda x: x[:2])

df_physicians.rename(columns = {'sector' : 'convention',
                                'c_norm' : 'c_base'},
                     inplace = True)

df_physicians_bu = df_physicians.copy()
#df_physicians = df_physicians[df_physicians['status'] != u'Hopital L']
df_physicians = df_physicians[~df_physicians['spe'].str.contains('MEE',
                                                                 na=False)]

# STATS DES

# Number by sector
print u''
print u'Nb of physicians by "secteur"'
print df_physicians['convention'].value_counts()

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

print u''
print u'Stats des on GPs in France (not exhaustive)'
print u'Prices are for sector 2 only (others: 23e)'
df_su_dpt.sort('Nb physicians', ascending = False, inplace = True)
print df_su_dpt.to_string()
# A few sector 1 have fees above 23 => switch to '1 DPD' ?

df_su_dpt['Pct sector 2'] =\
  df_su_dpt['Nb sector 2'] /  df_su_dpt['Nb physicians'].astype(float) * 100

df_su_dpt[df_su_dpt['Nb prices'] >= 10].plot(kind = 'scatter',
                                             x = 'Pct sector 2',
                                             y = 'Mean price')
plt.show()

print ''
print 'Low share of sector 2 but high avg price'
print df_su_dpt[(df_su_dpt['Pct sector 2'] <= 5) &\
                (df_su_dpt['Mean price'] >= 35) &\
                (df_su_dpt['Nb prices'] >= 10)].to_string()

# DATA ISSUES: NON EXHAUSTIVE COLLECT
# In paritcular: Paris 16: only zip 75116... not 75016
# Issue can be similar for other zip codes (not exhaustive)
# Can bias nb of competitors for a physician/within an area
# But in any not too small area: should have a big enough sample of physicians (biases?)

# Overview
lsd0 = ['dpt', 'gender', 'full_name',
        'zip', 'city', 'convention', 'card', 'spe', 'c_base',  'c_occu', 'c_min', 'c_max']
print ''
print df_physicians[(df_physicians['dpt'] == '01') &\
                    (df_physicians['convention'] == 'secteur2')][lsd0].to_string()
