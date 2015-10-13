#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
import numpy as np
import pandas as pd

path_source = os.path.join(path_data,
                           'data_supermarkets',
                           'data_source',
                           'data_qlmc_2007-12')

path_source_csv = os.path.join(path_source,
                               'data_csv')

path_built = os.path.join(path_data,
                          'data_supermarkets',
                          'data_built',
                          'data_qlmc_2007-12')

path_built_csv = os.path.join(path_built,
                              'data_csv')

# #######################
# FIX DF QLMC
# #######################

df_qlmc = pd.read_csv(os.path.join(path_source_csv,
                                   'df_qlmc_raw.csv'),
                      encoding = 'UTF-8')

# MERGE DF QLMC STORES

print u'\nMerge df_qlmc with df_stores (store info)'
df_stores = pd.read_csv(os.path.join(path_source_csv,
                                     'df_stores_w_municipality_and_lsa_id.csv'),
                        dtype = {'id_lsa': str,
                                 'INSEE_ZIP' : str,
                                 'INSEE_Departement' : str,
                                 'INSEE_Code' : str,
                                 'QLMC_Departement' : str},
                        encoding = 'UTF-8')

# todo: do before and drop
df_stores['Store'] = df_stores['Store_Chain'] + u' ' + df_stores['Store_Municipality']
df_qlmc = pd.merge(df_stores,
                   df_qlmc,
                   on = ['Period', 'Store'],
                   how = 'right')

# MERGE DF QLMC PRODUCTS

print u'\nMerge df_qlmc with df_product_names (standardizaton)'
df_prod_names = pd.read_csv(os.path.join(path_source_csv,
                                         'df_product_names.csv'),
                          encoding='utf-8')
df_qlmc = pd.merge(df_prod_names,
                   df_qlmc,
                   on = 'Product',
                   how = 'right')

# BUILD NORMALIZED PRODUCT INDEX (needed? rather inter periods?)
print u'\nAdd Product_norm: normalized product name'
for field in ['Product_brand', 'Product_name', 'Product_format']:
  df_qlmc[field].fillna(u'', inplace = True)
df_qlmc['Product_norm'] = df_qlmc['Product_brand'] + ' - ' +\
                          df_qlmc['Product_name'] + ' - ' +\
                          df_qlmc['Product_format']

# FIX STORES WHICH WERE LISTED UNDER TWO DIFFERENT NAMES WITHIN A PERIOD
ls_fix_stores = [[4, u'SUPER U ANGERS BOURG DE PAILLE',
                  u'SUPER U', u'BEAUCOUZE'],
                 [5, u'CHAMPION ST GERMAIN DU PUY',
                  u'CARREFOUR MARKET', u'ST GERMAIN DU PUY'],
                 [9, u'CARREFOUR MARKET CLERMONT CARRE JAUDE',
                  u'CARREFOUR MARKET', u'CLERMONT FERRAND JAUDE']]

for period, old_Store, new_Store_Chain, new_Store_Municipality in ls_fix_stores:
  df_qlmc.loc[(df_qlmc['Period'] == period) &\
              (df_qlmc['Store'] == old_Store),
              ['Store_Chain', 'Store_Municipality', 'Store']] =\
                [new_Store_Chain,
                 new_Store_Municipality,
                 new_Store_Chain + ' ' + new_Store_Municipality]

# To have perfect harmonization
df_qlmc.loc[(df_qlmc['Store'] == 'SUPER U BEAUCOUZE'),
            'INSEE_Municipality'] == u'BEAUCOUZE'

# ################
# GENERAL OVERVIEW
# ################

