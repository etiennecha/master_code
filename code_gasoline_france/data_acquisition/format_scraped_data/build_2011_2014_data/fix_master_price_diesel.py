#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *

path_dir_built_paper = os.path.join(path_data,
                                    'data_gasoline',
                                    'data_built',
                                    'data_scraped_2011_2014')
path_dir_built_json = os.path.join(path_dir_built_paper, 'data_json')

master_price = dec_json(os.path.join(path_dir_built_json,
                                     'master_price_diesel_raw.json'))

master_price['diesel_price'] = get_num_ls_ls(master_price['diesel_price'])
master_price_bu = copy.deepcopy(master_price['diesel_price'])

ls_start_end_bu, ls_nan_bu, dict_dilettante_bu =\
  get_overview_reporting_bis(master_price['diesel_price'],
                             master_price['dates'], 
                             master_price['missing_dates'])

master_price['diesel_price'], dict_corrections, dict_errors =\
  fill_prices_using_dates(master_price['diesel_price'],
                          master_price['diesel_date'],
                          master_price['dates'])

master_price['diesel_price'], dict_corrections_gaps =\
  fill_short_gaps(master_price['diesel_price'], 5)
ls_abnormal_prices = get_abnormal_price_values(master_price['diesel_price'], 1.0, 2.0)
ls_abnormal_price_values = format_ls_abnormal_prices(ls_abnormal_prices,
                                                     master_price['ids'],
                                                     master_price['dates'])
# for indiv_ind, indiv_id, price, ls_day_inds, ls_day_dates in ls_abnormal_price_values:
  # print indiv_ind, ls_day_inds, (indiv_id, price, ls_day_dates)

# Over period '20110904/20120514, following corrections (seems valid => 20121204)
ls_corrections_diesel =  [(u'2400008' , 1.56 , [u'20120216', u'20120219']), # 0.156
                          (u'11000008', 1.46 , [u'20130219']),              #0.146
                          (u'19300004', 1.45 , [u'20110913', u'20110925']), #0.145
                          (u'22290002', 0.85 , [u'20111104', u'20111107']), #no chge..
                          (u'41100002', 1.41 , [u'20130417', u'20130419']), #0.141
                          (u'42800002', 1.5  , [u'20120319']),              #0.001
                          (u'45650001', 1.4  , [u'20121013', u'20121014']), #0.014
                          (u'47000001', 1.5  , [u'20111119', u'20111120']), #0.001
                          (u'49160003', 1.51 , [u'20121121', u'20121122']), #0.151
                          (u'57160005', 1.55 , [u'20120314']),              #0.155
                          (u'57210001', 1.48 , [u'20121023', u'20121028']), #0.148
                          (u'83510003', 1.492, [u'20120724', u'20120729']), #0.001 unsure
                          (u'86170003', 1.378, [u'20111016', u'20111017']), #0.013
                          (u'93440003', 1.49 , [u'20120914', u'20120916']), #0.149
                          (u'93561001', 1.45 , [u'20111129']), #0.145
                          (u'78170006', np.nan, ['20130312', '20130318']), # surge
                          (u'26140005', np.nan, ['20130725', '20130727']), # drop, unsure
                          (u'93230004', np.nan, ['20120609', '20120621']), # surge
                          (u'88300005', np.nan, ['20141127', '20141204']),
                          (u'87430001', np.nan, ['20141204', '20141204']),
                          (u'84550001', np.nan, ['20130725', '20130727']), # drop, unsure
                          (u'75016001', np.nan, ['20141204', '20141204']),
                          (u'74130001', np.nan, ['20130918', '20130919']), # surge
                          (u'72700004', np.nan, ['20141204', '20141204']),
                          (u'68200013', np.nan, ['20120104', '20120107']), # surge
                          (u'66000012', np.nan, ['20130309', '20130317']), # 2 surges
                          (u'65200002', np.nan, ['20130417', '20130418']), # surge
                          (u'44490002', np.nan, ['20141022', '20141029']), # surge
                          (u'41100001', np.nan, ['20141203', '20141204']),
                          (u'28000004', np.nan, ['20141204', '20141204']),
                          (u'22100001', np.nan, ['20141204', '20141204']),
                          (u'20290003', np.nan, ['20120615', '20120619']),
                          (u'6000010' , np.nan, ['20141202', '20141204']),
                          (u'6250001' , np.nan, ['20130616', '20130617']), # surge
                          (u'20260003', np.nan, ['20141202', '20141204']),
                          (u'33480003', np.nan, ['20141129', '20141204']),
                          (u'33133002', np.nan, ['20141204', '20141204']),
                          (u'4600001' , np.nan, ['20130101', '20130330']), # isolated low price
                          (u'30700005', np.nan, ['20120716', '20120901']), # usolated high price
                          (u'99999001', np.nan, ['20130807', '20131128'])] # erase...

