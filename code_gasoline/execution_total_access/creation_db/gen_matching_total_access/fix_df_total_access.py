#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *

path_dir_built_paper = os.path.join(path_data,
                                    u'data_gasoline',
                                    u'data_built',
                                    u'data_paper_total_access')

path_dir_built_csv = os.path.join(path_dir_built_paper,
                                  u'data_csv')

path_dir_built_json = os.path.join(path_dir_built_paper,
                                   'data_json')

path_dir_built_graphs = os.path.join(path_dir_built_paper,
                                     'data_graphs')

path_dir_insee_extracts = os.path.join(path_data,
                                       'data_insee',
                                       'data_extracts')

# #########################
# LOAD INFO STATIONS
# #########################

df_info = pd.read_csv(os.path.join(path_dir_built_csv,
                                   'df_station_info_final.csv'),
                      encoding = 'utf-8',
                      dtype = {'id_station' : str,
                               'adr_zip' : str,
                               'adr_dpt' : str,
                               'ci_1' : str,
                               'ci_ardt_1' :str,
                               'ci_2' : str,
                               'ci_ardt_2' : str,
                               'dpt' : str},
                      parse_dates = [u'day_%s' %i for i in range(4)]) # fix
df_info.set_index('id_station', inplace = True)

# Exclude highway
df_info = df_info[df_info['highway'] != 1]

# ###########################
# LOAD INFO TA
# ###########################

df_info_ta = pd.read_csv(os.path.join(path_dir_built_csv,
                                      'df_info_ta.csv'),
                         encoding = 'utf-8',
                         dtype = {'id_station' : str,
                                  'adr_zip' : str,
                                  'adr_dpt' : str,
                                  'ci_1' : str,
                                  'ci_ardt_1' :str,
                                  'ci_2' : str,
                                  'ci_ardt_2' : str,
                                  'dpt' : str},
                         parse_dates = [u'day_%s' %i for i in range(4)] +\
                                       ['pp_chge_date', 'ta_chge_date'])
df_info_ta.set_index('id_station', inplace = True)

# ##############
# LOAD DF PRICES
# ##############

df_prices = pd.read_csv(os.path.join(path_dir_built_csv,
                                     'df_prices_ht_final.csv'),
                        parse_dates = ['date'])
df_prices.set_index('date', inplace = True)
ls_keep_ids = [id_station for id_station in df_prices.columns if\
                id_station in df_info.index]
df_prices = df_prices[ls_keep_ids]
se_mean_prices = df_prices.mean(1)

# #######################
# STATS DES TA POPULATION
# #######################

# ONLY TOTAL ACCESS OBSERVED 
# volume too small before, station temporarily closed... or pbm
print u'\nStations starting with brand TA:'
print len(df_info_ta[df_info_ta['brand_0'] == 'TOTAL_ACCESS'])
print df_info_ta[df_info_ta['brand_0'] == 'TOTAL_ACCESS']\
        [['name', 'adr_street', 'adr_city']].to_string()

## Check price series (could as well display activity periods)
#df_prices[['13130006', '2200002', '27600005', '44600008', '56690003']].plot()
#plt.show()
#df_prices[['60330003', '66000016', '86360004', '88300007', '93500006']].plot()
#plt.show()
## All except 86360003 which displays real price cut later => check it
## Seems there is interruption for 93500006: cut it
## Seems there is no(t much) data for 88300007: drop it?

# TOTAL ACCESS AFTER OTHER BRAND(S)

print u'\nStations starting with a brand before TA:'
print len(df_info_ta[df_info_ta['brand_1'] == 'TOTAL_ACCESS'])

print u'\nStations starting with two brands before TA:'
print len(df_info_ta[df_info_ta['brand_2'] == 'TOTAL_ACCESS'])

df_info_ta.loc[df_info_ta['brand_0'] == 'TOTAL_ACCESS', 'TA_day'] = df_info_ta['day_0']
df_info_ta.loc[df_info_ta['brand_1'] == 'TOTAL_ACCESS', 'TA_day'] = df_info_ta['day_1']
df_info_ta.sort('TA_day', ascending = True, inplace = True)

print u'\nInspect first TAs with change'
print df_info_ta[['name', 'adr_street', 'adr_city',
                  'brand_0', 'day_1', 'brand_1', 'TA_day']][0:10].to_string()

# TOTAL ACCESS WITH CHANGE

