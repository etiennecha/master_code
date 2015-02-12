#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
from generic_competition import *
import time
from statsmodels.distributions.empirical_distribution import ECDF
from scipy.stats import ks_2samp

pd.set_option('float_format', '{:,.3f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.3f}'.format(x)

# ###################
# LOAD DATA
# ###################

path_dir_built_paper = os.path.join(path_data,
                                    'data_gasoline',
                                    'data_built',
                                    'data_paper_dispersion')

path_dir_built_csv = os.path.join(path_dir_built_paper, u'data_csv')

path_dir_built_json = os.path.join(path_dir_built_paper, 'data_json')

path_dir_source = os.path.join(path_data, 'data_gasoline', 'data_source')

# LOAD DF PRICES
df_prices_ttc = pd.read_csv(os.path.join(path_dir_built_csv, 'df_prices_ttc_final.csv'),
                        parse_dates = ['date'])
df_prices_ttc.set_index('date', inplace = True)

df_prices_cl = pd.read_csv(os.path.join(path_dir_built_csv, 'df_cleaned_prices.csv'),
                          parse_dates = ['date'])
df_prices_cl.set_index('date', inplace = True)

# LOAD DF INFO
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
                               'dpt' : str})
df_info.set_index('id_station', inplace = True)

# LOAD DF STATION STATS
print '\nLoad df_station_stats'
df_station_stats = pd.read_csv(os.path.join(path_dir_built_csv,
                                            'df_station_stats.csv'),
                               encoding = 'utf-8',
                               dtype = {'id_station' : str})
df_station_stats.set_index('id_station', inplace = True)

# LOAD DF DISPERSION
print '\nLoad df_ppd'
ls_dtype_temp = ['id', 'ci_ardt_1']
dict_dtype = dict([('%s_b' %x, str) for x in ls_dtype_temp] +\
                  [('%s_a' %x, str) for x in ls_dtype_temp])
df_ppd = pd.read_csv(os.path.join(path_dir_built_csv,
                     'df_pair_raw_price_dispersion.csv'),
              encoding = 'utf-8',
              dtype = dict_dtype)

# SAME GROUP STATIONS: ALREADY EXCLUDED (?)
dict_brands = dec_json(os.path.join(path_dir_source,
                                    'data_other',
                                    'dict_brands.json'))
dict_std_brands = {v[0]: v for k, v in dict_brands.items()}

# ##################
# FILTER DATA
# ##################

# DROP PAIRS WITH INSUFFICIENT PRICE DATA (temp?)

print "Dropped pairs (insuff spread obs):",\
        len(df_ppd[(pd.isnull(df_ppd['avg_spread'])) | (df_ppd['nb_spread'] < 100)])
df_ppd = df_ppd[(~pd.isnull(df_ppd['avg_spread'])) & (df_ppd['nb_spread'] >= 100)]

ls_exclude_ids = df_station_stats.index[(df_station_stats['nb_chge'] < 10) |\
                                        (df_station_stats['pct_chge'] < 0.03)]

print "Dropped pairs (insuff price data):",\
        len(df_ppd[(df_ppd['id_a'].isin(ls_exclude_ids)) | (df_ppd['id_b'].isin(ls_exclude_ids))])
df_ppd = df_ppd[(~df_ppd['id_a'].isin(ls_exclude_ids)) & (~df_ppd['id_b'].isin(ls_exclude_ids))]

# EXCLUDE TOTAL ACCESS (temp)

ls_brand_fields = ['brand_0_a', 'brand_1_a', 'brand_2_a',
                   'brand_0_b', 'brand_1_b', 'brand_2_b']
for field in ls_brand_fields:
  df_ppd[field].fillna(u'', inplace = True)
df_ppd['all_brands'] = df_ppd.apply(\
                         lambda x: ','.join([x[brand_field] for brand_field\
                                               in ls_brand_fields if x[brand_field]]), axis = 1)