## BUILD DATETIME DATE COLUMN
#print u'\nParse dates'
#df_qlmc['Date_str'] = df_qlmc['Date']
#df_qlmc['Date'] = pd.to_datetime(df_qlmc['Date'], format = '%d/%m/%Y')
#
## DF DATES
#df_go_date = df_qlmc[['Date', 'Period']].groupby('P').agg([min, max])['Date']
#df_go_date['spread'] = df_go_date['max'] - df_go_date['min']
#
## DF ROWS
#df_go_rows = df_qlmc[['Product', 'Period']].groupby('P').agg(len)
#
## DF UNIQUE STORES / PRODUCTS
#df_go_unique = df_qlmc[['Product', 'Store', 'Period']].groupby('P').agg(lambda x: len(x.unique()))
#
## DF GO
#df_go = pd.merge(df_go_date, df_go_unique, left_index = True, right_index = True)
#df_go['Nb rows'] = df_go_rows['Product']
#for field in ['Nb rows', 'Store', 'Product']:
#  df_go[field] = df_go[field].astype(float) # to have thousand separator
#df_go['Date start'] = df_go['min'].apply(lambda x: x.strftime('%d/%m/%Y'))
#df_go['Date end'] = df_go['max'].apply(lambda x: x.strftime('%d/%m/%Y'))
#df_go['Avg nb products/store'] = df_go['Nb rows'] / df_go['Magasin']
#df_go.rename(columns = {'Store' : 'Nb stores',
#                        'Product' : 'Nb products'},
#             inplace = True)
#df_go.reset_index(inplace = True)
#
#pd.set_option('float_format', '{:4,.0f}'.format)
#
#print '\nGeneral overview of period records'
#
#print '\nString version:'
#print df_go[['Period', 'Date start', 'Date end',
#             'Nb rows', 'Nb stores', 'Nb products', 'Avg nb products/store']].to_string(index = False)
#
#print '\nLatex version:'
#print df_go[['Period', 'Date start', 'Date end',
#             'Nb rows', 'Nb stores', 'Nb products', 'Avg nb products/store']].to_latex(index = False)

# TODO: product categories

# ##########################
# REMEDIATION TO PRICES PBMS
# ##########################

# Period 0:
## Duplicates: probably two stores(check further)
#df_inspect = df_qlmc[['Product_norm', 'Price', 'Date']]\
#               [(df_qlmc['Store'] == u'GEANT CARCASSONNE') &\
#                (df_qlmc['Period'] == 0)].copy()
#df_inspect.sort(['Product_norm', 'Date'], inplace = True)
#print df_inspect[0:100].to_string()
#df_qlmc = df_qlmc[~((df_qlmc['Period'] == 0) & (df_qlmc['Store'] == u'GEANT CARCASSONNE'))].copy()

# Period 7
## Look for highest legitimate price
#print df_qlmc['Price'][(df_qlmc['Period'] == 7) &\
#                       (df_qlmc['Product_norm'] == u"Mumm Cordon rouge champagne brut 75cl")].max()
## All those between 10 and 35 appear legit
#print df_qlmc['Product_norm'][(df_qlmc['Period'] == 7) &\
#                              (df_qlmc['Price'] >= 10) &\
#                              (df_qlmc['Price'] <= 35)].value_counts()
## Products the price of which is above 35 and should not
#print df_qlmc['Product_norm'][(df_qlmc['Period'] == 7) &\
#                              (df_qlmc['Price'] >= 35)].value_counts().to_string()

df_qlmc.loc[(df_qlmc['Period'] == 7) &\
            (df_qlmc['Price'] >= 35), 'Price'] =\
  df_qlmc.loc[(df_qlmc['Period'] == 7) &\
              (df_qlmc['Price'] >= 35), 'Price'] / 100

# Period 6, 8, 9:

# Spread above 7/8 (makes sense... but won't capture high value goods)
for per in [6, 8, 9]:
  df_qlmc_per = df_qlmc[df_qlmc['Period'] == per]
  df_pero = df_qlmc_per[['Product_norm', 'Price']].groupby('Product_norm').\
              agg([len, np.median, np.mean, np.std, min, max])['Price']
  df_pero['spread'] = df_pero['max'] - df_pero['min']
  ls_fix = list(df_pero.index[df_pero['spread'] > 8])
  df_qlmc.loc[(df_qlmc['Period'] == per) &\
              (df_qlmc['Product_norm'].isin(ls_fix)) &\
              (df_qlmc['Price'] <= 3.5), 'Price'] =\
    df_qlmc.loc[(df_qlmc['Period'] == per) &\
                (df_qlmc['Product_norm'].isin(ls_fix)) &\
                (df_qlmc['Price'] <= 3.5), 'Price'] * 10

# High value goods... check Product_norm with high prices of other periods
set_hv = set()
for i in range(6) + [7] + range(10,13):
  df_qlmc_per = df_qlmc[df_qlmc['Period'] == i]
  df_pero = df_qlmc_per[['Product_norm', 'Price']].groupby('Product_norm').\
              agg([len, np.median, np.mean, np.std, min, max])['Price']
  set_hv.update(set(df_pero.index[df_pero['max'] >= 10]))

