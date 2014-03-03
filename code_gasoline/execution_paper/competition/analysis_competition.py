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
# DF COMPETITION
# ##############

# Rank each competitor list in distance increasing order
# There should be both None and [] in ls_ls_competitors: check they are preserved
ls_ls_competitors = [sorted(ls_competitors, key=lambda x: x[1]) 
                       if ls_competitors else ls_competitors
                         for ls_competitors in ls_ls_competitors]

# TODO: check if chged when not considering stations of same brand
ls_ls_df_competition = []
ls_nb_competitors_ranges = [1, 2, 3, 4, 5, 10]
ls_columns_nb_competitors = ['nb_comp_%s_km' %km_range for km_range in ls_nb_competitors_ranges]
for id_indiv, ls_competitors in zip(master_price['ids'], ls_ls_competitors):
  if ls_competitors is not None:
    # list nb competitors with range of km
    ls_nb_competitors = [len([comp_id for comp_id, distance in ls_competitors
                                if distance <= km_range]) for km_range in ls_nb_competitors_ranges]
    # closest competitor and supermarket
    distance_closest_competitor, distance_closest_supermarket = 10, 10
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

# TODO: investigate by region / department etc.

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
    highway = master_info[indiv_id]['highway'][3]
  ls_ls_info.append([city, zip_code, code_geo, code_geo_ardts, region, highway,
                     brand_1_b, brand_2_b, brand_type_b, brand_1_e, brand_2_e, brand_type_e])

ls_columns = ['city', 'zip_code', 'code_geo', 'code_geo_ardts', 'region', 'highway',
              'brand_1_b', 'brand_2_b', 'brand_type_b', 'brand_1_e', 'brand_2_e', 'brand_type_e']
df_info = pd.DataFrame(ls_ls_info, master_price['ids'], ls_columns)
print '\n', df_info.info()

# TODO: get rid of ',' for output to CSV

# #################
# DESCRIPTIVE STATS
# #################

pd.options.display.float_format = '{:6,.2f}'.format

df_competition = pd.merge(df_info, df_competitors, left_index = True, right_index = True)
print '\n', df_competition.info()

# Exclude highway and Corse
df_competition = df_competition[(df_competition['highway'] != 1) &\
                                (df_competition['region'] != 'Corse')]

# Generic station info stats desc (MOVE TO overview info)

print '\n Chge of type:', len(df_info[df_info['brand_type_b'] != df_info['brand_type_e']])

# Count stations by location/brand
dict_count_df = {}
for col in ['region', 'brand_1_b', 'brand_2_b', 'brand_type_b']:
  dict_count_df[col] = df_competition[col].value_counts()
print '\n', dict_count_df['region']
print '\n', dict_count_df['brand_2_b']
print '\n', dict_count_df['brand_type_b']
# TODO: add comparison with population for region or dpt
# TODO: add comparision between beg and end for brands / groups of brands

# DISTANCE TO CLOSEST COMPETITOR (TODO: robustess with 2nd closest)

# Check 0 distance to closest competitor (to be investigated as pairs)
df_competition[['city', 'zip_code', 'region', 'brand_1_b']][df_competition['dist_cl_comp']==0]

print '\nNo comp within 10 km:', len(df_competition[df_competition['dist_cl_comp'] == 10])
print '\nDistance to closest comp:', df_competition['dist_cl_comp'].describe()
print '\nDistance to closest comp (w/o 10):', df_competition['dist_cl_comp']\
                                                [df_competition['dist_cl_comp'] < 10].describe()

# By region (TODO: add total row)
ls_des_region = []
for region in np.unique(df_competition['region']):
  df_region = df_competition[df_competition['region'] == region]
  df_des_region = df_region['dist_cl_comp'].describe()
  df_des_region['% >10km'] = len(df_region[df_region['dist_cl_comp'] == 10])/\
                               df_des_region.ix['count']
  ls_des_region.append(df_des_region)
df_des_region = pd.DataFrame(ls_des_region, np.unique(df_competition['region']))
df_des_region[['count', '>10km']] = df_des_region[['count', '% >10km']].astype(int)
print df_des_region[['count', '25%', '50%', '75%', '% >10km']].to_string()
# print df_des_region[['count', '25%', '50%', '75%', '% >10km']].to_latex()

# WEAK COMPETITION BY TYPE

df_nb_monop_brand = df_competition['brand_1_b'][df_competition['dist_cl_comp'] == 10]\
                          .value_counts()
df_nb_monop_brand_type = df_competition['brand_type_b'][df_competition['dist_cl_comp'] == 10]\
                          .value_counts()
df_pct_monop_region = df_nb_monop_region / dict_count_df['region']
df_pct_monop_brand_type = df_nb_monop_brand_type / dict_count_df['brand_type_b']

# Correlation between series for nb of competitors
# Res: High from 3 to 10 competitors...
print '\n', df_competition[['nb_comp_%s_km'%i for i in ls_nb_competitors_ranges]].corr()
