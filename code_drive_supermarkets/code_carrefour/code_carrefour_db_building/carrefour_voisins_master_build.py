# -*- coding: iso-8859-1 -*-
import os, sys
import json
import pprint

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_stock_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

# path_data: data folder at different locations at CREST vs. HOME
# could do the same for path_code if necessary (import etc).
if os.path.exists(r'W:\Bureau\Etienne_work\Data'):
  path_data = r'W:\Bureau\Etienne_work\Data'
else:
  path_data = r'C:\Users\etna\Desktop\Etienne_work\Data'
# structure of the data folder should be the same
folder_source_carrefour_voisins_prices = r'\data_drive_supermarkets\data_carrefour\data_source\data_json_carrefour_voisins'

test_0 = dec_json(path_data + folder_source_carrefour_voisins_prices +  r'\20130418_carrefour_voisins')

test_1 = dec_json(path_data + folder_source_carrefour_voisins_prices +  r'\20131123_carrefour_voisins')

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

# TODO: build master... see price variations apart from sales still
# TODO: fix scrap_script + auchan's to get good info on sales at last... + EAN or whatever