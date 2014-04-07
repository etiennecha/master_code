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

path_dir_insee = os.path.join(path_data, 'data_insee')
path_dict_dpts_regions = os.path.join(path_dir_insee, 'dpts_regions', 'dict_dpts_regions.json')

master_price = dec_json(path_diesel_price)
master_info = dec_json(path_info)
ls_ls_competitors = dec_json(path_ls_ls_competitors)
ls_tuple_competitors = dec_json(path_ls_tuple_competitors)
dict_brands = dec_json(path_dict_brands)
dict_dpts_regions = dec_json(path_dict_dpts_regions)

# #####################
# BRAND CHANGES (MOVE?)
# #####################

dict_std_brands = {v[0]: v for k, v in dict_brands.items()}

# Builds dict with keys: tuple of brand changes combinations, ctent: list of station ids
dict_brand_chges = {}
for indiv_id, indiv_info in master_price['dict_info'].items():
  if len(indiv_info['brand_std']) > 1:
    tup_indiv_brands = tuple([brand[0] for brand in indiv_info['brand_std']])
    dict_brand_chges.setdefault(tup_indiv_brands, []).append(indiv_id)
# Display significant brand changes
print '\nBrand changes concerning at least 4 stations'
for k, v in dict_brand_chges.items():
  if len(v) >= 5: 
    print k, len(v)
# Print intra SUP changes
print '\nBrand changes between supermarkets'
for k, v in dict_brand_chges.items():
  if all(dict_std_brands[x][2] == 'SUP' for x in k):
    print k, len(v)
# Print intra OIL changes
print '\nBrand changes between oil stations'
for k,v in dict_brand_chges.items():
  if all(dict_std_brands[x][2] == 'OIL' for x in k):
    print k, len(v)

# Deal with temp chges ? e.g. (u'KAI', u'INDEPENDANT SANS ENSEIGNE', u'KAI', u'KAI')
# Describe: Rebranding, chges with no impact on price, chges with impact on price, other

# ###############
# DF STATION INFO
# ###############

ls_ls_info = []
for indiv_ind, indiv_id in enumerate(master_price['ids']):
  # from master_price
  indiv_dict_info = master_price['dict_info'][indiv_id]
  city = indiv_dict_info['city']
  zip_code = '%05d' %int(indiv_id[:-3]) # TODO: improve if must be used alone
  region = dict_dpts_regions[zip_code[:2]]
  code_geo = indiv_dict_info.get('code_geo')
  code_geo_ardts = indiv_dict_info.get('code_geo_ardts')
  brand_1_b = indiv_dict_info['brand_std'][0][0]
  brand_2_b = dict_std_brands[indiv_dict_info['brand_std'][0][0]][1]
  brand_type_b = dict_std_brands[indiv_dict_info['brand_std'][0][0]][2]
  brand_1_e = indiv_dict_info['brand_std'][-1][0]
  brand_2_e = dict_std_brands[indiv_dict_info['brand_std'][-1][0]][1]
  brand_type_e = dict_std_brands[indiv_dict_info['brand_std'][-1][0]][2]
  # from master_info
  highway = None
  if master_info.get(indiv_id):
    highway = master_info[indiv_id]['highway'][-1]
  ls_ls_info.append([city, zip_code, code_geo, code_geo_ardts, region, highway,
                     brand_1_b, brand_2_b, brand_type_b, brand_1_e, brand_2_e, brand_type_e])

ls_columns = ['city', 'zip_code', 'code_geo', 'code_geo_ardts', 'region', 'highway',
              'brand_1_b', 'brand_2_b', 'brand_type_b', 'brand_1_e', 'brand_2_e', 'brand_type_e']
df_info = pd.DataFrame(ls_ls_info, master_price['ids'], ls_columns)
print '\n', df_info.info()

# ###############
# DF COMPETITION
# ##############

# Rank each competitor list in distance increasing order
# TODO: should distinguish None and [] in ls_ls_competitors
ls_ls_competitors = [sorted(ls_competitors, key=lambda x: x[1]) 
                       if ls_competitors else ls_competitors
                         for ls_competitors in ls_ls_competitors]

