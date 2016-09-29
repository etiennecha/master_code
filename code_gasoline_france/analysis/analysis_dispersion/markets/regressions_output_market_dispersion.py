#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
from generic_competition import *
import time
from statsmodels.iolib.summary2 import summary_col

path_dir_built = os.path.join(path_data,
                              u'data_gasoline',
                              u'data_built',
                              u'data_scraped_2011_2014')
path_dir_built_csv = os.path.join(path_dir_built, u'data_csv')
path_dir_built_json = os.path.join(path_dir_built, u'data_json')
path_dir_built_graphs = os.path.join(path_dir_built, u'data_graphs')

path_dir_built_dis = os.path.join(path_data,
                                  u'data_gasoline',
                                  u'data_built',
                                  u'data_dispersion')
path_dir_built_dis_csv = os.path.join(path_dir_built_dis, u'data_csv')
path_dir_built_dis_json = os.path.join(path_dir_built_dis, u'data_json')

path_dir_built_other = os.path.join(path_data,
                                    u'data_gasoline',
                                    u'data_built',
                                    u'data_other')
path_dir_built_other_csv = os.path.join(path_dir_built_other, 'data_csv')

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# ################
# LOAD DATA
# ################

# DF INFO
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

# DF STATION STATS
df_station_stats = pd.read_csv(os.path.join(path_dir_built_csv,
                                            'df_station_stats.csv'),
                               encoding = 'utf-8',
                               dtype = {'id_station' : str})
df_station_stats.set_index('id_station', inplace = True)

# DF MARGIN CHGE
df_margin_chge = pd.read_csv(os.path.join(path_dir_built_csv,
                                          'df_margin_chge.csv'),
                               encoding = 'utf-8',
                               dtype = {'id_station' : str})
df_margin_chge.set_index('id_station', inplace = True)

# COMPETITORS
dict_ls_comp = dec_json(os.path.join(path_dir_built_json,
                                     'dict_ls_comp.json'))

# STABLE MARKETS
ls_dict_stable_markets = dec_json(os.path.join(path_dir_built_json,
                                               'ls_dict_stable_markets.json'))
ls_robust_stable_markets = dec_json(os.path.join(path_dir_built_json,
                                                 'ls_robust_stable_markets.json'))
# 0 is 3km, 1 is 4km, 2 is 5km
ls_stable_markets = [stable_market for nb_sellers, stable_markets\
                       in ls_dict_stable_markets[2].items()\
                          for stable_market in stable_markets]

# DF PRICES
df_prices_ttc = pd.read_csv(os.path.join(path_dir_built_csv,
                                         'df_prices_ttc_final.csv'),
                        parse_dates = ['date'])
df_prices_ttc.set_index('date', inplace = True)

df_prices_ht = pd.read_csv(os.path.join(path_dir_built_csv,
                                        'df_prices_ht_final.csv'),
                        parse_dates = ['date'])
df_prices_ht.set_index('date', inplace = True)

df_prices_cl = pd.read_csv(os.path.join(path_dir_built_csv,
                                        'df_cleaned_prices.csv'),
                          parse_dates = ['date'])
df_prices_cl.set_index('date', inplace = True)

# FILTER DATA
# exclude stations with insufficient (quality) price data
df_filter = df_station_stats[~((df_station_stats['pct_chge'] < 0.03) |\
                               (df_station_stats['nb_valid'] < 90))]
ls_keep_ids = list(set(df_filter.index).intersection(\
                     set(df_info[(df_info['highway'] != 1) &\
                                 (df_info['reg'] != 'Corse')].index)))
#df_info = df_info.ix[ls_keep_ids]
#df_station_stats = df_station_stats.ix[ls_keep_ids]
#df_prices_ttc = df_prices_ttc[ls_keep_ids]
#df_prices_ht = df_prices_ht[ls_keep_ids]
#df_prices_cl = df_prices_cl[ls_keep_ids]

ls_drop_ids = list(set(df_prices_ttc.columns).difference(set(ls_keep_ids)))
df_prices_ttc[ls_drop_ids] = np.nan
df_prices_ht[ls_drop_ids] = np.nan
# highway stations may not be in df_prices_cl (no pbm here)
ls_drop_ids_nhw =\
  list(set(ls_drop_ids).difference(set(df_info[df_info['highway'] == 1].index)))
df_prices_cl[ls_drop_ids_nhw] = np.nan

# GEN LOW PRICE AND HIGH PRICE MARKETS
# pbm with chging discounters btw...
# (check with describe / hist if ok over time...)
df_info.loc['17240001', 'brand_last'] = 'TOTAL_ACCESS'
# temp fix ... todo check 95230007
ls_discounter = ['ELF', 'ESSO_EXPRESS', 'TOTAL_ACCESS']
df_info.loc[df_info['brand_last'].isin(ls_discounter),
             'group_type_last'] = 'DIS'
