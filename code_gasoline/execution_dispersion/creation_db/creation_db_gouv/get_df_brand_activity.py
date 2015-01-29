#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
from matching_insee import *
import pprint

path_dir_built_paper = os.path.join(path_data,
                                    'data_gasoline',
                                    'data_built',
                                    'data_paper_dispersion')

path_dir_built_json = os.path.join(path_dir_built_paper, 'data_json')
path_dir_built_csv = os.path.join(path_dir_built_paper, 'data_csv')

path_dir_source = os.path.join(path_data, 'data_gasoline', 'data_source')

# ######################
# LOAD GAS STATION DATA
# ######################

master_price = dec_json(os.path.join(path_dir_built_json,
                                     'master_price_diesel_fixed.json'))
master_info = dec_json(os.path.join(path_dir_built_json,
                                    'master_info_fixed.json'))

dict_brands = dec_json(os.path.join(path_dir_source,
                                    'data_other',
                                    'dict_brands.json'))

# ##################
# BUILD DF ACTIVITY
# ##################

# todo: refactor / replace?
ls_ls_price_durations = get_price_durations(master_price['diesel_price'])
# ls_ls_price_variations = get_price_variations_nan(ls_ls_price_durations)
ls_start_end, ls_none, dict_dilettante =\
   get_overview_reporting_bis(master_price['diesel_price'],
                              master_price['dates'],
                              master_price['missing_dates'])

ls_index, ls_rows_activity = [], []
for i, indiv_id in enumerate(master_price['ids']):
  ls_index.append(indiv_id)
  ls_rows_activity.append(list(ls_start_end[i])+\
                          [len(dict_dilettante.get(i, []))])

# todo: change to dates ?
df_activity = pd.DataFrame(ls_rows_activity,
                           index = ls_index,
                           columns = ['start', 'end', 'dilettante'])

# ###############
# BUILD DF BRANDS
# ###############

# Fix (caution: not robust to a change in beginning of period studied!)
ls_adhoc_brand_fix = [['51100035', [[u'TOTAL ACCESS', 577]]],
                      ['60230003', [[u'TOTAL ACCESS', 523]]],
                      ['1130001',  [[u'ELF', 0]]], # became Total (renovation) then TA... (not here)
                      ['31700002', [[u'ELF', 0], [u'TOTAL ACCESS', 533]]],
                      ['84700001', [[u'ELF', 0], [u'TOTAL ACCESS', 527]]],
                      ['91590008', [[u'TOTAL ACCESS', 298]]], # TA created as Total (renovation) then TA (was Elf before)
                      ['93420006', [[u'TOTAL ACCESS', 521]]],
                      ['78150001', [[u'ELF', 0], [u'TOTAL ACCESS', 19]]], # double change TOTAL ELF TOTAL TA simplified
                      ['86360003', [[u'TOTAL', 0], [u'TOTAL ACCESS', 448]]]] # same with TOTAL

for id_gouv, ls_fixed_station_brands in ls_adhoc_brand_fix:
  master_price['dict_info'][id_gouv]['brand'] = ls_fixed_station_brands

# Update dict brands if needed
for indep in [u'AUCUNE', u'GME', u'S.D.L', u'NEANT', u'X.BEE', u'CCVB',
              u'AUTOMAT24/24', u'AUTOMAT.DKV.UTA', u'BROSSIER',
              u'STATION', u'PETROSUD', u'GALLIEN', u'GARCIN FRERES',
              u'SUPERMARCHE', u'SOS PETRO', u'DISCOUNT', u'AIREC',
              u'QUANTIUM 500T', u'Q8', u'STATION CHLOE', u'AGENT FORD']:
  dict_brands[indep] = [u'INDEPENDANT', u'INDEPENDANT', u'IND']