print '\nStation with brand change after TA'
print len(df_info_ta[(df_info_ta['brand_1'] == 'TOTAL_ACCESS') &\
                     (~pd.isnull(df_info_ta['brand_2']))])

print df_info_ta[(df_info_ta['brand_1'] == 'TOTAL_ACCESS') &\
                 (~pd.isnull(df_info_ta['brand_2']))]\
                [['name', 'adr_street', 'adr_city',
                 'brand_0', 'day_1', 'brand_1', 'day_2', 'brand_2', 'TA_day']].to_string()
# todo: check for real double rebranding

# TABLE OF PREVIOUS BRAND WHEN KNOWN
print df_info_ta['brand_0'][df_info_ta['brand_1'] == 'TOTAL_ACCESS'].value_counts()
print df_info_ta['brand_0'][(df_info_ta['brand_1'] == 'TOTAL_ACCESS') &\
                            (df_info_ta['pp_chge'].abs() > 0.02)].value_counts()

print '\nStation with pp change st. above 0.02:'
print df_info_ta['brand_0'][(df_info_ta['brand_1'] == 'TOTAL_ACCESS') &\
                            (df_info_ta['pp_chge'] > 0.02)].value_counts()

print '\nStation with pp change st. above 0.04:'
print df_info_ta['brand_0'][(df_info_ta['brand_1'] == 'TOTAL_ACCESS') &\
                            (df_info_ta['pp_chge'] > 0.04)].value_counts()

## Check ELF: error due to period during with station closed => use margin or suppr prices
#print df_info_ta.index[(df_info_ta['brand_0'] == 'ELF') &\
#                       (df_info_ta['pp_chge'] > 0.04)]
#
## Check ESSO: real change of price policy
#print df_info_ta.index[(df_info_ta['brand_0'] == 'ESSO') &\
#                       (df_info_ta['pp_chge'] > 0.04)]
#
## Check other TOTAL stations
#print df_info_ta.index[(df_info_ta['brand_0'] == 'TOTAL') &\
#                       (df_info_ta['pp_chge'] > 0.04)][0:10]
#
## Check unexpected inverse changes
#len(df_info_ta['brand_0'][(df_info_ta['brand_1'] == 'TOTAL_ACCESS') &\
#                          (df_info_ta['pp_chge'] < -0.01)])

df_pp_chge = df_info_ta[(df_info_ta['brand_1'] == 'TOTAL_ACCESS') &\
                        (df_info_ta['pp_chge'] > 0.02)].copy()

# GRAPHS OF STATIONS WITH PP CHGE

#for row_ind, row in df_pp_chge.iterrows():
#  id_station = row_ind
#  pp_chge = row['pp_chge']
#  pp_chge_date = row['pp_chge_date']
#  gov_chge_date = row['TA_day']
#  ta_chge_date = row['ta_chge_date']
#  plt.rcParams['figure.figsize'] = 16, 6
#  ax = df_prices[id_station].plot()
#  se_mean_prices.plot(ax=ax)
#  handles, labels = ax.get_legend_handles_labels()
#  ax.legend(handles, [id_station, u'mean price'], loc = 1)
#  ax.axvline(x = pp_chge_date, color = 'b', ls = 'dashed')
#  ax.axvline(x = ta_chge_date, color = 'r', ls = 'dashed')
#  ax.axvline(x = gov_chge_date, color = 'b', ls = 'dotted')
#  #plt.ylim(plt.ylim()[0]-0.5, plt.ylim()[1])
#  #print ax.get_position()
#  #ax.set_position((0.125, 0.2, 0.8, 0.7))
#  
#  footnote_text = '\n'.join([row['name'], row['adr_street'], row['adr_city'], row['ci_ardt_1']])
#  plt.figtext(0.1, -0.1, footnote_text) 
#  # plt.text(.02, .02, footnote_text)
#  # plt.tight_layout()
#  # plt.show()
#  plt.savefig(os.path.join(path_dir_built_graphs,
#                           'total_access_pp_chge_02',
#                           '%s_%s.png' %(id_station, pp_chge)), dpi = 200, bbox_inches='tight')
#  plt.close()

# STATION CLOSED INTERVAL

id_station = df_pp_chge.index[0]
pp_chge_date = df_pp_chge['pp_chge_date'].iloc[0]
# could check if price same as day before or day after (not very important)
df_prices[id_station][pp_chge_date] ==\
   df_prices[id_station][pp_chge_date - pd.Timedelta(days=1)]

