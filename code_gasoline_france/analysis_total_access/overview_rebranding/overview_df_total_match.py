#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *

path_dir_built_scraped = os.path.join(path_data,
                                      u'data_gasoline',
                                      u'data_built',
                                      u'data_scraped_2011_2014')

path_dir_built_scraped_csv = os.path.join(path_dir_built_scraped,
                                          u'data_csv')

path_dir_built_ta = os.path.join(path_data,
                                 u'data_gasoline',
                                 u'data_built',
                                 u'data_total_access')

path_dir_built_ta_json = os.path.join(path_dir_built_ta, 
                                      'json')

path_dir_built_ta_csv = os.path.join(path_dir_built_ta, 
                                     'csv')

path_dir_built_ta_graphs = os.path.join(path_dir_built_ta, 
                                        'graphs')

# #########
# LOAD DATA
# #########

# DF STATION INFO

df_info = pd.read_csv(os.path.join(path_dir_built_scraped_csv,
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
df_info = df_info[df_info['highway'] != 1]

# DF PRICES

df_prices_ht = pd.read_csv(os.path.join(path_dir_built_scraped_csv,
                                        'df_prices_ht_final.csv'),
                           parse_dates = ['date'])
df_prices_ht.set_index('date', inplace = True)

df_prices_ttc = pd.read_csv(os.path.join(path_dir_built_scraped_csv,
                                        'df_prices_ttc_final.csv'),
                           parse_dates = ['date'])
df_prices_ttc.set_index('date', inplace = True)

ls_keep_ids = [id_station for id_station in df_prices_ht.columns if\
                id_station in df_info.index]

df_prices = df_prices_ht[ls_keep_ids]

se_mean_prices = df_prices.mean(1)

# DF MARGIN CHGE

df_margin_chge = pd.read_csv(os.path.join(path_dir_built_scraped_csv,
                                          'df_margin_chge.csv'),
                             encoding = 'utf-8',
                             dtype = {'id_station' : str},
                             parse_dates = ['date'])
df_margin_chge.set_index('id_station', inplace = True)

# DICT TOTAL SA DATES

dict_ta_dates_str = dec_json(os.path.join(path_dir_built_ta_json,
                                          'dict_ta_dates_str.json'))

# #####################
# BUILD DF TOTAL ACCESS
# #####################

# Create dummies to identify TA and TA chges
df_info['TA'] = 0
df_info['TA_chge'] = 0
for i in range(3):
  df_info.loc[df_info['brand_{:d}'.format(i)] == 'TOTAL_ACCESS',
              'TA'] = 1
  df_info.loc[(df_info['brand_%s' %i] != 'TOTAL_ACCESS') &\
              (df_info['brand_%s' %(i+1)] == 'TOTAL_ACCESS'),
              'TA_chge'] = 1
print u'\nNb Total Acces:', df_info['TA'].sum()
print u'\nNb Total Acces chges:', df_info['TA_chge'].sum()

# Add chges in margin detected by max before/after difference
df_info['pp_chge'] = df_margin_chge['value']
df_info['pp_chge_date'] = df_margin_chge['date']

## Check chge in policy not TA
## todo: add distance to closest total access (move?)
#df_info = pd.merge(df_info, df_ta,
#                   left_index = True, right_index = True, how = 'left')
#
#ls_disp = ['name', 'adr_city', 'adr_dpt', 'brand_0', 'brand_1', 'brand_2',
#           'pp_chge_date', 'id_cl_ta_0', 'dist_cl_ta_0']
ls_disp = ['name', 'adr_city', 'adr_dpt', 'brand_0', 'brand_1', 'brand_2',
           'pp_chge', 'pp_chge_date']
print '\nMargin chge not Total Access:'
print df_info[ls_disp][(df_info['pp_chge'].abs() >= 0.04) &\
                       (df_info['TA'] != 1)].to_string()
## Not TA => Gvt announces?
#ax = df_prices[['93420001', '93420006']].plot()
#ax.axvline(x = pd.to_datetime('2012-10-15'), color = 'k', ls = 'dashed')
#ax.axvline(x = pd.to_datetime('2012-10-26'), color = 'k', ls = 'dashed')
#df_prices.mean(1).plot(ax = ax)
#plt.show()

# TA chge date candidates from Total SA data
df_info['ta_chge_date'] = np.datetime64()
print u'\nFill df_info with info from Total SA'
for id_station, ls_dates in dict_ta_dates_str.items():
  ls_dates = [pd.to_datetime(x, format = '%d/%m/%Y') for x in ls_dates]
  if id_station in df_info.index:
    df_info.loc[id_station,
                'ta_chge_date'] = max(ls_dates)
  else:
   print id_station, 'not in df_info_ta'

# TA chge date candidates from gouv data
for i in range(3):
  df_info.loc[df_info['brand_{:d}'.format(i)] == 'TOTAL_ACCESS',
              'ta_brand_day'] = df_info['day_{:d}'.format(i)]

## ################
## OUTPUT
## ################
#
#df_info.to_csv(os.path.join(path_dir_built_ta_csv,
#                            'df_info_ta.csv'),
#               encoding = 'utf-8')

# ########################
# STATS DES ON TA STATIONS
# ########################

# ONLY TOTAL ACCESS OBSERVED 
# volume too small before, station temporarily closed... or pbm

print u'\nNb stations starting with brand TA:',\
         len(df_info[df_info['brand_0'] == 'TOTAL_ACCESS'])

print u'\nOverview stations starting with brand TA:'
print df_info[df_info['brand_0'] == 'TOTAL_ACCESS']\
        [['name', 'adr_street', 'adr_city']].to_string()
## Check price series (could as well display activity periods)
## Seems there is interruption for 93500006: why not cut?
## Seems there is no(t much) data for 88300007: drop it?

# TOTAL ACCESS AFTER OTHER BRAND(S)

print u'\nNb stations starting with a brand before TA:',\
        len(df_info[df_info['brand_1'] == 'TOTAL_ACCESS'])

print u'Nb stations starting with two brands before TA:',\
        len(df_info[df_info['brand_2'] == 'TOTAL_ACCESS'])

df_info.sort('ta_brand_day', ascending = True, inplace = True)

print u'\nInspect first TAs with change:'
print df_info[['name', 'adr_street', 'adr_city',
               'brand_0', 'day_1', 'brand_1', 'ta_brand_day']][0:10].to_string()

print '\nNb station with brand change after TA',\
         len(df_info[(df_info['TA_chge'] == 1) &\
                     (df_info['brand_last'] != 'TOTAL_ACCESS')])

print u'\nOverview stations leaving TA:'
print df_info[(df_info['TA_chge'] == 1) &\
              (df_info['brand_last'] != 'TOTAL_ACCESS')]\
                [['name', 'adr_street', 'adr_city',
                 'brand_0', 'day_1', 'brand_1', 'day_2', 'brand_2', 'ta_brand_day']].to_string()

# TABLE OF STARTING BRAND WHEN KNOWN
print u'\nBrands of TA (chge):'
print df_info['brand_0'][df_info['TA_chge'] == 1].value_counts()

print u'\nBrands of TA (chge) with pp change st. above 0.02:'
print df_info['brand_0'][(df_info['TA_chge'] == 1) &\
                         (df_info['pp_chge'].abs() > 0.02)].value_counts()

# todo: check Total not Total Access pp_chge
print u'\nOverview Total not TA with pp_chge:'
print df_info[(df_info['TA'] != 1) &\
              (df_info['brand_0'] == 'TOTAL') &\
              (df_info['pp_chge'] <= -0.02)][ls_disp].to_string()

# ########################
# STATION CLOSING INTERVAL
# ########################

df_pp_chge = df_info[(df_info['TA'] == 1) &\
                     (df_info['pp_chge'].abs() > 0.02)].copy()

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

print '\nNb intervals with no nan at beg/end:',\
         len(df_interval[(df_interval['nb_nan_beg'] == 0) &\
                         (df_interval['nb_nan_end'] == 0)])

print '\nOverview of intervals with no nan at beg/end:'
print df_interval[(df_interval['nb_nan_beg'] == 0) &\
                  (df_interval['nb_nan_end'] == 0)]['length'].describe()

print '\nOverview of intervals (<= 10) with no nan at beg/end:'
print df_interval[(df_interval['nb_nan_beg'] == 0) &\
                  (df_interval['nb_nan_end'] == 0) &\
                  (df_interval['length'] <= 10)].to_string()

print '\nOverview of intervals incl. nan:'
print df_interval['length_w_nan'].describe()

df_pp_chge = pd.merge(df_pp_chge,
                      df_interval,
                      left_index = True,
                      right_index = True)

## ######
## GRAPHS
## ######

# todo: non total access (threshold? reg before/after?)
# todo: total access with no margin chge detected

#for row_ind, row in df_pp_chge.iterrows():
#  id_station = row_ind
#  pp_chge = row['pp_chge']
#  pp_chge_date = row['pp_chge_date'] # margin chge detected
#  gov_chge_date = row['ta_brand_day'] # date from gov data
#  ta_chge_date = row['ta_chge_date'] # date from total
#  date_beg = row['date_beg']
#  date_end = row['date_end']
#  plt.rcParams['figure.figsize'] = 16, 6
#  ax = df_prices[id_station].plot()
#  se_mean_prices.plot(ax=ax)
#  handles, labels = ax.get_legend_handles_labels()
#  ax.legend(handles, [id_station, u'mean price'], loc = 1)
#  # margin chge: date and interval
#  ax.axvspan(date_beg, date_end, alpha=0.2, color='blue')
#  ln_da_0 = ax.axvline(x = pp_chge_date, color = 'b', ls = '--', alpha = 0.8, lw = 1.2)
#  ln_da_0.set_dashes([8,8])
#  # brand chge from gov data: date
#  ln_da_1 = ax.axvline(x = ta_chge_date, color = '#FFA500', ls = '--', alpha = 0.8, lw = 1.2)
#  ln_da_1.set_dashes([8,8])
#  # brand chge from Total SA data: date 
#  ln_da_2 = ax.axvline(x = gov_chge_date, color = 'r', ls = '--', alpha = 0.8, lw = 1.2)
#  ln_da_2.set_dashes([4,4])
#  footnote_text = '\n'.join(row[['name',
#                                 'adr_street',
#                                 'adr_city',
#                                 'ci_ardt_1']].values)
#  plt.figtext(0.1, -0.1, footnote_text) 
#  if row['TA'] == 1:
#    file_name = '_'.join([row['brand_0'],
#                          id_station,
#                          u'{:.3f}'.format(pp_chge)]) + '.png'
#    path_file = os.path.join(path_dir_built_ta_graphs,
#                             'price_series',
#                             'ta_pp_chge',
#                             file_name)
#  else:
#    file_name = '_'.join([row['brand_0'],
#                          row['brand_last'],
#                          id_station,
#                          u'{:.3f}'.format(pp_chge)]) + '.png'
#    path_file = os.path.join(path_dir_built_ta_graphs,
#                             'price_series',
#                             'other_pp_chge',
#                             file_name)
#  plt.savefig(path_file,
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

# ############################
# TA WITHOUT PRICE POLY CHANGE
# ############################

df_ta_no_pp_chge = df_info[(df_info['TA'] == 1) &\
                           (df_info['pp_chge'].abs() < 0.02)].copy()

# FIX BASED ON ta_gap examination
# only those announced too early by Total doc
# otherwise gov website is assumed to be updated with delay

ls_fix_ta_chge_date =\
  [['56690003', '27/01/2014', '02/04/2014'], # seems confirmed
   ['95400002', pd.NaT      , '13/04/2012'],
   ['78760003', '10/09/2012', '28/09/2012'],
   ['6600017' , pd.NaT      , '22/01/2013'], # no info, TA day credible though missing per
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

# 17138005: info not in dict_ta_dates_str but is in pdf so: matching mistake?

for id_station, date_beg, date_end in ls_fix_ta_chge_date:
  df_ta_no_pp_chge.loc[id_station,
                       'ta_chge_date'] = pd.to_datetime(date_end)

len(df_ta_no_pp_chge[~pd.isnull(df_ta_no_pp_chge['ta_chge_date'])])
#df_ta_no_pp_chge['ta_gap'] = pd.to_datetime(df_ta_no_pp_chge['TA_day']) -\
#                            pd.to_datetime(df_ta_no_pp_chge['ta_chge_date'])
df_ta_no_pp_chge['ta_gap'] = df_ta_no_pp_chge['ta_brand_day'] - df_ta_no_pp_chge['ta_chge_date']
df_ta_no_pp_chge['ta_gap'].describe()
df_ta_no_pp_chge.sort('ta_gap', ascending = True, inplace = True)

ls_di_ta_gap = ['name', 'adr_street', 'adr_city',
                'brand_0', 'day_1', 'brand_1',
                'ta_brand_day', 'ta_chge_date', 'ta_gap']

# gov website announces sooner than total doc
print u'\nOverview of TA (no chge) announced sooner by gov than Total SA:'
print df_ta_no_pp_chge[ls_di_ta_gap][0:10].to_string()

# gov website late on total doc
print u'\nOverview of TA (no chge) announced sooner by Total SA than gov:'
print df_ta_no_pp_chge[ls_di_ta_gap][~pd.isnull(df_ta_no_pp_chge['ta_gap'])][-10:].to_string()

print u'\nNb of TA (no chge) for which gov website has to be relied on so far:',\
          len(df_ta_no_pp_chge[pd.isnull(df_ta_no_pp_chge['ta_chge_date'])])

print u'\nOverview TA (no chge) for which gov website has to be relied on so far:'
print df_ta_no_pp_chge[ls_di_ta_gap][pd.isnull(df_ta_no_pp_chge['ta_gap'])][0:20].to_string()
# can check those which are credible given activity... (and look in total doc...)

# Looks gov always late... rather trust gov website?
len(df_ta_no_pp_chge[df_ta_no_pp_chge['ta_gap'] > pd.Timedelta(days = 30)])
len(df_ta_no_pp_chge[df_ta_no_pp_chge['ta_gap'] < -pd.Timedelta(days = 30)])

## CONCATENATE AND OUTPUT
#
#df_info_ta_final = pd.concat([df_pp_chge,
#                              df_ta_no_pp_chge])
## for output
#df_info_ta_final['ta_gap'] = df_info_ta_final['ta_gap'].apply(\
#                               lambda x: str(pd.Timedelta(x).days) if not pd.isnull(x) else '')
#
##df_info_ta_final.to_csv(os.path.join(path_dir_built_csv,
##                                     'df_info_ta_fixed.csv'),
##                                     encoding = 'utf-8')
