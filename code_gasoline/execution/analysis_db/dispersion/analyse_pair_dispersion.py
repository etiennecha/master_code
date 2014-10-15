#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path_sub
from add_to_path_sub import path_data
from generic_master_price import *
from generic_master_info import *
from generic_competition import *
import time
from statsmodels.distributions.empirical_distribution import ECDF
from scipy.stats import ks_2samp

path_dir_built_paper = os.path.join(path_data, 'data_gasoline', 'data_built', 'data_paper')

path_dir_built_json = os.path.join(path_dir_built_paper, 'data_json')
path_diesel_price = os.path.join(path_dir_built_json, 'master_price_diesel.json')
path_info = os.path.join(path_dir_built_json, 'master_info_diesel.json')
path_ls_ids_final = os.path.join(path_dir_built_json, 'ls_ids_final.json')
path_ls_ls_competitors = os.path.join(path_dir_built_json, 'ls_ls_competitors.json')
path_ls_tuple_competitors = os.path.join(path_dir_built_json, 'ls_tuple_competitors.json')

path_dir_source = os.path.join(path_data, 'data_gasoline', 'data_source')
path_dict_brands = os.path.join(path_dir_source, 'data_other', 'dict_brands.json')
path_csv_insee_data = os.path.join(path_dir_source, 'data_other', 'data_insee_extract.csv')

path_dir_built_csv = os.path.join(path_dir_built_paper, 'data_csv')

path_dir_insee = os.path.join(path_data, 'data_insee')
path_dict_dpts_regions = os.path.join(path_dir_insee, 'dpts_regions', 'dict_dpts_regions.json')

master_price = dec_json(path_diesel_price)
master_info = dec_json(path_info)
ls_ids_final = dec_json(path_ls_ids_final)
ls_ls_competitors = dec_json(path_ls_ls_competitors)
ls_tuple_competitors = dec_json(path_ls_tuple_competitors)
dict_brands = dec_json(path_dict_brands)
dict_dpts_regions = dec_json(path_dict_dpts_regions)

zero_threshold = np.float64(1e-10)
pd.options.display.float_format = '{:6,.4f}'.format

start = time.clock()

# DF PRICES
ls_dates = [pd.to_datetime(date) for date in master_price['dates']]
df_prices = pd.DataFrame(master_price['diesel_price'], master_price['ids'], ls_dates).T
df_prices[[x for x in df_prices.columns if x not in ls_ids_final]] = np.nan 

# DF CLEAN PRICES

## Prices cleaned with R / STATA
#path_csv_price_cl_R = os.path.join(path_dir_built_paper_csv, 'price_cleaned_R.csv')
#df_prices_cl_R = pd.read_csv(path_csv_price_cl_R,
#                             dtype = {'id' : str,
#                                      'date' : str,
#                                      'price': np.float64,
#                                      'price.cl' : np.float64})
#df_prices_cl_R  = df_prices_cl_R.pivot(index='date', columns='id', values='price.cl')
#df_prices_cl_R.index = [pd.to_datetime(x) for x in df_prices_cl_R.index]
#idx = pd.date_range('2011-09-04', '2013-06-04')
#df_prices_cl_R = df_prices_cl_R.reindex(idx, fill_value=np.nan)
#df_price_cl = df_prices_cl_R

df_prices_cl = pd.read_csv(os.path.join(path_dir_built_csv, 'df_cleaned_prices.csv'),
                          index_col = 0,
                          parse_dates = True)
df_prices_cl[[x for x in df_prices_cl.columns if x not in ls_ids_final]] = np.nan 

# ################
# BUILD DATAFRAME
# ################

km_bound = 3
diff_bound = 0.02

# todo: iterate with various  (high value: no cleaning of prices)