def get_price_length(se_prices, date_ref):
  # index must be dates and include date_ref
  price = se_prices[date_ref]
  nb_days_after = 0
  while (date_ref + pd.Timedelta(days = nb_days_after + 1) <= se_prices.index[-1]) and\
        (price == se_prices[date_ref + pd.Timedelta(days = nb_days_after + 1)]):
    nb_days_after += 1
  nb_days_before = 0
  while (date_ref - pd.Timedelta(days = nb_days_after + 1) >= se_prices.index[0]) and\
        (price == se_prices[date_ref - pd.Timedelta(days = nb_days_before + 1)]):
    nb_days_before += 1
  # count nan days after end
  day_after_end = date_ref + pd.Timedelta(days = nb_days_after + 1)
  nb_nan_end = 0
  while (date_ref + pd.Timedelta(days=nb_days_after+nb_nan_end+1) <= se_prices.index[-1]) and\
        (pd.isnull(se_prices[date_ref + pd.Timedelta(days=nb_days_after+nb_nan_end+1)])):
    nb_nan_end += 1
  # count nan days before beginning
  day_before_beg = date_ref - pd.Timedelta(days = nb_days_before + 1)
  nb_nan_beg = 0
  while (date_ref - pd.Timedelta(days = nb_days_after+nb_nan_beg+1) >= se_prices.index[0]) and\
        (pd.isnull(se_prices[date_ref - pd.Timedelta(days=nb_days_before+nb_nan_beg+1)])):
    nb_nan_beg += 1
  return nb_days_before, nb_days_after, nb_nan_beg, nb_nan_end

# Test
se_prices = df_prices[id_station]
date_ref = pp_chge_date - pd.Timedelta(days=1)
price = se_prices[date_ref]
nb_days_before, nb_days_after, nan_beg, nan_end =\
    get_price_length(df_prices[id_station], pp_chge_date - pd.Timedelta(days=1))
print u'\nTest of interval detection:'
print nb_days_before, nb_days_after, nan_beg, nan_end
print df_prices[id_station][date_ref - pd.Timedelta(days = nb_days_before + 1):\
                            date_ref + pd.Timedelta(days = nb_days_after + 1)]

# Loop
ls_interval_rows = []
for id_station, row_station in df_pp_chge.iterrows():
  pp_chge_date = row_station['pp_chge_date']
  # assumes last price is price the day before detection... (check it?)
  date_ref = pp_chge_date - pd.Timedelta(days=1)
  # may not be true...
  nb_days_before, nb_days_after, nb_nan_beg, nb_nan_end =\
      get_price_length(df_prices[id_station], date_ref)
  ls_interval_rows.append([date_ref - pd.Timedelta(days = nb_days_before + nb_nan_beg),
                           date_ref + pd.Timedelta(days = nb_days_after + nb_nan_end),
                           nb_days_before + nb_days_after + 1,
                           nb_days_before + nb_days_after + nb_nan_beg + nb_nan_end + 1,
                           nb_nan_beg,
                           nb_nan_end])

df_interval = pd.DataFrame(ls_interval_rows,
                           index = df_pp_chge.index,
                           columns = ['date_beg', 'date_end',
                                      'length', 'length_w_nan',
                                      'nb_nan_beg', 'nb_nan_end'])

print '\nIntervals with no nan at end and beginning:'
len(df_interval[(df_interval['nb_nan_beg'] == 0) &\
                (df_interval['nb_nan_end'] == 0)])

print df_interval[(df_interval['nb_nan_beg'] == 0) &\
                  (df_interval['nb_nan_end'] == 0)]['length'].describe()

print df_interval[(df_interval['nb_nan_beg'] == 0) &\
                  (df_interval['nb_nan_end'] == 0) &\
                  (df_interval['length'] <= 10)].to_string()

print '\nIntervals incl. nan:'
print df_interval['length_w_nan'].describe()

df_pp_chge = pd.merge(df_pp_chge, df_interval, left_index = True, right_index = True)

