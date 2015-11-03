#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
import os
from datetime import date, timedelta
from functions_generic_drive import *

path_built = os.path.join(path_data,
                          u'data_supermarkets',
                          u'data_built',
                          u'data_drive',
                          u'data_leclerc')

path_built_csv = os.path.join(path_built,
                              u'data_csv')

ls_df_leclerc_2015 = ['df_master_leclerc_2015',
                      'df_prices_leclerc_2015',
                      'df_products_leclerc_2015']

ls_disp_prod = ['idProduit', 'title', 'label']

dict_df = {}
for df_file_title in ls_df_leclerc_2015:
  dict_df[df_file_title] =\
    pd.read_csv(os.path.join(path_built_csv,
                             '{:s}.csv'.format(df_file_title)),
                dtype = {'date' : str,
                         'lib_0' : str,
                         'lib_1' : str,
                         'loyalty': str,
                         'promo_per_unit' : str,
                         'lib_promo' : str,
                         'dum_promo' : bool},
                encoding = 'utf-8')

df_master = dict_df['df_master_leclerc_2015']
df_prices = dict_df['df_prices_leclerc_2015']
df_products = dict_df['df_products_leclerc_2015']

# #########################
# CHECK NAN AND DUPLICATES
# #########################

# todo: move to formatting?

print u'\nNb rows with nan a. everywhere {:d}'.format(\
       len(df_master[pd.isnull(df_master['label']) &\
                     pd.isnull(df_master['total_price'])]))

df_master = df_master[~(pd.isnull(df_master['label']) &\
                        pd.isnull(df_master['total_price']))]


# Can on idProduit be in several families? YES
ls_dup_cols_0 = ['store', 'date', 'idProduit']
df_dup_0 = df_master[df_master.duplicated(ls_dup_cols_0, take_last = False) |
                     df_master.duplicated(ls_dup_cols_0, take_last = True)].copy()
df_dup_0.sort(ls_dup_cols_0, inplace = True)

# Do duplicate idProduit (several families) have the same price? YES
ls_dup_cols_1 = ['store', 'date', 'idProduit', 'unit_price']
df_dup_1 = df_master[df_master.duplicated(ls_dup_cols_1, take_last = False) |
                     df_master.duplicated(ls_dup_cols_1, take_last = True)].copy()

ls_dup_pbms = list(set(df_dup_0.index).difference(set(df_dup_1.index)))
ls_id_prod_pbms = df_master.ix[ls_dup_pbms]['idProduit'].unique().tolist()
df_pbms = df_master[df_master['idProduit'].isin(ls_id_prod_pbms)].copy()
df_pbms.sort(['store', 'date', 'idProduit'], inplace = True)
# print df_pbms[0:10].to_string()

# todo:
# keep info about families products are listed in
# drop duplicate product lines

# Check if idProduit 1-to-1 with (brand, title, label) => NO => use idProduit
df_u_idP = df_master[['idProduit', 'brand', 'title', 'label']]\
                    .drop_duplicates(['idProduit'])
ls_dup_idP = ['brand', 'title', 'label']
df_amb_prod = df_u_idP[df_u_idP.duplicated(ls_dup_idP, take_last = True) |\
                       df_u_idP.duplicated(ls_dup_idP, take_last = False)].copy()
df_amb_prod.sort(['brand', 'title', 'label'], inplace = True)
print u'\nOverview diff idProduit for same (brand, title, label):'
print df_amb_prod[0:10].to_string()
#print df_master[(df_master['idProduit'].isin([8025, 8024])) &\
#                (df_master['store'] == 'Clermont Ferrand')].to_string()
# Drop them for now
ls_drop_idP = df_amb_prod['idProduit'].unique().tolist()
df_master = df_master[~df_master['idProduit'].isin(ls_drop_idP)]

# lib_promo can be dropped (same as dum_promo)
df_prices = df_master[['date', 'store', 'idProduit',
                       'brand', 'title', 'label',
                       'stock', 'total_price', 'unit_price', 'unit',
                       'promo', 'promo_per_unit', # those are prices
                       'dum_promo', 'lib_0', 'loyalty']]\
              .drop_duplicates(['store', 'date', 'idProduit'])