# group is in fact only normalized brand for now
df_ppd['groups_a'] = df_ppd.apply(\
                         lambda x: ','.join([dict_std_brands[x[brand_field]][1] for brand_field\
                                               in ls_brand_fields[:3] if x[brand_field]]), axis = 1)

df_ppd['groups_b'] = df_ppd.apply(\
                         lambda x: ','.join([dict_std_brands[x[brand_field]][1] for brand_field\
                                               in ls_brand_fields[3:] if x[brand_field]]), axis = 1)
# not equivalent for now because can be 'TOTAL' and 'TOTAL_ACCESS' => deprecate
df_ppd['sg_a'] = df_ppd.apply(lambda x: any([y in x['groups_a']\
                                               for y in x['groups_b'].split(',')]), axis = 1)
df_ppd['sg_b'] = df_ppd.apply(lambda x: any([y in x['groups_b']\
                                               for y in x['groups_a'].split(',')]), axis = 1)

print 'Nb pairs before dropping same group:', len(df_ppd)
df_ppd = df_ppd[(~df_ppd['sg_a']) & (~df_ppd['sg_b'])]
print 'Nb pairs after dropping same group:', len(df_ppd)

# STILL SUSPECT (Small number of rank reversals but long...)
ls_disp = ['id_a', 'id_b', 'groups_a', 'groups_b', 'nb_chges_a','nb_chges_b', 'pct_rr']
# df_ppd['rr<=5'] = df_ppd[['rr_1', 'rr_2', 'rr_3', 'rr_4', 'rr_5']].sum(axis = 1)
#print len(df_ppd[(df_ppd['rr>20'] > 0) & (df_ppd['nb_rr'] < 5)])
#print df_ppd[ls_disp][(df_ppd['rr>20'] > 0) & (df_ppd['nb_rr'] < 5)][0:10].to_string()
#df_ppd = df_ppd[~((df_ppd['rr>20'] > 0) & (df_ppd['nb_rr'] < 5))]
df_ppd['avg_rr_len'] = (df_ppd['nb_spread'] * df_ppd['pct_rr']) / df_ppd['nb_rr']
df_ppd['avg_rr_len'] = df_ppd['avg_rr_len'].replace(np.inf, np.nan)
df_ppd = df_ppd[(pd.isnull(df_ppd['avg_rr_len'])) | (df_ppd['avg_rr_len'] <= 15)]

# SEPARATE PAIRS WITH A TOTAL ACCESS

df_ppd_ta = df_ppd[df_ppd['all_brands'].str.contains('TOTAL_ACCESS')]
df_ppd_nota = df_ppd[~(df_ppd['all_brands'].str.contains('TOTAL_ACCESS'))]

# need to separate since change in brand tends to inflate pct_rr artificially
# todo: generalize to rule out significant chges in margin

# ##########
# STATS DESC
# ##########

pd.set_option('float_format', '{:,.2f}'.format)
diff_bound = 0.01

# Histogram of average spreads (abs value required)
hist_test = plt.hist(df_ppd['avg_spread'].abs().values,
                     bins = 100,
                     range = (0, 0.3))
plt.show()

print '\nRank reversal: All'
print df_ppd['pct_rr'].describe()

print '\nRank reversal: Total Access (TA)'
print df_ppd_ta['pct_rr'].describe()

print '\nRank reversal: All except TA'
print df_ppd_nota['pct_rr'].describe()

print '\nRank reversal: No differentiation, no TA'
print df_ppd_nota['pct_rr'][df_ppd_nota['avg_spread'].abs() <= diff_bound].describe()

print '\nRank reversal: Differentiation, no TA'
print df_ppd_nota['pct_rr'][df_ppd_nota['avg_spread'].abs() > diff_bound].describe()

# CAUTION: RESTRICTION TO NON TOTAL ACCESS
# df_ppd = df_ppd_nota

