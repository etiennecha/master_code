#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
import os
from datetime import date, timedelta
from functions_generic_drive import *
import matplotlib.pyplot as plt

path_auchan = os.path.join(path_data,
                           u'data_drive_supermarkets',
                           u'data_auchan')

path_price_source_csv = os.path.join(path_auchan,
                                     u'data_source',
                                     u'data_csv_auchan')

path_price_built_csv = os.path.join(path_auchan,
                                    u'data_built',
                                    u'data_csv_auchan')

dict_files = {'velizy_0' : 'df_auchan_velizy_20121122_20130411.csv',
              'velizy_1' : 'df_auchan_velizy_20130411_20130808.csv',
              'plaisir_1' : 'df_auchan_plaisir_20130627_20130808.csv'}

dict_dfs = {}
for file_title, file_name in dict_files.items():
  dict_dfs[file_title] =\
      pd.read_csv(os.path.join(path_price_source_csv, file_name),
                               parse_dates = ['date'],
                               dtype = {'available' : str,
                                        'pictos' : str,
                                        'promo' : str,
                                        'promo_vignette' : str},
                               encoding = 'utf-8')

# ############
# GENERIC FIX
# ############

ls_prod_id_cols = ['date', 'department', 'sub_department', 'title']
dict_nodup_dfs = {}
for file_title in ['velizy_0', 'velizy_1', 'plaisir_1']:
  df_master = dict_dfs[file_title].copy()
  
  print u'\nProcessing {:s}'.format(file_title)

  # get rid of null sub_departments
  print u'Nb obs with null sub_department: {:d} (dropped)'.format(\
            len(df_master[df_master['sub_department'].isnull()]))
  df_master = df_master[~df_master['sub_department'].isnull()]
  
  # sort: ascending and nan as last by default
  df_master.sort(['date', 'title', 'department', 'sub_department', 'total_price'],
                   inplace = True)

  # store result back
  dict_dfs[file_title] = df_master

  # store df no duplicates
  df_nodup = df_master[~((df_master.duplicated(ls_prod_id_cols)) |\
                         (df_master.duplicated(ls_prod_id_cols,
                                             take_last = True)))].copy()
  dict_nodup_dfs[file_title] = df_nodup

# Check [u"Martini royale rosato 8° -75cl", u"Bébé", u"Repas bébé"]

# ##########################################
# OUPUT DATA AUCHAN (VELIZY + PLAISIR) 2013
# ##########################################

ls_dup_id_cols = ['store', 'date', 'department', 'sub_department', 'title']

df_velizy_1 = dict_dfs['velizy_1'].copy()
df_velizy_1['store'] = 'velizy' # changes original anyway?

df_plaisir_1 = dict_dfs['plaisir_1'].copy()
df_plaisir_1['store'] = 'plaisir'

df_master_auchan_2013 = pd.concat([df_velizy_1, df_plaisir_1],
                                  axis = 0)

dict_auchan_2013 = {'df_master_auchan_2013' : df_master_auchan_2013}

# GET df_prices AND df_products

# (could be even more strict: retain title if ambig in one period and suppr in all periods)
# (right now: still some risk of merging different products across periods)

#df_dup_auchan_2013 =\
#  df_master_auchan_2013[(df_master_auchan_2013.duplicated(ls_dup_id_cols)) |\
#                        (df_master_auchan_2013.duplicated(ls_dup_id_cols,
#                                                          take_last = True))].copy()

df_nodup_auchan_2013 =\
  df_master_auchan_2013[~((df_master_auchan_2013.duplicated(ls_dup_id_cols)) |\
                          (df_master_auchan_2013.duplicated(ls_dup_id_cols,
                                                            take_last = True)))]

ls_price_cols = ['store', 'date', 'title',
                 'pictos', 'flag', 'available',
                 'promo', 'promo_vignette',
                 'total_price', 'unit_price', 'unit']

dict_auchan_2013['df_prices_auchan_2013'] =\
  df_nodup_auchan_2013[ls_price_cols].drop_duplicates(['date', 'store', 'title'])

dict_auchan_2013['df_products_auchan_2013'] =\
  df_nodup_auchan_2013[ls_prod_id_cols[1:]].drop_duplicates(ls_prod_id_cols[1:])

