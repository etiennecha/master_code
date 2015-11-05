#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
import os
from datetime import date, timedelta
from functions_generic_drive import *
import matplotlib.pyplot as plt

path_built = os.path.join(path_data,
                           u'data_supermarkets',
                           u'data_built',
                           u'data_drive',
                           u'data_carrefour')

path_built_csv = os.path.join(path_built,
                              u'data_csv')

ls_df_voisins_2013_2014 = ['df_master_voisins_2013-14',
                            'df_prices_voisins_2013-14',
                            'df_products_voisins_2013-14']

dict_df = {}
for df_file_title in ls_df_voisins_2013_2014:
  dict_df[df_file_title] =\
    pd.read_csv(os.path.join(path_built_csv,
                             '{:s}.csv'.format(df_file_title)),
                dtype = {'date' : str,
                         'promo' : str},
                encoding = 'utf-8')

df_master   = dict_df['df_master_voisins_2013-14']
df_prices   = dict_df['df_prices_voisins_2013-14']
df_products = dict_df['df_products_voisins_2013-14']

pd.set_option('display.float_format', '{:,.2f}'.format)

# ##################
# FIX PROMO (MOVE?)
# ##################

# Create Boolean (todo: check distinction with loyalty)
for df_temp in [df_master, df_prices]:
  # create promo dummy
  df_temp['dum_promo'] = False
  df_temp.loc[(~df_temp['promo'].isnull()) &\
              (~df_temp['promo'].str.contains(u'fidélité',
                                              case = False,
                                              na = False)),
              'dum_promo'] = True
  # create loyalty dummy
  df_temp['dum_loyalty'] = False
  df_temp.loc[(~df_temp['promo'].isnull()) &\
              (df_temp['promo'].str.contains(u'fidélité',
                                             case = False,
                                             na = False)),
              'dum_loyalty'] = True
  # create loyalty field, fill if must be and then erase promo
  df_temp['loyalty'] = None
  df_temp.loc[df_temp['dum_loyalty'],
              'loyalty'] = df_temp['promo']
  df_temp.loc[df_temp['dum_loyalty'],
              'promo'] = None

# ######################
# OVERVIEW BY PERIOD
# ######################

# - nb unique section/family/product
# - nb unique products
# - nb unique section/family/promo
# - nb unique promo
# - same with loyalty?

# - redo by section

# - desc types of promo (loyalty?) used, by section
# - promo, loyalty in terms of value?

ls_cols_prod_0 = ['date', 'section', 'family', 'brand', 'title', 'label']
ls_cols_prod_1 = ['date', 'brand', 'title', 'label']

se_nb_prod_0 = df_master.drop_duplicates(ls_cols_prod_0).groupby('date').agg(len)['title']
se_nb_prod_1 = df_master.drop_duplicates(ls_cols_prod_1).groupby('date').agg(len)['title']

# loop to include loyalty?
se_nb_promo_0 = df_master[~df_master['promo'].isnull()]\
                  .drop_duplicates(ls_cols_prod_0).groupby('date').agg(len)['title']

se_nb_promo_1 = df_master[~df_master['promo'].isnull()]\
                  .drop_duplicates(ls_cols_prod_1).groupby('date').agg(len)['title']

df_overview = pd.concat([se_nb_prod_0,
                         se_nb_prod_1,
                         se_nb_promo_0,
                         se_nb_promo_1],
                        axis = 1,
                        keys = ['nb_prod', 'nb_u_prod', 'nb_promo', 'nb_u_promo'])
df_overview.index = pd.to_datetime(df_overview.index, format = '%Y%m%d')

ind_overview = pd.date_range(start = df_overview.index[0],
                             end   = df_overview.index[-1], 
                             freq='D')
df_overview = df_overview.reindex(ind_overview, fill_value = np.nan)

df_overview[['nb_prod', 'nb_u_prod']].plot()
plt.show()

df_overview[['nb_promo', 'nb_u_promo']].plot()
plt.show()

df_overview['pct_promo'] = df_overview['nb_promo'] / df_overview['nb_prod']
df_overview['pct_u_promo'] = df_overview['nb_u_promo'] / df_overview['nb_u_prod']

df_overview[['pct_promo', 'pct_u_promo']].plot()
plt.show()

# ######################
# TYPES OF PROMOTIONS
# ######################

print u'\nOverview types of promotions:'
se_promo_vc = df_master[~df_master['promo'].isnull()]['promo'].value_counts()
print se_promo_vc[0:20].to_string()
# Can parse:
# "PROMO - X%"
# "X achetés Y de remise"
# "Prenez en X Payez en Y"
# => "TOP AFFAIRE" ? & "Vu au catalogue"?

print u'\nOverview types of loyalty promotions:'
se_loyalty_vc = df_master[~df_master['loyalty'].isnull()]['loyalty'].value_counts()
print se_loyalty_vc[0:20].to_string()
# Simpler... an amount

