#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
import datetime

path_dir_built_paper = os.path.join(path_data, u'data_gasoline', u'data_built', u'data_paper')
path_dir_built_csv = os.path.join(path_dir_built_paper, u'data_csv')
path_dir_built_json = os.path.join(path_dir_built_paper, 'data_json')

path_dir_source = os.path.join(path_data, 'data_gasoline', 'data_source')
path_dir_other = os.path.join(path_dir_source, 'data_other')

ls_tup_duplicates = dec_json(os.path.join(path_dir_other,
                                          'ls_id_reconciliations.json'))

ls_tup_duplicates_update = [('13010002', '13010010'),
                            ('13370001', '13370005'),
                            ('16300003', '16300004'), # CM => ITM (LSA)
                            ('20200007', '20200008'),
                            ('22600001', '22600008'), # CM/HChamp => ITM (LSA)
                            ('26270001', '26270005'), # highway
                            ('29760003', '29760004'),
                            ('35560001', '35560004'),
                            ('40300001', '40300007'), # highway
                            ('42370002', '42370004'),
                            ('42440001', '42440008'), # highway
                            ('48200002', '48200006'),
                            ('51100031', '51100035'),
                            ('5600001' , '5600005' ), # check: unsure
                            ('57370005', '57370006'), # drop ? (unsure)
                            ('57370006', '57370007'), # drop ? (unsure)
                            ('59211001', '59211002'),
                            ('59492001', '59492002'), # CM => ITM (LSA)
                            ('62120002', '62120013'),  # CM => ITM (LSA)
                            ('62128003', '62128006'), # SHOPI => CarrCont (LSA)
                            ('62217004', '62217006'), # ELF => TA
                            ('62720001', '62720002'),
                            ('63190006', '63190009'),
                            ('66300005', '66300013'), # highway
                            ('73390001', '73390008'), # highway
                            ('86700002', '86700004'),
                            ('86800001', '86800005'),
                            ('91800001', '91800008'), # fix brand
                            ('94651001', '94651002'),
                            ('95330007', '95330008')]
ls_tup_duplicates += ls_tup_duplicates_update

# #########################
# LOAD INFO STATIONS
# #########################

df_info = pd.read_csv(os.path.join(path_dir_built_csv,
                                   'df_station_info.csv'),
                      encoding = 'utf-8',
                      dtype = {'id_station' : str,
                               'adr_zip' : str,
                               'adr_dpt' : str,
                               'ci_1' : str,
                               'ci_ardt_1' :str,
                               'ci_2' : str,
                               'ci_ardt_2' : str,
                               'dpt' : str},
                      parse_dates = ['start', 'end', 'day_0', 'day_1', 'day_2'])
df_info.set_index('id_station', inplace = True)

ls_di0 = ['name', 'adr_street', 'adr_city', 'ci_1',
          'lat_gov_1', 'lng_gov_1']
ls_di1 = ls_di0 + ['start', 'end', 'brand_0']

# #########################
# LOAD PRICES
# #########################

df_prices_ht = pd.read_csv(os.path.join(path_dir_built_csv, 'df_prices_ht.csv'),
                        parse_dates = ['date'])
df_prices_ht.set_index('date', inplace = True)

df_prices_ttc = pd.read_csv(os.path.join(path_dir_built_csv, 'df_prices_ttc.csv'),
                        parse_dates = ['date'])
df_prices_ttc.set_index('date', inplace = True)

# ##############################
# DROP THOSE WITH NO PRICE INFO
# ##############################

df_info_bu = df_info.copy()
df_prices_ttc_bu = df_prices_ttc.copy()
df_prices_ht_bu = df_prices_ht.copy()

for id_station in df_info.index[pd.isnull(df_info['start'])]:
	if id_station in df_prices_ttc.columns:
		df_prices_ttc.drop(id_station, 1, inplace = True)
		df_prices_ht.drop(id_station, 1, inplace = True)
df_info = df_info[~pd.isnull(df_info['start'])]

# adhoc fixes
df_info.loc['51100035', 'brand_0'] = 'TOTAL_ACCESS'
df_info.loc['51100035', 'brand_1'] = np.nan
df_info.loc['51100035', 'day_1'] = np.nan
df_info.loc['60230003', 'brand_0'] = 'TOTAL_ACCESS'
df_info.loc['60230003', 'brand_1'] = np.nan
df_info.loc['60230003', 'day_1'] = np.nan