# Find Product_norm to fix (+ still need to check for goods not present in other periods)
for per in [6, 8, 9]:
  df_qlmc_per = df_qlmc[df_qlmc['Period'] == per]
  df_pero = df_qlmc_per[['Product_norm', 'Price']].groupby('Product_norm').\
              agg([len, np.median, np.mean, np.std, min, max])['Price']
  df_pero.reset_index(inplace = True)
  ls_fix = list(df_pero['Product_norm'][(df_pero['mean'] < 5) &\
                                        (df_pero['Product_norm'].isin(list(set_hv)))])
  df_qlmc.loc[(df_qlmc['Period'] == per) &\
              (df_qlmc['Product_norm'].isin(ls_fix)), 'Price'] =\
    df_qlmc.loc[(df_qlmc['Period'] == per) &\
                (df_qlmc['Product_norm'].isin(ls_fix)), 'Price'] * 10

# ##########################
# OVERVIEW OF EACH PERIOD
# ##########################

# Check min, max price by period
print '\nPeriod min and max price:'
for per in range(13):
 df_per_prices = df_qlmc['Price'][df_qlmc['Period'] == per]
 print 'Period', per, ':', df_per_prices.min(), df_per_prices.max()

# Check if only one Family/Department per product within each period
print '\nExamination of Department and Family by product:'
for per in range(13):
  ls_col_temp = ['Period', 'Department', 'Family', 'Product_norm',
                 'Product_brand', 'Product_name', 'Product_format']
  df_products_per_st = df_qlmc[ls_col_temp][df_qlmc['Period'] == per].\
                         drop_duplicates(subset = ['Product_brand',
                                                   'Product_name',
                                                   'Product_format',
                                                   'Department',
                                                   'Family'])
  df_products_per = df_qlmc[ls_col_temp][df_qlmc['Period'] == per].\
                      drop_duplicates(subset = ['Product_brand', 'Product_name', 'Product_format'])
  if len(df_products_per) == len(df_products_per_st):
    print 'Department / Family regular for period:', per
  else:
    print 'Department / Family can differ for the same product in period:', per

# Overview of product prices per period
pd.set_option('float_format', '{:4,.2f}'.format)
format_str = lambda x: u'{:}'.format(x[:20])

for per in range(13):
  print '\n', u'-'*40, '\n'
  print 'Stats descs: per', per
  df_qlmc_per = df_qlmc[df_qlmc['Period'] == per]
  df_pero = df_qlmc_per[['Product_norm', 'Price']].groupby('Product_norm').\
              agg([len, np.median, np.mean, np.std, min, max])['Price']
  df_pero['spread'] = df_pero['max'] - df_pero['min']
  df_pero['r_spread'] = (df_pero['max'] - df_pero['min']) / df_pero['mean']
  df_pero['cv'] = df_pero['std'] / df_pero['mean']
  
  # Top XX most and least common products
  print '\nTop 10 most and least common products'
  df_pero.sort('len', inplace = True, ascending = False)
  #print df_pero[:10].to_string()
  #print df_pero[-10:].to_string()
  df_temp = pd.concat([df_pero[0:10], df_pero[-10:]])
  df_temp.reset_index(inplace = True)
  print df_temp.to_string(formatters = {'Product_norm' : format_str})
  
  # Top XX most and lest expensive products
  print '\nTop 10 most and least expensive products'
  df_pero.sort('mean', inplace = True, ascending = False)
  #print df_pero[:10].to_string()
  #print df_pero[-10:].to_string()
  print pd.concat([df_pero[0:10], df_pero[-10:]]).to_string()
  
  # Top XX highest spread (or else but look for errors!)
  print '\nTop 20 highest relative spread products'
  df_pero.sort('r_spread', inplace = True, ascending = False)
  print df_pero[0:20].to_string()
  
  # Products with duplicate records
  print '\nDuplicates within period'
  se_dup_bool = df_qlmc.duplicated(subset = ['Period', 'Store', 'Product_norm'])
  df_dup = df_qlmc[['Period', 'Store', 'Product_norm', 'Price']][se_dup_bool]
  print df_dup['Product_norm'][df_dup['Period'] == per].value_counts()[0:10]
  ## check if not b/c of Product_norm losing information
  
  ## Summary of Departments and Familys
  #
  ## Get Department DF
  #df_qlmc_r = df_qlmc_per[['Department', 'Product']].groupby('Department').agg([len])['Product']
  #
  ## Get unique Departments and Family DF
  #df_qlmc_per_rayons =\
  #   df_qlmc_per[['Department', 'Family']].drop_duplicates(['Department', 'Family'])
  #df_qlmc_per_familles =\
  #    df_qlmc_per_prod[['Family', 'Product']].groupby('Family').agg([len])['Product']
  #df_qlmc_per_familles.reset_index(inplace = True)
  #if len(df_qlmc_per_familles) == len(df_qlmc_per_rayons):
  #  df_pero_su = pd.merge(df_qlmc_per_rayons,
  #                        df_qlmc_per_familles,
  #                        left_on = 'Family',
  #                        right_on = 'Family') 
  #
  ## Get SE Family by Department
  #df_qlmc_per_rp = 
  #  df_qlmc_per[['Department', 'Family', 'Product']].drop_duplicates(['Department', 'Family', 'Product'])
  #for rayon in df_qlmc_per_rp['Department'].unique():
  #  se_rp_vc = df_qlmc_per_rp['Family'][df_qlmc_per_rp['Department'] == rayon].value_counts()
  #  print '\n', rayon, se_rp_vc.sum()
  #  print se_rp_vc


