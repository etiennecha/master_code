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

path_dir_source = os.path.join(path_data,
                               'data_gasoline',
                               'data_source')

path_dir_built = os.path.join(path_data,
                              u'data_gasoline',
                              u'data_built')

# ###############
# READ EXCEL DATA
# ###############

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

df_plp['id_station'] = df_plp['id_station'].apply(lambda x: '{:d}'.format(x))

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

# Convert prices to float
df_plp['diesel'] = df_plp['diesel'].astype(float)
df_plp['unleaded95'] = df_plp['unleaded95'].astype(float)
df_plp['lpg'] = df_plp['lpg'].astype(float)

# Fix dates
def fix_date_field(some_date):
  if isinstance(some_date, datetime.datetime):
    pass
  elif isinstance(some_date, unicode):
    try:
      some_date = pd.to_datetime(some_date, format = '%d/%m/%Y')
    except:
      some_date = pd.NaT
  else:
    some_date = pd.NaT
  return some_date

for date_field in ['diesel_date', 'unleaded95_date', 'lpg_date']:
  df_plp[date_field] = df_plp[date_field].apply(lambda x: fix_date_field(x))

# Fix prices
# todo: use more sophisted error detection tools
# maybe a few cases where should multiply by 10 => check
# print df_plp['diesel'][df_plp['diesel'] <= 0.5].to_string()
df_plp.loc[df_plp['diesel'] <= 0.5, 'diesel'] = np.nan
# not so sure below 0.85: might be promotions...
df_plp.loc[df_plp['diesel'] >= 1.9, 'diesel'] = np.nan

# Harmonize brands
# todo: harmonize brands
dict_str_harmo = {u'è' : u'e',
                  u'é' : u'e',
                  u'À' : u'a',
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

dict_brands = dec_json(os.path.join(path_dir_source,
                                    'data_other',
                                    'dict_brands.json'))
df_plp['brand_bu'] = df_plp['brand']

df_plp['brand'] =\
  df_plp['brand_bu'].apply(lambda x: dict_brands.get(x, [None])[0])

df_plp['group'] =\
  df_plp['brand_bu'].apply(lambda x: dict_brands.get(x, [None, None])[1])

# todo: exclude highway (requires to add info...)

## ###########
## OVERVIEW
## ###########
#
#fuel = 'unleaded95'
#
#print u'\nInspect {:s} price distribution on 2007-03-12 (first day):'.format(fuel)
#print df_plp[fuel][df_plp['date'] == '2007-03-12'].describe()
#df_plp[fuel][df_plp['date'] == '2007-03-12'].plot(kind = 'hist', bins = 30)
#plt.show()
#
#print u'\nInspect national avg {:s} price trend over period:'.format(fuel)
#se_fuel = df_plp[[fuel, 'date']].groupby('date').mean()
#se_fuel.plot()
#plt.show()
#
#print u'\nInspect {:s} price trends by brand over period:'.format(fuel)
#df_fuel_brands = pd.pivot_table(df_plp,
#                                columns = 'brand',
#                                index = 'date',
#                                values = fuel,
#                                aggfunc = 'mean')
## print df_diesel_brands.columns.tolist()
#df_fuel_brands['ALL'] = se_fuel
#
#df_fuel_brands[['TOTAL', 'ESSO', 'LECLERC', 'INTERMARCHE', 'ALL']].plot()
#plt.show()
#
## Check brand distributions
## todo: create comparison between TOTAL and ESSO with exogeneously defined bins
#ax = df_plp['diesel'][(df_plp['date'] == '2007-03-12') &\
#                       (df_plp['brand'] == 'TOTAL')]\
#       .plot(kind = 'hist', bins = 30, alpha = 0.3, label = 'TOTAL')
#df_plp[fuel][(df_plp['date'] == '2007-03-12') &\
#                 (df_plp['brand'] == 'ESSO')]\
#  .plot(kind = 'hist', bins = 30, alpha = 0.3, label = 'ESSO', ax = ax)
#plt.show()
## todo: before/after test on all stations, in particular on ESSO (ESSO EXPRESS?)

# ##################
# OUTPUT
# ##################

# PRICES (ONLY DIESEL FOR NOW)

# Create dataframe with daily prices
# todo: improve efficiency
index = pd.date_range(start = df_plp['date'].min(),
                      end   = df_plp['date'].max(), 
                      freq='D')
df_diesel = pd.DataFrame(None, index = index)
for row_ind, row in df_plp.iterrows():
  if not pd.isnull(row['diesel_date']):
    df_diesel.loc[row['diesel_date']:row['date'],
                  row['id_station']] = row['diesel']     
  else:
    df_diesel.loc[row['date'],
                  row['id_station']] = row['diesel']     
df_diesel.to_csv(os.path.join(path_dir_source,
                              'data_plp',
                              'df_plp_diesel.csv'),
                 index = False,
                 encoding = 'utf-8')

# STATION INFO (INCL BRANDS

df_info = df_plp[['id_station', 'name', 'city']]\
            .drop_duplicates('id_station', take_last = True)

# Check if null brands

#print len(df_plp[pd.isnull(df_plp['brand_bu'])])
#print len(df_plp[pd.isnull(df_plp['brand'])])
#df_plp[df_plp['brand'].isnull()]

df_plp.loc[df_plp['brand'].isnull(),
           ['brand', 'group']] = [u'INDEPENDANT', u'INDEPENDANT']
df_plp.loc[df_plp['brand'].isnull(),
           'group'] = u'INDEPENDANT'

# Create dataframe with brand info 
# would be heaver if missing values)
df_plp.sort(['id_station', 'date'], ascending = True, inplace = True)
ls_ls_station_brands = []
for id_station, df_station in df_plp.groupby('id_station'):
  ls_station_brands = [df_station[['brand', 'date']].iloc[0].tolist()]
  for row_i, row in df_station.iterrows():
    if row['brand'] != ls_station_brands[-1][0]:
      ls_station_brands.append(row[['brand', 'date']].tolist())
  ls_ls_station_brands.append([id_station] +\
                              [x for ls_x in ls_station_brands for x in ls_x])
df_brands = pd.DataFrame(ls_ls_station_brands)
ls_cols = ['id_station'] +\
          [x for ls_x in [['brand_{:d}'.format(i),
                           'date_{:d}'.format(i)]\
                             for i in range(len(df_brands.columns) /2)]\
                 for x in ls_x]
dict_brand_cols = {i: field for i, field in enumerate(ls_cols)}
df_brands.rename(columns = dict_brand_cols, inplace = True)

# Fix brands (todo: finish)

#print df_brands[~df_brands['brand_3'].isnull()].to_string()

df_brands.loc[~df_brands['brand_3'].isnull(),
              ['brand_2', 'date_2', 'brand_3', 'date_3']] = [None, None, None, None]
df_brands.drop(['brand_3', 'date_3'], axis = 1, inplace = True)

print df_brands[~df_brands['brand_2'].isnull()].to_string()
# weird... most are probably mistakes

df_info = pd.merge(df_info,
                   df_brands,
                   how = 'left',
                   left_on = 'id_station',
                   right_on = 'id_station')

df_info.to_csv(os.path.join(path_dir_source,
                            'data_plp',
                            'df_plp_info.csv'),
               index = False,
               encoding = 'utf-8')
