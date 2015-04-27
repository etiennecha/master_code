#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
import json
import re
import math
import pandas as pd
import numpy as np
from datetime import date, timedelta

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

def get_date_range(start_date, end_date):
  """
  creates a list of dates based on its arguments (beginning and end dates)
  """
  ls_dates = []
  for n in range((end_date + timedelta(1) - start_date).days):
    temp_date = start_date + timedelta(n)
    ls_dates.append(temp_date.strftime('%Y%m%d'))
  return ls_dates

def explore_key(ls_dict_product, field):
  """
  analysis of fields which are lists (still contain html btw)
  """
  dict_len = {}
  ls_ls_unique = []
  for dict_product in ls_dict_product:
    # Get all product content lengths for this field
    if len(dict_product[field]) not in dict_len.keys():
      dict_len[len(dict_product[field])] = 1
      ls_ls_unique.append([])
    else:
      dict_len[len(dict_product[field])] +=1
    # Get all unique product contents by position for this field
    while len(ls_ls_unique) < len(dict_product[field]):
      ls_ls_unique.append([])
    for i, elt in enumerate(dict_product[field]):
      if elt not in ls_ls_unique[i]:
        ls_ls_unique[i].append(elt)
  return [dict_len, ls_ls_unique]
