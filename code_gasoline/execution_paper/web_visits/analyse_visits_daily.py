#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import add_to_path_sub
from add_to_path_sub import path_data
from generic_master_price import *
from generic_master_info import *
from generic_competition import *
import copy
import collections

path_dir_built_paper = os.path.join(path_data, 'data_gasoline', 'data_built', 'data_paper')

path_dir_built_json = os.path.join(path_dir_built_paper, 'data_json')
path_diesel_price = os.path.join(path_dir_built_json, 'master_price_diesel.json')
path_info = os.path.join(path_dir_built_json, 'master_info_diesel.json')
path_info_output = os.path.join(path_dir_built_json, 'master_info_diesel_for_output.json')

path_dir_source = os.path.join(path_data, 'data_gasoline', 'data_source')
path_dict_brands = os.path.join(path_dir_source, 'data_other', 'dict_brands.json')
path_csv_insee_data = os.path.join(path_dir_source, 'data_other', 'data_insee_extract.csv')

path_dir_zagaz = os.path.join(path_dir_source, 'data_stations', 'data_zagaz')

path_dir_insee = os.path.join(path_data, 'data_insee')
path_dir_match_insee_codes = os.path.join(path_dir_insee, 'match_insee_codes')
path_dict_dpts_regions = os.path.join(path_dir_insee, 'dpts_regions', 'dict_dpts_regions.json')

path_dir_web_visits = os.path.join(path_dir_source, 'data_web_visits')
path_dir_rotterdam = os.path.join(path_dir_source, 'data_rotterdam')
path_xlsx_ufip = os.path.join(path_dir_rotterdam, 'ufip-valeurs_2006-01-01_au_2013-12-31.xlsx')

master_price = dec_json(path_diesel_price)
master_info = dec_json(path_info_output)
dict_brands = dec_json(path_dict_brands)
dict_dpts_regions = dec_json(path_dict_dpts_regions)

# ############
# LOAD FILES
# ############

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

# Price level and price changes
zero = 0.000001
ls_dates = [pd.to_datetime(date) for date in master_price['dates']]
df_price = pd.DataFrame(master_price['diesel_price'], master_price['ids'], ls_dates).T
df_price_chge = df_price.shift(1) - df_price
ls_res = []
for ind in df_price_chge.index:
  ls_res.append(len(df_price_chge.ix[ind][np.abs(df_price_chge.ix[ind]) > zero]))
se_nb_chges = pd.Series(ls_res, ls_dates)
se_nb_chges[se_nb_chges < zero] = np.nan

df_registrations['nb_chges'] = se_nb_chges
df_registrations['price_gazole_ttc'] = df_price.mean(1)

# Harmonize (base 100) and plot registrations, nb price changes and price
df_visits = df_registrations['2011-09-04':'2013-06-04']
df_visits['registrations_base100'] = df_visits['registrations'] /\
                                         df_visits['registrations'].max() * 100
df_visits['nb_chges_base100'] = df_visits['nb_chges'] /\
                                         df_visits['nb_chges'].max() * 100
df_visits['price_gazole_ttc_base100'] = df_visits['price_gazole_ttc'] /\
                                                 df_visits['price_gazole_ttc'].max() * 100
# df_visits[['nb_chges_base100', 'price_gazole_ttc_base100', 'registrations_base100']].plot()
df_visits[['price_gazole_ttc_base100', 'registrations_base100']].plot()
plt.show()

# Plot registrations, and price (two y axis)
fig = plt.figure()
ax1 = fig.add_subplot(111)
df_visits['registrations'].plot(ax = ax1 , c='g')
ax2 = ax1.twinx()
df_visits['price_gazole_ttc'].plot(ax = ax2, c='b')
ax1.grid()
plt.show()

# Plot registrations, and price (two y axis)
fig = plt.figure()
ax1 = fig.add_subplot(111)
df_visits['registrations'].plot(ax = ax1 , c='g')
ax2 = ax1.twinx()
df_visits['nb_chges'].plot(ax = ax2, c='b')
ax1.grid()
plt.show()

# Regressions
df_visits['week_day'] = [x.weekday() for x in df_visits.index]
df_visits['tax_cut'] = 0
df_visits['tax_cut'][(df_visits.index == '2012-08-28') |\
                     (df_visits.index == '2012-08-29')] = 1
df_visits['price_gazole_ttc_D'] = df_visits['price_gazole_ttc'] -  df_visits['price_gazole_ttc'].shift(1)
df_visits['price_gazole_ttc_Da'] = df_visits['price_gazole_ttc_D'].abs()

formula = 'registrations ~ nb_chges + price_gazole_ttc + C(week_day) + tax_cut + price_gazole_ttc_D'
print smf.ols(formula = formula,
              missing = 'drop',
              data = df_visits).fit().summary()

# TODO: check cointegration

df_visits['price_gazole_ttc_l1'] = df_visits['price_gazole_ttc'].shift(1)
df_visits['registrations_l1'] = df_visits['registrations'].shift(1)

for i in range(1, 10):
  df_visits['price_gazole_ttc_l%s' %i] = df_visits['price_gazole_ttc'].shift(i)

# #################
# PLOT AND ANALYSE
# #################

# 2011-03 : Articles sur prix records
# http://www.lefigaro.fr/conso/2011/02/28/05007-20110228ARTFIG00578-les-prix-de-l-essence-frolent-leurs-records-de-2008.php => is it because of time delta?
# http://tempsreel.nouvelobs.com/economie/20110307.OBS9264/prix-de-l-essence-record-historique-a-la-pompe.html
# 2011-08 : Articles sur Besson qui exige baisse rapide
# http://www.lefigaro.fr/conso/2011/08/11/05007-20110811ARTFIG00271-besson-veut-que-les-prix-a-la-pompe-baisse-avant-le-15-aout.php
# http://www.tf1.fr/auto-moto/actualite/le-prix-de-l-essence-a-baisse-moins-que-prevu-en-aout-2011-6663328.html
# 2012-08-26 : Communique de Moscovici sur baisse des prix du carburant etc.
# http://www.lefigaro.fr/conso/2012/08/27/05007-20120827ARTFIG00376-la-baisse-du-prix-de-l-essence-limitee-a-quelques-centimes.php

## Graph with all small peaks (40)
#ax = df_google_2[['prix_carburant', 'gazole_ttc_base100']].plot()
#for date in df_google_2.index[df_google_2['prix_carburant'] > 50]:
#  ax.axvline(x=date, linewidth=1, color='r')
#  print date
#plt.show()
#
## With zagaz data
#df_google_2['zagaz'] = df_registrations_w['registrations']
#df_google_2['zagaz_base100'] = df_google_2['zagaz'] / df_google_2['zagaz'].max()*100
#ax = df_google_2[['prix_carburant', 'gazole_ttc_base100', 'zagaz_base100']].plot()
#plt.show()