# DF PAIR PRICE DISPERSION
ls_ppd = []
ls_ar_rrs = []
ls_rr_lengths = []
for (indiv_id, comp_id), distance in ls_tuple_competitors:
  if distance <= km_bound: 
    se_prices_1 = df_prices[indiv_id]
    se_prices_2 = df_prices[comp_id]
    avg_spread = (se_prices_2 - se_prices_1).mean()
    if np.abs(avg_spread) > diff_bound:
      #se_prices_1 = df_price_cl[indiv_id]
      #se_prices_2 = df_price_cl[comp_id]
      se_prices_1 = df_prices[indiv_id]
      se_prices_2 = df_prices[comp_id]
    ls_comp_pd = get_pair_price_dispersion(se_prices_1.as_matrix(),
                                           se_prices_2.as_matrix(), light = False)
    ls_comp_chges = get_stats_two_firm_price_chges(se_prices_1.as_matrix(),
                                                   se_prices_2.as_matrix())
    ls_ppd.append([indiv_id, comp_id, distance] +\
                  ls_comp_pd[0][:9] + [avg_spread] + ls_comp_pd[0][10:]+\
                  get_ls_standardized_frequency(ls_comp_pd[3][0]) +\
                  ls_comp_chges[:-2])
    ls_ar_rrs.append(ls_comp_pd[2][1])
    ls_rr_lengths += ls_comp_pd[3][0]

ls_scalars  = ['nb_spread', 'nb_same_price', 'nb_a_cheaper', 'nb_b_cheaper', 
               'nb_rr', 'pct_rr', 'avg_abs_spread_rr', 'med_abs_spread_rr',
               'avg_abs_spread', 'avg_spread', 'std_spread']

ls_freq_std = ['rr_1', 'rr_2', 'rr_3', 'rr_4', 'rr_5', '5<rr<=20', 'rr>20']

ls_chges    = ['nb_days_1', 'nb_days_2', 'nb_prices_1', 'nb_prices_2',
               'nb_ctd_1', 'nb_ctd_2', 'nb_chges_1', 'nb_chges_2', 'nb_sim_chges',
               'nb_1_fol', 'nb_2_fol']

ls_columns  = ['id_1', 'id_2', 'distance'] + ls_scalars + ls_freq_std + ls_chges

df_ppd = pd.DataFrame(ls_ppd, columns = ls_columns)
df_ppd['pct_same_price'] = df_ppd['nb_same_price'] / df_ppd['nb_spread']
# Create same corner variables
df_ppd['sc_500'] = 0
df_ppd['sc_500'][df_ppd['distance'] <= 0.5] = 1
df_ppd['sc_750'] = 0
df_ppd['sc_500'][df_ppd['distance'] <= 0.75] = 1
df_ppd['sc_1000'] = 0
df_ppd['sc_1000'][df_ppd['distance'] <= 1] = 1

# DF BRAND (LIGHT)
dict_std_brands = {v[0]: v for k, v in dict_brands.items()}
ls_brands = []
for indiv_id in master_price['ids']:
  indiv_dict_info = master_price['dict_info'][indiv_id]
  brand_1_b = indiv_dict_info['brand_std'][0][0]
  brand_2_b = dict_std_brands[indiv_dict_info['brand_std'][0][0]][1]
  brand_type_b = dict_std_brands[indiv_dict_info['brand_std'][0][0]][2]
  brand_1_e = indiv_dict_info['brand_std'][-1][0]
  brand_2_e = dict_std_brands[indiv_dict_info['brand_std'][-1][0]][1]
  brand_type_e = dict_std_brands[indiv_dict_info['brand_std'][-1][0]][2]
  ls_brands.append([brand_1_b, brand_2_b, brand_type_b,
                    brand_1_e, brand_2_e, brand_type_e])
ls_columns = ['brand_1_b', 'brand_2_b', 'brand_type_b', 'brand_1_e', 'brand_2_e', 'brand_type_e']
df_brands = pd.DataFrame(ls_brands, index = master_price['ids'], columns = ls_columns)
df_brands['id'] = df_brands.index

# DF PPD WITH BRANDS (Merge may change order of pdd)
df_brands = df_brands.rename(columns={'id': 'id_1'})
df_ppd = pd.merge(df_ppd, df_brands, on='id_1')
df_brands = df_brands.rename(columns={'id_1': 'id_2'})
df_ppd = pd.merge(df_ppd, df_brands, on='id_2', suffixes=('_1', '_2'))

print 'Pair price dispersion dataframe built in:', time.clock() - start

# Build categories (are they really relevant?)
df_ppd['pair_type'] = None
df_ppd['pair_type'][((df_ppd['brand_type_e_1'] == 'SUP') &\
                     (df_ppd['brand_type_e_2'] == 'OIL')) |\
                    ((df_ppd['brand_type_e_1'] == 'OIL') &\
                     (df_ppd['brand_type_e_2'] == 'SUP'))] = 'OIL-SUP'