df_products = df_master[['section', 'family',
                         'brand', 'title', 'label',
                         'idProduit',
                         'idRayon', 'idFamille', 'idSousFamille']]\
                .drop_duplicates()

# todo: check if can get rid of idXXX (except for idProduit)
## idXXX do not allow to find EAN (bar code...)
#print df_master[df_master['title'].str.contains('heinz',
#                                                case = False ,
#                                                na=False)]\
#               [['brand', 'title', 'label',
#                 'idProduit', 'idRayon',
#                 'idFamille', 'idSousFamille']].drop_duplicates().to_string()

ls_stores = df_master['store'].unique().tolist()

# ####################
# STORE PRICE CHANGES
# ####################

df_master_s = df_master[df_master['store'] == 'Clermont Ferrand']

# Build df store products (idProduit not unique: several families)
lsd_prod = ['idProduit', 'brand', 'title', 'label', 'family', 'section']
df_products_s = df_master[lsd_prod].drop_duplicates()

# Build df with product prices in columns
df_prices_s = df_master_s.drop_duplicates(['date', 'idProduit'])
df_prices_sc = df_prices_s.pivot(index = 'date',
                                 columns = 'idProduit',
                                 values = 'total_price')
df_prices_sc.index= pd.to_datetime(df_prices_sc.index,
                                   format = '%Y%m%d')
index_dr = pd.date_range(df_prices_sc.index[0],
                         df_prices_sc.index[-1],
                         freq = 'D')
df_prices_sc = df_prices_sc.reindex(index_dr)

# Build df with product prices incl promo in columns
# Some promo have promo == 0 (e.g. buy 4 products to get discount)
df_prices_sp = df_prices_s.copy()
df_prices_sp.loc[(df_prices_sp['dum_promo'] == True) &\
                 (df_prices_sp['promo'] != 0),
                 'total_price'] = df_prices['promo']
df_prices_spc = df_prices_sp.pivot(index = 'date',
                                   columns = 'idProduit',
                                   values = 'total_price')
df_prices_spc.index= pd.to_datetime(df_prices_spc.index,
                                    format = '%Y%m%d')
index_dr = pd.date_range(df_prices_spc.index[0],
                         df_prices_spc.index[-1],
                         freq = 'D')
df_prices_spc = df_prices_spc.reindex(index_dr)

# todo:
# - can fill backward to count chges in prices
# - count nb_chges / nb_chges due to promo by idProduit
# - add nb stats to df_products_s
# - stats des: promo by section
# - stats des: impact on basket value (?)
# - see if can use variations in qtities in stats des?

# caution: some idProduit only for promo?
# caution: inspect when both promo chges and non promo chges

df_prices_scf = df_prices_sc.fillna(method = 'bfill',
                                    axis = 'columns')
df_prices_scfd = df_prices_scf - df_prices_scf.shift(1)
se_scfd_nb_chges = df_prices_scfd.apply(lambda x: (x.abs()>0).sum(),
                                        axis = 0)

df_prices_spcf = df_prices_spc.fillna(method = 'bfill',
                                      axis = 'columns')
df_prices_spcfd = df_prices_spcf - df_prices_spcf.shift(1)
se_spcfd_nb_chges = df_prices_spcfd.apply(lambda x: (x.abs()>0).sum(),
                                          axis = 0)

df_prod_chges = pd.concat([se_scfd_nb_chges,
                           se_spcfd_nb_chges],
                           keys = ['nb_chges', 'nb_chges_w_promo'],
                          axis = 1)
df_prod_chges['nb_chges_promo'] = df_prod_chges['nb_chges_w_promo'] -\
                                    df_prod_chges['nb_chges']

print u'\Overview of price chges'
print df_prod_chges.describe().to_string()
# make sure no negative nb_chges_promo (todo: check further)
print df_prod_chges[df_prod_chges['nb_chges_promo'] < 0].to_string()

# Interesting (non captured) promo and price vars

lsd_pp = ['date', 'idProduit', 'brand', 'title', 'label',
          'total_price', 'promo', 'lib_promo', 'dum_promo',
          'unit', 'promo_per_unit', 'family', 'section']
print df_prices_s[lsd_pp][df_prices_s['idProduit'] == 2588].to_string(index=False)