dict_brands[u'BP EXPRESS'] = [u'BP_EXPRESS', u'BP', u'OIL']
dict_brands[u'COCCIMARKET'] = [u'COCCINELLE', u'COLRUYT', u'SUP'] # INDPT?
dict_brands[u'CARREFOUR EXPRESS'] = [u'CARREFOUR_EXPRESS', u'CARREFOUR', u'SUP']
dict_brands[u'PROXI SUPER'] = [u'AUTRE_GMS', u'AUTRE_GMS', u'SUP'] # COLRUYT?
dict_brands[u'LIDL'] = [u'LIDL', u'LIDL', u'SUP']
dict_brands[u'SPAR'] = [u'SPAR', u'CASINO', u'SUP']
dict_brands[u'U'] = [u'SYSTEMEU', u'SYSTEMEU', u'SUP']
dict_brands[u'U EXPRESS'] = [u'U_EXPRESS', u'SYSTEMEU', u'SUP']
dict_brands[u'ENI FRANCE'] = [u'AGIP', u'AGIP', u'OIL']
dict_brands[u'MARKET'] = [u'CARREFOUR_MARKET', u'CARREFOUR', u'SUP']

enc_json(dict_brands, os.path.join(path_dir_source,
                                   'data_other',
                                   'dict_brands.json'))

# Harmonizes brands (softly though so far)
for indiv_id, indiv_info in master_price['dict_info'].items():
  if indiv_info['brand']:
    master_price['dict_info'][indiv_id]['brand'] = [[get_str_no_accent_up(brand), day_ind]\
                                                       for brand, day_ind in indiv_info['brand']]

# Resets brand starting date consistent with price series
ls_to_be_chged = []
for i, (start, end) in enumerate(ls_start_end):
  if start != master_price['dict_info'][master_price['ids'][i]]['brand'][0][1]:
    ls_to_be_chged.append(i)
    if start:
      master_price['dict_info'][master_price['ids'][i]]['brand'][0][1] = start
      
# Adds brand_std to dict_info in master_price and create corresponding dict_std_brands:
dict_std_brands = {v[0]: v for k, v in dict_brands.items()}
for indiv_id, indiv_info in master_price['dict_info'].items():
  ls_brand_std = [[dict_brands[name][0], day_ind] for name, day_ind in indiv_info['brand']]
  i = 1 
  while i < len(ls_brand_std):
    if ls_brand_std[i][0] == ls_brand_std[i-1][0]:
      del(ls_brand_std[i])
    else:
      i += 1
  master_price['dict_info'][indiv_id]['brand_std'] = ls_brand_std

# check multi brands, reduce?
dict_len_brands = {}
ls_index, ls_rows_brands = [], []
for indiv_id, indiv_info in master_price['dict_info'].items():
  dict_len_brands.setdefault(len(indiv_info['brand_std']), []).append(indiv_id)
  ls_index.append(indiv_id)
  ls_rows_brands.append([x for ls_x in indiv_info['brand_std'] for x in ls_x])

#print dict_len_brands.keys()
ls_ls_columns = [['brand_%s' %i, 'day_%s' %i]\
                   for i in range(np.max(dict_len_brands.keys()))]
ls_columns = [column for ls_columns in ls_ls_columns for column in ls_columns]

df_brands = pd.DataFrame(ls_rows_brands,
                         index = ls_index,
                         columns = ls_columns)

# #######################
# BUILD DF BRAND ACTIVITY
# #######################

df_brand_activity = pd.merge(df_activity, df_brands, left_index = True, right_index = True)

for field in ['start', 'end', 'day_0', 'day_1', 'day_2']:
  df_brand_activity[field] = df_brand_activity[field].apply(\
                               lambda x: master_price['dates'][int(x)]\
                                           if not pd.isnull(x) else x)
  df_brand_activity[field] = pd.to_datetime(df_brand_activity[field],
                                            format = '%Y%m%d',
                                            coerce = True)

#for year in ['2011', '2012', '2013']:
#  print u'Nb starting after %s:' %year,\
#        len(df_brand_activity[df_brand_activity['start'] > year])

# todo: group and brand

# OUTPUT TO CSV
df_brand_activity.to_csv(os.path.join(path_dir_built_csv,
                                      'df_brand_activity.csv'),
                         index_label = 'id_station',
                         float_format= '%.3f',
                         encoding = 'utf-8')

# TODO: check ids not in master_info