df_ppd['pair_type'][((df_ppd['brand_type_e_1'] == 'SUP') &\
                     (df_ppd['brand_type_e_2'] == 'IND')) |\
                    ((df_ppd['brand_type_e_1'] == 'IND') &\
                     (df_ppd['brand_type_e_2'] == 'SUP'))] = 'IND-SUP'
df_ppd['pair_type'][((df_ppd['brand_type_e_1'] == 'OIL') &\
                     (df_ppd['brand_type_e_2'] == 'IND')) |\
                    ((df_ppd['brand_type_e_1'] == 'IND') &\
                     (df_ppd['brand_type_e_2'] == 'OIL'))] = 'IND-OIL'
df_ppd['pair_type'][(df_ppd['brand_type_e_1'] == 'OIL') &\
                    (df_ppd['brand_type_e_2'] == 'OIL')] = 'OIL'
df_ppd['pair_type'][(df_ppd['brand_type_e_1'] == 'SUP') &\
                    (df_ppd['brand_type_e_2'] == 'SUP')] = 'SUP'
df_ppd['pair_type'][(df_ppd['brand_type_e_1'] == 'IND') &\
                    (df_ppd['brand_type_e_2'] == 'IND')] = 'IND'

# ##################
# PPD: DF STATS DES
# ##################

#ls_view_1 =['id_1', 'id_2', 'brand_1_e_1', 'brand_1_e_2', 
#            'nb_days_spread', 'avg_abs_spread', 'avg_spread', 'std_spread', 
#            'percent_rr', 'max_len_rr', 'avg_abs_spread_rr', 'nb_rr']

# Drop pairs with insufficient price data
print "Dropped pairs:".format(len(df_ppd[(pd.isnull(df_ppd['avg_spread'])) |\
                                         (df_ppd['nb_spread'] < 100)]))
df_ppd = df_ppd[(~pd.isnull(df_ppd['avg_spread'])) & (df_ppd['nb_spread'] >= 100)]

# Rank reversal length?
ar_rr_lengths = np.array(ls_rr_lengths)

# Histogram of average spreads
hist_test = plt.hist(df_ppd['avg_spread'].abs().values,
                     bins = 100,
                     range = (0, 0.3))
plt.show()

#for i in range(10):
#  print i, len(df_ppd[np.abs(df_ppd['avg_spread']) > i * 10**(-2)]),\
#        len(df_ppd[(np.abs(df_ppd['avg_spread']) > i * 10**(-2)) & (df_ppd['nb_rr'] > 10)])

# Exclude Total Access from analysis

df_ppd_nota = df_ppd[(df_ppd['brand_2_e_1'] != 'TOTAL_ACCESS') &\
                     (df_ppd['brand_2_e_2'] != 'TOTAL_ACCESS')]


print '\nRank reversal: All'
print df_ppd['pct_rr'].describe()

print '\nRank reversal: Total Access'
print df_ppd.ix[[ind for ind in df_ppd.index if ind not in df_ppd_nota.index]]['pct_rr'].describe()

df_ppd = df_ppd_nota

print '\nRank reversal: All (No TA)'
print df_ppd_nota['pct_rr'].describe()

print '\nRank reversal: No differentiation (No TA)'
print df_ppd_nota['pct_rr'][df_ppd_nota['avg_spread'].abs() <= diff_bound].describe()

print '\nRank reversal: Differentiation (No TA)'
print df_ppd_nota['pct_rr'][df_ppd_nota['avg_spread'].abs() > diff_bound].describe()

# Build dataframes: differentiation vs. no differentiation
df_ppd_nodiff = df_ppd[np.abs(df_ppd['avg_spread']) <= diff_bound]
df_ppd_diff = df_ppd[np.abs(df_ppd['avg_spread']) > diff_bound]
ls_ppd_names = ['All', 'No differentation', 'Differentiation']

