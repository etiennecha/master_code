#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path_sub
from add_to_path_sub import path_data
from generic_master_price import *
from generic_master_info import *
from generic_competition import *
from functions_string import *
from BeautifulSoup import BeautifulSoup
import copy
import collections
import pandas as pd

path_dir_built_paper = os.path.join(path_data, 'data_gasoline', 'data_built', 'data_paper')

path_dir_built_json = os.path.join(path_dir_built_paper, 'data_json')
path_diesel_price = os.path.join(path_dir_built_json, 'master_price_diesel.json')
path_info = os.path.join(path_dir_built_json, 'master_info_diesel.json')
path_info_output = os.path.join(path_dir_built_json, 'master_info_diesel_for_output.json')

path_dir_source = os.path.join(path_data, 'data_gasoline', 'data_source')
path_dict_brands = os.path.join(path_dir_source, 'data_other', 'dict_brands.json')
path_csv_insee_data = os.path.join(path_dir_source, 'data_other', 'data_insee_extract.csv')

path_dir_zagaz = os.path.join(path_dir_source, 'data_stations', 'data_zagaz')

path_dir_insee = os.path.join(path_data, 'data_insee')
path_dir_match_insee_codes = os.path.join(path_dir_insee, 'match_insee_codes')
path_dict_dpts_regions = os.path.join(path_dir_insee, 'dpts_regions', 'dict_dpts_regions.json')

master_price = dec_json(path_diesel_price)
master_info = dec_json(path_info_output)
dict_brands = dec_json(path_dict_brands)
dict_dpts_regions = dec_json(path_dict_dpts_regions)

dict_zagaz_stations_2012 = dec_json(os.path.join(path_dir_zagaz, '2012_dict_zagaz_info_gps.json'))
dict_zagaz_station_ids = dec_json(os.path.join(path_dir_zagaz,\
                                               '20140124_dict_zagaz_station_ids.json'))
dict_zagaz_prices = dec_json(os.path.join(path_dir_zagaz, '20140127_dict_zagaz_ext_prices.json'))
#dict_zagaz_users = dec_json(os.path.join(path_dir_zagaz, '20140124_dict_zagaz_users.json'))
dict_zagaz_users = dec_json(os.path.join(path_dir_zagaz, '20140408_dict_zagaz_user_info.json'))

# Content of station description within dict_zagaz_stations:
# [id, brand, name, comment, street, zip_code, city, gps_tup, other?]

# Build dicts: brands, gps quality and zip
#dict_zagaz_brands, dict_zagaz_gps_quality, dict_zagaz_zip = {}, {}, {}
#for zagaz_id, ls_zagaz_info in dict_zagaz_stations.items():
#  dict_zagaz_brands.setdefault(ls_zagaz_info[1], []).append(zagaz_id)
#  dict_zagaz_gps_quality.setdefault(ls_zagaz_info[7][2], []).append(zagaz_id)
#  dict_zagaz_zip.setdefault(ls_zagaz_info[5], []).append((zagaz_id, ls_zagaz_info[4]))

## Check matching between (old) zagaz gps file and (recent) info/price files
ls_missing_gps_zagaz = [indiv_id for indiv_id, indiv_info in dict_zagaz_station_ids.items()\
                          if indiv_id not in dict_zagaz_stations_2012]
print len(ls_missing_gps_zagaz), 'gps coordinates missing vs. 2012 files'
# TODO: pbm: need to have all insee codes if those are used for matching

dict_dict_contribs = {}
ls_user_nb_contribs = []
ls_user_station_contribs = []
for user_id, user_info in dict_zagaz_users.items():
  ls_user_nb_contribs.append(len(user_info[1]))
  dict_user_contrib = {}
  for row in user_info[1]:
    dict_user_contrib.setdefault(row[0], []).append(row[1])
  dict_dict_contribs[user_id] = dict_user_contrib
  ls_user_station_contribs.append(len(dict_user_contrib))

# Nb of contributions / stations contributed by user
se_user_nb_contribs = pd.Series(ls_user_nb_contribs)
print 'users w/ 3+ contribs:', len(se_user_nb_contribs[se_user_nb_contribs > 3]) 
print 'users w/ 4+ contribs:', len(se_user_nb_contribs[se_user_nb_contribs > 4]) 
print 'users w/ 5+ contribs:', len(se_user_nb_contribs[se_user_nb_contribs > 5]) 

