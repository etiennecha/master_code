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

path_dir_built_other = os.path.join(path_data,
                                    u'data_gasoline',
                                    u'data_built',
                                    u'data_other')
path_dir_built_other_csv = os.path.join(path_dir_built_other, 'data_csv')

path_dir_built_dis = os.path.join(path_data,
                                  u'data_gasoline',
                                  u'data_built',
                                  u'data_dispersion')
path_dir_built_dis_csv = os.path.join(path_dir_built_dis, u'data_csv')
path_dir_built_dis_json = os.path.join(path_dir_built_dis, u'data_json')

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

# DF COST (WHOLESALE GAS PRICES)
df_cost = pd.read_csv(os.path.join(path_dir_built_other_csv,
                                   'df_quotations.csv'),
                                 encoding = 'utf-8',
                                 parse_dates = ['date'])
df_cost.set_index('date', inplace = True)

# GEN LOW PRICE AND HIGH PRICE MARKETS
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

dict_nb_c_3km = {}
for k,v in dict(list(dict_ls_comp_low.items())  +\
                list(dict_ls_comp_high.items())).items(): 
  dict_nb_c_3km[k] = [(id_comp, dist) for id_comp, dist in v if dist <= 3]

df_nb_comp = pd.DataFrame([[k, len(v) + 1] for k,v in dict_nb_c_3km.items()],
                          columns = ['id_station', 'nb_c_3km'])

# #########################
# GET DF MARKET DISPERSION
# #########################

## PARAMETERS
#km_bound = 5
#ls_markets = get_ls_ls_market_ids(dict_ls_comp, km_bound)
#ls_markets_st = get_ls_ls_market_ids_restricted(dict_ls_comp, km_bound)
#ls_markets_st_rd = get_ls_ls_market_ids_restricted(dict_ls_comp, km_bound, True)

# MEAN NAT PRICE (RAW)
se_mean_price = df_prices_ttc.mean(1) * 100

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

# for each market:
# market desc: (max) nb firms, mean nb firms observed,
# dispersion: mean- range / gfs / std / gfs
# finally: display mean and std over all markets
# alternatively: Tappata approach : mean over all market-days, not markets


ls_df_market_stats, ls_se_disp_mean, ls_se_disp_std = [], [], []
ls_df_mds = []
for title, df_prices, ls_markets_temp in ls_loop_markets[7:8]:
  
  print()
  print(title)
  
  ls_df_md = []
  # Euros to cent
  df_prices = df_prices * 100
  
  ls_df_market_dispersion =\
    [get_market_price_dispersion(market_ids, df_prices, ddof = 1.5)\
          for market_ids in ls_markets_temp]
  
    # cv useless when using residual prices (div by almost 0)
  ls_stats = ['range', 'gfs', 'std', 'cv', 'nb_comp', 'nb_comp_t']
  ls_ls_market_stats = []
  ls_market_ref_ids = []
  for ls_market_ids, df_market_dispersion in zip(ls_markets_temp, ls_df_market_dispersion):
    if len(df_market_dispersion) > 0:
      df_md = df_market_dispersion[(df_market_dispersion['nb_comp'] >= 3) &\
                                   (df_market_dispersion['nb_comp_t']/\
                                    df_market_dispersion['nb_comp'].astype(float)\
                                      >= 2.0/3)].copy()
      if len(df_md) > 90:
        df_md['id'] = ls_market_ids[0]
        df_md['price'] = se_mean_price # index pbm?
        df_md['date'] = df_md.index
        ls_df_md.append(df_md)
        ## Save average/std for this local market
        #ls_ls_market_stats.append([df_md[field].mean()\
        #                            for field in ls_stats] +\
        #                          [df_md[field].std()\
        #                            for field in ls_stats] +\
        #                          [len(df_md)])
        #ls_market_ref_ids.append(ls_market_ids[0])
  
  ## Summary table for each local market
  #ls_columns = ['avg_%s' %field for field in ls_stats]+\
  #             ['std_%s' %field for field in ls_stats]+\
  #             ['nb_obs']
  #df_market_stats = pd.DataFrame(ls_ls_market_stats, ls_market_ref_ids, ls_columns)
  #ls_df_market_stats.append(df_market_stats)

  # Build dfs of local markets
  df_mds = pd.concat(ls_df_md, ignore_index = True)
  # add cost
  df_mds.set_index('date', inplace = True)
  df_mds['cost'] =  df_cost['UFIP RT Diesel R5 EL'] * 100
  df_mds.reset_index(drop = False, inplace = True)

  # Drop if margin chge around
  df_mds = df_mds[~df_mds['id'].isin(ls_drop_3km)]
  
  # Restrict to one or two day(s) per week: robustness checks
  df_md.set_index('date', inplace = True)
  df_md['dow'] = df_md.index.dayofweek
  df_md.reset_index(drop = False, inplace = True)
  df_md = df_md[(df_md['dow'] == 2) | (df_md['dow'] == 4)] # Friday
  df_mds = df_mds[~df_mds['cost'].isnull()]
  
  # Prepare vars for clustering
  df_mds['str_date'] = df_mds['date'].apply(lambda x: x.strftime('%Y%m%d'))
  df_mds['int_date'] = df_mds['str_date'].astype(int)
  df_mds['int_id'] = df_mds['id'].astype(int)
  
  df_mds = pd.merge(df_mds,
                    df_nb_comp,
                    left_on = 'id',
                    right_on = 'id_station',
                    how = 'left')
  # LOW => HIGH were discarded...
  df_mds = df_mds[~df_mds['nb_c_3km'].isnull()]

  #df_mds = df_mds[df_mds['nb_comp'] <= 15]

  # ls_df_mds.append(df_mds)
  
  # REGRESSIONS
  ls_res, ls_names = [], []
  for title_temp, df_temp in [['All', df_mds],
                              ['Before', df_mds[df_mds['date'] <= '2012-07-01']],
                              ['After', df_mds[df_mds['date'] >= '2013-02-01']]]:
    #print()
    #print('-'*60)
    #print(title_temp)
    #print()
    for disp_stat in ['range', 'std']:
      formula = '{:s} ~ cost + nb_c_3km'.format(disp_stat)
      res = smf.ols(formula,
                     data = df_temp).fit()
      res = res.get_robustcov_results(cov_type = 'cluster',
                                      groups = df_temp[['int_id', 'int_date']].values,
                                      use_correction = True)
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
  print(su)
