#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
from generic_competition import *
import copy
import collections

path_dir_built_paper = os.path.join(path_data,
                                    'data_gasoline',
                                    'data_built',
                                    'data_paper_dispersion')

path_dir_built_csv = os.path.join(path_dir_built_paper, 'data_csv')

path_dir_source = os.path.join(path_data,
                               'data_gasoline',
                               'data_source')

path_dir_zagaz = os.path.join(path_dir_source, 'data_stations', 'data_zagaz')

path_dir_web_visits = os.path.join(path_dir_source, 'data_web_visits')

# ############
# LOAD FILES
# ############

# LOAD ZAGAZ USER FILES
dict_zagaz_users = dec_json(os.path.join(path_dir_zagaz,
                                         '20140408_dict_zagaz_user_info.json'))

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

# LOAD DF PRICES
zero = 1e-5

df_prices_ttc = pd.read_csv(os.path.join(path_dir_built_csv,
                                         'df_prices_ttc_final.csv'),
                        parse_dates = ['date'])
df_prices_ttc.set_index('date', inplace = True)

# BUILD DF AGG CHANGES
df_price_changes = df_prices_ttc - df_prices_ttc.shift(1)
ls_rows_agg_chges = []
for ind in df_price_changes.index:
  se_day_chges = df_price_changes.ix[ind]
  ls_rows_agg_chges.append([se_day_chges[df_price_changes.ix[ind] > zero].count(),
                            se_day_chges[df_price_changes.ix[ind] < -zero].count(),
                            se_day_chges[df_price_changes.ix[ind].abs() > zero].count(),
                            se_day_chges.count()])
df_agg_chges = pd.DataFrame(ls_rows_agg_chges,
                            index = df_price_changes.index,
                            columns = ['nb_pos_chges',
                                       'nb_neg_chges',
                                       'nb_chges',
                                       'nb_obs'])
# Caution: need to set nb chges to nan instead of 0 if nb_obs == 0
df_agg_chges.loc[df_agg_chges['nb_obs'] == 0,
                 ['nb_pos_chges', 'nb_neg_chges', 'nb_chges']] = np.nan

# UPDATE ZAGAZ FILES
df_registrations['nb_chges'] = df_agg_chges['nb_chges']
df_registrations['nb_neg_chges'] = df_agg_chges['nb_neg_chges']
df_registrations['nb_pos_chges'] = df_agg_chges['nb_pos_chges']
df_registrations['price_gazole_ttc'] = df_prices_ttc.mean(1)

# Harmonize (base 100) and plot registrations, nb price changes and price
df_visits = df_registrations['2011-09-04':'2013-06-04'].copy()
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
df_visits.loc['2012-08-28':'2012-09-01', 'tax_cut'] = 1
df_visits['price_gazole_ttc_D'] = df_visits['price_gazole_ttc'] -  df_visits['price_gazole_ttc'].shift(1)
df_visits['price_gazole_ttc_Da'] = df_visits['price_gazole_ttc_D'].abs()

formula = 'registrations ~ nb_chges + price_gazole_ttc + C(week_day) + tax_cut + price_gazole_ttc_D'
print smf.ols(formula = formula,
              missing = 'drop',
              data = df_visits).fit().summary()
# seems: nb of changes has no impact


# todo: check cointegration

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
