#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_ameli import *
import numpy as np
import pandas as pd
import pprint

#path_dir_built_hdf5 = os.path.join(path_dir_built, 'hdf5')
#ameli_data = pd.HDFStore(os.path.join(path_dir_built_hdf5, 'ameli_data.h5'))

path_dir_built_json = os.path.join(path_data, u'data_ameli', 'data_built', 'json')
file_extension = u'ophtalmologiste_75'
ls_ls_physicians = dec_json(os.path.join(path_dir_built_json, '%s.json' %file_extension))

ls_columns = ['id_physician', 'gender', 'name', 'surname',
              'street', 'zip_city', 'convention', 'carte_vitale', 'status',
              'injection_med', 'examen_mot', 'imagerie', 'traitement_las',
              'fond', 'examen_vis', 'chirurgie_cat', 'consultation', 'avis']
df_physicians = pd.DataFrame(ls_ls_physicians, columns = ls_columns)
df_physicians.index = df_physicians['id_physician']

# DISPLAY DATA
ls_disp_base = ['gender','name', 'surname', 'street', 'zip_city',
                'convention', 'carte_vitale', 'status']
ls_disp_services = ['consultation', 'avis', 'fond', 'imagerie', 'chirurgie_cat']

# print df_physicians[ls_disp_base + ls_disp_services].to_string()
print df_physicians[ls_disp_base + ls_disp_services]\
        [pd.isnull(df_physicians['consultation'])].to_string()

# COMPANY CREATION DATE
path_dir_societe = os.path.join(path_data, u'data_ameli', 'data_source', u'societe')
dict_results = dec_json(os.path.join(path_dir_societe, u'societe_dict_ophtalmo'))
ls_no_result = dec_json(os.path.join(path_dir_societe, u'societe_ls_no_result_ophtalmo'))

dict_ste_physicians = {}
for id_physician, info_physician in dict_results.items():
  if u'médecin' in info_physician[2][0]:
    dict_ste_physicians[id_physician] = info_physician[:2] +\
                                        [[elt.strip() if elt else elt\
                                           for elt in info_physician[3]]]
  else:
    dict_results[id_physician][2] =\
      [elt.strip() if elt else elt\
        for elt in info_physician[2][0].replace('\n', '').split(';')]
    dict_results[id_physician][3] =\
      [elt.strip() if elt else elt for elt in info_physician[3]]
    print '\n', id_physician
    pprint.pprint(dict_results[id_physician])

df_physicians['immatriculation'] = None
for id_physician, info_physician in dict_ste_physicians.items():
  len_info_ste = len(info_physician[2])
  ls_titles = [info_physician[2][i] for i in range(len_info_ste) if i%2 == 0]
  ls_contents = [info_physician[2][i] for i in range(len_info_ste) if i%2 != 0]
  dict_info_ste = dict(zip(ls_titles, ls_contents))
  dict_ste_physicians[id_physician][2] = dict_info_ste 
  # print id_physician, dict_info_ste.get('Immatriculation')
  df_physicians.ix[id_physician, 'immatriculation'] = dict_info_ste.get('Immatriculation')
df_physicians['immatriculation'] =\
  df_physicians['immatriculation'].apply(lambda x: float(x[-4:]) if x else None)

##Stats desc:
##df_temp[['convention', 'Consultation']].groupby('convention').agg([len, np.mean])
#df_cross = df_physicians[['convention','immatriculation','Consultation']].\
#             groupby(['convention','immatriculation'])
#df_cross = df_cross.count()['Consultation'].unstack(0)
#df_cross_cum = df_cross.cumsum()
#df_cross_cum_graph = df_cross_cum.fillna(method='bfill').fillna(method='pad')

# Some info wrong: 1900 => 2000 after verification with other site
df_physicians['immatriculation'][df_physicians['immatriculation'] == 1900] = 2000
# Misses 5
# df_physicians['zip_city'][df_physicians['zip_city'].str.startswith('75116')] = '75016 PARIS'
df_temp = df_physicians[(df_physicians['convention'] == '1') |\
                        (df_physicians['convention'] == '2')]
import statsmodels.formula.api as smf
formula = 'consultation ~ C(zip_city) + immatriculation + C(convention)'
res01 = smf.ols(formula = formula, data = df_temp, missing= 'drop').fit()
print res01.summary()
# todo: investigate immatriculation... would be better to have age probably
# todo: represent nb of immatriculation per year (cf gasoline zagaz registrations)

# CHECK OSM ROUTE SERVICE : http://wiki.openstreetmap.org/wiki/OpenRouteService
