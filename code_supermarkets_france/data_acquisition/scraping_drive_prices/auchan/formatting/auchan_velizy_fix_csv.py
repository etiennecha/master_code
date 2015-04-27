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

path_price_built_csv = os.path.join(path_auchan,
                                    u'data_built',
                                    u'data_csv_auchan_velizy')

df_prices_1 = pd.read_csv(os.path.join(path_price_built_csv,
                                       'df_auchan_velizy_20121122_20130411.csv'),
                          parse_dates = ['date'],
                          dtype = {'available' : str,
                                   'promo' : str,
                                   'promo_vignette' : str},
                          encoding = 'utf-8')

df_prices_2 = pd.read_csv(os.path.join(path_price_built_csv,
                                       'df_auchan_velizy_20130411_20130809.csv'),
                          parse_dates = ['date'],
                          dtype = {'available' : str,
                                   'pictos' : str,
                                   'promo' : str,
                                   'promo_vignette' : str},
                          encoding = 'utf-8')

# ##############
# 2/ df_prices_2
# ##############

# contains products with null sub_dpt which are to be erased
# contains duplicates of (period title dpt subdpt): keep only lowest price
# all subdpt should be proper

print u'\nNb obs with null sub_department: {:d} (dropped)'.format(\
          len(df_prices_2[~df_prices_2['sub_department'].isnull()]))
df_prices_2 = df_prices_2[~df_prices_2['sub_department'].isnull()]

# sort: ascending and nan as last by default
df_prices_2.sort(['date', 'title', 'department', 'sub_department', 'total_price'],
                 inplace = True)

# drop_duplicates: takes first by default
df_prices_2.drop_duplicates(['date', 'title', 'department', 'sub_department'],
                            inplace = True)

ls_u_title_2 = df_prices_2['title'].unique().tolist()


df_2_dsd = df_prices_2[['title', 'department', 'sub_department']].drop_duplicates()

# Check [u"Martini royale rosato 8° -75cl", u"Bébé", u"Repas bébé"]

# ##############
# 1/ df_prices_1
# ##############

# contains products with null sub_dpt which are to be erased
# contains duplicates of (period title dpt subdpt): keep only lowest price
# contains (title dpt subdpt) in which subdpt not relevant to product: check df_prices_2

print u'\nNb obs with null sub_department: {:d} (dropped)'.format(\
          len(df_prices_1[~df_prices_1['sub_department'].isnull()]))
df_prices_1 = df_prices_1[~df_prices_1['sub_department'].isnull()]

# sort: ascending and nan as last by default
df_prices_1.sort(['date', 'title', 'department', 'sub_department', 'total_price'],
                 inplace = True)

# drop_duplicates: takes first by default
df_prices_1.drop_duplicates(['date', 'title', 'department', 'sub_department'],
                            inplace = True)

ls_u_title_1 = df_prices_1['title'].unique().tolist()

ls_u_title_12 = list(set(ls_u_title_1).intersection(ls_u_title_2))
# for those: keep only dpt and subdpt from file 2 (check that looks good)

df_prices_1_sub = df_prices_1[~df_prices_1['title'].isin(ls_u_title_12)].copy()
df_1_sub_dsd = df_prices_1_sub[['title', 'department', 'sub_department']].drop_duplicates()

ls_dsd_dup = df_1_sub_dsd['title'][df_1_sub_dsd['title'].duplicated()].unique().tolist()

print u'\nOverview of some products not in df_prices_2 with several s_dpts'
print df_1_sub_dsd[df_1_sub_dsd['title'].isin(ls_dsd_dup)][0:20].to_string()

print u'\nOverview of products not in df_prices_2 with highest nb of s_dpts'
print df_1_sub_dsd['title'].value_counts()[0:20]

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

# to be continued in more efficient way

for title, ls_sub_departments in ls_fix_dsd:
  df_1_sub_dsd = df_1_sub_dsd[(df_1_sub_dsd['title'] != title) |\
                              ((df_1_sub_dsd['title'] == title) &\
                               (df_1_sub_dsd['sub_department'].isin(ls_sub_departments)))]

# ###############
# 3/ Concatenate
# ###############

# Need to concatenate and build two databases
# A product price database where products are unique
# A product dpt subdpt database

# Keep unique product price (no loss of info on promo etc?)
df_prod_prices_1 = df_prices_1[['title',
                                'total_price',
                                'unit_price',
                                'available',
                                'flag',
                                'promo',
                                'promo_vignette',
                                'date']].drop_duplicates(['date', 'title'])

df_prod_prices_1['pictos'] = None

df_prod_1_dsd = df_prices_1[['title',
                             'department',
                             'sub_department']].drop_duplicates()

df_prod_prices_2 = df_prices_2[['title',
                                'total_price',
                                'unit_price',
                                'available',
                                'flag',
                                'promo',
                                'promo_vignette',
                                'pictos',
                                'date']].drop_duplicates(['date', 'title'])

df_prod_2_dsd = df_prices_2[['title',
                             'department',
                             'sub_department']].drop_duplicates()

df_prod_prices = pd.concat([df_prod_prices_1,
                            df_prod_prices_2],
                           axis = 0)