# TEMP: Solve pbm: no diff between no gps and no comp, and if comp > 10 not in ls_ls_comp
print '\nDeal with stations with no comp within 10km'
ar_cross_distances = np.load(os.path.join(path_dir_built_json, 'ar_cross_distances.npy'))
dict_ls_ids_gps = dec_json(os.path.join(path_dir_built_json, 'dict_ls_ids_gps.json'))
ls_comp_over_10 =  []
ls_no_gps = []
for i, (gps, ls_competitors) in enumerate(zip(dict_ls_ids_gps['gps'], ls_ls_competitors)):
  if gps:
    if ls_competitors == []:
      comp_id = master_price['ids'][np.nanargmin(ar_cross_distances[i])]
      distance = np.nanmin(ar_cross_distances[i])
      if distance < 50:
        ls_ls_competitors[i] = [[comp_id, distance]]
        ls_comp_over_10.append(i) 
      else:
        print master_price['ids'][i], ': gps info a.s. wrong: inspect!'
        ls_no_gps.append(i)
  else:
    ls_no_gps.append(i)
print len(ls_no_gps), 'stations have currently no gps'
print len(ls_comp_over_10), 'stations have first comp over 10km (before restriction)'

# DF COMPETITION
ls_ls_df_competition = []
ls_nb_competitors_ranges = [1, 2, 3, 4, 5, 10]
ls_columns_nb_competitors = ['nb_comp_%s_km' %km_range for km_range in ls_nb_competitors_ranges]
for id_indiv, ls_competitors in zip(master_price['ids'], ls_ls_competitors):
  if ls_competitors:
    # list nb competitors with range of km
    ls_nb_competitors = [len([comp_id for comp_id, distance in ls_competitors
                                if distance <= km_range]) for\
                                  km_range in ls_nb_competitors_ranges]
    # closest competitor and supermarket
    if ls_competitors:
      distance_closest_competitor = ls_competitors[0][1]
      for comp_id, distance in ls_competitors:
        if dict_std_brands[master_price['dict_info'][comp_id]['brand_std'][-1][0]][2] == 'SUP':
          distance_closest_supermarket = distance
  else:
    ls_nb_competitors = [None for km_range in ls_nb_competitors_ranges]
    distance_closest_competitor, distance_closest_supermarket = None, None
  ls_ls_df_competition.append(ls_nb_competitors +\
                               [distance_closest_competitor, distance_closest_supermarket])

ls_columns = ls_columns_nb_competitors + ['dist_cl_comp', 'dist_cl_sup']
df_competitors = pd.DataFrame(ls_ls_df_competition, master_price['ids'], ls_columns)
print '\n', df_competitors.info()
# The 2 stations with no competitor with 20km have proper gps (checked)

# #################
# FINAL MERGE
# #################

df_competition = pd.merge(df_info, df_competitors, left_index = True, right_index = True)
print '\n', df_competition.info()
pd.options.display.float_format = '{:6,.2f}'.format

se_gps = pd.Series(dict_ls_ids_gps['gps'], index = dict_ls_ids_gps['ids'])
df_competition['gps'] = se_gps # check properties of such operations...
df_competition['gps'] = df_competition['gps'].\
                          apply(lambda ls_x: ' '.join([str(x) for x in ls_x]) if ls_x else None)
df_competition['city'] = df_competition['city'].apply(lambda x: x.replace(',', ' '))
#df_competition['highway'] = df_competition['highway'].\
#                              apply(lambda x: int(x) if not pd.isnull(x) else x)

# OUTPUT FOR DISPLAY
path_dir_built_csv = os.path.join(path_dir_built_paper, 'data_csv')
df_competition.to_csv(os.path.join(path_dir_built_csv, 'df_info_locations.csv'),
                      float_format='%.4f',
                      encoding='utf-8')

# priori: not possible to realize nice screenshots... => draw maps (try in webpage..)
