#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
import os, sys
import json
import pprint

path_carrefour = os.path.join(path_data,
                           u'data_drive_supermarkets',
                           u'data_carrefour')

path_price_source = os.path.join(path_carrefour,
                                 u'data_source',
                                 u'data_json_carrefour_voisins')

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

test_0 = dec_json(os.path.join(path_price_source,
                               u'20130418_carrefour_voisins'))

test_1 = dec_json(os.path.join(path_price_source,
                               u'20131123_carrefour_voisins'))

ls_price_int = []
ls_price = []
for i, product_info in enumerate(test_0):
  try:
    ls_price_int.append(float(product_info['main_price_bloc'][0].replace(',','.')))
  except:
    print i, product_info['main_price_bloc']
  if 'decimal' not in product_info['main_price_bloc'][2]:
    print i, product_info['main_price_bloc']
  try:
    ls_price.append(float(product_info['sec_price_bloc'][0].replace(',','.')))
  except:
    print i, product_info['sec_price_bloc']

# NO INFO ON SALES.. SH...
