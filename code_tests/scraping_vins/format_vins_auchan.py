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
                     .replace(u'\n', u'')\
                     .replace(u'\u20ac', u'')\
                     .strip()
  return some_str

dict_auchan =\
  dec_json(ur'W:\Bureau\Etienne_work\Code\code_tests\scraping_vins\dict_auchan_wine.json')

# Get dict of dict
dict_dict_auchan = {}
for k,v in dict_auchan.items():
  dict_dict_auchan[k] = {l:w for l,w in v}
  # convert list to string
  if 'price_per_unit' in dict_dict_auchan[k]:
    dict_dict_auchan[k]['price_per_unit'] = ' '.join(dict_dict_auchan[k]['price_per_unit'])

# Get unique fields
ls_fields = list(set([x for k,v in dict_dict_auchan.items() for x in v.keys()]))

ls_rows = []
for k, v in dict_dict_auchan.items():
  row = [v.get(field) for field in ls_fields]
  row = [clean_text(x) if x else x for x in row]
  ls_rows.append(row)

df_auchan_wine = pd.DataFrame(ls_rows, columns = ls_fields)

df_auchan_wine.to_csv(ur'W:\Bureau\Etienne_work\Code\code_tests\scraping_vins\df_auchan_wine.csv',
                      encoding = 'utf-8',
                      index = False)
