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

# DF COMP

df_comp = pd.read_csv(os.path.join(path_dir_built_csv,
                                   'df_comp.csv'),
                               encoding = 'utf-8',
                               dtype = {'id_station' : str})
df_comp.set_index('id_station', inplace = True)

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
# todo check 95230007
ls_discounter = ['ELF', 'ESSO_EXPRESS', 'TOTAL_ACCESS']
df_info.loc[df_info['brand_last'].isin(ls_discounter),
             'group_type_last'] = 'DIS'
df_info.loc[(df_info['brand_0'].isin(ls_discounter)) |\
            (df_info['brand_last'] == 'ESSO_EXPRESS'),
             'group_type'] = 'DIS'
# should exclude margin chge stations?

df_info['type_last'] = 'HIGH'
df_info.loc[(df_info['brand_last'].isin(ls_discounter)) |\
            (df_info['group_type_last'] == 'SUP'),
            'type_last'] = 'LOW'

df_info['type'] = 'HIGH'
df_info.loc[(df_info['brand_0'].isin(ls_discounter)) |\
            (df_info['brand_last'] == 'ESSO_EXPRESS') |\
            (df_info['group_type'] == 'SUP'),
            'type'] = 'LOW'

set_low_ids = set(df_info[(df_info['type'] == 'LOW') &\
                          (df_info['type_last'] == 'LOW')].index)
set_high_ids = set(df_info[(df_info['type'] == 'HIGH') &\
                           (df_info['type_last'] == 'HIGH')].index)
dict_ls_comp_low, dict_ls_comp_high = {}, {}
for k, v in dict_ls_comp.items():
  if k in set_low_ids:
    dict_ls_comp_low[k] = [(id_comp, dist) for id_comp, dist in v if id_comp in set_low_ids]
  elif k in set_high_ids:
    dict_ls_comp_high[k] = [(id_comp, dist) for id_comp, dist in v if id_comp in set_high_ids]
# could gain efficiency by restricting distance first and using set intersections

#Nb comp of same type
dict_nb_c_3km = {}
for k,v in dict(list(dict_ls_comp_low.items())  +\
                list(dict_ls_comp_high.items())).items(): 
  dict_nb_c_3km[k] = [(id_comp, dist) for id_comp, dist in v if dist <= 3]

df_nb_comp = pd.DataFrame([[k, len(v)] for k,v in dict_nb_c_3km.items()],
                          columns = ['id_station', 'nb_c_3km'])
df_nb_comp.set_index('id_station', inplace = True)

# ###########################
# ALTERNATIVE PRICE CLEANING
# ###########################

# - low / high series by region
# - then station FE (mean)
# - see if series look more like noise

ind_drop = df_info[((df_info['reg'].isnull()) |\
                    (df_info['type'].isnull())) |\
                   (df_info['type_last'] != df_info['type'])].index
print('Nb dropped', len(ind_drop))
df_info = df_info.loc[~df_info.index.isin(ind_drop)]
df_prices_ttc.drop(list(ind_drop), axis = 1, inplace = True)
ls_cl_drop = list(set(df_prices_cl.columns).intersection(set(ind_drop)))
df_prices_cl.drop(ls_cl_drop, axis = 1, inplace = True)

dict_trends = {}
for reg_type, df_reg_type in df_info.groupby(['reg', 'type']):
  se_mp = df_prices_ttc[df_reg_type.index].mean(1)
  dict_trends[reg_type] = se_mp

ls_ids, ls_se_prices = [], []
for id_station, se_prices_ttc in df_prices_ttc.iteritems():
  reg_type = tuple(df_info.ix[id_station][['reg', 'type']].values)
  se_prices = se_prices_ttc - dict_trends[reg_type]
  ls_ids.append(id_station)
  ls_se_prices.append(se_prices)
df_prices_cl2 = pd.concat(ls_se_prices,
                          keys  = ls_ids,
                          axis = 1)
df_prices_cl2 = df_prices_cl2.apply(lambda row: row - row.mean(), axis = 0)

