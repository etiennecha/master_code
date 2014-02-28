#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
from functions_string import *

path_dir_built_paper = os.path.join(path_data, 'data_gasoline', 'data_built', 'data_paper')

path_dir_built_json = os.path.join(path_dir_built_paper, 'data_json')
path_diesel_price = os.path.join(path_dir_built_json, 'master_price_diesel.json')
path_info = os.path.join(path_dir_built_json, 'master_info_diesel.json')
path_ls_ls_competitors = os.path.join(path_dir_built_json, 'ls_ls_competitors.json')
path_ls_tuple_competitors = os.path.join(path_dir_built_json, 'ls_tuple_competitors.json')

path_dir_built_csv = os.path.join(path_dir_built_paper, 'data_csv')
path_csv_insee_data = os.path.join(path_dir_built_csv, 'master_insee_output.csv') 

path_dir_source = os.path.join(path_data, 'data_gasoline', 'data_source')
path_dict_brands = os.path.join(path_dir_source, 'data_various', 'dict_brands.json')
path_dir_insee = os.path.join(path_data, 'data_insee')
path_dict_dpts_regions = os.path.join(path_dir_insee, 'dpts_regions', 'dict_dpts_regions.json')

master_price = dec_json(path_diesel_price)
master_info = dec_json(path_info)
ls_ls_competitors = dec_json(path_ls_ls_competitors)
ls_tuple_competitors = dec_json(path_ls_tuple_competitors)
dict_brands = dec_json(path_dict_brands)
dict_dpts_regions = dec_json(path_dict_dpts_regions)

# #####################
# IMPORT INSEE DATA
# #####################

pd_df_insee = pd.read_csv(path_csv_insee_data, encoding = 'utf-8', dtype= str)
# excludes dom tom
pd_df_insee = pd_df_insee[~pd_df_insee[u'Département - Commune CODGEO'].str.contains('^97')]
pd_df_insee['Population municipale 2007 POP_MUN_2007'] = \
  pd_df_insee['Population municipale 2007 POP_MUN_2007'].apply(lambda x: float(x))

# #####################
# MARKET DEFINITIONS
# #####################

pd_df_insee['id_code_geo'] = pd_df_insee[u'Département - Commune CODGEO']
pd_df_insee = pd_df_insee.set_index('id_code_geo')
dict_markets_insee = {}
dict_markets_au = {}
dict_markets_uu = {}
# some stations don't have code_geo (short spells which are not in master_info)
for id_station, info_station in master_price['dict_info'].items():
  if 'code_geo' in info_station:
    dict_markets_insee.setdefault(info_station['code_geo'], []).append(id_station)
    station_uu = pd_df_insee.ix[info_station['code_geo']][u"Code géographique de l'unité urbaine UU2010"]
    dict_markets_uu.setdefault(station_uu, []).append(id_station)
    station_au = pd_df_insee.ix[info_station['code_geo']][u'Code AU2010']
    dict_markets_au.setdefault(station_au, []).append(id_station)

# #####################
# BRAND CHANGES
# #####################

dict_comp_total_access = {}
dict_comp_total_access_short = {}
for indiv_ind, indiv_id in enumerate(master_price['ids']):
  station_info = master_price['dict_info'][indiv_id]
  if station_info['brand']:
    # generalize to all (single) brand changes ?
    if 'TOTAL_ACCESS' in [dict_brands[get_str_no_accent_up(brand)][0] \
                            for (brand, day_ind) in station_info['brand']]:
      if ls_ls_competitors[indiv_ind]:
        for (competitor_id, competitor_distance) in ls_ls_competitors[indiv_ind]:
          dict_comp_total_access.setdefault(competitor_id, []).append((indiv_id, competitor_distance))
for indiv_id, list_stations in dict_comp_total_access.items():
  dict_comp_total_access[indiv_id] = sorted(list_stations, key = lambda x: x[1])
  dict_comp_total_access_short[indiv_id] = dict_comp_total_access[indiv_id][0:2]

# #########
# SERVICES 
# #########

ls_services = [service for indiv_id, indiv_info in master_info.items()\
                 if indiv_info['services'][-1] for service in indiv_info['services'][-1]]
ls_services = list(set(ls_services))
for indiv_id, indiv_info in master_info.items():
  if indiv_info['services'][-1]:
    ls_station_services = [0 for i in ls_services]
    for service in indiv_info['services'][-1]:
      service_ind = ls_services.index(service)
      ls_station_services[service_ind] = 1
  else:
    ls_station_services = [None for i in ls_services]
  master_info[indiv_id]['list_service_dummies'] = ls_station_services


# ######
# BRANDS
# ######

ls_ls_ls_brands = []
for i in range(3):
  ls_ls_brands =  [[[dict_brands[get_str_no_accent_up(brand)][i], period]\
                        for brand, period in master_price['dict_info'][id_indiv]['brand']]\
                          for id_indiv in master_price['ids']]
  ls_ls_brands = [get_expanded_list(ls_brands, len(master_price['dates'])) for ls_brands in ls_ls_brands]
  ls_ls_ls_brands.append(ls_ls_brands)


