#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from scraping_drive_prices import ScrapAuchan
from functions_generic_drive import *
import os
import pprint
import json
from datetime import date

ls_store_subset = [u'VELIZY Cedex']

path_auchan = os.path.join(path_data,
                              u'data_drive_supermarkets',
                              u'data_auchan')

today_date = date.today().strftime(u"%Y%m%d")

path_dict_prices_today =  os.path.join(path_auchan,
                                       u'data_source',
                                       u'data_json_auchan',
                                       u'{:s}_dict_auchan'.format(today_date))

if os.path.exists(path_dict_prices_today):
  dict_prices = dec_json(path_dict_prices_today)
else:
  dict_prices = {}

scrap_auchan = ScrapAuchan()
dict_stores = scrap_auchan.dict_store_urls
ls_store_ids = dict_stores.keys()

#ls_store_add = [store_id for store_id in ls_store_ids\
#                  if store_id not in dict_prices][0:10]
#
#pprint.pprint(ls_store_add)

dict_prices_add = scrap_auchan.scrap_stores(ls_store_subset)

# dict_prices.update(dict_prices_add)

# enc_json(dict_prices, path_dict_prices_today)