# #########################
# STATION LEVEL DISPERSION
# #########################

#df_prices = df_prices_cl2 * 100
df_prices = df_prices_cl * 100
#df_prices = df_prices_ttc * 100

# Robustness check: restrict period
df_prices = df_prices.ix['2013-02-01':'2014-08-30']
df_prices = df_prices.ix['2013-02-01':]
#df_prices = df_prices.ix[:'2012-07-01':]

# Robustness check: use price only upon change
df_chges = df_prices_ttc - df_prices_ttc.shift(1)
df_prices_uc = df_prices[df_chges.abs() > 1e-5]

ls_rows_disp, ls_ids = [], []
for id_station in df_prices.columns:
  se_prices_all = df_prices[id_station][~df_prices[id_station].isnull()]
  price_mean = se_prices_all.mean()
  # choose if keep only prices upon change or not (but then cv has no meaning?)
  se_prices = df_prices[id_station][~df_prices[id_station].isnull()]
  # keep only if observed every day (adhoc condition here... check nb missing)
  if len(se_prices_all) == 532:
    se_prices_a = se_prices[(se_prices >= se_prices.quantile(q=0.025)) &\
                            (se_prices <= se_prices.quantile(q=0.975))]
    se_prices_b = se_prices[(se_prices >= se_prices.quantile(q=0.05)) &\
                            (se_prices <= se_prices.quantile(q=0.95))]
    price_std = se_prices.std()
    try:
      price_kurt = se_prices.kurtosis()
    except:
      price_kurt = np.nan
    try:
      price_skew = se_prices.skew()
    except:
      price_skew = np.nan
    ls_station_disp = [len(se_prices), price_mean, price_std, price_kurt, price_skew]
    for se_prices_temp in [se_prices, se_prices_a, se_prices_b]:
      price_range = se_prices_temp.max() - se_prices_temp.min()
      ls_station_disp += [price_range]
    ls_rows_disp.append(ls_station_disp)
    ls_ids.append(id_station)

ls_disp_cols = ['nb_obs', 'mean', 'std',
                'kurtosis', 'skew',
                'range_0', 'range_1', 'range_2']

df_disp = pd.DataFrame(ls_rows_disp,
                       columns = ls_disp_cols,
                       index = ls_ids)

df_disp['cv'] = df_disp['std'] / df_disp['mean'] * 100

df_disp = pd.merge(df_info,
                   df_disp,
                   how = 'left',
                   left_index = True,
                   right_index = True)

df_disp = pd.merge(df_disp,
                   df_comp,
                   how = 'left',
                   left_index = True,
                   right_index = True)

# Use nb competitors of same type => check impact
df_disp.drop('nb_c_3km', axis = 1, inplace = True)
df_disp['nb_c_3km'] = df_nb_comp['nb_c_3km']

#df_disp = df_disp[df_disp['nb_c_3km'] <= 15]

df_disp = df_disp[df_disp['nb_obs'] >= 100]
df_disp = df_disp[(~df_disp['std'].isnull()) &\
                  (~df_disp['range_1'].isnull()) &\
                  (~df_disp['nb_c_3km'].isnull()) &\
                  (~df_disp['dist_c'].isnull())]

# todo: nb_comp of same type, dist comp same type
for price_type in ['LOW', 'HIGH']:
  print()
  print(price_type)
  print(df_disp[ls_disp_cols][df_disp['type'] == price_type].describe().to_string())

# merge oil and ind
df_disp.loc[df_disp['group_type'] == 'IND',
            'group_type'] = 'OIL'

# get rid of obs with high nb comp count

ls_ls_regs_0 = [[df_disp, ['nb_c_3km + C(group_type)']],
                [df_disp, ['nb_c_3km + C(group_type) + C(reg)']],
                #[df_disp, ['dist_c * C(type)']],
                #[df_disp, ['dist_c * C(type)', 'C(reg)']],
                #[df_disp, ['dist_c * C(type)', 'C(reg)']],
                [df_disp, ['nb_c_3km:C(group_type)', 'C(group_type)']],
                [df_disp, ['nb_c_3km:C(group_type)', 'C(group_type)', 'C(reg)']]]

