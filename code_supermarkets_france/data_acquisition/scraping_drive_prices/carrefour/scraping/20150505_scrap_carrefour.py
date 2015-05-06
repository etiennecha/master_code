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

#def enc_json(data, path_data):
#  with open(path_data, 'w') as f:
#    json.dump(data, f)

ls_stores_subset = [u'06 - ANTIBES (HYPER)',
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
                              u'data_drive_supermarkets',
                              u'data_carrefour')

today_date = date.today().strftime(u"%Y%m%d")

path_dict_prices_today =  os.path.join(path_carrefour,
                                       u'data_source',
                                       u'data_json_carrefour',
                                       u'{:s}_dict_carrefour'.format(today_date))

dict_prices = dec_json(path_dict_prices_today)

scrap_carrefour = ScrapCarrefour()
pprint.pprint(scrap_carrefour.ls_ls_stores[0:10])

ls_store_ids = [row_store[-1] for row_store in scrap_carrefour.ls_ls_stores]
ls_stores_add = [store_id for store_id in ls_store_ids if store_id not in dict_prices][0:10]

dict_prices_add = scrap_carrefour.scrap_stores(ls_stores_add)

# enc_json(dict_prices, path_dict_prices_today)