df_info.loc[df_info['brand_0'].isin(ls_discounter),
             'group_type'] = 'DIS'
# should exclude margin chge stations?

df_info['type_last'] = 'HIGH'
df_info.loc[(df_info['brand_last'].isin(ls_discounter)) |\
            (df_info['group_type_last'] == 'SUP'),
            'type_last'] = 'LOW'
df_info['type'] = 'HIGH'
df_info.loc[(df_info['brand_0'].isin(ls_discounter)) |\
            (df_info['group_type'] == 'SUP'),
            'type'] = 'LOW'

set_low_ids = set(df_info[(df_info['type'] == 'LOW') & (df_info['type_last'] == 'LOW')].index)
set_high_ids = set(df_info[(df_info['type'] == 'HIGH') & (df_info['type_last'] == 'HIGH')].index)
dict_ls_comp_low, dict_ls_comp_high = {}, {}
for k, v in dict_ls_comp.items():
  if k in set_low_ids:
    dict_ls_comp_low[k] = [(id_comp, dist) for id_comp, dist in v if id_comp in set_low_ids]
  elif k in set_high_ids:
    dict_ls_comp_high[k] = [(id_comp, dist) for id_comp, dist in v if id_comp in set_high_ids]
# could gain efficiency by restricting distance first and using set intersections

# GET MARKETS
dict_markets = {}
for km_bound in [1, 3, 5]:
  dict_markets['All_{:d}km'.format(km_bound)] =\
      get_ls_ls_market_ids(dict_ls_comp, km_bound)
  dict_markets['Restricted_{:d}km'.format(km_bound)] =\
      get_ls_ls_market_ids_restricted(dict_ls_comp, km_bound)
  dict_markets['Restricted_{:d}km_random'.format(km_bound)] =\
      get_ls_ls_market_ids_restricted(dict_ls_comp, km_bound, True)
  dict_markets['Low_{:d}km'.format(km_bound)] =\
      get_ls_ls_market_ids(dict_ls_comp_low, km_bound)
  dict_markets['High_{:d}km'.format(km_bound)] =\
      get_ls_ls_market_ids(dict_ls_comp_high, km_bound)

# GET MARKET DISPERSION
ls_loop_markets = [('3km_Raw_prices', df_prices_ttc, dict_markets['All_3km']),
                   ('3km_Residuals', df_prices_cl, dict_markets['All_3km']),
                   ('1km_Residuals', df_prices_cl, dict_markets['All_1km']),
                   ('5km_Raw_prices', df_prices_ttc, dict_markets['All_5km']),
                   ('5km_Residuals', df_prices_cl, dict_markets['All_5km']),
                   ('3km_Rest_Residuals', df_prices_cl, dict_markets['Restricted_3km']),
                   ('Stable_Markets_Raw_prices', df_prices_ttc, ls_stable_markets),
                   ('Stable_Markets_Residuals', df_prices_cl, ls_stable_markets),
                   ('Low_3km', df_prices_ttc, dict_markets['Low_3km']),
                   ('High_3km', df_prices_ttc, dict_markets['High_3km']),
                   ('Low_3km_Residuals', df_prices_cl, dict_markets['Low_3km']),
                   ('High_3km_Residuals', df_prices_cl, dict_markets['High_3km'])]

# DROP MARKETS WITH MARGIN CHGE (CENTER OR IN)
margin_chge_bound = 0.03
ls_ids_margin_chge =\
  df_margin_chge[df_margin_chge['value'].abs() >= margin_chge_bound].index
dict_ls_comp_3km = {x : [y[0] for y in ls_y if y[1] <= 3]\
                        for x, ls_y in dict_ls_comp.items()}
ls_drop_3km = [x for x, ls_y in dict_ls_comp_3km.items()\
                 if set(ls_y).intersection(set(ls_ids_margin_chge))]
ls_drop_3km = list(set(ls_drop_3km).union(ls_ids_margin_chge))

# interest: 0, 1, 6, 7, 8, 9 (or 10, 11?)
# keep for output:
# - reg with 3 km high and low - raw
# - reg with 3 km high and low - res
# - reg with stable markets - res