# build pd_mi_prices (long form)
ls_all_prices = [price for ls_prices in master_price['diesel_price'] for price in ls_prices]
ls_all_ids = [id_indiv for id_indiv in master_price['ids'] for x in range(len(master_price['dates']))]
ls_all_dates = [date for id_indiv in master_price['ids'] for date in master_price['dates']]
ls_ls_all_brands = [[brand for ls_brands in ls_ls_brands for brand in ls_brands]\
                        for ls_ls_brands in ls_ls_ls_brands]
index = pd.MultiIndex.from_tuples(zip(ls_all_ids, ls_all_dates), names= ['id','date'])
columns = ['price', 'brand_1', 'brand_2', 'brand_type']
pd_mi_prices = pd.DataFrame(zip(*[ls_all_prices] + ls_ls_all_brands), index = index, columns = columns)
pd_pd_prices = pd_mi_prices.to_panel()
# build pd_df_info (simple info dataframe)
ls_rows = []
for indiv_ind, indiv_id in enumerate(master_price['ids']):
  city = master_price['dict_info'][indiv_id]['city']
  if city:
    city = city.replace(',',' ')
  zip_code = '%05d' %int(indiv_id[:-3])
  code_geo = master_price['dict_info'][indiv_id].get('code_geo')
  code_geo_ardts = master_price['dict_info'][indiv_id].get('code_geo_ardts')
  highway = None
  if master_info.get(indiv_id):
    highway = master_info[indiv_id]['highway'][3]
  region = dict_dpts_regions[zip_code[:2]]
  row = [indiv_id, city, zip_code, code_geo, code_geo_ardts, highway, region]
  ls_rows.append(row)
header = ['id', 'city', 'zip_code', 'code_geo', 'code_geo_ardts', 'highway', 'region']
pd_df_master_info = pd.DataFrame(zip(*ls_rows), header).T
# merge info and prices
pd_df_master_info = pd_df_master_info.set_index('id')
pd_mi_prices = pd_mi_prices.reset_index()
pd_mi_final = pd_mi_prices.join(pd_df_master_info, on = 'id')
pd_mi_final = pd_mi_final.set_index(['id','date'])

# # TODO: restrict size to begin with (time/location)
# # pd_mi_final.ix['1500007',:] # based on id
# # pd_mi_final[pd_mi_final['code_geo'].str.startswith('01', na=False)] # based on insee
# # http://stackoverflow.com/questions/17242970/multi-index-sorting-in-pandas
# pd_mi_final_alt = pd_mi_final.swaplevel('id', 'date')
# pd_mi_final_alt = pd_mi_final_alt.sort()
# pd_mi_final_extract = pd_mi_final_alt.ix['20110904':'20111004']
# # pd_pd_final_extract = pd_mi_final_extract.to_panel()

# CONVERT MULTI INDEX TO PANEL DATA
pd_pd_final = pd_mi_final.to_panel()

# GET COLUMN OCCURENCES
ar_brand_1 = np.unique(pd_pd_final['brand_1'].values)
se_brand_1_end = pd_pd_final.minor_xs('20130604')['brand_1'].dropna().value_counts()
ls_big_brands_end = list(se_brand_1_end.index)[0:5]

# MEAN PRICE PER GROUP (BRAND, TODO: REGION / DPT etc.)
ls_se_mean_big_brands_end = []
for brand in ls_big_brands_end:
  ls_se_mean_big_brands_end.append(pd_pd_final['price'][pd_pd_final['brand_1'] == brand].mean())
# TODO: inspect ls_se_mean_big_brands_end[1][53:57] # brand: u'INTERMARCHE'

# BRAND PRICES
day, brand = '20111027', 'INTERMARCHE'
for day in pd_pd_final.minor_axis[50:60]:
  pd_df_day = pd_pd_final.minor_xs(day)
  pd_df_day_brand = pd_df_day['price'][pd_df_day['brand_1'] == brand]
  pd_df_day_brand.describe()

# TODO: identify 'INTERMARCHE' which change price between day 52 and day 53
pd_df_brand = pd_pd_final['price'][pd_pd_final['brand_1'] == "INTERMARCHE"]
ls_select_inds = np.where((pd.notnull(pd_df_brand[pd_pd_final.minor_axis[52]])) &\
                   (pd_df_brand[pd_pd_final.minor_axis[52]]!=pd_df_brand[pd_pd_final.minor_axis[53]]))[0]
