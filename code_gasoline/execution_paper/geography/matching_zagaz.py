#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path_sub
from add_to_path_sub import path_data
from generic_master_price import *
from generic_master_info import *
from functions_string import *

path_dir_built_paper = os.path.join(path_data, 'data_gasoline', 'data_built', 'data_paper')

path_dir_built_json = os.path.join(path_dir_built_paper, 'data_json')
path_diesel_price = os.path.join(path_dir_built_json, 'master_price_diesel.json')
path_info = os.path.join(path_dir_built_json, 'master_info_diesel.json')
path_ls_ls_competitors = os.path.join(path_dir_built_json, 'ls_ls_competitors.json')
path_ls_tuple_competitors = os.path.join(path_dir_built_json, 'ls_tuple_competitors.json')

path_dir_source = os.path.join(path_data, 'data_gasoline', 'data_source')
path_dict_brands = os.path.join(path_dir_source, 'data_other', 'dict_brands.json')
path_csv_insee_data = os.path.join(path_dir_source, 'data_other', 'data_insee_extract.csv')

path_dir_zagaz = os.path.join(path_dir_source, 'data_stations', 'data_zagaz')

path_dir_insee = os.path.join(path_data, 'data_insee')
path_dict_dpts_regions = os.path.join(path_dir_insee, 'dpts_regions', 'dict_dpts_regions.json')

master_price = dec_json(path_diesel_price)
master_info = dec_json(path_info)
ls_ls_competitors = dec_json(path_ls_ls_competitors)
ls_tuple_competitors = dec_json(path_ls_tuple_competitors)
dict_brands = dec_json(path_dict_brands)
dict_dpts_regions = dec_json(path_dict_dpts_regions)

dict_zagaz_gps = dec_json(os.path.join(path_dir_zagaz, 'zagaz_info_and_gps_stations.json'))
dict_zagaz_all = dec_json(os.path.join(path_dir_zagaz, '20140124_zagaz_stations.json'))
dict_zagaz_prices = dec_json(os.path.join(path_dir_zagaz, '20140127_zagaz_dict_ext_prices.json'))
dict_zagaz_users = dec_json(os.path.join(path_dir_zagaz, '20140124_zagaz_dict_active_users.json'))
 
# Check matching between (old) zagaz gps file and (recent) info/price files
ls_missing_gps_zagaz = [indiv_id for indiv_id, indiv_info in dict_zagaz_all.items()\
                          if indiv_id not in dict_zagaz_gps]
print len(ls_missing_gps_zagaz), 'gps coordinates are to be collected'
# TODO: pbm: need to have all insee codes if those are used for matching