df_prod_dsd = pd.concat([df_prod_2_dsd,
                         df_1_sub_dsd],
                        axis = 0)

# #########################
# 4/ Finish formatting data
# #########################

# FORMAT COLUMN total_price

df_prod_prices['total_price'] =\
  df_prod_prices['total_price'].apply(lambda x: x.replace(',', '.')\
                                                  .replace(u'\\u20ac', u''))
df_prod_prices['total_price'] = df_prod_prices['total_price'].astype(float)

# ADD NB OF PRICE OBS BY PRODUCT IN df_prod_dsd

se_prod_vc = df_prod_prices['title'].value_counts()
df_prod_dsd.set_index('title', inplace = True)
df_prod_dsd['nb_obs'] = se_prod_vc
df_prod_dsd.reset_index(inplace = True)
df_prod_dsd.sort('nb_obs', inplace = True, ascending = False)

# ADD NB OF PRICE CHGES

df_prod_prices.sort(['title', 'date'], inplace = True)

## too slow: use groupby
#df_prod_dsd['nb_price_chges'] = 0
#for prod_title in df_prod_dsd['title'].unique():
#  se_prices = df_prod_prices['total_price']\
#                [df_prod_prices['title'] == prod_title]
#  se_price_diff = se_prices - se_prices.shift(1) 
#  nb_price_chges = len(se_price_diff[se_price_diff.abs() > 1e-5])
#  df_prod_dsd.loc[df_prod_dsd['title'] == prod_title,
#                  'nb_price_chges'] = nb_price_chges

def count_nb_chges(se_prices):
  se_price_diff = se_prices - se_prices.shift(1) 
  nb_price_chges = len(se_price_diff[se_price_diff.abs() > 1e-5])
  return nb_price_chges

df_nb_price_chges = df_prod_prices[['title', 'total_price']]\
                      .groupby('title').agg([count_nb_chges])

# todo: avoid doing twice
df_prod_dsd.set_index('title', inplace = True)
df_prod_dsd['nb_price_chges'] = df_nb_price_chges['total_price']['count_nb_chges']
df_prod_dsd.reset_index(inplace = True)
df_prod_dsd.sort('nb_price_chges', inplace = True, ascending = False)

# #########
# OVERVIEW
# #########

print u'\nOverview nb_obs and nb_price_chges'
print df_prod_dsd[['nb_obs', 'nb_price_chges']].describe()

print u'\nOverview products with high nb_price_chges'
print df_prod_dsd[0:20].to_string()

ls_titles = [u'chou fleur  pièce',
             u'pommes de terre blonde filet 2,5kg vapeur,salade, sautées',
             u'concombre pièce',
             u'pommes gala tenroy sachet 1,5kg et plus',
             u'courgettes filet 1kg',
df_prices = df_prod_prices[['title', 'date', 'total_price']]\
              [df_prod_prices['title'].isin(ls_titles)]
df_prices_wide = df_prices.pivot('date', 'title', 'total_price')
index = pd.date_range(start = df_prod_prices['date'].min(),
                      end   = df_prod_prices['date'].max(), 
                      freq='D')
df_prices_wide = df_prices_wide.reindex(index = list(index))
df_prices_wide.plot()
plt.show()

## #################
## EXAMPLE: COCA
## #################
#
## todo: check issues with product categories...
## print df_prod_dsd[df_prod_dsd['title'].str.contains('Coca')].to_string()
#
#df_ex = df_prod_prices[['date', 'total_price']]\
#          [df_prod_prices['title'] == u'Coca-Cola Classic 2l']
#df_ex.set_index('date', inplace = True)
#df_ex['total_price'].plot()
#
## Coca with highest number of observations
#
#print df_prod_dsd[(df_prod_dsd['title'].str.contains('Coca', case = False))].to_string()
#
#
#ls_coca_title =\
#  df_prod_dsd['title'][(df_prod_dsd['title'].str.contains('Coca', case = False)) &\
#                       (df_prod_dsd['title'].str.contains('1,5L', case = False)) &\
#                       (df_prod_dsd['nb_obs'] >= 200)]\
#                  .unique().tolist()
#df_coca = df_prod_prices[['title', 'date', 'total_price']]\
#            [df_prod_prices['title'].isin(ls_coca_title)]
#df_coca_wide = df_coca.pivot('date', 'title', 'total_price')
#
#index = pd.date_range(start = df_prod_prices['date'].min(),
#                      end   = df_prod_prices['date'].max(), 
#                      freq='D')
#df_coca_wide = df_coca_wide.reindex(index = list(index))
#
## a lot of products have few price observations
## add in database: nb of obs, nb price changes
#
## u"Coca Cola classic 12x1,5l", # 37 obs
## u'Coca Cola 8x1,5l format spécial', # 1 obs
#ls_coca_15_classic = [u'Coca Cola 6x1,5l offre économique', # 23 obs
#                      u"Coca-Cola 6x1,5l offre 100% remboursé différée", # 60 obs
#                      u'Coca-Cola standard 6x1,5l', # 173 obs
#                      u'Coca-Cola standard 1,5l'] # 213 obs
