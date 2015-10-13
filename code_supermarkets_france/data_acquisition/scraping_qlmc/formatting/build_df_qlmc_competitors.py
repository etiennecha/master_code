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

dict_reg_leclerc = dec_json(os.path.join(path_qlmc_scraped,
                                         'dict_reg_leclerc_stores.json'))

dict_leclerc_comp = dec_json(os.path.join(path_qlmc_scraped,
                                          'dict_leclerc_comp.json'))


# ##############################
# BUILD DF ALL COMPETITOR PAIRS
# ##############################

# df with all comparisons including those not scraped

# Get dict of leclerc with leclerc info
dict_leclerc_stores = {}
for reg, ls_reg_dict_leclerc_stores in dict_reg_leclerc.items():
  for dict_leclerc_store in ls_reg_dict_leclerc_stores:
    dict_leclerc_stores[dict_leclerc_store['slug']] = dict_leclerc_store

# Exclude Leclerc from competitors (not compared on website)
for leclerc_id, ls_comp in dict_leclerc_comp.items():
  ls_comp_cl = [comp for comp in ls_comp if comp['signCode'] != u'LEC']
  dict_leclerc_comp[leclerc_id] = ls_comp_cl

# Build df
ls_rows_all = []
for leclerc_id, ls_comp in dict_leclerc_comp.items():
  for dict_comp in ls_comp:
    row = [leclerc_id,
           dict_leclerc_stores[leclerc_id]['title'],
           dict_leclerc_stores[leclerc_id]['latitude'],
           dict_leclerc_stores[leclerc_id]['longitude'],
           dict_comp['slug'],
           dict_comp['title'],
           dict_comp['latitude'],
           dict_comp['longitude'],
           dict_comp['signCode']]
    ls_rows_all.append(row)

df_all = pd.DataFrame(ls_rows_all,
                      columns = ['lec_id',
                                 'lec_name',
                                 'lec_lat',
                                 'lec_lng',
                                 'comp_id',
                                 'comp_name',
                                 'comp_lat',
                                 'comp_lng',
                                 'comp_chain'])

# ##################################
# BUILD DF SCRAPED COMPETITOR PAIRS
# ##################################

ls_regions = [u'picardie',
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

ls_rows_res = []
for region in ls_regions:
  path_dict_reg_comparisons = os.path.join(path_qlmc_scraped,
                                           'dict_reg_comparisons_{:s}.json'.format(region))
  if os.path.exists(path_dict_reg_comparisons):
    dict_reg_comparisons_json = dec_json(path_dict_reg_comparisons)
    # convert keys from string to tuple
    dict_reg_comparisons = {tuple(json.loads(k)):v\
                       for k,v in dict_reg_comparisons_json.items()}
    print u'Found and loaded dict_reg_comparisons for {:s}'.format(region)
  else:
    dict_reg_comparisons = {}
    print u'No dict_reg_comparisons for {:s} so created one (empty)'.format(region)

  # READ GENERAL INFORMATION
  #for k,v in dict_reg_comparisons.items():
  #  print v[0][0]
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
    ls_rows_res.append([region] + row_res)

df_scraped = pd.DataFrame(ls_rows_res,
                          columns = ['region',
                                     'lec_id',
                                     'comp_id',
                                     'date_beg',
                                     'date_end',
                                     'qlmc_nb_obs',
                                     'qlmc_pct_compa',
                                     'qlmc_winner'])

df_scraped['qlmc_nb_obs'] =\
   df_scraped['qlmc_nb_obs'].apply(lambda x: x.replace(' ', '')).astype(float)

df_scraped['qlmc_pct_compa'] = df_scraped['qlmc_pct_compa'].astype(float)

# ########
# MERGE
# ########

df_qlmc_competitors = pd.merge(df_all,
                               df_scraped,
                               on = ['lec_id', 'comp_id'],
                               how = 'left')

# #########
# OUTPUT
# #########

df_qlmc_competitors.to_csv(os.path.join(path_csv,
                                        'df_qlmc_competitors.csv'),
                           encoding = 'UTF-8',
                           float_format='%.3f',
                           index = False)
