#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
import datetime, time
import matplotlib.pyplot as plt

path_dir_raw_plp = os.path.join(path_data,
                                'data_gasoline',
                                'data_raw',
                                'data_prices',
                                '20070311_20090330_plp')

path_dir_built = os.path.join(path_data,
                              u'data_gasoline',
                              u'data_built')

plp_excel = pd.ExcelFile(os.path.join(path_dir_raw_plp,
                                      '2007_2009_plp_nodup.xlsx'))
ls_plp_sheets = plp_excel.sheet_names

#sheet_name = ls_plp_sheets[0]
ls_df_sheet = []
for sheet_name in ls_plp_sheets:
  if re.match('PompeLaPompe(.*?).xlsx', sheet_name):
    df_sheet = plp_excel.parse(sheet_name,
                              header = None,
                              parse_dates = True,
                              na_values = ['--'])
    str_date = re.match('PompeLaPompe(.*?).xlsx', sheet_name).group(1)
    df_sheet['date'] = pd.to_datetime(str_date, format = '%y%m%d')
    ls_df_sheet.append(df_sheet)

df_plp = pd.concat(ls_df_sheet, ignore_index = True)

ls_replace_cols = {0 : 'id_station',
                   1 : 'city',
                   2 : 'name',
                   3 : 'brand',
                   4 : 'diesel',
                   5 : 'diesel_date',
                   6 : 'unleaded95', # make sure, E10 may not have existed?
                   7 : 'unleaded95_date',
                   8 : 'lpg',
                   9 : 'lpg_date'}
df_plp.rename(columns = ls_replace_cols, inplace = True)

## Check no duplicates
#df_dup = df_plp[df_plp.duplicated(['id_station', 'date'], take_last = False) |\
#                df_plp.duplicated(['id_station', 'date'], take_last = True)]
#print len(df_dup)

# Fix observed pbm (station 83700005 from 2008-02-18 on)
# print df_plp[df_plp['city'].isnull()].to_string()
indexes_tofix = df_plp[df_plp['city'].isnull()].index
ls_col_fix_replace = [['city', 'name'],
                      ['name', 'brand'],
                      ['brand', 'diesel'],
                      ['diesel', 'diesel_date'],
                      ['diesel_date', 'unleaded95'],
                      ['unleaded95', 'unleaded95_date'],
                      ['unldeaded95', 'lpg']]
for old_col, new_col in ls_col_fix_replace:
  df_plp.loc[indexes_tofix,
             old_col] = df_plp[new_col]
# pbm... read value as date... get rid of those obs (few anyway)
df_plp.loc[indexes_tofix,
           ['diesel', 'unleaded95', 'lpg']] = np.nan
df_plp.loc[indexes_tofix,
           ['diesel_date', 'unleaded95_date', 'lpg_date']] = pd.NaT

df_plp['diesel'] = df_plp['diesel'].astype(float)

# todo: use more sophisted error detection tools
# maybe a few cases where should multiply by 10 => check
# print df_plp['diesel'][df_plp['diesel'] <= 0.5].to_string()
df_plp.loc[df_plp['diesel'] <= 0.5, 'diesel'] = np.nan
# not so sure below 0.85: might be promotions...
df_plp.loc[df_plp['diesel'] >= 1.9, 'diesel'] = np.nan

print u'\nInspect diesel price distribution on 2007-03-12 (first day):'
print df_plp['diesel'][df_plp['date'] == '2007-03-12'].describe()
df_plp['diesel'][df_plp['date'] == '2007-03-12'].plot(kind = 'hist', bins = 30)
plt.show()

print u'\nInspect diesel price trend over period:'
se_diesel = df_plp[['diesel', 'date']].groupby('date').mean()
se_diesel.plot()
plt.show()

print u'\nInspect diesel price trends by brand over period:'
# todo: exclude highway (requires to add info...)
# todo: harmonize brands
dict_str_harmo = {u'è' : u'e',
                  u'é' : u'e',
                  u'\xc0' : u'a',
                  u'\xcf' : u'i',
                  u"'" : u"",
                  u'"' : u"",
                  u'.' : u''}
def harmonize_str(some_str):
  for old_char, new_char in dict_str_harmo.items():
    some_str = some_str.replace(old_char, new_char)
  return some_str.upper()

df_plp['brand'] = df_plp['brand'].apply(lambda x: harmonize_str(x)\
                                          if not pd.isnull(x) else x)

df_diesel_brands = pd.pivot_table(df_plp,
                                  columns = 'brand',
                                  index = 'date',
                                  values = 'diesel',
                                  aggfunc = 'mean')
# print df_diesel_brands.columns.tolist()
df_diesel_brands['ALL'] = se_diesel

df_diesel_brands[['TOTAL', 'ESSO', 'LECLERC', 'INTERMARCHE', 'ALL']].plot()
plt.show()