dict_df_mds = {}
for market_def in ls_loop_markets[1:2] + ls_loop_markets[6:]:
  title = market_def[0]
  df_md = pd.read_csv(os.path.join(path_dir_built_dis_csv,
                                   'df_market_dispersion_{:s}.csv'.format(title)),
                      encoding = 'utf-8',
                      parse_dates = ['date'],
                      dtype = {'id' : str})

  # Restrict to one or two day(s) per week: robustness checks
  df_md.set_index('date', inplace = True)
  df_md['dow'] = df_md.index.dayofweek
  df_md.reset_index(drop = False, inplace = True)
  df_md = df_md[(df_md['dow'] == 2) | (df_md['dow'] == 4)] # Friday
  
  # drop if margin chge around
  df_md = df_md[~df_md['id'].isin(ls_drop_3km)]
   
  # restrict max nb_comp
  df_md = df_md[df_md['nb_comp'] <= 10]

  # need to get rid of nan to be able to cluster
  df_md = df_md[~df_md['cost'].isnull()]
  df_md['str_date'] = df_md['date'].apply(lambda x: x.strftime('%Y%m%d'))
  df_md['int_date'] = df_md['str_date'].astype(int)
  df_md['int_id'] = df_md['id'].astype(int)

  # add trend
  dict_date = dict(zip(df_prices_ttc.index, range(len(df_prices_ttc.index))))
  df_md['trend'] = df_md['date'].apply(lambda x: dict_date[x])
  
  # create dummy for Low/High if necessary
  if ('Low' in title):
    df_md['d_high'] = 0
  elif ('High' in title):
    df_md['d_high'] = 1
  dict_df_mds[title] = df_md

dict_df_regs = {'all_res' : dict_df_mds['3km_Residuals'],
                'no_overlap_res' : dict_df_mds['Stable_Markets_Residuals']}
                
dict_df_regs['3km_lh_raw'] = pd.concat([dict_df_mds['Low_3km'],
                                        dict_df_mds['High_3km']])
dict_df_regs['3km_lh_res'] = pd.concat([dict_df_mds['Low_3km_Residuals'],
                                        dict_df_mds['High_3km_Residuals']])

# robustness checks for nb_comp
dict_df_regs['3km_l_res'] = dict_df_mds['Low_3km_Residuals'].copy()
dict_df_regs['3km_h_res'] = dict_df_mds['High_3km_Residuals'].copy()
dict_df_regs['3km_l_res'].drop('d_high', axis = 1, inplace = True)
dict_df_regs['3km_h_res'].drop('d_high', axis = 1, inplace = True)

for str_df in ['all_res',
               'no_overlap_res',
               #'3km_lh_raw',
               #'3km_lh_res',
               '3km_l_res',
               '3km_h_res']:

  df_md = dict_df_regs[str_df]
  #df_md = dict_df_regs['no_overlap_res']
  #df_md = df_md[df_md['nb_comp'] >= 4]
  
  # loop on each period
  ls_res, ls_names = [], []
  for title_temp, df_temp in [['All', df_md],
                              ['Before', df_md[df_md['date'] <= '2012-07-01']],
                              ['After', df_md[df_md['date'] >= '2013-02-01']]]:
    #print()
    #print('-'*60)
    #print(title_temp)
    #print()
    for disp_stat in ['range', 'std']:
      formula = '{:s} ~ trend + cost + nb_comp'.format(disp_stat)
      if 'd_high' in df_temp.columns:
        formula = formula + '+ d_high'
        # formula = formula + ' : C(d_high)'
      res = smf.ols(formula, data = df_temp).fit()
      res = res.get_robustcov_results(cov_type = 'cluster',
                                      groups = df_temp[['int_id', 'int_date']].values,
                                      use_correction = True)
      #print()
      #print(disp_stat)
      #print(res.summary())
      ls_res.append(res)
      ls_names.append(title_temp[0:2] + '-' + disp_stat)
  
  su = summary_col(ls_res,
                   model_names=ls_names,
                   stars=True,
                   float_format='%0.2f',
                   info_dict={'N':lambda x: "{0:d}".format(int(x.nobs)),
                              'R2':lambda x: "{:.2f}".format(x.rsquared)})

  print()
  print(str_df)
  print(su)

# toco: check if loss of signif. on cost using friday only due to insuff vars in cost?
# todo: check if there are markets with supermarkets / no supermarkets?

## Simulations: range and std increase in nb firms for same distribution?
#for i in range(10):
#  print()
#  nb_markets = 10000
#  df_sim = pd.DataFrame(np.random.normal(0, 0.01, (10000, 10)))
#  df_sim['nb_sellers'] = 3
#  for i in range(3, 11):
#    df_sim.loc[nb_markets/10*(i-1)+1:, 'nb_sellers'] = i
#  df_sim['range'] = df_sim.apply(lambda row: row[:int(row['nb_sellers'])].max() -\
#                                             row[:int(row['nb_sellers'])].min(),
#                                 axis = 1)
#  df_sim['std'] = df_sim.apply(lambda row: row[:int(row['nb_sellers'])].std(ddof = 1.5),
#                               axis = 1)
#
#  print(smf.ols('std ~ nb_sellers', df_sim).fit().summary())
#  for i in range(3, 11):
#  	print(df_sim[df_sim['nb_sellers'] == i]['std'].mean())
#
## degree of freedom of 1.3 seems to decrease the bias