df_ppd_nodiff = df_ppd[np.abs(df_ppd['avg_spread']) <= diff_bound]
df_ppd_diff = df_ppd[np.abs(df_ppd['avg_spread']) > diff_bound]
ls_ppd_names = ['All', 'No differentation', 'Differentiation']

zero = np.float64(1e-10)

for ppd_name, df_ppd_temp in zip(ls_ppd_names, [df_ppd, df_ppd_nodiff, df_ppd_diff]):
  print '\n', ppd_name
  print "\nNb pairs", len(df_ppd_temp)
  
  print "Of which no rank rank reversals",\
           len(df_ppd_temp['pct_rr'][df_ppd_temp['pct_rr'] <= zero])
  
  # RR & SPREAD VS DISTANCE + PER TYPE OF BRAND
  #hist_test = plt.hist(df_ppd_nodiff['pct_rr'][~pd.isnull(df_ppd_nodiff['pct_rr'])], bins = 50)
  df_all = df_ppd_temp[(~pd.isnull(df_ppd_temp['pct_rr'])) & (df_ppd_temp['distance'] <= 3)]
  df_close = df_ppd_temp[(~pd.isnull(df_ppd_temp['pct_rr'])) & (df_ppd_temp['distance'] <= 1)]
  df_far = df_ppd_temp[(~pd.isnull(df_ppd_temp['pct_rr'])) & (df_ppd_temp['distance'] > 1)]
  
  # Plot ECDF of rank reversals: close vs. far
  ecdf = ECDF(df_all['pct_rr'])
  ecdf_close = ECDF(df_close['pct_rr'])
  ecdf_far = ECDF(df_far['pct_rr'])
  x = np.linspace(min(df_all['pct_rr']), max(df_all['pct_rr']), num=100)
  y = ecdf(x)
  y_close = ecdf_close(x)
  y_far = ecdf_far(x)
  plt.rcParams['figure.figsize'] = 8, 6
  ax = plt.subplot()
  ax.step(x, y_close, label = r'$d_{ij} \leq 1km$')
  ax.step(x, y_far, label = r'$1km < d_{ij} \leq 3km$')
  plt.title(ppd_name)
  plt.legend()
  plt.tight_layout()
  plt.show()
  
  print '\nK-S test of equality of rank reversal distributions'
  print ks_2samp(df_close['pct_rr'], df_far['pct_rr'])
  # one side test not implemented in python ? (not in scipy at least)
  
  print '\nNb of pairs', len(df_all['pct_rr'])
  print 'Nb of pairs w/ short distance', len(df_close['pct_rr'])
  print 'Nb of pairs w/ longer distance', len(df_far['pct_rr'])
  
  #print '\nPair types representation among all pairs, close pairs, far pairs'
  #for df_temp, name_df in zip([df_all, df_close, df_far], ['All', 'Close', 'Far']):
  #  print '\n%s' %name_df, len(df_temp), 'pairs'
  #  for pair_type in np.unique(df_temp['pair_type']):
  #    print "{:20} {:>4.2f}".\
  #            format(pair_type, len(df_temp[df_temp['pair_type'] == pair_type]) /\
  #                     float(len(df_temp)))
  
# RR VS. TOTAL ACCESS / RR DURATION
## Find suspect rank reversal
#print 'Station with max length rank reversal:', np.argmax(df_ppd['max_len_rr'])

# INSPECT OUTLIERS
len(df_ppd[(df_ppd['avg_spread'].abs() > 0.01) & (df_ppd['pct_rr']> 0.4)])
ls_disp = ['id_a', 'id_b', 'groups_a', 'groups_b', 'pct_rr', 'nb_rr']
print df_ppd[ls_disp][(df_ppd['avg_spread'].abs() > 0.01) &\
                      (df_ppd['pct_rr']> 0.4)].to_string()

# todo: filter pairs on frequency of changes (todo everywhere incl. price cleaning)
# todo: filter chge of price policy: df_prices_ttc[['63000013','63000019']].plot()