ls_corrections_diesel_e = expand_ls_price_corrections(ls_corrections_diesel,
                                                      master_price['dates'])

master_price['diesel_price'] = correct_abnormal_price_values(ls_corrections_diesel_e,
                                                             master_price['ids'],
                                                             master_price['dates'],
                                                             master_price['diesel_price'])
dict_opposit, dict_single, master_price['diesel_price'] =\
  correct_abnormal_price_variations(master_price['diesel_price'], 0.1)

ls_ls_price_durations = get_price_durations(master_price['diesel_price'])
ls_duration_corrections, master_price['diesel_price'] =\
  correct_abnormal_price_durations(master_price['diesel_price'], ls_ls_price_durations, 60)

# Stats des after modifications
ls_ls_price_durations = get_price_durations(master_price['diesel_price'])
ls_ls_price_variations = get_price_variations(ls_ls_price_durations)
ls_start_end, ls_nan, dict_dilettante =\
  get_overview_reporting_bis(master_price['diesel_price'],
                             master_price['dates'],
                             master_price['missing_dates'])

# Get rid of periods with too few observations
master_price['diesel_price'] = get_rid_missing_periods(master_price['diesel_price'], 8000)
 
enc_json(master_price, os.path.join(path_dir_built_json,
                                    'master_price_diesel_fixed.json'))

print u'\nCreation of master_price_diesel_fixed.json successful'
print type(master_price)
print u'Length:', len(master_price)

## Inspect abnormal prices (see if corrected due to abnormal variations)
#for x in ls_abnormal_price_values:
#  print 'Station id_gouv', x[1], x[0]
#  se_prices = pd.Series(master_price['diesel_price'][x[0]])
#  se_prices.plot()
#  plt.show()

## Inspect remaining abnormal price variations
#df_prices = pd.DataFrame(master_price['diesel_price'],
#                         index = master_price['ids'],
#                         columns = pd.to_datetime(master_price['dates'],
#                                                  format = '%Y%m%d')).T
#df_chge = df_prices - df_prices.shift(1)
#df_chge[df_chge.abs() <= 1e-5] = np.nan
## general detection
#se_pbms = df_chge.apply(lambda row: 1 if len(row[row.abs() >= 0.15])> 0 else 0,
#                        axis = 0)
#se_pbms = se_pbms[se_pbms != 0]
#for id_station in se_pbms.index:
#  print ''
#  print id_station
#  print df_chge[id_station][df_chge[id_station].abs() >= 0.15]
## focus beginning and end (lower threshold)
#df_chge.fillna(method = 'backfill', axis = 0, inplace = True)
#df_chge.fillna(method = 'ffill', axis = 0, inplace = True)
#print ''
#print df_chge.ix[-1][df_chge.ix[-1].abs() >= 0.1] # a few to fix
#print df_chge.ix[0][df_chge.ix[0].abs() >= 0.1]  # no pbm
#
## legit variations... one-off if not specified
#ls_checked = ['37170004',
#              '33370009',
#              '94000002',
#              '92210001',
#              '83550003', # doubt not one-off but seems legit
#              '82130001', # doubt
#              '79160003', # doubt
#              '75007003', # rigid
#              '75018009', # rigid
#              '75005001',
#              '42410001', # rigid
#              '34070003', # rigid (?)
#              '11000004',
#              '34800002', # rigid
#              '32000008'] # rigid

## Compare original vs fixed
#df_prices_bu = pd.DataFrame(master_price_bu,
#                            index = master_price['ids'],
#                            columns = pd.to_datetime(master_price['dates'],
#                                                     format = '%Y%m%d')).T
#for station_ind, ls_corrs in dict_opposit.items()[0:10]:
#  print station_ind, ls_corrs
#  day_ind_0, day_ind_1 = ls_corrs[0][0]-20,  ls_corrs[0][1]+20
#  ax = df_prices[df_prices.columns[station_ind]].iloc[day_ind_0:day_ind_1].plot()
#  df_prices_bu[df_prices.columns[station_ind]].iloc[day_ind_0:day_ind_1].plot()
#  plt.show()

## Check changes robust to missing prices (checked also with 0.15)
#df_prices_ff = df_prices.fillna(method = 'ffill', axis = 0)
#df_chge_ff = df_prices_ff - df_prices_ff.shift(1)
#se_pbms_ff = df_chge_ff.apply(lambda row: 1 if len(row[row.abs() >= 0.20])> 0 else 0,
#                              axis = 0)
#se_pbms_ff = se_pbms_ff[se_pbms_ff != 0]
#for id_station in se_pbms_ff.index:
#  if id_station not in ls_checked:
#    print id_station
#    ax = df_prices[id_station].plot()
#    df_prices.mean(1).plot(ax=ax)
#    plt.show()