for ppd_name, df_ppd_temp in zip(ls_ppd_names, [df_ppd, df_ppd_nodiff, df_ppd_diff]):
  print '\n', ppd_name
  print "\nNb pairs", len(df_ppd_temp)
  
  print "Of which no rank rank reversals",\
           len(df_ppd_temp['pct_rr'][df_ppd_temp['pct_rr'] <= zero_threshold])
  
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
  plt.legend()
  plt.tight_layout()
  plt.show()
  
  print '\nK-S test of equality of rank reversal distributions'
  print ks_2samp(df_close['pct_rr'], df_far['pct_rr'])
  # one side test not implemented in python ? (not in scipy at least)
  
  print '\nNb of pairs', len(df_all['pct_rr'])
  print 'Nb of pairs w/ short distance', len(df_close['pct_rr'])
  print 'Nb of pairs w/ longer distance', len(df_far['pct_rr'])
  
  print '\nPair types representation among all pairs, close pairs, far pairs'
  for df_temp, name_df in zip([df_all, df_close, df_far], ['All', 'Close', 'Far']):
    print '\n%s' %name_df, len(df_temp), 'pairs'
    for pair_type in np.unique(df_temp['pair_type']):
      print "{:20} {:>4.2f}".\
              format(pair_type, len(df_temp[df_temp['pair_type'] == pair_type]) /\
                       float(len(df_temp)))
  
# RR VS. TOTAL ACCESS / RR DURATION

## Find suspect rank reversal
#print 'Station with max length rank reversal:', np.argmax(df_ppd['max_len_rr'])

# ####################
# DF PAIR PD TEMPORAL
# ####################

# All, Total Access, No Total Access
ls_ar_rrs_ta, ls_ar_rrs_nota = [], []
for ar_rrs, ls_pair_ppd in zip(ls_ar_rrs, ls_ppd): 
  if (df_brands['brand_1_e'][ls_pair_ppd[0]] == 'TOTAL_ACCESS') or\
     (df_brands['brand_1_e'][ls_pair_ppd[1]] == 'TOTAL_ACCESS'):
    ls_ar_rrs_ta.append(ar_rrs)
  else:
    ls_ar_rrs_nota.append(ar_rrs)

# Stations with low differentiation and not Total Access
ls_ar_rrs_nodiff = [] 
for ar_rrs, ls_pair_ppd in zip(ls_ar_rrs, ls_ppd):
  if (not df_brands['brand_1_e'][ls_pair_ppd[0]] == 'TOTAL_ACCESS') &\
     (not df_brands['brand_1_e'][ls_pair_ppd[1]] == 'TOTAL_ACCESS') &\
     (np.abs(ls_pair_ppd[12]) <= diff_bound): # CHANGE !?!
    ls_ar_rrs_nodiff.append(ar_rrs)
 
ls_df_rrs_su = []
for ls_ar_rrs_temp in [ls_ar_rrs, ls_ar_rrs_ta, ls_ar_rrs_nota, ls_ar_rrs_nodiff]:
  ls_dates = [pd.to_datetime(date) for date in master_price['dates']]
  df_rrs_temp = pd.DataFrame(ls_ar_rrs_temp, columns = ls_dates)
  se_nb_valid = df_rrs_temp.apply(lambda x: (~pd.isnull(x)).sum())
  se_nb_rr    = df_rrs_temp.apply(lambda x: (np.abs(x) > zero_threshold).sum())
  se_avg_rr   = df_rrs_temp.apply(lambda x: np.abs(x[np.abs(x) > zero_threshold]).mean())
  se_std_rr   = df_rrs_temp.apply(lambda x: np.abs(x[np.abs(x) > zero_threshold]).std())
  se_med_rr   = df_rrs_temp.apply(lambda x: np.abs(x[np.abs(x) > zero_threshold]).median())
  df_rrs_su_temp = pd.DataFrame({'se_nb_valid' : se_nb_valid,
                                 'se_nb_rr'    : se_nb_rr,
                                 'se_avg_rr'   : se_avg_rr,
                                 'se_std_rr'   : se_std_rr,
                                 'se_med_rr'   : se_med_rr})
  df_rrs_su_temp['pct_rr'] = df_rrs_su_temp['se_nb_rr'] / df_rrs_su_temp['se_nb_valid']
  ls_df_rrs_su.append(df_rrs_su_temp) 

# Merge: to be improved? (more dataframes potentially?)
df_rrs_su_all = pd.merge(ls_df_rrs_su[0], ls_df_rrs_su[1],\
                         right_index = True, left_index = True, suffixes=('', '_ta'))
