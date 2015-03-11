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
df_prices_ttc = pd.read_csv(os.path.join(path_dir_built_csv,
                                         'df_prices_ttc_final.csv'),
                        parse_dates = ['date'])
df_prices_ttc.set_index('date', inplace = True)

df_prices_cl = pd.read_csv(os.path.join(path_dir_built_csv,
                                        'df_cleaned_prices.csv'),
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
dict_dtype = dict([('%s_1' %x, str) for x in ls_dtype_temp] +\
                  [('%s_2' %x, str) for x in ls_dtype_temp])
df_pairs = pd.read_csv(os.path.join(path_dir_built_csv,
                     'df_pairs.csv'),
              encoding = 'utf-8',
              dtype = dict_dtype)

# COMPETITORS VS. SAME BRAND
#df_pairs_sg = df_pairs[(df_pairs['group_1'] == df_pairs['group_2']) &\
#                       (df_pairs['group_last_1'] == df_pairs['group_last_2'])]
df_pairs = df_pairs[(df_pairs['group_1'] != df_pairs['group_2']) &\
                    (df_pairs['group_last_1'] != df_pairs['group_last_2'])]

# ##################
# FILTER DATA
# ##################

# STILL SUSPECT (Small number of rank reversals but long...)
ls_disp = ['id_a', 'id_b', 'groups_a', 'groups_b', 'nb_chges_a','nb_chges_b', 'pct_rr']
# df_pairs['rr<=5'] = df_pairs[['rr_1', 'rr_2', 'rr_3', 'rr_4', 'rr_5']].sum(axis = 1)
#print len(df_pairs[(df_pairs['rr>20'] > 0) & (df_pairs['nb_rr'] < 5)])
#print df_pairs[ls_disp][(df_pairs['rr>20'] > 0) & (df_pairs['nb_rr'] < 5)][0:10].to_string()
#df_pairs = df_pairs[~((df_pairs['rr>20'] > 0) & (df_pairs['nb_rr'] < 5))]
df_pairs['avg_rr_len'] = (df_pairs['nb_spread'] * df_pairs['pct_rr']) / df_pairs['nb_rr']
df_pairs['avg_rr_len'] = df_pairs['avg_rr_len'].replace(np.inf, np.nan)
df_pairs = df_pairs[(pd.isnull(df_pairs['avg_rr_len'])) | (df_pairs['avg_rr_len'] <= 15)]

# SEPARATE PAIRS WITH A TOTAL ACCESS

df_pairs_ta = df_pairs[(df_pairs['brand_last_1'] == 'TOTAL_ACCESS') |\
                       (df_pairs['brand_last_2'] == 'TOTAL_ACCESS')]

df_pairs_nota = df_pairs[(df_pairs['brand_last_1'] != 'TOTAL_ACCESS') &\
                         (df_pairs['brand_last_2'] != 'TOTAL_ACCESS')]

# need to separate since change in brand tends to inflate pct_rr artificially
# todo: generalize to rule out significant chges in margin

# ##########
# STATS DESC
# ##########

pd.set_option('float_format', '{:,.2f}'.format)
diff_bound = 0.01

# Histogram of average spreads (abs value required)
hist_test = plt.hist(df_pairs['mean_spread'].abs().values,
                     bins = 100,
                     range = (0, 0.3))
plt.show()

print '\nRank reversal: All'
print df_pairs['pct_rr'].describe()

print '\nRank reversal: Total Access (TA)'
print df_pairs_ta['pct_rr'].describe()

print '\nRank reversal: All except TA'
print df_pairs_nota['pct_rr'].describe()

print '\nRank reversal: No differentiation, no TA'
print df_pairs_nota['pct_rr'][df_pairs_nota['mean_spread'].abs() <= diff_bound].describe()

print '\nRank reversal: Differentiation, no TA'
print df_pairs_nota['pct_rr'][df_pairs_nota['mean_spread'].abs() > diff_bound].describe()

# CAUTION: RESTRICTION TO NON TOTAL ACCESS
# df_pairs = df_pairs_nota

df_pairs_nodiff = df_pairs[np.abs(df_pairs['mean_spread']) <= diff_bound]
df_pairs_diff = df_pairs[np.abs(df_pairs['mean_spread']) > diff_bound]
ls_ppd_names = ['All', 'No differentation', 'Differentiation']

zero = np.float64(1e-10)

for ppd_name, df_pairs_temp in zip(ls_ppd_names, [df_pairs, df_pairs_nodiff, df_pairs_diff]):
  print '\n', ppd_name
  print "\nNb pairs", len(df_pairs_temp)
  
  print "Of which no rank rank reversals",\
           len(df_pairs_temp['pct_rr'][df_pairs_temp['pct_rr'] <= zero])
  
  # RR & SPREAD VS DISTANCE + PER TYPE OF BRAND
  #hist_test = plt.hist(df_pairs_nodiff['pct_rr'][~pd.isnull(df_pairs_nodiff['pct_rr'])], bins = 50)
  df_all = df_pairs_temp[(~pd.isnull(df_pairs_temp['pct_rr'])) &\
                         (df_pairs_temp['distance'] <= 3)]
  df_close = df_pairs_temp[(~pd.isnull(df_pairs_temp['pct_rr'])) &\
                           (df_pairs_temp['distance'] <= 1)]
  df_far = df_pairs_temp[(~pd.isnull(df_pairs_temp['pct_rr'])) &\
                         (df_pairs_temp['distance'] > 1)]
  
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
#print 'Station with max length rank reversal:', np.argmax(df_pairs['max_len_rr'])

# INSPECT OUTLIERS (???)
print u'\nInspect outliers'
len(df_pairs[(df_pairs['mean_spread'].abs() > 0.01) & (df_pairs['pct_rr']> 0.4)])
ls_disp = ['id_1', 'id_2', 'group_last_1', 'group_last_2', 'pct_rr', 'nb_rr']
print df_pairs[ls_disp][(df_pairs['mean_spread'].abs() > 0.01) &\
                      (df_pairs['pct_rr']> 0.4)].to_string()

# todo: filter pairs on frequency of changes (todo everywhere incl. price cleaning)
# todo: filter chge of price policy: df_prices_ttc[['63000013','63000019']].plot()

# CLOSE PRICES
print u'\nOverview pct_rr'
print df_pairs['pct_rr'].describe()

print u'\nClose prices'
print len(df_pairs[(df_pairs['pct_same'] >= 0.33)]) # todo: harmonize pct i.e. * 100
print len(df_pairs[(df_pairs['mean_spread'].abs() <= 0.01)])
# Pct same vs. mean_spread: make MSE appear? (i.e. close prices but no steady gap...)
# Very radical criterion though (show it with second... both side?)
print len(df_pairs[(df_pairs['mean_spread'].abs() <= 0.01) &\
                   (df_pairs['freq_mc_spread'] < 10)])

# High prevalence of two spread values with opposit signs
# Good candidates MSE with fixed grid? (why so few?... freq too strong?)
# Check nb rank reversals
print len(df_pairs[(df_pairs['freq_mc_spread'] > 10) &\
                   (df_pairs['freq_smc_spread'] > 10) &\
                   ((df_pairs['mc_spread'] * df_pairs['smc_spread']) < 0)])

# Not so many without checking it (check inexistence of a reference spread?)
print len(df_pairs[((df_pairs['mc_spread'] * df_pairs['smc_spread']) < 0)])
