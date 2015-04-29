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

path_current_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
dict_prices = dec_json(os.path.join(path_current_dir,
                                    u'dict_carrefour_prelim_prices.json'))
dict_info = dec_json(os.path.join(path_current_dir,
                                       u'dict_carrefour_prelim_info.json'))
dict_carrefour = dec_json(os.path.join(path_current_dir,
                                       u'dict_carrefour_wine.json'))

# dict_prices
# Goal is to xtract prix unitaire for each Lot
# todo: check all existing conditionnement_lot contents
# todo: check that all except A l unite have a prix unitaire

# dict_info
# Copy format_vins_auchan

# dict_carrefour
# todo: find how to format notes (clean and check common 1st item: Wine Spectator etc)
# todo: format desc... just a long string to be cleaned? can separate?