# ###################
# OVERVIEW DUPLICATES
# ###################

# EXACT DUPLICATES

ls_dup_disp = ['Period',
               'Store',
               'Department',
               'Family',
               'Product_norm',
               'Date',
               'Price']

df_qlmc_exact_dup = df_qlmc[df_qlmc.duplicated(take_last = False) |\
                            df_qlmc.duplicated(take_last = True)]

print u'\nOverview exact duplicates (1):'
print df_qlmc_exact_dup[0:4].T.to_string()

print u'\nOverview exact duplicates (2):'
print df_qlmc_exact_dup[ls_dup_disp][0:100].to_string()

#df_qlmc.drop_duplicates(inplace = True)
#
#ls_unique_cols = ['P', 'Store', 'Product_norm']
#df_qlmc_dup = df_qlmc[df_qlmc.duplicated(ls_unique_cols, take_last = False) |\
#                      df_qlmc.duplicated(ls_unique_cols, take_last = True)]
#print df_qlmc_dup[['P', 'Store', 'Department', 'Family',
#                   'Product_norm', 'Date', 'Price']][0:10].to_string()

# DUPLICATES BY PERIOD AND PRODUCT

ls_dup_pp = ['Period', 'Store', 'Department', 'Family', 'Product_norm']
df_qlmc_dup_pp = df_qlmc[df_qlmc.duplicated(ls_dup_pp, take_last = False) |\
                         df_qlmc.duplicated(ls_dup_pp, take_last = True)]

df_su_dup_pp = pd.pivot_table(data = df_qlmc_dup_pp[['Period', 'Product_norm']],
                              index = ['Period', 'Product_norm'],
                              aggfunc = len,
                              fill_value = 0).astype(int)

print u'\nProducts (by period) with high duplicate count (over 10)'
print df_su_dup_pp[df_su_dup_pp > 10].to_string()
# Drop those problematic products (a lot from period 10 on)
dict_dup_pp_drop = {}
for Period, Product_norm in df_su_dup_pp[df_su_dup_pp > 10].index:
	# print Period, Product_norm
  dict_dup_pp_drop.setdefault(Period, []).append(Product_norm)
ls_dup_pp_drop = [(k,v) for k,v in dict_dup_pp_drop.items()]

for Period, ls_Product_norm in ls_dup_pp_drop:
  df_qlmc.drop(df_qlmc[(df_qlmc['Period'] == Period) &\
                       (df_qlmc['Product_norm'].isin(ls_Product_norm))].index,
               axis = 0,
               inplace = True)

# DUPLICATES BY PERIOD AND STORE

df_su_dup_ps = pd.pivot_table(data = df_qlmc_dup_pp[['Period', 'Store']],
                              index = ['Period', 'Store'],
                              aggfunc = len,
                              fill_value = 0).astype(int)
print u'\nStores (by period) with high duplicate count (over 200)'
print df_su_dup_ps[df_su_dup_ps > 200].to_string()
# Drop those problematic products (a lot from period 10 on)
# Probably overlap with previous pbms
dict_dup_ps_drop = {}
for Period, Store in df_su_dup_ps[df_su_dup_ps > 200].index:
	# print Period, Store
  dict_dup_ps_drop.setdefault(Period, []).append(Store)