df_rrs_su_all = pd.merge(df_rrs_su_all, ls_df_rrs_su[2],\
                         right_index = True, left_index = True, suffixes=('', '_nota'))
df_rrs_su_all = pd.merge(df_rrs_su_all, ls_df_rrs_su[3],\
                         right_index = True, left_index = True, suffixes=('', '_nodiff'))

df_rrs_su_all[df_rrs_su_all['pct_rr_nota'] == np.inf] = np.nan
print '\n', df_rrs_su_all['pct_rr_nota'].describe()
print 'argmax', df_rrs_su_all['pct_rr_nota'].argmax()

df_rrs_su_all[df_rrs_su_all['pct_rr_nodiff'] == np.inf] = np.nan
print '\n', df_rrs_su_all['pct_rr_nodiff'].describe()

plt.rcParams['figure.figsize'] = 16, 6
ax = df_rrs_su_all[['pct_rr', 'pct_rr_ta', 'pct_rr_nota', 'pct_rr_nodiff']].plot()
handles, labels = ax.get_legend_handles_labels()
labels = ['All', 'Total Access', 'All but Total Access', 'No differentiation']
ax.legend(handles, labels)
plt.tight_layout()
plt.show()

# Price obs: stats descs + graph observations (investigate price cleaning too)

# Check very close prices (Output to folder: graph + map (Google?))
# todo: check if same result with average spread small
df_ppd['pair_type'][(df_ppd['pct_same_price'] > 0.5) &\
                    (df_ppd['brand_2_e_1'] != df_ppd['brand_2_e_2'])].value_counts()
df_ppd[['id_1', 'id_2', 'pair_type']][(df_ppd['pct_same_price'] > 0.5) &\
                                      (df_ppd['brand_2_e_1'] != df_ppd['brand_2_e_2'])][0:10]
# Set size of plot
ax = df_prices[['1500007', '1500001']].plot()
handles, labels = ax.get_legend_handles_labels()
ax.legend(handles, [df_brands.ix[indiv_id]['brand_2_e'] for indiv_id in labels])
plt.title(master_price['dict_info']['1500007']['city'])
plt.show()

# pd.set_option('display.max_columns', 500)

# Check leader follower
# todo: check if can add follow 1 follow 2 and sim (?)
# todo: make more systematic and output graphs with relevant info + maps
# todo: static dispersion but sim changes... more or less same trend (work on variations?)
df_ppd[(df_ppd['brand_2_e_1'] != df_ppd['brand_2_e_2']) &\
       (df_ppd['nb_1_fol'] / df_ppd[['nb_chges_1', 'nb_chges_2']].min(axis=1) > 0.5)]

# todo: add same brand pair var to make lighter + get rid of/signal abnormal obs (rigid prices)

# Examine support through spread

# todo: add order (always do more expensive less cheaper...)
# todo: need to round diff before value count
ls_rows_spread = []
for count, row in df_ppd.iterrows():
  id_1, id_2 = row['id_1'], row['id_2']
  se_spread = df_prices[id_1] - df_prices[id_2]
  se_spread = se_spread.round(3) # no price has more than 3 digits
  ls_rows_spread.append([id_1, id_2, se_spread.value_counts()])

#for id_1, id_2, se_vc in ls_rows_spread:
#  if se_vc.max() / float(se_vc.sum()) > 0.5:
#    print '\n', id_1, id_2
#    print se_vc.iloc[0:min(len(se_vc, 5)]

# DEPRECATED

# #######################################
# PAIR PRICE DISPERSION: NORMALIZED PRICES
# ########################################

