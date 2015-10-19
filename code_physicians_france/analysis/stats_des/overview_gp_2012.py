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

# LOAD DATA

df_physicians = pd.read_csv(os.path.join(path_built_csv,
                                         'df_gp_2012.csv'),
                            encoding = 'utf-8')

# STATS DES

# Number by sector
print u'\nNb of physicians by "secteur"'
print df_physicians['sector'].value_counts()

## Overview
#print df_physicians[(df_physicians['dpt'] == '01') &\
#                    (df_physicians['sector'] == 'secteur2')]\
#        [ls_columns + ['Consultation']].to_string()

# Number by dpt and sector
print u'\nNb of physicians by "département" and "secteur"'
df_physicians['dpt'] = df_physicians['zip'].apply(lambda x: x[:2])
se_nb_by_dpt_and_sector = df_physicians.groupby(['sector', 'dpt']).size()
# print se_nb_by_dpt_and_sector.to_string()
ls_str_sectors = ('nonconv', 'secteur2', 'secteur1')
ls_se_sectors_by_dpt = []
for str_sector in ls_str_sectors:
  df_sector = df_physicians[df_physicians['sector'] == str_sector]
  ls_se_sectors_by_dpt.append(df_sector.groupby('dpt').size())
df_sectors_by_dpt = pd.concat(dict(zip(ls_str_sectors, ls_se_sectors_by_dpt)), axis= 1)
df_sectors_by_dpt = df_sectors_by_dpt.fillna(0)
df_sectors_by_dpt['total'] = df_sectors_by_dpt.sum(axis = 1)
#df_sectors_by_dpt['total'] = df_sectors_by_dpt['nonconv'] +\
#                             df_sectors_by_dpt['secteur2'] +\
#                             df_sectors_by_dpt['secteur1']
print df_sectors_by_dpt.to_string()

# plt.scatter(df_sectors_by_dpt['total'], df_sectors_by_dpt['secteur2'])
# plt.show()

# REMARKS:
# Paris 16: only zip 75116... not 75016
# Issue can be similar for other zip codes
# Can bias nb of competitors for a physician/within an area
# Still in any not too small area: should have a big enough sample of physicians (biases?)
# Secteur 2 in paris
df_physicians.sort('zip_city', inplace = True)
print df_physicians[ls_disp_base_2 + ls_disp_services]\
        [(df_physicians['convention'] == '2') &\
         (df_physicians['spe'] == 'MG')].to_string()

# todo: either drop pediatrie or generalize price extraction