ls_select_ids = [pd_pd_final.major_axis[ind] for ind in ls_select_inds]
ls_valid_inds = np.where(pd.notnull(pd_df_brand[pd_pd_final.minor_axis[52]]))[0]
ls_valid_ids = [pd_pd_final.major_axis[ind] for ind in ls_valid_inds]
ls_unselected_ids = [indiv_id for indiv_id in ls_valid_ids if indiv_id not in ls_select_ids]
# total valid prices: (pd.notnull(pd_df_brand[pd_pd_final.minor_axis[52]])).sum()
plt.plot(pd_pd_final.major_xs('1000009')['price'])
plt.show()

# check competition
ls_ls_competitors = [sorted(ls_competitors, key=lambda x: x[1])\
                      if ls_competitors else ls_competitors for 
                        ls_competitors in ls_ls_competitors]

# TODO: loop + create functions... (also: might want to check sp95 if similar event?)
# add brands on graph + other info
select_ind = ls_select_inds[0]
plt.plot(master_price['diesel_price'][select_ind])
ls_competitors = ls_ls_competitors[select_ind][0:5]
if ls_competitors:
  for competitor_id, competitor_distance in ls_competitors:
    competitor_ind = master_price['ids'].index(competitor_id)
    plt.plot(master_price['diesel_price'][competitor_ind])
plt.show()


# # Brand Total: missing periods should be set to NAN: strong bias
# # Stations Total in missing periods are those with low prices (visible from margin)
# plt.plot(pd_df_price_total.count(1)/float(max(pd_df_price_total.count(1))))
# plt.plot(pd_df_mean_comp_2)
# # pd_df_mean_comp_2[pdf_df_mean_comp_2<0.04] Total premium is esp. low on 2012-08-30, due to Total strong decrease !
# # pd_df_temp = pd.DataFrame(pd_df_price_total.ix['2012-08-30'], dtype = np.float32)
# # pd_df_temp.sort('2012-08-30').head()
# # print pdf_df_mean_comp.to_string()

# # # GET COUNT STATS DES ON CATEGORICAL VARIABLE

# # Categorical variable stat des (static)
# pd_pd_master.minor_xs('region').ix['2013-06-04'].value_counts()
# # Categorical variable stat des not taking NAN into account (otherwise same in any period)
# pd_df_temp = pd_pd_master.major_xs('2011-09-04').T
# pd_df_temp = pd_df_temp.dropna(how = 'any')
# pd_df_temp['region'].value_counts()

# # # GET STATS DES ON CONTINUOUS VARIABLE

# # # Can get a dataframe by selecting column
# # pd_df_temp = pd_pd_master.minor_xs('brand')[pd_pd_master.minor_xs('department') == '34']
# # pd_df_temp.ix['2013-06-04'].describe()
# # pd_df_temp.ix['2013-06-04'].dropna().value_counts()
# # pd_df_temp.ix['2013-06-04'].describe()
# # pd_df_temp.ix['2013-06-04'].value_counts()
# # pd_df_temp = pd_pd_master.minor_xs('price')[pd_pd_master.minor_xs('department') == '34']

# # # Harder to keep a panel data object
# # # list_ids_to_keep = ['10000001']

# # TOTAL - TOTAL ACCESS : Seems to be real change in prices (COMPARE ELF => TOTAL ACCESS ?)
# list_ids_total_total_access = dict_stats_brand_changes['TOTAL - TOTAL ACCESS']
# pd_pd_total_access = pd_pd_master.filter(list_ids_total_total_access)
# pd_df_mean_comp_total_access = pd.concat([pd_pd_master.minor_xs('price').mean(1),\
                                          # pd_pd_total_access.minor_xs('price').mean(1)],\
                                          # keys = ['All', 'Total Access'] , axis = 1)
# # pd_df_mean_comp_total_access.plot()
  
# # CARREFOUR MARKET - COOP - SYSTEME U
# list_ids_interest = dict_stats_brand_changes['CARREFOUR MARKET - COOP - SYSTEME U']
# pd_pd_interest = pd_pd_master.filter(list_ids_interest)
# # pd_pd_interest.minor_xs('price').astype('float').plot()
# pd_df_mean_comp_interest = pd.concat([pd_pd_master.minor_xs('price').mean(1),\
                                      # pd_pd_interest.minor_xs('price').mean(1)],\
                                      # keys = ['All', 'Carrefour - Systeme U'] , axis = 1)
# pd_series_comp = pd_pd_master.minor_xs('price').mean(1) - pd_pd_interest.minor_xs('price').mean(1)
# pd_series_comp_2 = pd_pd_master.minor_xs('price')[pd_pd_master.minor_xs('brand') == 'CARREFOUR'].mean(1) - \
                    # pd_pd_interest.minor_xs('price').mean(1)
# # Decreasing trend in diff (price increase) + sales in October ?
# # Quite a few appear to be in Dpt 17 => Leave Carrefour at same time: shock on competition?

# # TODO: CHECK SHELL => AVIA & AVIA => SHELL ? SAME LOCATION ?
# # TODO: CHECK TOTAL => ESSO & TOTAL => ELAN
# # TODO: CHECK SHELL => ESSO & ESSO => AVIA
