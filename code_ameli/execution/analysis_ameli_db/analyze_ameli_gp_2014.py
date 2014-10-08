#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_ameli import *
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


path_dir_ameli = os.path.join(path_data, u'data_ameli', 'data_source', 'ameli_2014')
path_dir_built_csv= os.path.join(path_data, u'data_ameli', 'data_built', 'csv')
path_dir_built_json = os.path.join(path_data, u'data_ameli', 'data_built', 'json')
#path_dir_built_hdf5 = os.path.join(path_data, u'data_ameli', 'data_built', 'hdf5')
#ameli_data = pd.HDFStore(os.path.join(path_dir_built_hdf5, 'ameli_data.h5'))

df_physicians = pd.read_csv(os.path.join(path_dir_built_csv, 'gp_2014.csv'),
                            encoding = 'utf-8')

# TODO: add INSEE data

# Stats descs
pd.set_option('float_format', '{:.1f}'.format)

# All
gb_zc = df_physicians[['zip_city', 'c_base']].groupby('zip_city')
df_zc = gb_zc.agg([len, np.mean, np.median])['c_base']
df_zc['len'] = df_zc['len'].astype(int)
print df_zc.to_string()

# todo: density rather than nb of physicians
plt.scatter(df_zc_s2['len'], df_zc_s2['mean'])
plt.show()

# Secteur 2 (reproduce with min and max?)
df_physicians_s2 = df_physicians[df_physicians['convention'] == '2'].copy()
gb_zc_s2 = df_physicians_s2[['zip_city', 'c_base']].groupby('zip_city')
df_zc_s2 = gb_zc_s2.agg([len, np.mean, np.median])['c_base']
df_zc_s2['len'] = df_zc_s2['len'].astype(int)
print df_zc_s2.to_string()

# todo: density rather than nb of physicians
plt.scatter(df_zc_s2['len'], df_zc_s2['mean'])
plt.show()

#df_cross = df_physicians[['convention','immatriculation','Consultation']].\
#df_physicians['zip_city'][df_physicians['zip_city'].str.startswith('75116')] = '75016 PARIS'
#df_temp = df_physicians[~df_physicians['zip_city'].str.contains('CEDEX')]
#formula = 'Consultation ~ C(zip_city) + immatriculation + C(convention)'
#res01 = smf.ols(formula = formula, data = df_temp, missing= 'drop').fit()
## todo: represent homogeneity within ardts

# JSON DEPRECATED?

#path_dir_built_json = os.path.join(path_data, u'data_ameli', 'data_built', 'json')
#file_extension = u'ophtalmologiste_75'
#ls_ls_physicians = dec_json(os.path.join(path_dir_built_json, '%s.json' %file_extension))
#
#ls_columns = ['id_physician', 'gender', 'name', 'surname',
#              'street', 'zip_city', 'convention', 'carte_vitale', 'status',
#              'injection_med', 'examen_mot', 'imagerie', 'traitement_las',
#              'fond', 'examen_vis', 'chirurgie_cat', 'consultation', 'avis']
#df_physicians = pd.DataFrame(ls_ls_physicians, columns = ls_columns)
#df_physicians.index = df_physicians['id_physician']
#
## DISPLAY DATA
#ls_disp_base = ['gender','name', 'surname', 'street', 'zip_city',
#                'convention', 'carte_vitale', 'status']
#ls_disp_services = ['consultation', 'avis', 'fond', 'imagerie', 'chirurgie_cat']
#
## print df_physicians[ls_disp_base + ls_disp_services].to_string()
#print df_physicians[ls_disp_base + ls_disp_services]\
#        [pd.isnull(df_physicians['consultation'])].to_string()
