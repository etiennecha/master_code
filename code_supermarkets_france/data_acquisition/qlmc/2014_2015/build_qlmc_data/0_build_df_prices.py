#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import add_to_path
from add_to_path import *
from functions_generic_qlmc import *
import os, sys
import json
import re
import pandas as pd

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

path_qlmc_scraped = os.path.join(path_data,
                                 'data_supermarkets',
                                 'data_source',
                                 'data_qlmc_2015',
                                 'data_scraped_201503')

path_csv = os.path.join(path_data,
                        'data_supermarkets',
                        'data_built',
                        'data_qlmc_2015',
                        'data_csv_201503')

ls_fra_regions = [u'picardie',
                  u'franche-comte',
                  u'languedoc-roussillon',
                  u'rhone-alpes',
                  u'basse-normandie',
                  u'poitou-charentes',
                  u'pays-de-la-loire',
                  u'lorraine',
                  u'midi-pyrenees',
                  u'nord-pas-de-calais',
                  u'centre',
                  u'bretagne',
                  u'bourgogne',
                  u'aquitaine',
                  u'auvergne',
                  u'alsace',
                  u'corse',
                  u'champagne-ardenne',
                  u'haute-normandie',
                  u'ile-de-france',
                  u'provence-alpes-cote-d-azur',
                  u'limousin']

dict_chains = {'LEC' : 'LECLERC',
               'ITM' : 'INTERMARCHE',
               'USM' : 'SUPER U',
               'CAR' : 'CARREFOUR',
               'CRM' : 'CARREFOUR MARKET', # or MARKET
               'AUC' : 'AUCHAN',
               'GEA' : 'GEANT CASINO',
               'CAS' : 'CASINO',
               'SCA' : 'CASINO',
               'HSM' : 'HYPER U',
               'UHM' : 'HYPER U',
               'COR' : 'CORA',
               'SIM' : 'SIMPLY MARKET',
               'MAT' : 'SUPERMARCHE MATCH',
               'HCA' : 'HYPER CASINO',
               'UEX' : 'U EXPRESS',
               'ATA' : 'ATAC',
               'MIG' : 'MIGROS',
               'G20' : 'G 20',
               'REC' : 'RECORD',
               'HAU' : "LES HALLES D'AUCHAN"}

ls_df_regions = []
for region in ls_fra_regions:
  path_dict_reg_comparisons = (
      os.path.join(path_qlmc_scraped,
                   'dict_reg_comparisons_{:s}.json'.format(region)))
  dict_reg_comparisons_json = dec_json(path_dict_reg_comparisons)
  # convert keys from string to tuple
  dict_reg_comparisons = ({tuple(json.loads(k)): v
                             for k,v in dict_reg_comparisons_json.items()})
  ls_df_pair_products = []
  for pair_ids, pair_comparison in dict_reg_comparisons.items():
    leclerc_id, competitor_id = pair_ids
    dict_pair_products = pair_comparison[1]
    ls_rows_products = []
    for family, dict_sfamily in dict_pair_products.items():
      for sfamily, ls_sfamily_products in dict_sfamily.items():
        for ls_prod in ls_sfamily_products:
          ls_rows_products.append([family,
                                   sfamily,
                                   ls_prod[0]] + ls_prod[1][0])
          ls_rows_products.append([family,
                                   sfamily,
                                   ls_prod[0]] + ls_prod[1][1])
    
    df_pair_products = pd.DataFrame(ls_rows_products,
                               columns = ['section',
                                          'family',
                                          'product',
                                          'date',
                                          'store_chain',
                                          'price'])
    
    dict_replace_family = {u'familyId_2'  : u'Fruits et Légumes',
                           u'familyId_4'  : u'Frais',
                           u'familyId_5'  : u'Surgelés',
                           u'familyId_6'  : u'Epicerie salée',
                           u'familyId_7'  : u'Epicerie sucrée',
                           u'familyId_8'  : u'Aliments bébé et Diététique',
                           u'familyId_9'  : u'Boissons',
                           u'familyId_10' : u'Hygiène et Beauté',
                           u'familyId_11' : u'Nettoyage',
                           u'familyId_12' : u'Animalerie',
                           u'familyId_13' : u'Bazar et textile'}
    
    # extract store_chain trigram and replace by explicit store_chain
    df_pair_products['store_chain'] = (
      df_pair_products['store_chain'].apply(
        lambda x: dict_chains[
                    re.match(u'/bundles/qelmcsite/images/signs/header/(.*?)\.png',
                             x).group(1)]))
    
    # check robustness
    df_pair_products['store_id'] = leclerc_id
    df_pair_products.loc[df_pair_products['store_chain'] != 'LECLERC',
                         'store_id'] = competitor_id
    
    df_pair_products['section'] = (
       df_pair_products['section'].apply(lambda x: dict_replace_family[x]))
    
    df_pair_products['price'] = (
      df_pair_products['price'].apply(lambda x: x.replace(u'\xa0\u20ac', u''))
                                                 .astype(float))
    
    
    df_pair_products['date'] = (
      df_pair_products['date'].apply(lambda x: re.match(u'Prix relevé le (.*?)$',
                                                        x).group(1)))

    #df_pair_products['product'] = (
    #   df_pair_products['product'].apply(lambda x: x.encode('utf-8')))
    
    ls_df_pair_products.append(df_pair_products)
  
  df_region = pd.concat(ls_df_pair_products)
  df_region.sort(['store_id', 'section', 'family', 'product'], inplace = True)
  
  # drop duplicate at this stage but must do also with global df
  df_region.drop_duplicates(['store_id', 'section', 'family', 'product'],
                            inplace = True)
  
  #df_region.to_csv(os.path.join(path_csv,
  #                              'df_region_{:s}.csv'.format(region)),
  #                   encoding = 'utf-8',
  #                   float_format='%.3f',
  #                   index = False)
  ls_df_regions.append(df_region)

# Build price df
df_prices = pd.concat(ls_df_regions)

# Drop duplicates
df_prices.sort(['store_id', 'section', 'family', 'product'],
               inplace = True)
df_prices.drop_duplicates(['store_id', 'section', 'family', 'product'],
                          inplace = True)

## Products lister under several family/sections?
#print('\nOverview nb obs by product:')
#df_products = df_prices[['section', 'family', 'product']].drop_duplicates()
#se_prod_vc = df_prices['product'].value_counts()
#df_products.set_index('product', inplace = True)
#df_products['nb_obs'] = se_prod_vc
#df_products.sort('nb_obs', ascending = False, inplace = True)
#print df_products['nb_obs'].describe()

# Drop unique instance of product listed under two family/sections
df_prices = (df_prices[~((df_prices['family'] == u'Traiteur') &
                         (df_prices['product'] == u"DANIEL DESSAINT CRÊPES " +
                                                  u"MOELLEUSE SUCRÉES X8 400G " +
                                                  u"DANIEL DESSAINT"))])

# Drop product(s) with weird prices (from future investigations)
ls_suspicious_prods = [u'VIVA LAIT TGV 1/2 ÉCRÉMÉ VIVA BP 6X50CL']
df_prices = df_prices[~df_prices['product'].isin(ls_suspicious_prods)]

# Adhoc text fix
df_prices['product'] = (
  df_prices['product'].apply(lambda x: x.replace(u'\x8c', u'OE')))

df_prices.to_csv(os.path.join(path_csv,
                              'df_prices.csv'),
                   encoding = 'utf-8',
                   float_format='%.3f',
                   index = False)
