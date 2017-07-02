#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from scraping_drive_prices import ScrapCarrefour
from functions_generic_drive import *
import os
import pprint
import json
from datetime import date

ls_store_subset = [u'06 - ANTIBES (HYPER)',
                   u'06 - NICE LINGOSTIERE',
                   u'13 - AIX EN PROVENCE',
                   u'69 - ECULLY',
                   u'69 - VENISSIEUX',
                   u'91 - LES ULIS',
                   u'91 - VILLABE',
                   u'92 - CLAMART',
                   u"78 - VOISINS LE BRETONNEUX",
                   u'33 - MERIGNAC (HYPER)']

path_carrefour = os.path.join(path_data,
                              u'data_supermarkets',
                              u'data_drive',
                              u'data_carrefour')

today_date = date.today().strftime(u"%Y%m%d")

path_dict_prices_today =  os.path.join(path_carrefour,
                                       u'data_source',
                                       u'data_json_carrefour',
                                       u'{:s}_dict_carrefour'.format(today_date))

if os.path.exists(path_dict_prices_today):
  dict_prices = dec_json(path_dict_prices_today)
else:
  dict_prices = {}

scrap_carrefour = ScrapCarrefour()

ls_store_ids = scrap_carrefour.dict_store_urls.keys()

#ls_store_add = [store_id for store_id in ls_store_ids\
#                  if store_id not in dict_prices][0:10]
#pprint.pprint(ls_store_add)

dict_prices_add = scrap_carrefour.scrap_stores(ls_store_subset)
dict_prices.update(dict_prices_add)
enc_json(dict_prices, path_dict_prices_today)