#for row_ind, row in df_pp_chge.iterrows():
#  id_station = row_ind
#  pp_chge = row['pp_chge']
#  pp_chge_date = row['pp_chge_date']
#  gov_chge_date = row['TA_day']
#  ta_chge_date = row['ta_chge_date']
#  date_beg = row['date_beg']
#  date_end = row['date_end']
#  plt.rcParams['figure.figsize'] = 16, 6
#  ax = df_prices[id_station].plot()
#  se_mean_prices.plot(ax=ax)
#  handles, labels = ax.get_legend_handles_labels()
#  ax.legend(handles, [id_station, u'mean price'], loc = 1)
#  ax.axvline(x = ta_chge_date, color = 'r', ls = '-', alpha = 0.8)
#  ax.axvline(x = date_beg, color = 'b', ls = '--')
#  ax.axvline(x = date_end, color = 'b', ls = '--')
#  ax.axvline(x = gov_chge_date, color = 'b', ls = ':')
#  footnote_text = '\n'.join([row['name'], row['adr_street'], row['adr_city'], row['ci_ardt_1']])
#  plt.figtext(0.1, -0.1, footnote_text) 
#  if pd.isnull(ta_chge_date):
#    file_name = '_'.join([row['brand_0'],
#                           id_station,
#                           u'{:.3f}'.format(pp_chge)]) + '_notadate.png'
#  else:
#    file_name = '_'.join([row['brand_0'],
#                           id_station,
#                           u'{:.3f}'.format(pp_chge)]) + '.png'
#  plt.savefig(os.path.join(path_dir_built_graphs,
#                           'total_access_pp_chge_interval',
#                           file_name),
#              dpi = 200,
#              bbox_inches='tight')
#  plt.close()

# todo: get last date when change... check with graph that it's ok
# todo: fix manually if needed (+ get sample diff pp_chge_date vs. rebranding)
# todo: analyse change in margin of competitors + dispersion (price war?) etc.

# TA later than pp chge (check)
# 14200004, 14400008, 33110002, 38500004 (constr?)
# 40100003, 63000006, 72400002, 91400004

# 1160001 date ref is on nan... and price is interupted by a nan period
# 13700008 price also interupted by nan period
# 54300003 interupted by nan hence interval largely underestimated
# 69008006 interupted by nan
# 95370004 interupted by nan: missing a few days after?
# 51430003 wrong detection
# 84110001 check what can be done

# check new version 919400004 if superposed?

ls_fix_date_ref = [['6800011', +10], # enough?
                   ['51430003', +30], # check
                   ['56100006', -20], # check... very unsure
                   ['62450002', -20], # check... very unsure
                   ['88140001', -10],
                   ['71260005', +130]] # check, pp change detected way too early

# TODO: fix according to all this info

# Check gap between date given by total and date detected (prefered?)
df_pp_chge['gap'] = df_pp_chge['ta_chge_date'] - df_pp_chge['date_end']

## GRAPHS OF STATIONS WITHOUT PP CHGE (chge definition?)

df_no_pp_chge = df_info_ta[~((df_info_ta['brand_1'] == 'TOTAL_ACCESS') &\
                             (df_info_ta['pp_chge'] > 0.02))].copy()

#for row_ind, row in df_no_pp_chge.iterrows():
#  id_station = row_ind
#  pp_chge = row['pp_chge']
#  pp_chge_date = row['pp_chge_date']
#  gov_chge_date = row['TA_day']
#  ta_chge_date = row['ta_chge_date']
#  plt.rcParams['figure.figsize'] = 16, 6
#  ax = df_prices[id_station].plot()
#  se_mean_prices.plot(ax=ax)
#  handles, labels = ax.get_legend_handles_labels()
#  ax.legend(handles, [id_station, u'mean price'], loc = 1)
#  ax.axvline(x = ta_chge_date, color = 'r', ls = '-', alpha = 0.8, lw = 1.5)
#  ax.axvline(x = gov_chge_date, color = 'b', ls = '--', alpha = 1.0, lw = 1.5)
#  ax.axvline(x = pp_chge_date, color = 'b', ls = ':', alpha = 1.0, lw = 1.5)
#  footnote_text = '\n'.join([row['name'], row['adr_street'], row['adr_city'], row['ci_ardt_1']])
#  plt.figtext(0.1, -0.1, footnote_text) 
#  if pd.isnull(ta_chge_date):
#    file_name = '_'.join([row['brand_0'],
#                           id_station,
#                           u'{:.3f}'.format(pp_chge)]) + '_notadate.png'
#  else:
#    file_name = '_'.join([row['brand_0'],
#                           id_station,
#                           u'{:.3f}'.format(pp_chge)]) + '.png'
#  plt.savefig(os.path.join(path_dir_built_graphs,
#                           'total_access_no_pp_chge',
#                           file_name),
#              dpi = 200,
#              bbox_inches='tight')
#  plt.close()