## DETECT DUPLICATES
#first_date, last_date = df_info['start'].min(), df_info['end'].max()
#
#ls_check = []
#for ci_1 in df_info['ci_1'].unique():
#  # could check cross distances within and alert if 0 here
#  df_temp = df_info[(df_info['ci_1'] == ci_1) &
#                    ((df_info['start'] != first_date) | (df_info['end'] != last_date))].copy()
#  if len(df_temp) > 1:
#    df_ee = df_temp[(df_temp['start'] == first_date) & (df_temp['end'] != last_date)]
#    df_ls = df_temp[(df_temp['start'] != first_date) & (df_temp['end'] == last_date)]
#    df_sh = df_temp[(df_temp['start'] != first_date) & (df_temp['end'] != last_date)]
#    if (len(df_temp) != len(df_ee)) and (len(df_temp) != len(df_ls)):
#        ls_check.append(ci_1)
#        print '\n', '-'*30
#        print df_temp[ls_di1].to_string()
#
#print '\nDuplicates about to be fixed:'
#for x, y in ls_tup_duplicates:
#  if x in df_info.index and y in df_info.index:
#    print x,y

# DELETE DUPLICATES (W/O LOSING INFO: EX BRAND / EX ADDRESS ?)
for x, y in ls_tup_duplicates:
  if x in df_info.index and y in df_info.index:
    # just to make sure:
    if df_info.ix[y]['start'] > df_info.ix[x]['start']:
      
      # fix prices
      date_switch = df_info.ix[y]['start']
      df_prices_ttc.loc[:date_switch-datetime.timedelta(days=1), y] =\
         df_prices_ttc.loc[:date_switch-datetime.timedelta(days=1), x]
      df_prices_ht.loc[:date_switch-datetime.timedelta(days=1), y] =\
         df_prices_ht.loc[:date_switch-datetime.timedelta(days=1), x]
      
      # drop prices
      df_prices_ttc.drop(x, axis = 1, inplace = True)
      df_prices_ht.drop(x, axis = 1, inplace = True)
      
      # TODO: fix start date + other fields not to lose info

      # fix brand (assuming weird stuffs may be possible)
      ls_tup_x = [(df_info.ix[x]['brand_%s' %i],
                   df_info.ix[x]['day_%s' %i]) for i in range(3)\
                      if not pd.isnull(df_info.ix[x]['brand_%s' %i])]
      ls_tup_y = [(df_info.ix[y]['brand_%s' %i],
                   df_info.ix[y]['day_%s' %i]) for i in range(3)\
                      if not pd.isnull(df_info.ix[y]['brand_%s' %i])]
      ls_tup_xy = ls_tup_x + ls_tup_y
      # sort on date to be sure
      ls_tup_xy = sorted(ls_tup_xy, key=lambda tup: tup[1])
      # avoid duplicate brand
      ls_tup_xy_final = [ls_tup_xy[0]]
      for tup_brand in ls_tup_xy[1:]:
        if tup_brand[0] != ls_tup_xy_final[-1][0]:
          ls_tup_xy_final.append(tup_brand)
      # add to df (will break if more than 3)
      for i, tup_brand in enumerate(ls_tup_xy_final):
        df_info.loc[y, 'brand_%s' %i] = tup_brand[0]
        df_info.loc[y, 'day_%s' %i] = tup_brand[1]
      
      # drop info
      df_info.drop(x, axis = 0, inplace = True)

# DETECT REMAINING DUPLICATES
first_date, last_date = df_info['start'].min(), df_info['end'].max()

ls_check = []
for ci_1 in df_info['ci_1'].unique():
  # could check cross distances within and alert if 0 here
  df_temp = df_info[(df_info['ci_1'] == ci_1) &
                    ((df_info['start'] != first_date) | (df_info['end'] != last_date))].copy()
  if len(df_temp) > 1:
    df_ee = df_temp[(df_temp['start'] == first_date) & (df_temp['end'] != last_date)]
    df_ls = df_temp[(df_temp['start'] != first_date) & (df_temp['end'] == last_date)]
    df_sh = df_temp[(df_temp['start'] != first_date) & (df_temp['end'] != last_date)]
    if (len(df_temp) != len(df_ee)) and (len(df_temp) != len(df_ls)):
        ls_check.append(ci_1)
        print '\n', '-'*30
        print df_temp[ls_di1].to_string()

# OUTPUT

df_info.to_csv(os.path.join(path_dir_built_csv,
                                    'df_station_info_final.csv'),
                       index_label = 'id_station',
                       float_format= '%.3f',
                       encoding = 'utf-8')

df_prices_ttc.to_csv(os.path.join(path_dir_built_csv, 'df_prices_ttc_final.csv'),
                     index_label = 'date',
                     float_format= '%.3f',
                     encoding = 'utf-8')

df_prices_ht.to_csv(os.path.join(path_dir_built_csv, 'df_prices_ht_final.csv'),
                    index_label = 'date',
                    float_format= '%.3f',
                    encoding = 'utf-8')
