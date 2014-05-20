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

df_price_cl = pd.read_csv(os.path.join(path_dir_built_csv, 'df_cleaned_prices.csv'),
                          index_col = 0,
                          parse_dates = True)

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

# RR LENGTHS
ar_rr_lengths = np.array(ls_rr_lengths)

# HISTOGRAM OF AVERAGE SPREADS
hist_test = plt.hist(np.abs(df_ppd['avg_spread'])[~pd.isnull(df_ppd['avg_spread'])].values,
                     bins = 100)
plt.show()

for i in range(10):
  print i, len(df_ppd[np.abs(df_ppd['avg_spread']) > i * 10**(-2)]),\
        len(df_ppd[(np.abs(df_ppd['avg_spread']) > i * 10**(-2)) & (df_ppd['nb_rr'] > 10)])

df_ppd_nodiff = df_ppd[np.abs(df_ppd['avg_spread']) <= diff_bound]
df_ppd_diff = df_ppd[np.abs(df_ppd['avg_spread']) > diff_bound]
ls_ppd_names = ['All', 'No differentation', 'Differentiation']

for ppd_name, df_ppd_temp in zip(ls_ppd_names, [df_ppd, df_ppd_nodiff, df_ppd_diff]):
  print '-'*40
  print '\n', ppd_name
  print "\nNb pairs", len(df_ppd_temp)
  
  print "Of which no rank rank reversals",\
           len(df_ppd_temp['pct_rr'][df_ppd_temp['pct_rr'] <= zero_threshold])
  
  # RR & SPREAD VS DISTANCE + PER TYPE OF BRAND
  #hist_test = plt.hist(df_ppd_nodiff['pct_rr'][~pd.isnull(df_ppd_nodiff['pct_rr'])], bins = 50)
  df_all = df_ppd_temp[(~pd.isnull(df_ppd_temp['pct_rr'])) & (df_ppd_temp['distance'] <= 3)]
  df_close = df_ppd_temp[(~pd.isnull(df_ppd_temp['pct_rr'])) & (df_ppd_temp['distance'] <= 1)]
  df_far = df_ppd_temp[(~pd.isnull(df_ppd_temp['pct_rr'])) & (df_ppd_temp['distance'] > 1)]
  
  df_05 = df_ppd_temp[(~pd.isnull(df_ppd_temp['pct_rr'])) & (df_ppd_temp['distance'] <= 0.5)]
  df_05_1 = df_ppd_temp[(~pd.isnull(df_ppd_temp['pct_rr'])) &\
                        (df_ppd_temp['distance'] > 0.5) & (df_ppd_temp['distance'] <= 1)]
  df_1_2 = df_ppd_temp[(~pd.isnull(df_ppd_temp['pct_rr'])) &\
                        (df_ppd_temp['distance'] > 1) & (df_ppd_temp['distance'] <= 2)]
  df_2_3 = df_ppd_temp[(~pd.isnull(df_ppd_temp['pct_rr'])) & (df_ppd_temp['distance'] > 2)]
  
  # Plot ECDF of rank reversals: close vs. far
  plt.rcParams['figure.figsize'] = 8, 6
  ax = plt.subplot()
  x = np.linspace(min(df_all['pct_rr']), max(df_all['pct_rr']), num=200)
  ls_df_temp = [df_05, df_05_1, df_1_2, df_2_3]
  ls_label_temp = [r'$d_{ij} \leq 0.5km$', 
                   r'$0.5km < d_{ij} \leq 1km$',
                   r'$1km < d_{ij} \leq 2km$',
                   r'$2km \leq d_{ij} < 3km$']
  for df_temp, label_temp in zip(ls_df_temp, ls_label_temp):
    print label_temp, len(df_temp)
    ecdf = ECDF(df_temp['pct_rr'])
    y = ecdf(x)
    ax.step(x, y, label = label_temp)
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