## OUTPUT
#
#for file_title, df_file in dict_auchan_2013.items():
#  df_file.to_csv(os.path.join(path_price_built_csv,
#                              '{:s}.csv'.format(file_title)),
#                   encoding = 'utf-8',
#                   float_format='%.2f',
#                   index = False)

# ##################################
# OUPUT DATA AUCHAN VELIZY 2012-13
# ##################################

print u'\nProcessing df_velizy_0 duplicates:'
df_velizy_0_nodup = dict_nodup_dfs['velizy_0'].copy()
df_velizy_1_nodup = dict_nodup_dfs['velizy_1'].copy()

# PREPARE TO GET RID OF WRONG DPT/SUB_DPT ASSOCIATIONS

# If product in second period, want to use its dpt/sub_dpts from future
ls_u_title_0 = df_velizy_0_nodup['title'].unique().tolist()
ls_u_title_1 = df_velizy_1_nodup['title'].unique().tolist()
ls_u_title_01 = list(set(ls_u_title_0).intersection(ls_u_title_1))

# Keep products not listed in period 2... need to deal with them
df_velizy_0_nodup_sub =\
  df_velizy_0_nodup[~df_velizy_0_nodup['title'].isin(ls_u_title_01)].copy()

df_products_sub_0 = df_velizy_0_nodup_sub[['title',
                                           'department',
                                           'sub_department']].drop_duplicates()

print u'\nOverview of some products not in df_master_2 with several s_dpts:'
ls_ps0_dup = df_products_sub_0['title']\
               [df_products_sub_0['title'].duplicated()].unique().tolist()
print df_products_sub_0[df_products_sub_0['title'].isin(ls_ps0_dup)][0:20].to_string()

print u'\nOverview of products not in df_master_2 with highest nb of s_dpts:'
print df_products_sub_0['title'].value_counts()[0:20]

# Most issues seem to be with dpt: boissons
# When doubt... check with re in ls_u_title_2 to find similar products

ls_fix_dsd = [[u'Label 5 whisky flask 40° -20cl',
                 [u'Whiskies']],
              [u'Get 31 peppermint 24° -70cl',
                 [u'Punchs - Cocktails - Rhums',
                  u'Digestifs']],
              [u"Croc'Frais olives à la provençale 250g +10% gratuit",
                 [u'Olives',
                  u'Idées apéritives',
                  u"Pour l'Apéritif"]],
              [u'Garnier BB cream soin miracle anti-âge médium 50ml',
                 [u'Maquillage',
                  u'Soins femme']],
              [u'Martini spumante prosecco 11,5° -75cl',
                [u'Portos & À base de vins']],
              [u'kaki pièce',
                 [u'Fruits et légumes à la pièce',
                  u'Fruits frais']],
              [u'Auchan pomelos bio pièce',
                 [u'Fruits et légumes à la pièce',
                  u'Fruits frais']],
              [u'Martini Bianco 14,4° -1l',
                 [u'Portos & À base de vins']],
              [u"Auchan olives à l'ail 150g",
                 [u'Olives',
                  u'Idées apéritives',
                  u"Pour l'Apéritif"]],
              [u"noix sèche calibre 32+ 1kg",
                 [u"Fruits secs",
                  u"Sucre-Farine-Aides pâtissières"]],
              [u'Poire passe-crassane piece',
                 [u'Fruits et légumes à la pièce',
                  u'Fruits frais']],
              [u'Tawny Coelva porto 19° 75cl',
                 [u'Portos & À base de vins']],
              [u'Martini Bianco 100cl +1 verre short drink',
                [u'Portos & À base de vins']],
              [u'noix sèche calibre 28+ 1kg',
                 [u"Fruits secs",
                  u"Sucre-Farine-Aides pâtissières"]],
              [u'Lazy Lemmon  jus de citron dosette x6 +1 gratuite 8ml',
                 [u'Poissonnerie',
                  u'Traiteur',
                  u'Aides culinaires']],
              [u'Ambre Solaire gel teinté autobronzant tube 150ml',
                 [u'Produits solaires',
                  u'Pour le voyage']],
              [u'Auchan olives fromage 150g',
                 [u'Olives',
                  u'Idées apéritives',
                  u"Pour l'Apéritif"]],
              [u'Auchan olives piquantes 150g',
                 [u'Olives',
                  u'Idées apéritives',
                  u"Pour l'Apéritif"]],
              [u'Porto Cruz pink 19° -75cl  prix choc',
                [u'Portos & À base de vins']],
              [u'Poire passe-crassane pièce', # same prod but accent added
                 [u'Fruits et légumes à la pièce',
                  u'Fruits frais']],
              [u'Garnier Uv Ski stick lèvres protecteur invisible fps20 -15g',
                 [u'Pour le voyage',
                  u'Produits solaires',
                  u'Soins femme']]]
