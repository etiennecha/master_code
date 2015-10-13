#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import *
import os, sys
import httplib
import urllib, urllib2
from bs4 import BeautifulSoup
import re
import json
import pandas as pd

def enc_json(data, path_file):
  with open(path_file, 'w') as f:
    json.dump(data, f)

def dec_json(path_file):
  with open(path_file, 'r') as f:
    return json.loads(f.read())

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

ls_df_regions = []
for region in ls_fra_regions:
  path_dict_reg_comparisons = os.path.join(path_qlmc_scraped,
                                           'dict_reg_comparisons_{:s}.json'.format(region))
  dict_reg_comparisons_json = dec_json(path_dict_reg_comparisons)
  # convert keys from string to tuple
  dict_reg_comparisons = {tuple(json.loads(k)):v\
                            for k,v in dict_reg_comparisons_json.items()}
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
                                   ls_prod[0]]+\
                                  ls_prod[1][0])
          ls_rows_products.append([family,
                                   sfamily,
                                   ls_prod[0]]+\
                                  ls_prod[1][1])
    
    df_pair_products = pd.DataFrame(ls_rows_products,
                               columns = ['family',
                                          'subfamily',
                                          'product',
                                          'date',
                                          'chain',
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
    
    df_pair_products['family'] =\
       df_pair_products['family'].apply(lambda x: dict_replace_family[x])
    
    df_pair_products['price'] =\
      df_pair_products['price'].apply(lambda x: x.replace(u'\xa0\u20ac', u'')).astype(float)
    
    df_pair_products['chain'] =\
      df_pair_products['chain'].apply(\
        lambda x: re.match(u'/bundles/qelmcsite/images/signs/header/(.*?)\.png',
                           x).group(1))
    
    df_pair_products['date'] =\
      df_pair_products['date'].apply(\
        lambda x: re.match(u'Prix relevé le (.*?)$',
                           x).group(1))

    #df_pair_products['product'] =\
    #   df_pair_products['product'].apply(lambda x: x.encode('utf-8'))
    
    # can do more robust?
    df_pair_products['store_id'] = leclerc_id
    df_pair_products.loc[df_pair_products['chain'] != 'LEC', 'store_id'] = competitor_id
    
    ls_df_pair_products.append(df_pair_products)
  
  df_region = pd.concat(ls_df_pair_products)
  df_region.sort(['store_id', 'family', 'subfamily', 'product'], inplace = True)
  
  # drop duplicate at this stage but must do also with global df
  df_region.drop_duplicates(['store_id', 'family', 'subfamily', 'product'], inplace = True)
  
  #df_region.to_csv(os.path.join(path_csv,
  #                              'df_region_{:s}.csv'.format(region)),
  #                   encoding = 'utf-8',
  #                   float_format='%.3f',
  #                   index = False)
  ls_df_regions.append(df_region)

df_prices = pd.concat(ls_df_regions)
df_prices.sort(['store_id', 'family', 'subfamily', 'product'], inplace = True)
df_prices.drop_duplicates(['store_id', 'family', 'subfamily', 'product'], inplace = True)

df_prices.to_csv(os.path.join(path_csv,
                              'df_prices.csv'),
                   encoding = 'utf-8',
                   float_format='%.3f',
                   index = False)
