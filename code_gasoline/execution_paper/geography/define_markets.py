#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path_sub
from add_to_path_sub import path_data
from generic_master_price import *
from generic_master_info import *
from generic_competition import *
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

path_dir_insee = os.path.join(path_data, 'data_insee')
path_dict_dpts_regions = os.path.join(path_dir_insee, 'dpts_regions', 'dict_dpts_regions.json')

master_price = dec_json(path_diesel_price)
master_info = dec_json(path_info)
ls_ls_competitors = dec_json(path_ls_ls_competitors)
ls_tuple_competitors = dec_json(path_ls_tuple_competitors)
dict_brands = dec_json(path_dict_brands)
dict_dpts_regions = dec_json(path_dict_dpts_regions)

ls_dict_markets = []
for distance in [3,4,5]:
  print '\nMarkets with distance', distance
  ls_markets = get_ls_ls_distance_market_ids(master_price['ids'], ls_ls_competitors, distance)
  dict_market_ind = {ls_ids[0]: i for i, ls_ids in enumerate(ls_markets)}
  # todo: keep centers of market and periphery?
  ls_closed_markets = []
  for market in ls_markets:
    dum_closed_market = True
    for indiv_id in market[1:]:
      if any(comp_id not in market for comp_id in ls_markets[dict_market_ind[indiv_id]]):
        dum_closed_market = False
        break
    market = sorted(market)
    if dum_closed_market == True and market not in ls_closed_markets:
      ls_closed_markets.append(market)
  # Dict: markets by nb of competitors
  dict_market_size = {}
  for market in ls_closed_markets:
  	dict_market_size.setdefault(len(market), []).append(market)
  for k,v in dict_market_size.items():
  	print k, len(v)
  ls_dict_markets.append(dict_market_size)

# Most stable markets
dict_refined, dict_rejected = {}, {}
for market_size, ls_markets in ls_dict_markets[0].items():
  for market in ls_markets:
    if all((market_size in dict_market) and (market in dict_market[market_size])\
             for dict_market in ls_dict_markets[1:]):
      dict_refined.setdefault(market_size, []).append(market)
    else:
      dict_rejected.setdefault(market_size, []).append(market)
for k, v in dict_refined.items():
  print k, len(v)


#    if ((market_size in ls_dict_markets[1]) and (market in ls_dict_markets[1][market_size])) and\
#       ((market_size in ls_dict_markets[2]) and (market in ls_dict_markets[2][market_size])):