## COMPUTE PAIR PRICE DISPERSION
#start = time.clock()
#ls_pair_price_dispersion = []
#ls_pair_competitors = []
#for ((indiv_id_1, indiv_id_2), distance) in ls_tuple_competitors:
#  # could check presence btw...
#  indiv_ind_1 = master_price['ids'].index(indiv_id_1)
#  indiv_ind_2 = master_price['ids'].index(indiv_id_2)
#  if distance < km_bound:
#    ls_pair_competitors.append(((indiv_id_1, indiv_id_2), distance))
#    ar_price_1 = master_np_prices[indiv_ind_1]
#    ar_price_2 = master_np_prices[indiv_ind_2]
#    ar_diff = ar_price_1 - ar_price_2
#    ar_price_1_norm = ar_price_1 - ar_diff[~np.isnan(ar_diff)].mean()
#    ls_pair_price_dispersion.append(get_pair_price_dispersion(ar_price_1_norm,
#                                                              ar_price_2,
#                                                              light = False))
#print 'Pair price dispersion:', time.clock() - start
#
#def get_plot_normalized(ar_price_1, ar_price2):
#  # TODO: see if orient towards pandas or not
#  ar_diff = ar_price_1 - ar_price_2
#  ar_price_1_norm = ar_price_1 - ar_diff[~np.isnan(ar_diff)].mean()
#  plt.plot(ar_price_1_norm)
#  plt.plot(ar_price_2)
#  plt.plot(ar_price_1)
#  plt.show()
#  return
#
## DF PAIR PD STATS
#ls_ppd_for_df = [elt[0] for elt in ls_pair_price_dispersion]
#ls_columns = ['avg_abs_spread', 'avg_spread', 'std_spread', 'nb_days_spread',
#              'percent_rr', 'avg_abs_spread_rr', 'med_abs_spread_rr', 'nb_rr_conservative']
#df_ppd = pd.DataFrame(ls_ppd_for_df, columns = ls_columns)
#ls_max_len_rr = [np.max(elt[3][0]) if elt[3][0] else 0 for elt in ls_pair_price_dispersion]
#df_ppd['max_len_rr'] = ls_max_len_rr
#df_ppd['id_1'] = [comp[0][0] for comp in ls_pair_competitors]
#df_ppd['id_2'] = [comp[0][1] for comp in ls_pair_competitors]
#
#df_brands = df_brands.rename(columns={'id_2': 'id_1'})
#df_ppd_brands = pd.merge(df_ppd, df_brands, on='id_1')
#df_brands = df_brands.rename(columns={'id_1': 'id_2'})
#df_ppd_brands = pd.merge(df_ppd_brands, df_brands, on='id_2', suffixes=('_1', '_2'))
#
#df_ppd_brands = df_ppd_brands.rename(columns={'nb_rr_conservative': 'nb_rr'})
#
#plt.hist(np.array(df_ppd_brands['avg_abs_spread'][~pd.isnull(df_ppd_brands['avg_abs_spread'])]), bins = 100)
#plt.hist(np.array(df_ppd_brands['max_len_rr'][~pd.isnull(df_ppd_brands['max_len_rr'])]), bins = 100)
#plt.hist(np.array(df_ppd_brands['nb_rr'][~pd.isnull(df_ppd_brands['nb_rr'])]), bins = 100)
#
### Change in price policy => high avg_abs_spread with low nb_rr => clear cut: exlude!
##print df_ppd_brands[ls_view_1][df_ppd_brands['avg_abs_spread'] > 0.03].to_string()
#print df_ppd_brands[ls_view_1][(df_ppd_brands['avg_abs_spread'] < 0.02) & \
#                               (df_ppd_brands['nb_rr'] > 30)].to_string()
#get_plot_normalized(np.array(df_price['95190001']), np.array(df_price['95500005']))

# ##################################
# PAIR PD: LOOK FOR REAL COMPETITORS 
# ##################################

#Km_bound = 20
#ls_ls_indiv_pd = []
#for indiv_id, ls_indiv_comp in zip(master_price['ids'], ls_ls_competitors):
#  ls_indiv_pd = []
#  indiv_ind_1 = master_price['ids'].index(indiv_id)
#  for (comp_id, distance) in ls_indiv_comp:
#    indiv_ind_2 = master_price['ids'].index(comp_id)
#    if distance < km_bound:
#      ls_comp_pd = get_pair_price_dispersion(master_np_prices[indiv_ind_1],
#                                             master_np_prices[indiv_ind_2],
#                                             light = False)
#      if (ls_comp_pd[0][3] > 100) and (ls_comp_pd[0][1] < 0.2) and (ls_comp_pd[0][7] > 5):
#        ls_indiv_pd.append([comp_id,
#                            distance,
#                            [ls_comp_pd[0], ls_comp_pd[1], ls_comp_pd[3]]])
#  ls_ls_indiv_pd.append(ls_indiv_pd)
