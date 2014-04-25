#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import add_to_path_sub
from add_to_path_sub import path_data
from generic_master_price import *
from generic_master_info import *
import copy
import collections

path_dir_source = os.path.join(path_data, 'data_gasoline', 'data_source')

path_dir_web_visits = os.path.join(path_dir_source, 'data_web_visits')
path_csv_google = os.path.join(path_dir_web_visits, u'20140422_google_trend_prix_carburant.csv')
path_csv_dgec = os.path.join(path_dir_web_visits, u'20140424_dgec_prix_carburants.csv')
path_dir_rotterdam = os.path.join(path_dir_source, 'data_rotterdam')
path_xlsx_ufip = os.path.join(path_dir_rotterdam, 'ufip-valeurs_2006-01-01_au_2013-12-31.xlsx')

path_dir_zagaz = os.path.join(path_dir_source, 'data_stations', 'data_zagaz')

# ############
# LOAD FILES
# ############

# UFIP FILE (keep? replace by reuters?)
ufip_excel_file = pd.ExcelFile(path_xlsx_ufip)
df_ufip = ufip_excel_file.parse('Worksheet')
#ls_u_drop = ['GAZOLE TTC', 'GAZOLE HTT',
#             'SP95 HTT', 'SP95 TTC',
#             'FOD HTT', 'FOD TTC', 'FOD (Rotterdam)']
#df_ufip.drop(ls_u_drop, inplace = True, axis = 1)
dict_u_cols = {u'Marge de raffinage (€/t)': 'UFIP Ref margin ET',
               u'GAZOLE (Rotterdam)'      : 'UFIP RT Diesel R5 EL',
               u'SP95 (Rotterdam)'        : 'UFIP RT SP95 R5 EL',
               u'Brent ($ / baril)'       : 'UFIP Brent R5 DB',
               u'Brent (€ / baril)'       : 'UFIP Brent R5 EB',
               u'Parité (€/$)'            : 'UFIP Rate ED'}
df_ufip = df_ufip.rename(columns = dict_u_cols)
df_ufip.set_index('Date', inplace = True)

# Google Trend file
df_google = pd.read_csv(path_csv_google, index_col = 0, parse_dates = [0])
del(df_google['semaine_range']) # move to formatting file

# DGEC price file
df_dgec = pd.read_csv(path_csv_dgec, index_col = 0, parse_dates = [0])

# Zagaz user file
dict_zagaz_users = dec_json(os.path.join(path_dir_zagaz, '20140408_dict_zagaz_user_info.json'))
ls_registration_dates = [v[0][3][1] for k,v in dict_zagaz_users.items() if v and v[0]]
dict_registration_dates = dict(collections.Counter(ls_registration_dates))
df_registrations_temp = pd.DataFrame([(k,v) for k,v in dict_registration_dates.items()],
                                     columns = ['date', 'nb_registrations'])
df_registrations_temp.index = [pd.to_datetime(date) for date in df_registrations_temp['date']]

index = pd.date_range(start = pd.to_datetime('20060101'),
                      end   = pd.to_datetime('20140423'), 
                      freq='D')
df_registrations = pd.DataFrame(None, index = index)
df_registrations['registrations'] = df_registrations_temp['nb_registrations']
df_registrations['registrations'] = df_registrations['registrations'].fillna(0)
#df_registrations['registrations'].plot()
#plt.show()
df_registrations_w = df_registrations.resample('W', how = 'sum')

# ###########
# MERGE FILES
# ###########

## Harmonize week starting dates (fundamental pbm though)
# df_google['2004':]
# df_dgec['2004':]
df_dgec.index = pd.Series(df_dgec.index).apply(lambda x: \
                  x + pd.tseries.offsets.timedelta(days=2))
# Import DGEC data in Google dataframe (same week start luckily)
df_google['gazole_ttc'] = df_dgec[u'Gazole PRIX DE VENTE T.T.C.']
df_google['gazole_ht'] = df_dgec[u'Gazole PRIX DE VENTE H.T.T.']
df_google['sp95_ttc'] = df_dgec[u'Super SP95 PRIX DE VENTE T.T.C.']
df_google['sp95_ht'] = df_dgec[u'Super SP95 PRIX DE VENTE H.T.T.']

## BASE 100 from 2004
df_google['gazole_ttc_base100'] = df_google['gazole_ttc'] / df_google['gazole_ttc'].max() * 100
#df_google[['prix_carburant', 'gazole_ttc_base100']].plot()
#plt.show()

# BASE 100 from 2004
df_google_2 = df_google['2007-04':]
df_google_2['gazole_ttc_base100'] = df_google_2['gazole_ttc'] / df_google_2['gazole_ttc'].max() * 100
df_google_2['prix_carburant'] = df_google_2['prix_carburant'] / df_google_2['prix_carburant'].max() * 100
ax = df_google_2[['prix_carburant', 'gazole_ttc_base100']].plot()
# Annonce dispo 28/08/2012
ax.axvline(x=pd.to_datetime('2012-08-26'), linewidth=1, color='r')
# Annonce fin dispo 28/11/2012 (dbt de fin 01/12/2012)
ax.axvline(x=pd.to_datetime('2012-11-28'), linewidth=1, color='r')
# Dispo totalement termine 11/01/2013
ax.axvline(x=pd.to_datetime('2012-12-30'), linewidth=1, color='r')
plt.show()

# TODO: add baril prices

# Largest peaks (60): explanations
print df_google_2[df_google_2['prix_carburant'] > 60]
# 2011-03 : Articles sur prix records
# http://www.lefigaro.fr/conso/2011/02/28/05007-20110228ARTFIG00578-les-prix-de-l-essence-frolent-leurs-records-de-2008.php => is it because of time delta?
# http://tempsreel.nouvelobs.com/economie/20110307.OBS9264/prix-de-l-essence-record-historique-a-la-pompe.html
# 2011-08 : Articles sur Besson qui exige baisse rapide
# http://www.lefigaro.fr/conso/2011/08/11/05007-20110811ARTFIG00271-besson-veut-que-les-prix-a-la-pompe-baisse-avant-le-15-aout.php
# http://www.tf1.fr/auto-moto/actualite/le-prix-de-l-essence-a-baisse-moins-que-prevu-en-aout-2011-6663328.html
# 2012-08-26 : Communique de Moscovici sur baisse des prix du carburant etc.
# http://www.lefigaro.fr/conso/2012/08/27/05007-20120827ARTFIG00376-la-baisse-du-prix-de-l-essence-limitee-a-quelques-centimes.php

# Graph with all small peaks (40)
ax = df_google_2[['prix_carburant', 'gazole_ttc_base100']].plot()
for date in df_google_2.index[df_google_2['prix_carburant'] > 50]:
  ax.axvline(x=date, linewidth=1, color='r')
  print date
plt.show()

# With zagaz data
df_google_2['zagaz'] = df_registrations_w['registrations']
df_google_2['zagaz_base100'] = df_google_2['zagaz'] / df_google_2['zagaz'].max()*100
ax = df_google_2[['prix_carburant', 'gazole_ttc_base100', 'zagaz_base100']].plot()
plt.show()
