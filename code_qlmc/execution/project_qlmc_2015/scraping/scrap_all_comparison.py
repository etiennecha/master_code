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

def enc_json(data, path_file):
  with open(path_file, 'w') as f:
    json.dump(data, f)

def dec_json(path_file):
  with open(path_file, 'r') as f:
    return json.loads(f.read())

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

ls_fra_regions = [u'picardie', # ok (home)
                  u'franche-comte',
                  u'languedoc-roussillon',
                  u'rhone-alpes',
                  u'basse-normandie', # ok (rerun - home)
                  u'poitou-charentes',
                  u'pays-de-la-loire', # in progress (crest)
                  u'lorraine', # ok (rerun)
                  u'midi-pyrenees',
                  u'nord-pas-de-calais', # ok
                  u'centre', # ok (rerun home)
                  u'bretagne', # ok (rerun home)
                  u'bourgogne',
                  u'aquitaine',
                  u'auvergne',
                  u'alsace', # in progress (crest)
                  u'corse',
                  u'champagne-ardenne', # ok
                  u'haute-normandie', # ok
                  u'ile-de-france', # ok (todo: rerun)
                  u'provence-alpes-cote-d-azur',
                  u'limousin']

# Choice of region
region = 'franche-comte'
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

# Loop on pairs
for store_id, comp_id in ls_pairs:
  if (store_id, comp_id) not in dict_reg_comparisons.keys():
    try:
      # Visit competitor's page
      url_comp = u'http://www.quiestlemoinscher.com/local/{:s}/{:s}'.\
                    format(store_id, comp_id)
      response_comp = urllib2.urlopen(url_comp)
      data_comp = response_comp.read()
      soup_comp = BeautifulSoup(data_comp)
      # Get link to family/subfamilies of products
      bloc_families = soup_comp.find('div', {'id' : 'menuLev2', 'class' : 'onTop'})
      ls_family_blocs = bloc_families.findAll('ul', {'id' : True})
      dict_families = {}
      for family_bloc in ls_family_blocs:
        family_name = family_bloc['id']
        ls_subfamily_blocs = family_bloc.findAll('a', {'href' : True})
        ls_subfamilies = [(x.text, x['href']) for x in ls_subfamily_blocs]
        dict_families[family_name] = ls_subfamilies
      # Get comparison result
      bloc_comparison = soup_comp.find('div', {'id' : 'battleHomeLocal'})
      ls_compa = [bloc_comparison.find('p', {'class' : 'mention'}),
                  bloc_comparison.find('h2', {'class' : 'sign textblue'}),
                  bloc_comparison.find('p', {'class' : 'result textblue'}),
                  bloc_comparison.find('h2', {'class' : 'sign textred'}),
                  bloc_comparison.find('p', {'class' : 'result textred'})]
      ls_compa = [x.text if x else None for x in ls_compa]
      
      # Visit competitor's (sub)family pages
      #family = dict_families.keys()[0]
      #sf, sf_url_extension = dict_families[family][0]
      dict_comp =  {}
      for family, ls_sub_families in dict_families.items():
        dict_comp[family] = {}
        for sf, sf_url_extension in ls_sub_families:
          sf_url = u'http://www.quiestlemoinscher.com{:s}'.format(sf_url_extension)
          sf_response = urllib2.urlopen(sf_url)
          sf_data = sf_response.read()
          sf_soup = BeautifulSoup(sf_data)
          ls_prod_blocs = sf_soup.findAll('article', {'class' : 'listProducts'})
          ls_sf_products = []
          for prod_bloc in ls_prod_blocs:
            product_name = prod_bloc.find('div', {'class' : 'txtProducts'}).h3.text
            ls_prod_info = []
            ls_prod_sub_blocs = prod_bloc.findAll('div', {'class' : 'txtCompare'})
            for prod_sub_bloc in ls_prod_sub_blocs:
              releve_date = prod_sub_bloc.find('div', {'class' : 'mentionReleve'}).text
              psb_temp = prod_sub_bloc.find('div', {'class' : re.compile('signPrice*.')})
              releve_store = psb_temp.find('img')['src']
              releve_price = psb_temp.text
              ls_prod_info.append([releve_date, releve_store, releve_price])
            ls_sf_products.append([product_name, ls_prod_info])
          dict_comp[family][sf] = ls_sf_products
          
      dict_reg_comparisons[(store_id, comp_id)] = [ls_compa, dict_comp]
      print 'Got data for pair {:s} {:s}'.format(store_id, comp_id)
    except:
      print 'Failed for pair {:s} {:s}'.format(store_id, comp_id)
      pass

# Can not store tuples in json: convert to string
dict_reg_comparisons_json = {u'["{:s}", "{:s}"]'.format(*k):v\
                        for k, v in dict_reg_comparisons.items()}
enc_json(dict_reg_comparisons_json,
         os.path.join(path_dict_reg_comparisons))