ls_dup_ps_drop = [(k,v) for k,v in dict_dup_ps_drop.items()]

for Period, ls_Store in ls_dup_ps_drop:
  df_qlmc.drop(df_qlmc[(df_qlmc['Period'] == Period) &\
                       (df_qlmc['Store'].isin(ls_Store))].index,
               axis = 0,
               inplace = True)

# DROP REMAINING DUPLICATES (only redundant obs?)

ls_dup_sup = ['Period', 'Store', 'Department', 'Family', 'Product_norm']
df_qlmc = df_qlmc[~(df_qlmc.duplicated(ls_dup_sup, take_last = False) |\
                    df_qlmc.duplicated(ls_dup_sup, take_last = True))]

# INSPECT ASSOCIATIONS OF ONE id_lsa WITH TWO STORES WITHIN A PERIOD
# fixed at the beginning of this script hence no more results

ls_store_cols = df_stores.columns.tolist()
df_stores = df_qlmc[ls_store_cols].drop_duplicates(['Period', 'Store', 'id_lsa'])

se_stores_dup = pd.pivot_table(data = df_stores[['Period', 'id_lsa']],
                               index = ['Period', 'id_lsa'],
                               aggfunc = len,
                               fill_value = 0).astype(int)
print se_stores_dup[se_stores_dup != 1]

for Period, id_lsa in se_stores_dup[se_stores_dup != 1].index:
  print df_stores[(df_stores['Period'] == Period) &\
                  (df_stores['id_lsa'] == id_lsa)].to_string()

# PRODUCTS LISTED UNDER SEVERAL DPTS/FAMILIES?

print len(df_qlmc[df_qlmc.duplicated(['Period', 'Store', 'Product_norm'], take_last = True) |\
                  df_qlmc.duplicated(['Period', 'Store', 'Product_norm'], take_last = False)])

### ######
### OUTPUT
### ######
#
#df_qlmc.drop(['id_fra_stores', 'id_fra_stores_2', 'street_fra_stores'],
#             axis = 1,
#             inplace = True)
#
#df_qlmc.to_csv(os.path.join(path_built_csv,
#                            'df_qlmc.csv'),
#                  float_format='%.2f',
#                  encoding='utf-8',
#                  index=False)
#
## todo: try working with lighter files
## - split between products and stores
## - drop Product_norm (can be easily re-created)



