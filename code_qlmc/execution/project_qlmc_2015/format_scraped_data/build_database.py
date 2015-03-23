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

path_qlmc_scrapped = os.path.join(path_data,
                                  'data_qlmc',
                                  'data_source',
                                  'data_scrapped')

dict_reg_leclerc = dec_json(os.path.join(path_qlmc_scrapped,
                                         'dict_reg_leclerc_stores.json'))

dict_leclerc_comp = dec_json(os.path.join(path_qlmc_scrapped,
                                          'dict_leclerc_comp.json'))

# Define list of pairs to scrap by region
# Want to minimize number of pairs to collect
# Check that at least one not scraped before
# Arbitrary order (keys in dict_reg_leclerc...)

ls_covered_comp = [] # should be stored and updated?
ls_pairs = []
dict_reg_pairs = {}
for region, ls_leclerc in dict_reg_leclerc.items():
  ls_reg_pairs = []
  for leclerc in ls_leclerc:
    ls_comp = dict_leclerc_comp[leclerc['slug']]
    # keep competitors not met in scrapping so far (store itself included in list)
    ls_comp_todo = [comp for comp in ls_comp if\
                      (comp['slug'] not in ls_covered_comp) and\
                      (comp['signCode'] != u'LEC')]
    # if all scrapped, take first one to get current Leclerc's prices
    if not ls_comp_todo:
      ls_comp_todo = ls_comp[:1]
    for comp in ls_comp_todo:
      ls_pairs.append((leclerc['slug'], comp['slug']))
      ls_reg_pairs.append((leclerc['slug'], comp['slug']))
      ls_covered_comp.append(comp['slug'])
  dict_reg_pairs[region] = ls_reg_pairs

ls_regions_done = [u'nord-pas-de-calais', # crest
                   u'ile-de-france',
                   u'champagne-ardenne',
                   u'haute-normandie',
                   u'lorraine',
                   u'pays-de-la-loire',
                   u'rhone-alpes',
                   u'picardie', # home / one leclerc beaten
                   u'auvergne',
                   u'alsace',
                   u'basse-normandie',
                   u'bourgogne',
                   u'bretagne',
                   u'franche-comte',
                   u'limousin',
                   u'languedoc-roussillon',
                   u'centre', # one leclerc beaten
                   u'midi-pyrenees',
                   u'provence-alpes-cote-d-azur']

# Choice of region
region = ls_regions_done[-12] 
ls_pairs = dict_reg_pairs[region]

# Load dict region if exists or create it
path_dict_reg_comparisons = os.path.join(path_qlmc_scrapped,
                                         'dict_reg_comparisons_{:s}.json'.format(region))
if os.path.exists(path_dict_reg_comparisons):
  dict_reg_comparisons_json = dec_json(path_dict_reg_comparisons)
  # convert keys from string to tuple
  dict_reg_comparisons = {tuple(json.loads(k)):v\
                     for k,v in dict_reg_comparisons_json.items()}
  print u'Found and loaded dict_reg_comparisons for {:s}'.format(region)
else:
  dict_reg_comparisons = {}
  print u'No dict_reg_comparisons for {:s} so created one'.format(region)

# READ GENERAL INFORMATION
#for k,v in dict_reg_comparisons.items():
#  print v[0][0]
ls_rows_res = []
for k,v in dict_reg_comparisons.items():
  row_res = list(k)
  re_general = re.search(u'Prix collectés entre le '
                         u'(.*?) et le (.*?) 2015 sur '
                         u'(.*?) produits comparés', v[0][0])
  if re_general:
    row_res += [re_general.group(1),
                re_general.group(2),
                re_general.group(3)]
  else:
    row_res += [None, None, None]
  # % comparison
  pct_compa, winner = None, None
  if v[0][-1]:
    re_compa = re.match(u'(.*?)%', v[0][-1])
    if re_compa:
      pct_compa = re_compa.group(1)
    if 'PLUS CHER que E.Leclerc' in v[0][-1]:
      winner = 'LEC'
  elif 'MOINS CHER que E.Leclerc' in v[0][2]:
    re_compa = re.match(u'(.*?)%', v[0][2])
    if re_compa:
      pct_compa = re_compa.group(1)
    winner = 'OTH'
  row_res += [pct_compa, winner]
  ls_rows_res.append(row_res)

df_overview = pd.DataFrame(ls_rows_res, columns = ['leclerc',
                                                   'competitor',
                                                   'date_beg',
                                                   'date_end',
                                                   'nb_obs',
                                                   'pct_compa',
                                                   'winner'])

df_overview['nb_obs'] =\
   df_overview['nb_obs'].apply(lambda x: x.replace(' ', '')).astype(float)

df_overview['pct_compa'] = df_overview['pct_compa'].astype(float)

print df_overview.to_string()

# READ PRODUCT COMPARISONS

#print u'\n', dict_reg_comparisons[dict_reg_comparisons.keys()[0]][0]
#dict_pair_products = dict_reg_comparisons[dict_reg_comparisons.keys()[0]][1]

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
  
  # can do more robust?
  df_pair_products['store_id'] = leclerc_id
  df_pair_products.loc[df_pair_products['chain'] != 'LEC', 'store_id'] = competitor_id
  
  ls_df_pair_products.append(df_pair_products)

  df_products = pd.concat(ls_df_pair_products)
  df_products.sort(['store_id', 'family', 'subfamily', 'product'], inplace = True)
  
  # drop duplicate at this stage but must do also with global df
  df_products.drop_duplicates(['store_id', 'family', 'subfamily', 'product'], inplace = True)