# to be continued (in a more efficient way?)

for title, ls_sub_departments in ls_fix_dsd:
  df_products_sub_0 = df_products_sub_0[(df_products_sub_0['title'] != title) |\
                              ((df_products_sub_0['title'] == title) &\
                               (df_products_sub_0['sub_department'].isin(ls_sub_departments)))]

# CONCATENATE BOTH PERIODS

df_prices_0 = df_velizy_0_nodup[ls_price_cols[1:]].drop_duplicates(['date', 'title'])

#df_products_0 = df_master_1[['title',
#                             'department',
#                             'sub_department']].drop_duplicates()

df_prices_1 = df_velizy_1_nodup[ls_price_cols[1:]].drop_duplicates(['date', 'title'])
df_products_1 = df_velizy_1_nodup[['title',
                                   'department',
                                   'sub_department']].drop_duplicates()

df_products_velizy = pd.concat([df_products_sub_0,
                                df_products_1],
                               axis = 0)

df_prices_velizy = pd.concat([df_prices_0,
                              df_prices_1],
                             axis = 0)

# Check that there were never two different prices for one title across dpt/sub_dpts?
df_master_velizy = pd.merge(df_products_velizy,
                            df_prices_velizy,
                            on = 'title',
                            how = 'left')

# OUTPUT

dict_velizy_201213 = {'df_master_auchan_velizy_2012-13' : df_master_velizy,
                      'df_prices_auchan_velizy_2012-13' : df_prices_velizy,
                      'df_products_auchan_velizy_2012-13': df_products_velizy}

for file_title, df_file in dict_velizy_201213.items():
  df_file.to_csv(os.path.join(path_price_built_csv,
                              '{:s}.csv'.format(file_title)),
                   encoding = 'utf-8',
                   float_format='%.2f',
                   index = False)

## todo: UPDATE & INVESTIGATE CONCATENATION
## results in larger file: how problematic?

# len(df_master[df_master['date'] == '2013-06-11'])
# len(df_master_2[df_master_2['date'] == '2013-06-11'])
# More in master than in master_2... could mean trouble

#len(df_master_2[df_master_2.duplicated(['date', 'title'])])
#len(df_master_2[df_master_2.duplicated(['date', 'title', 'total_price'])])

#l1 = df_master_2[df_master_2['date'] == '2013-06-11']\
#       [['title', 'department', 'sub_department']].values.tolist()
#l2 = df_master[df_master['date'] == '2013-06-11']\
#       [['title', 'department', 'sub_department']].values.tolist()
#l_audit = list(set([tuple(x) for x in l2]).difference(set([tuple(y) for y in l1])))