ls_ls_regs_1 = [[df_disp[df_disp['group_type'] == 'DIS'], ['nb_c_3km', 'C(reg)']],
                [df_disp[df_disp['group_type'] == 'OIL'], ['nb_c_3km', 'C(reg)']],
                [df_disp[df_disp['group_type'] == 'SUP'], ['nb_c_3km', 'C(reg)']]]

for ls_ls_regs in [ls_ls_regs_0, ls_ls_regs_1]:
  ls_res = []
  ls_names = []
  for df_temp, ls_idpt_vars in ls_ls_regs:
    #print()
    #print(smf.ols('std ~ ' + '+'.join(ls_idpt_vars),
    #      data = df_disp).fit().summary())
    #print()
    #print(smf.ols('range_1 ~' + '+'.join(ls_idpt_vars),
    #      data = df_disp).fit().summary())
    
    df_temp = df_temp[df_temp['nb_c_3km'] >= 2]
    df_temp = df_temp[df_temp['nb_c_3km'] <= 10]
    
    for idpt_var in ['cv', 'std', 'range_1']:
      res = smf.ols('{:s} ~ {:s}'.format(idpt_var, '+'.join(ls_idpt_vars)),
                    data = df_temp).fit(cov_type='cluster',
                                        cov_kwds={'groups': df_temp['reg']})
      ls_res.append(res)
      ls_names.append(idpt_var)
  
  su = summary_col(ls_res,
                   model_names = ls_names,
                   stars=True,
                   float_format='%0.2f',
                   info_dict={'N':lambda x: "{0:d}".format(int(x.nobs)),
                              'R2':lambda x: "{:.2f}".format(x.rsquared)})
  print(su)

# scipy.stats.mstats.normaltest(ls_se_prices[0][~ls_se_prices[0].isnull()])

#from scipy.stats import norm
#se_prices = df_prices[df_prices.columns[1]]
#se_prices = se_prices[~se_prices.isnull()]
#mu, std = norm.fit(se_prices)
#bins = plt.hist(se_prices.values, bins=25, normed=True, alpha=0.6, color='g')
#xmin, xmax = plt.xlim()
#x = np.linspace(xmin, xmax, 100)
#p = norm.pdf(x, mu, std)
#plt.plot(x, p, 'k', linewidth=2)
#plt.show()
#
### Data issues?
##print()
##print('Inspect possible data issues')
##print(df_disp[df_disp['range_0'] >= 20]\
##             [['brand_0', 'brand_last', 'range_0', 'std_0']].to_string())
##
### Inspect first and last change for all prices
##df_chge = df_prices_ttc - df_prices_ttc.shift(1)
##df_chge[df_chge.abs() <= 1e-5] = np.nan
##df_chge.fillna(method = 'backfill', axis = 0, inplace = True)
##df_chge.fillna(method = 'ffill', axis = 0, inplace = True)
##print(df_chge.ix[-1][df_chge.ix[-1].abs() >= 0.1]) # a few to fix
##print(df_chge.ix[0][df_chge.ix[0].abs() >= 0.1]) # no pbm
### issue otherwise
##se_test = df_chge.apply(lambda row: 1 if len(row[row.abs() > 0.15])> 0 else 0, axis = 0)
##print(se_test[se_test != 0])
#
#set_low_ids = set_low_ids.intersection(set(df_prices_ttc.columns))
#set_high_ids = set_high_ids.intersection(set(df_prices_ttc.columns))
#ax = df_prices_ttc[list(set_low_ids)].ix['2013-06-01'].plot(kind = 'hist',
#                                                            bins = 50,
#                                                            alpha = 0.5)
#df_prices_ttc[list(set_high_ids)].ix['2013-06-01'].plot(kind = 'hist',
#                                                        bins = 50,
#                                                        alpha = 0.5,
#                                                        ax=ax)
#plt.show()