se_user_station_contribs = pd.Series(ls_user_station_contribs)
print 'users w/ 3+ stations:', len(se_user_station_contribs[se_user_station_contribs > 3]) 
print 'users w/ 4+ stations:', len(se_user_station_contribs[se_user_station_contribs > 4]) 
print 'users w/ 5+ stations:', len(se_user_station_contribs[se_user_station_contribs > 5]) 

ls_ls_user_contrib = []
for user_id, dict_user_contrib in dict_dict_contribs.items():
  ls_user_contrib = [(k,len(v)) for k,v in dict_user_contrib.items()]
  ls_user_contrib = sorted(ls_user_contrib, key = lambda tup: tup[1], reverse = True)
  ls_ls_user_contrib.append(ls_user_contrib)

# GRAPHS: check:
# http://nbviewer.ipython.org/github/cs109/content/blob/master/lec_03_statistical_graphs.ipynb

# todo: both on same graphs with two colors...

## Registration dates
#ls_registration_dates = [v[0][3][1] for k,v in dict_zagaz_users.items() if v and v[0]]
#ls_registration_years = [date[-4:] for date in ls_registration_dates]
#
#dict_registration_years = dict(collections.Counter(ls_registration_years))
#ls_years = [int(x) for x in sorted(dict_registration_years.keys())]
#ls_heights = [dict_registration_years['%s' %k] for k in ls_years]
#plt.bar([year - 0.4 for year in ls_years], ls_heights)
#plt.xlim(2005.5, 2014.5)
#plt.xticks(ls_years, ls_years)
#for x, y in zip(ls_years, ls_heights):
#    plt.annotate("%i" % y, (x, y + 200), ha='center')
#plt.show()
#
## Last visit
#ls_activity_dates = [v[0][4][1] for k,v in dict_zagaz_users.items() if v and v[0]]
#ls_activity_years = [date[6:10] for date in ls_activity_dates]
#
#dict_activity_years = dict(collections.Counter(ls_activity_years))
#ls_years = [int(x) for x in sorted(dict_activity_years.keys())]
#ls_heights = [dict_activity_years['%s' %k] for k in ls_years]
#plt.bar([year - 0.4 for year in ls_years], ls_heights)
#plt.xlim(2005.5, 2014.5)
#plt.xticks(ls_years, ls_years)
#for x, y in zip(ls_years, ls_heights):
#    plt.annotate("%i" % y, (x, y + 200), ha='center')
#plt.show()

# Dict station relations

# 1/ Without user weight
dict_user_relations = {}
for user_id, dict_user_contribs in dict_dict_contribs.items():
  ls_zagaz_ids = list(set(dict_user_contribs.keys()))
  for i, zagaz_id in enumerate(ls_zagaz_ids):
    for zagaz_id_2 in ls_zagaz_ids[i+1:]:
      dict_user_relations.setdefault(zagaz_id, []).append(zagaz_id_2)
      dict_user_relations.setdefault(zagaz_id_2, []).append(zagaz_id)

import operator
dict_dict_stations_relations = {}
dict_tup_stations_relations = {}
dict_relations_stats = {}
print 'Length dict user relations', len(dict_user_relations)
for zagaz_id, ls_zagaz_ids in dict_user_relations.items():
  dict_count_relations = dict(Counter(ls_zagaz_ids))
  dict_dict_stations_relations[zagaz_id] = dict_count_relations
  dict_tup_stations_relations[zagaz_id] = sorted([(k,v) for k,v in dict_count_relations.items()],
                                                 key = lambda x: x[1],
                                                 reverse = True)
  # maybe several.. keep only one arbitrarily here
  val_max = max(dict_count_relations.iteritems(), key=operator.itemgetter(1))[1]
  for id_max in [k for k, v in dict_count_relations.items() if v == val_max]:
    dict_relations_stats.setdefault(val_max, []).append((zagaz_id, id_max))

for k, v in dict_relations_stats.items():
	print k, len(v)

  # todo: map of zagaz stations.. would be cool to make display of markets easy
  # markets around stations or general?
  # view javascript? 