## ##########
## STATS DES
## ##########
#
## ADD NB OF PRICE OBS BY PRODUCT IN df_prod_dsd
#
#se_prod_vc = df_prod_prices['title'].value_counts()
#df_prod_dsd.set_index('title', inplace = True)
#df_prod_dsd['nb_obs'] = se_prod_vc
#df_prod_dsd.reset_index(inplace = True)
#df_prod_dsd.sort('nb_obs', inplace = True, ascending = False)
#
## ADD NB OF PRICE CHGES
#
#df_prod_prices.sort(['title', 'date'], inplace = True)
#
### too slow: use groupby
##df_prod_dsd['nb_price_chges'] = 0
##for prod_title in df_prod_dsd['title'].unique():
##  se_prices = df_prod_prices['total_price']\
##                [df_prod_prices['title'] == prod_title]
##  se_price_diff = se_prices - se_prices.shift(1) 
##  nb_price_chges = len(se_price_diff[se_price_diff.abs() > 1e-5])
##  df_prod_dsd.loc[df_prod_dsd['title'] == prod_title,
##                  'nb_price_chges'] = nb_price_chges
#
#def count_nb_chges(se_prices):
#  se_price_diff = se_prices - se_prices.shift(1) 
#  nb_price_chges = len(se_price_diff[se_price_diff.abs() > 1e-5])
#  return nb_price_chges
#
#df_nb_price_chges = df_prod_prices[['title', 'total_price']]\
#                      .groupby('title').agg([count_nb_chges])
#
## todo: avoid doing twice
#df_prod_dsd.set_index('title', inplace = True)
#df_prod_dsd['nb_price_chges'] = df_nb_price_chges['total_price']['count_nb_chges']
#df_prod_dsd.reset_index(inplace = True)
#df_prod_dsd.sort('nb_price_chges', inplace = True, ascending = False)
#
#print u'\nOverview nb_obs and nb_price_chges'
#print df_prod_dsd[['nb_obs', 'nb_price_chges']].describe()
#
#print u'\nOverview products with high nb_price_chges'
#print df_prod_dsd[0:20].to_string()
#
#ls_titles = [u'chou fleur  pièce',
#             u'pommes de terre blonde filet 2,5kg vapeur,salade, sautées',
#             u'concombre pièce',
#             u'pommes gala tenroy sachet 1,5kg et plus',
#             u'courgettes filet 1kg']
#
#df_prices = df_prod_prices[['title', 'date', 'total_price']]\
#              [df_prod_prices['title'].isin(ls_titles)]
#df_prices_wide = df_prices.pivot('date', 'title', 'total_price')
#index = pd.date_range(start = df_prod_prices['date'].min(),
#                      end   = df_prod_prices['date'].max(), 
#                      freq='D')
#df_prices_wide = df_prices_wide.reindex(index = list(index))
#df_prices_wide.plot()
#plt.show()
#
#print u'\nOverview dpt and subdpts'
#df_dsd = df_prod_dsd[['department', 'sub_department']].drop_duplicates()
#df_dsd.sort(['department', 'sub_department'], inplace = True)
#
### Extract vins
##len(df_prod_dsd[df_prod_dsd['sub_department'] == 'Vins'])
##ls_title_vins = df_prod_dsd['title'][df_prod_dsd['sub_department'] == 'Vins'].unique().tolist()
##df_prices_vins = df_prod_prices[df_prod_prices['title'].isin(ls_title_vins)]
#
### EXAMPLE: COCA
##
### todo: check issues with product categories...
### print df_prod_dsd[df_prod_dsd['title'].str.contains('Coca')].to_string()
##
##df_ex = df_prod_prices[['date', 'total_price']]\
##          [df_prod_prices['title'] == u'Coca-Cola Classic 2l']
##df_ex.set_index('date', inplace = True)
##df_ex['total_price'].plot()
##
### Coca with highest number of observations
##
##print df_prod_dsd[(df_prod_dsd['title'].str.contains('Coca', case = False))].to_string()
##
##
##ls_coca_title =\
##  df_prod_dsd['title'][(df_prod_dsd['title'].str.contains('Coca', case = False)) &\
##                       (df_prod_dsd['title'].str.contains('1,5L', case = False)) &\
##                       (df_prod_dsd['nb_obs'] >= 200)]\
##                  .unique().tolist()
##df_coca = df_prod_prices[['title', 'date', 'total_price']]\
##            [df_prod_prices['title'].isin(ls_coca_title)]
##df_coca_wide = df_coca.pivot('date', 'title', 'total_price')
##
##index = pd.date_range(start = df_prod_prices['date'].min(),
##                      end   = df_prod_prices['date'].max(), 
##                      freq='D')
##df_coca_wide = df_coca_wide.reindex(index = list(index))
##
### a lot of products have few price observations
### add in database: nb of obs, nb price changes
##
### u"Coca Cola classic 12x1,5l", # 37 obs
### u'Coca Cola 8x1,5l format spécial', # 1 obs
##ls_coca_15_classic = [u'Coca Cola 6x1,5l offre économique', # 23 obs
##                      u"Coca-Cola 6x1,5l offre 100% remboursé différée", # 60 obs
##                      u'Coca-Cola standard 6x1,5l', # 173 obs
##                      u'Coca-Cola standard 1,5l'] # 213 obs
