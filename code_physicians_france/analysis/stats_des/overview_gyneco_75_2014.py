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
                                         'df_gyneco_75_2014.csv'),
                            encoding = 'utf-8')

# STATS DES

df_physicians_a = df_physicians[df_physicians['status'] != u'Hopital L'].copy()

# old way => used pd
print u'\nNb of Physicians, mean and median visit price by ardt'
print u'-'*30
ls_title_print = [u'Ardt', u'#Phys', u'#Phys1', u'#Phys2', u'Mean', u'Med']
print u'{0:12}{1:>10}{2:>10}{3:>10}{4:>10}{5:>10}'.format(*ls_title_print)
for zc in df_physicians_a['zip_city'].unique():
  nb_physicians = len(df_physicians_a[df_physicians_a['zip_city'] == zc])
  nb_physicians_1 = len(df_physicians_a[(df_physicians_a['zip_city'] == zc) &\
                                        (df_physicians_a['convention'] == '1')]) 
  nb_physicians_2 = len(df_physicians_a[(df_physicians_a['zip_city'] == zc) &\
                                        (df_physicians_a['convention'] == '2')]) 
  mean_consultation = df_physicians_a['consultation'][df_physicians_a['zip_city'] == zc].mean()
  med_consultation = df_physicians_a['consultation'][df_physicians_a['zip_city'] == zc].median()
  print u'{0:12}{1:10d}{2:10d}{3:10d}{4:10.2f}{5:10.2f}'.format(zc,
                                                 nb_physicians,
                                                 nb_physicians_1,
                                                 nb_physicians_2,
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
