#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

path_dir_qlmc = os.path.join(path_data, 'data_qlmc')
path_dir_built_csv = os.path.join(path_dir_qlmc, 'data_built' , 'data_csv')
#path_dir_built_hdf5 = os.path.join(path_dir_qlmc, 'data_built', 'data_hdf5')

# #######################
# BUILD DF QLMC
# ####################### 

# LOAD DF PRICES
print u'Loading qlmc prices'
# date parsing slow... better if specified format?
df_qlmc = pd.read_csv(os.path.join(path_dir_built_csv,
                                   'df_qlmc_prices.csv'),
                      encoding = 'utf-8')

# LOAD DF STORES
print u'Loading qlmc stores (inc. LSA id)'
df_stores = pd.read_csv(os.path.join(path_dir_built_csv,
                                     'df_qlmc_stores.csv'),
                        dtype = {'id_lsa': str,
                                 'INSE_ZIP' : str,
                                 'INSEE_Dpt' : str,
                                 'INSEE_Code' : str,
                                 'QLMC_Dpt' : str},
                        encoding = 'UTF-8')
df_stores['Magasin'] = df_stores['Enseigne'] + u' ' + df_stores['Commune']
df_stores = df_stores[['P', 'Magasin', 'Enseigne', 'id_lsa',
                       'INSEE_Code', 'INSEE_Commune']]

# LOAD DF COMP

df_comp_h = pd.read_csv(os.path.join(path_dir_built_csv,
                                     'df_comp_H_ac_vs_cont.csv'),
                        dtype = {'Ident': str},
                        encoding = 'latin-1')

df_comp_s = pd.read_csv(os.path.join(path_dir_built_csv,
                                     'df_comp_S_ac_vs_cont.csv'),
                        dtype = {'Ident': str},
                        encoding = 'latin-1')

df_comp = pd.concat([df_comp_h, df_comp_s],
                    axis = 0,
                    ignore_index = True)

df_comp.rename(columns = {u'Ident': 'id_lsa',
                          u'Surf Vente' : 'Surface',
                          u'Nbr de caisses' : u'Nb_checkouts',
                          u'Nbr emp' : 'Nb_emp',
                          u'Nbr parking' : 'Nb_parking',
                          u'Intégré / Indépendant' : u'Indpt'},
               inplace = True)

ls_lsa_info_cols = [u'Surface',
                    u'Nb_checkouts',
                    u'Nb_emp',
                    u'Nb_parking',
                    u'Indpt',
                    u'Groupe',
                    u'Groupe_alt',
                    u'Enseigne_alt',
                    u'Type_alt']

ls_lsa_comp_cols = ['ac_nb_store',
                    'ac_nb_comp',
                    'ac_store_share',
                    'ac_group_share',
                    'ac_hhi']

df_stores = pd.merge(df_stores,
                     df_comp[['id_lsa'] +\
                             ls_lsa_info_cols +\
                             ls_lsa_comp_cols],
                     on = 'id_lsa',
                     how = 'left')

# ######################################
# REG MOST COMMON PRODUCT PRICES ON COMP
# ######################################

df_qlmc = pd.merge(df_qlmc,
                   df_stores,
                   on = ['P', 'Magasin'],
                   how = 'left')

df_qlmc = df_qlmc[~df_qlmc['id_lsa'].isnull()]

se_prod = df_qlmc.groupby(['Rayon', 'Famille', 'Produit']).agg('size')
se_prod.sort(ascending = False, inplace = True)

rayon, famille, produit = se_prod.index[0]

df_qlmc_prod = df_qlmc[(df_qlmc['Rayon'] == rayon) &\
                       (df_qlmc['Famille'] == famille) &\
                       (df_qlmc['Produit'] == produit)].copy()

df_qlmc_prod['Surface'] = df_qlmc_prod['Surface'].apply(lambda x: x/1000.0)

reg = smf.ols('Prix ~ C(P) + Surface + Groupe_alt + ac_hhi',
              data = df_qlmc_prod[df_qlmc_prod['Type_alt'] == 'H'],
              missing = 'drop').fit()

print reg.summary()