## ##########################################
## DEPRECATED: INSPECTION OF PRICE DUPLICATES
## ##########################################
#
## per 0:
## Blédina: same day, 10c gap, unsure why
## Viva TGV 6x50cl: same day, big pricd diff, check if no price b/ 1 & 2: bottle vs. pack?
#
## per 1:
## Blédina: same as in per 0
## Elle & Vire 250g: same day, 10-20c gap, unsure why
## Viva TGV 6x50cl: same as in per 0
## Viva TGV 1L: same day, 10c gap, unsure why
## Silhouette UHT 1L: same day, 10-20c gap, unsure why
#
## per 2:
## Elle & Vire 250g: same as in 0, 1
## William Saurin: same day, 50c diff a.e., promotion?
## Geant Vert: same day, 50-150c diff a.e., promotion?
## Viva TGV 1L: same as in 1
## Viva TGV 6x50cl: same as in 0, 1
## Silhouette UHT 1L: same as in 1
## Silhouette UHT 6x1L: same day, in fact two prod names... small diff not everywhere
#
## per 3:
## Blédina: same as in per 0, 1, 2
## William Saurin: same as in per 2
## Elle & Vire 250g: same as in 0, 1, 2
## Geant Vert: same as in per 2
## Viva TGV 6x50cl: same as in 0, 1, 2
## Viva TGV 1L: same as in 1, 2
## Silhouette UHT 1L: same as in 1, 2
## Silhouette UHT 6x1L: same as in per 2
#
## per 4:
## Elle & Vire 250g: same as in 0, 1, 2, 3
## Viva TGV 1L: same as in 1, 2, 3
## Viva TGV 6x50cl: same as in 0, 1, 2, 3
## Silhouette UHT 1L: same as in 1, 2, 3
#
## per 5
## Viva TGV 6x50cl: same as in 0, 1, 2, 3, 4
## Viva TGV 1L: same as in 1, 2, 3, 4
## Silhouette UHT 1L: same as in 1, 2, 3, 4
#
## per 6
## Viva TGV 1L: same as in 1, 2, 3, 4, 5
## Silhouette UHT 1L: same as in 1, 2, 3, 4, 5
#
## per 7
## Viva TGV 1L: same as in 1, 2, 3, 4, 5, 6
## Viva TGV 6x50cl: same as in 0, 1, 2, 3, 4, 5
## Silhouette UHT 1L: same as in 1, 2, 3, 4, 5, 6
## Nos villages oeufs: same day, 50c diff, not everywhere
#
## per 8
## Viva TGV 1L: same as in 1, 2, 3, 4, 5, 6, 7
## Viva TGV 6x50cl: same as in 0, 1, 2, 3, 4, 5, 7
## Silhouette UHT 1L: same as in 1, 2, 3, 4, 5, 6, 7
## Nos villages oeufs: same as in 7 (Prod name differs tho)
#
## TBC: anyway drop all
#
#ls_dup_drop = [(0, u"Blédina - Pêche fraise dès 4 mois, 2 Pots - 260g"),
#               (0, u"Viva - Lait TGV demi-écrémé vitaminé, Bouteille plastique 6x50cl"),
#               (1, u"Blédina - Pêche fraise, 260g"),
#               (1, u"Elle & Vire - Beurre doux tendre, 250g"),
#               (1, u"Viva Lait TGV demi-écrémé vitaminé 6x50cl"),
#               (1, u"Viva - Lait TGV demi-écrémé vitaminé, 1L"),
#               (1, u"Silhouette - Lait UHT écrémé source équilibre, 1L"),
#               (2, u"Elle & Vire Beurre doux tendre 250g"),
#               (2, u"William Saurin Choucroute garnie au vin blanc 400g"),
#               (2, u"Geant Vert - Asperges blanches, 190g"),
#               (2, u"Viva - Lait TGV demi-écrémé vitaminé, 1L"),
#               (2, u"Viva - Lait TGV demi-écrémé vitaminé, 6x50cl"),
#               (2, u"Silhouette - Lait UHT écrémé source équilibre, 1L"),
#               (2, u"Silhouette - Lait UHT écrémé vitaminé, 6x1L"), # check both
#               (2, u" Silhouette -Lait UHT écrémé vitaminé, 6x1L"),
#               (3, u"Blédina Pêche fraise 260g"),
#               (3, u"William Saurin Choucroute garnie au vin blanc 400g"),
#               (3, u"Elle & Vire - Beurre doux tendre, 250g"),
#               (3, u"Geant Vert - Asperges blanches, 190g"),
#               (3, u"Viva Lait TGV demi-écrémé vitaminé 6x50cl"),
#               (3, u"Viva - Lait TGV demi-écrémé vitaminé, 1L"),
#               (3, u"Silhouette - Lait UHT écrémé source équilibre, 1L"),
#               (2, u"Silhouette - Lait UHT écrémé vitaminé, 6x1L"),
#               (3, u" Silhouette -Lait UHT écrémé vitaminé, 6x1L"),
#               (4, u"Elle & Vire - Beurre doux tendre, 250g"),
#               (4, u"Viva - Lait TGV demi-écrémé vitaminé, 1L"),
#               (4, u"Viva - Lait TGV demi-écrémé vitaminé, 6x50cl"),
#               (4, u"Silhouette - Lait UHT écrémé source équilibre, 1L"),
#               (5, u"Viva - Lait TGV demi-écrémé vitaminé, 6x50cl"),
#               (5, u"Viva - Lait TGV demi-écrémé vitaminé, 1L"),
#               (5, u"Silhouette - Lait UHT écrémé source équilibre, 1L"),
#               (6, u"Viva - Lait TGV demi-écrémé vitaminé, 1L"),
#               (6, u"Silhouette - Lait UHT écrémé source équilibre, 1L"),
#               (7, u"Viva - Lait TGV demi-écrémé vitaminé, 1L"),
#               (7, u"Viva - Lait TGV demi-écrémé vitaminé, 6x50cl"),
#               (7, u"Silhouette Lait UHT écrémé source équilibre 1L"),
#               (7, u'Nos villages - Gros Å"ufs fermiers, x6'),
#               (8, u'Viva - Lait TGV demi-écrémé vitaminé, 1L'),
#               (8, u"Viva - Lait TGV demi-écrémé vitaminé, 6x50cl"),
#               (8, u"Silhouette - Lait UHT écrémé source équilibre, 1L"),
#               (8, u"Nos villages - Gros Sufs fermiers, x6")]
