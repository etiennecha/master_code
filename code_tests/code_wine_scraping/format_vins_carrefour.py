#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
import json
import re
from datetime import date
import time
import pandas as pd

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

def clean_text(some_str):
  # euro sign dropped for now (u'\u20ac')
  some_str = some_str.replace(u'\xa0', u'')\
                     .replace(u'\r\n', u'')\
                     .replace(u'\n', u'')\
                     .replace(u'\r', u'')\
                     .replace(u'\t', u'')\
                     .replace(u'\u20ac', u'')\
                     .strip()
  return some_str

path_current_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
dict_prices = dec_json(os.path.join(path_current_dir,
                                    u'dict_carrefour_prelim_prices.json'))
dict_info = dec_json(os.path.join(path_current_dir,
                                       u'dict_carrefour_prelim_info.json'))
dict_carrefour = dec_json(os.path.join(path_current_dir,
                                       u'dict_carrefour_wine.json'))

# ###########
# dict_prices
# ###########

# Goal is to xtract prix unitaire for each Lot
# todo: check all existing conditionnement_lot contents
# todo: check that all except A l unite have a prix unitaire
dict_ls_dict_prices = {}
for k, v in dict_prices.items():
  ls_dict_prices = [dict(ls_prices) for ls_prices in v]
  dict_ls_dict_prices[k] = ls_dict_prices

# Check all fields in each dict_price
ls_price_fields = []
for k, ls_dict_prices in dict_ls_dict_prices.items():
  for dict_price in ls_dict_prices:
    ls_price_fields += dict_price.keys()
ls_price_fields = list(set(ls_price_fields))

# Check all contents of field lot
ls_lots = []
for k, ls_dict_prices in dict_ls_dict_prices.items():
  for dict_price in ls_dict_prices:
    ls_lots.append(dict_price.get('box_conditionnement_lot'))
ls_lots = list(set(ls_lots))

# Build dict with px unitaire, prix unitaire if 6, prix unitaire if 12
dict_dict_prices = {}
for k, ls_dict_prices in dict_ls_dict_prices.items():
  dict_dict_prices[k] = {}
  for dict_price in ls_dict_prices:
    if dict_price[u'box_conditionnement_lot'] == u"A l'unit\xe9":
      dict_dict_prices[k][u"A l'unit\xe9"] =\
          dict_price[u'box_conditionnement_prix'].replace(u'\u20ac', '')\
                                                 .replace(u'\xa0', '')\
                                                 .strip()
    else:
      dict_dict_prices[k][dict_price[u'box_conditionnement_lot']] =\
          dict_price[u'box_conditionnement_prix_unitaire']

# #########
# dict_info
# #########

# Copy format_vins_auchan
# Get dict of dict
dict_dict_info = {}
for k, v in dict_info.items():
  dict_dict_info[k] = {l:w for l,w in v}
  # convert list to string
  if 'situation' in dict_dict_info[k]:
    dict_dict_info[k]['situation'] = \
      clean_text(' '.join(dict_dict_info[k]['situation']))
  dict_dict_info[k] = {l: clean_text(w) for l,w in dict_dict_info[k].items()}

# ##############
# dict_carrefour
# ##############

dict_dict_carrefour = {}
for k, v in dict_carrefour.items():
  dict_dict_carrefour[k] = {l:w for l,w in v}
  # clean description (can do better? extract info with regex? Medailles? Guides?)
  dict_dict_carrefour[k]['desc'] = [clean_text(x) for x in dict_dict_carrefour[k]['desc']]
  dict_dict_carrefour[k]['desc'] = [x for x in dict_dict_carrefour[k]['desc'] if x]
  # overwrite short version in dict_dict_info
  dict_dict_info[k][u'box_listing_descriptif'] = ' '.join(dict_dict_carrefour[k]['desc'])
  # todo: clean notes
  # focus on guides... always last elt? (or then none??)
  ls_ls_notes_guides_clean = []
  for ls_note_guide in dict_dict_carrefour[k]['notes'][-1]:
    ls_note_guide_clean = [clean_text(x) for x in ls_note_guide]
    ls_note_guide_clean = [x for x in ls_note_guide_clean if x]
    ls_ls_notes_guides_clean.append(ls_note_guide_clean)
  dict_dict_carrefour[k]['notes_guides'] = ls_ls_notes_guides_clean

ls_guides = []
# List all guides (and btw cheek that only guides in this field indeed)
for k, v in dict_dict_carrefour.items():
  for ls_note_guide in v['notes_guides']:
    ls_guides.append(ls_note_guide[0])
ls_guides = list(set(ls_guides))

# Write "guide notes" in dict_dict_carrefour
# Note is always second element (checke)
for k, v in dict_dict_carrefour.items():
  for ls_note_guide in v['notes_guides']:
    #if len(ls_note_guide) != 2:
    #  print u'Unexpected length for ls_note_guide:', ls_note_guide
    dict_dict_carrefour[k][ls_note_guide[0]] = ls_note_guide[1]
  del(dict_dict_carrefour[k]['notes_guides'])

# #############
# build df
# #############

# todo: get from dict_dict_info
ls_info_fields = [u'situation',
                  u'box_listing_descriptif',
                  u'box_fiche_produit_type_vin_txt',
                  u'box_listing_nom_produit',
                  u'info_cl']

ls_rows = []
for k, v in dict_dict_info.items():
  row = [v.get(field) for field in ls_info_fields]
  k_dict_price = dict_dict_prices.get(k, {})
  row += [k_dict_price.get(field) for field in ls_lots]
  k_dict_carrefour = dict_dict_carrefour.get(k, {})
  row += [k_dict_carrefour.get(field) for field in ls_guides]
  ls_rows.append(row)

df_carrefour = pd.DataFrame(ls_rows,
                            columns = ls_info_fields + ls_lots + ls_guides)

df_carrefour.to_csv(os.path.join(path_current_dir,
                                   'df_carrefour_wine.csv'),
                    encoding = 'utf-8',
                    index = False)