# FIX BASED ON ta_gap examination
# only those announced too early by Total doc
# otherwise gov website is assumed to be updated with delay

ls_fix_ta_chge_date =\
  [['56690003', '27/01/2014', '02/04/2014'], # seems confirmed
   ['95400002', pd.NaT      , '13/04/2012'],
   ['78760003', '10/09/2012', '28/09/2012'],
   ['6600017' , pd.NaT      , '22/01/2013'], # no info, TA day credible thouth missing per
   ['62217006', '02/07/2012', '13/07/2012'], # why date from ouverture table?
   ['89470002', pd.NaT      , pd.NaT      ], # latest date: not conversion to TA but renovation
   ['37170001', '08/10/2012', '26/10/2012'], # why date from ouverture table?
   ['78380001', '25/02/2013', '08/03/2013'], # latest date: not conversion to TA
   ['77190002', '04/03/2013', '22/03/2013'], # latest date: not conversion to TA
   ['35000001', '09/07/2012', '27/07/2012'], # latest date: not conversion to TA
   ['53000001', '08/10/2012', '29/10/2012'], # latest date: not conversion to TA
   ['13100001', '07/01/2013', '25/01/2013'], # latest date: not conversion to TA
   ['91630005', '15/10/2012', '26/10/2012'], # latest date: not conversion to TA
   ['69170002', '12/11/2012', '30/11/2012'], # latest date: not conversion to TA
   ['79180001', '17/09/2012', '05/10/2012'], # latest date: not conversion to TA
   ['76600017', pd.NaT      , '03/08/2012'], # latest date: not conversion to TA
   ['29200003', '02/07/2012', '13/07/2012'], # latest date: not conversion to TA
   ['6200018' , '01/10/2012', '12/10/2012'], # two stations very close... which one
   ['61000007', '16/07/2012', '31/07/2012'], # two info: couldd have been delayed first time
   ['86360004', pd.NaT      , pd.NaT      ]] # unsure

for id_station, date_beg, date_end in ls_fix_ta_chge_date:
  df_no_pp_chge.loc[id_station, 'ta_chge_date'] = pd.to_datetime(date_end)

len(df_no_pp_chge[~pd.isnull(df_no_pp_chge['ta_chge_date'])])
#df_no_pp_chge['ta_gap'] = pd.to_datetime(df_no_pp_chge['TA_day']) -\
#                            pd.to_datetime(df_no_pp_chge['ta_chge_date'])
df_no_pp_chge['ta_gap'] = df_no_pp_chge['TA_day'] - df_no_pp_chge['ta_chge_date']
df_no_pp_chge['ta_gap'].describe()
df_no_pp_chge.sort('ta_gap', ascending = True, inplace = True)

ls_di_ta_gap = ['name', 'adr_street', 'adr_city',
                'brand_0', 'day_1', 'brand_1',
                'TA_day', 'ta_chge_date', 'ta_gap']

# gov website announces sooner than total doc
print df_no_pp_chge[ls_di_ta_gap][0:10].to_string()

# gov website late on total doc
print df_no_pp_chge[ls_di_ta_gap][~pd.isnull(df_no_pp_chge['ta_gap'])][-10:].to_string()

print u'\nNb of stations for which gov website has to be relied on so far:',\
        len(df_no_pp_chge[pd.isnull(df_no_pp_chge['ta_chge_date'])])
print u'\n',\
        df_no_pp_chge[ls_di_ta_gap][pd.isnull(df_no_pp_chge['ta_gap'])][0:20].to_string()
# can check those which are credible given activity... (and look in total doc...)

# CONCATENATE AND OUTPUT

df_info_ta_final = pd.concat([df_pp_chge, df_no_pp_chge])
# for output
df_info_ta_final['ta_gap'] = df_info_ta_final['ta_gap'].apply(\
                               lambda x: str(pd.Timedelta(x).days) if not pd.isnull(x) else '')

df_info_ta_final.to_csv(os.path.join(path_dir_built_csv,
                                     'df_info_ta_fixed.csv'),
                                     encoding = 'utf-8')