# ######################
# PROMOTIONS BY SECTION
# ######################

print u'\nOverview by section:'

# todo: loop
# aggfunc "count" counts 1 if non empty

df_section_prod = df_master.drop_duplicates(ls_cols_prod_0).pivot_table(index = 'date',
                                                                        columns = 'section',
                                                                        values = 'total_price',
                                                                        aggfunc = 'count')


print u'\nNb products by section:'
print df_section_prod.describe().to_string()

df_section_promo = df_master.drop_duplicates(ls_cols_prod_0).pivot_table(index = 'date',
                                                                         columns = 'section',
                                                                         values = 'promo',
                                                                         aggfunc = 'count')

print u'\nNb promo by section:'
print df_section_promo.describe().to_string()

df_section_prod.fillna(0, inplace = True)
df_section_promo_pct = df_section_promo / df_section_prod

print u'\Pct promo/product by section:'
print df_section_promo_pct.describe().to_string()

df_section_promo_pct[[u'Épicerie', u'Boissons']].plot()
plt.show()

print u'\nCorrelation in nb promo across sections:'
print df_section_promo.corr().to_string()

#### DEPARTMENTS: NB PRODUCTS AND PROMO
## Plot pct and nb (todo: add vertical lines on mondays)
#se_avg_dpt_nb_prod = df_dpt_nb_prod.mean()
#se_avg_dpt_nb_prod.sort(ascending = False)
##df_dpt_pct_promo['weekday'] = df_dpt_pct_promo.index.weekday
#
##ls_col_disp = se_avg_dpt_nb_prod.index[4:6]
#ls_col_disp = [u'Épicerie', u'Hygiène & Beauté', u'Boissons', u'Crèmerie']
#ax = df_dpt_pct_promo[ls_col_disp][50:230].plot()
#for date, dow in zip(df_dpt_pct_promo.index, df_dpt_pct_promo.index.weekday):
#  if dow == 0: # dow is monday
#    plt.axvline(date, color = 'k', linestyle = ':')
#ax.grid('on', which='major', axis='x', linestyle = '--')
## ax.grid('off', axis='y')
#plt.show()
#
##df_dpt_nb_promo[se_avg_dpt_nb_prod.index[0:2]][200:500].plot()
##plt.show()

#### SUBDEPARTMENTS: NB PRODUCTS AND PROMO
#
## Nb products
#df_subdpt_nb_prod = df_master_2013.pivot_table(values='total_price',
#                                          index='date',
#                                          columns=['section', 'family'],
#                                          aggfunc='count')
#df_subdpt_nb_prod.index = pd.to_datetime(df_subdpt_nb_prod.index, format = '%Y%m%d')
#df_subdpt_nb_prod = df_subdpt_nb_prod.reindex(index_overview, fill_value = np.nan)
#
#se_subdpt_max = df_subdpt_nb_prod.max()
#df_subdpt_desc = df_subdpt_nb_prod.describe().T
#
##print df_subdpt_desc.to_string()
#
## looks like never more than 100
## did not go beyond first page for each subdpt
## check with other dpts
## then only got a sample of products... compare with more recent data then
#
#print u"\nNb of subdpts with 100 products at least once: {:d} among {:d}"\
#          .format(len(df_subdpt_desc[df_subdpt_desc['max'] == 100]),
#                  len(df_subdpt_desc))
#
#print u"\nNb of subdpts with 100 products Q75% days: {:d} among {:d}"\
#          .format(len(df_subdpt_desc[df_subdpt_desc['75%'] == 100]),
#                  len(df_subdpt_desc))
#
## Nb products: focus on one departement (drop?) 
#df_sdpt_nb_prod = df_master_2013[df_master_2013['section'] == u'Maison & Entretien']\
#                  .pivot_table(values='total_price',
#                               index='date',
#                               columns='family',
#                               aggfunc='count')
#df_sdpt_nb_prod.index = pd.to_datetime(df_sdpt_nb_prod.index, format = '%Y%m%d')
#df_sdpt_nb_prod = df_sdpt_nb_prod.reindex(index_overview, fill_value = np.nan)
##df_sdpt_nb_prod.plot(ylim = (0,150))
##plt.show()
#
## Nb promo
#df_subdpt_nb_promo = df_master_2013[~df_master_2013['promo'].isnull()]\
#                       .pivot_table(values='total_price',
#                                    index='date',
#                                    columns=['section', 'family'],
#                                    aggfunc='count')
#df_subdpt_nb_promo.index = pd.to_datetime(df_subdpt_nb_promo.index, format = '%Y%m%d')
#df_subdpt_nb_promo = df_subdpt_nb_promo.reindex(index_overview, fill_value = np.nan)
