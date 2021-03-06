#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import add_to_path
from add_to_path import *
import os, sys
import json
import re
import pandas as pd

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

dict_reg_leclerc = dec_json(os.path.join(path_qlmc_scraped, 'dict_reg_leclerc_stores.json'))
dict_leclerc_comp = dec_json(os.path.join(path_qlmc_scraped, 'dict_leclerc_comp.json'))

# Exclude Leclerc from competitors (not compared on website)
for leclerc_id, ls_comp in dict_leclerc_comp.items():
  ls_comp_cl = [comp for comp in ls_comp if comp['signCode'] != u'LEC']
  dict_leclerc_comp[leclerc_id] = ls_comp_cl

# Count all competitor pairs from website
ls_all_pairs = ([(leclerc_id, comp['slug'])
                  for leclerc_id, ls_comp in dict_leclerc_comp.items()
                    for comp in ls_comp])

# Count competitor pairs actually queried
# NB: fragile... loop on dict and order matters
ls_covered_comp = [] # should be stored and updated?
ls_collect_pairs = []
dict_reg_pairs = {}
for region, ls_leclerc in dict_reg_leclerc.items():
  ls_reg_pairs = []
  for leclerc in ls_leclerc:
    ls_comp = dict_leclerc_comp[leclerc['slug']]
    # keep competitors not met in scrapping so far (store itself included in list)
    ls_comp_todo = ([comp for comp in ls_comp if (comp['slug'] not in ls_covered_comp)])
    # if all scraped, take first one to get current Leclerc's prices
    if not ls_comp_todo:
      ls_comp_todo = ls_comp[:1]
    for comp in ls_comp_todo:
      ls_collect_pairs.append((leclerc['slug'], comp['slug']))
      ls_reg_pairs.append((leclerc['slug'], comp['slug']))
      ls_covered_comp.append(comp['slug'])
  dict_reg_pairs[region] = ls_reg_pairs

# List competitor pairs not collected (on purpose)
ls_exclude_pairs = ([(leclerc_id, comp_id) for (leclerc_id, comp_id) in ls_all_pairs
                      if (leclerc_id, comp_id) not in ls_collect_pairs])

print(u'Total nb pairs listed on website {:d}'.format(len(ls_all_pairs)))
print(u'Number of pairs queried {:d}'.format(len(ls_collect_pairs)))
