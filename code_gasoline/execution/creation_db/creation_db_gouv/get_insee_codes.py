#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
from functions_string import *

path_dir_built_paper = os.path.join(path_data, 'data_gasoline', 'data_built', 'data_paper')
path_dir_built_json = os.path.join(path_dir_built_paper, 'data_json')

master_price_raw = dec_json(os.path.join(path_dir_built_json, 'master_price_diesel_raw.json'))
master_price = dec_json(os.path.join(path_dir_built_json, 'master_price_diesel.json'))
master_info_raw = dec_json(os.path.join(path_dir_built_json, 'master_info_diesel_raw.json'))
master_info = dec_json(os.path.join(path_dir_built_json, 'master_info_diesel.json'))
# master_price already generated
# master_info_raw should be preferred (master_info generated later)

# todo: automated insee code matching based on dpt and commune name
ls_match_res = []
for row_i, row in df_physicians.iterrows():
  city, dpt_code, zip_code = format_str_city_insee(row['city']), row['dpt'], row['zip']
  match_res = match_insee_code(correspondence, city, dpt_code, zip_code)
  ls_match_res.append(match_res)
# if several matched: check if only one code insee, if not: None + error message
ls_rows = []
for match_res in ls_match_res:
  if (len(match_res[0]) == 1) or\
     ([x[2] == match_res[0][0][2] for x in match_res[0]]):
    ls_rows.append(match_res[0][0][2])
  else:
    ls_rows.append(None)
se_insee_codes = pd.Series(ls_rows, index = df_physicians.index)
df_physicians['CODGEO'] = se_insee_codes
