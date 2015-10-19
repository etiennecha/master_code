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
                                         'df_ophtalmo_75_2014.csv'),
                            encoding = 'utf-8')

# STATS DES

df_physicians_a = df_physicians[df_physicians['status'] != u'Hopital L'].copy()

# old way => use pandas
print u'\nNb of Physicians, mean and median visit price by ardt'
print u'-'*30
print u'{0:12}{1:>8}{2:>10}{3:>10}'.format(u'Ardt', u'#Phys', u'Mean', u'Med')
for zc in df_physicians_a['zip_city'].unique():
  nb_physicians = len(df_physicians_a[df_physicians_a['zip_city'] == zc])
  mean_consultation = df_physicians_a['c_base'][df_physicians_a['zip_city'] == zc].mean()
  med_consultation = df_physicians_a['c_base'][df_physicians_a['zip_city'] == zc].median()
  print u'{0:12}{1:8d}{2:10.2f}{3:10.2f}'.format(zc,
                                                 nb_physicians,
                                                 mean_consultation,
                                                 med_consultation)

## SYNTAX ELEMENTS
##df_physicians[['zip_city', 'consultation']].groupby('convention').agg([len, np.mean])
#gb_zip_city = df_physicians[['zip_city'] + ls_disp_services].groupby('zip_city')
#df_ardt_count = gb_zip_city.count()
#df_ardt_mean = gb_zip_city.mean()
#df_ardt_med = gb_zip_city.median()
## print gb_zip_city.describe().to_string()

## todo: stats des by ardt with groupby
#df_physicians[['zip_city', 'consultation']].groupby('zip_city').aggregate([len, np.mean])

# TODO: GEOCODING (?), LOAD INSEE DATA + INTEGRATE WITH OTHER PHYSICIAN DATA
# TODO: PUT FOLLOWING IN ANOTHER SCRIPT (AND LOAD DF PHYSICIANS)
