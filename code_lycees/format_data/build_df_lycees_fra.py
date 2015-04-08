#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import *
import os, sys
import re
import pandas as pd

path_lycees = os.path.join(path_data,
                           'data_lycees')

df_schools_geo = pd.read_csv(os.path.join(path_lycees,
                                          'data_built',
                                          'csv',
                                          'df_schools_geo_fra.csv'),
                             dtype = {'code' : str},
                             encoding = 'utf-8')
df_schools_geo.set_index('code', inplace = True)

df_lycees_res = pd.read_csv(os.path.join(path_lycees,
                                      'data_source',
                                      'results',
                                      'gt',
                                      'MEN-DEPP-indicateurs-de-resultats-des-LEGT-2014.csv'),
                            dtype = {u'Taux Brut de Réussite Total séries': float,
                                     u'Taux Réussite Attendu/Acad Total séries' : float,
                                     u'Taux Réussite Attendu/France Total séries' : float},
                            na_values = ['ND'],
                            sep = ';',
                            encoding = 'latin-1')
df_lycees_res.set_index('Code Etablissement', inplace = True)

# Add locaton to res
df_lycees = pd.merge(df_lycees_res,
                     df_schools_geo[['lat', 'lng', 'l93_x', 'l93_y']],
                     left_index = True,
                     right_index = True,
                     how = 'left')

print len(df_lycees[~pd.isnull(df_lycees['lat'])])
print len(df_lycees[(~pd.isnull(df_lycees['lat']) |
                    (~pd.isnull(df_lycees['l93_x'])))])

ls_di = ['Etablissement', 'Ville', 'Commune']
ls_di_gps = ['lat', 'lng', 'l93_x', 'l93_y']

# print df_lycees[pd.isnull(df_lycees['lat'])][ls_di + ls_di_gps][0:30].to_string()
# Seems a lot of missing lat are in DOMTOM
print df_lycees[(df_lycees['lat'].isnull()) &\
                (~df_lycees['Commune'].str.startswith('97'))][ls_di + ls_di_gps][0:30].to_string()

ls_fix_gps = [['0134003F', (43.29869, 5.42747 )],
              ['0333273D', (44.78672, -0.56352)],
              ['0261505V', (44.91763, 4.91737 )],
              ['0740051D', (46.39968, 6.57868 )],
              ['0596925G', (50.52274, 3.21921 )],
              ['0624430D', (50.28812, 2.77624 )],
              ['0624440P', (50.47023, 2.66008 )],
              ['0342225J', (43.60469, 3.91229 )],
              ['0442765S', (47.20834, -1.53286)],
              ['0442774B', (47.23167, -1.56006)],
              ['0442725Y', (47.22207, -1.55881)],
              ['0492407A', (47.46007, -0.52711)],
              ['0492406Z', (47.05894, -0.87814)],
              ['0492420P', (47.49136, -0.50060)],
              ['0721684P', (48.00026, 0.21469 )],
              ['0851642Y', (46.68615, -1.43896)],
              ['0912321D', (48.71358, 2.24078 )],
              ['0952173W', (48.92140, 2.21587 )]]

for lycee_code, (lycee_lat, lycee_lng) in ls_fix_gps:
  df_lycees.loc[lycee_code, 'lat'] = lycee_lat
  df_lycees.loc[lycee_code, 'lng'] = lycee_lng

df_lycees_fm = df_lycees[(~df_lycees['Commune'].str.startswith('97'))].copy()

#df_lycees_fm.to_csv(os.path.join(path_lycees,
#                                 'data_built',
#                                 'csv',
#                                 'df_lycee_fra_m.csv'),
#                    encoding = 'utf-8',
#                    float_format='%.3f',
#                    index_label = 'Code')

# Compa réussite au bac public vs. prive
#ls_series = ['L', 'ES', 'S',
#             'STMG', 'STI2D', 'STD2A', 'STL', 'ST2S',
#             'Musiq Danse', 'Hotellerie']
#for serie in ls_series:
#  df_lycees_fm[u'Nb admis {:s}'.format(serie)] =\
#      df_lycees_fm[u'Effectif Présents série {:s}'.format(serie)].astype(float) *\
#        df_lycees_fm[u'Taux Brut de Réussite série {:s}'.format(serie)].astype(float)

df_lycees_fm[u'Nb admis'] = df_lycees_fm[u'Effectif Présents Total séries'].astype(float)*\
                              df_lycees_fm[u'Taux Brut de Réussite Total séries']/ 100.0
df_lycees_fm[u'Nb admis att. Ac'] = df_lycees_fm[u'Effectif Présents Total séries'].astype(float)*\
                                      df_lycees_fm[u'Taux Réussite Attendu/Acad Total séries'] / 100.0
df_lycees_fm[u'Nb admis att. Fr'] = df_lycees_fm[u'Effectif Présents Total séries'].astype(float)*\
                                      df_lycees_fm[u'Taux Réussite Attendu/France Total séries'] / 100.0

# Overview: bac success
print df_lycees_fm[[u'Nb admis',
                    u'Effectif Présents Total séries',
                    u'Taux Brut de Réussite Total séries']].describe().to_string()

# Overview: bac success vs. expectation
print df_lycees_fm[[u'Taux Brut de Réussite Total séries',
                    u'Taux Réussite Attendu/Acad Total séries',
                    u'Taux Réussite Attendu/France Total séries']].describe().to_string()

df_lycees_fm_prive = df_lycees_fm[df_lycees_fm[u'Secteur Public=PU Privé=PR'] == 'PR'].copy()
df_lycees_fm_public = df_lycees_fm[df_lycees_fm[u'Secteur Public=PU Privé=PR'] == 'PU'].copy()

dict_dfs = {'Tous' : df_lycees_fm,
            'Prive' : df_lycees_fm_prive,
            'Public' : df_lycees_fm_public}

for title, df_temp in dict_dfs.items():
  print u'\n', title
  print u'Effectif:', df_temp[u'Effectif Présents Total séries'].sum()
  print u'Reussite (%)', df_temp[u'Nb admis'].sum() * 100 /\
                           df_temp[u'Effectif Présents Total séries'].sum()
  print u'Reussite att. Ac (%)', df_temp[u'Nb admis att. Ac'].sum() * 100 /\
                                   df_temp[u'Effectif Présents Total séries'].sum()
  print u'Reussite att. Fr(%)', df_temp[u'Nb admis att. Fr'].sum() * 100 /\
                                   df_temp[u'Effectif Présents Total séries'].sum()
