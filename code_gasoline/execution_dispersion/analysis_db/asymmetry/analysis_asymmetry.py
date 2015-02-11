#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
import datetime, time
import statsmodels.api as sm
import statsmodels.formula.api as smf

path_dir_built_paper = os.path.join(path_data,
                                    u'data_gasoline',
                                    u'data_built',
                                    u'data_paper_dispersion')

path_dir_built_csv = os.path.join(path_dir_built_paper, u'data_csv')

# ########################
# LOAD DF PRICES AND COSTS
# ########################

# LOAD DF COST
df_cost = pd.read_csv(os.path.join(path_dir_built_csv,
                                   'df_quotations.csv'),
                                 encoding = 'utf-8',
                                 parse_dates = ['date'])
df_cost.set_index('date', inplace = True)

# LOAD DF PRICES TTC
df_prices_ttc = pd.read_csv(os.path.join(path_dir_built_csv,
                                         'df_prices_ttc_final.csv'),
                        parse_dates = ['date'])
df_prices_ttc.set_index('date', inplace = True)

# LOAD DF PRICES HT
df_prices_ht = pd.read_csv(os.path.join(path_dir_built_csv,
                                         'df_prices_ht_final.csv'),
                        parse_dates = ['date'])
df_prices_ht.set_index('date', inplace = True)

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
                               'dpt' : str},
                      parse_dates = ['day_0', 'day_1', 'day_2'])
df_info.set_index('id_station', inplace = True)
df_info = df_info[df_info['highway'] != 1]

# ########
# ANALYSIS
# ########

# not sure if need to keep this... compare UFIP for robustness if needed
df_cost_nowe = df_cost[~((df_cost.index.weekday == 5) |\
                         (df_cost.index.weekday == 6))]
df_cost_nowe['ULSD 10 CIF NWE S1 EL'] = df_cost_nowe['ULSD 10 CIF NWE EL'].shift(1)
df_cost_nowe['ULSD 10 CIF NWE S1 R5 EL'] = pd.stats.moments.rolling_apply(
                                             df_cost_nowe['ULSD 10 CIF NWE S1 EL'], 5,
                                             lambda x: x[~pd.isnull(x)].mean(), 2)
df_cost['ULSD 10 CIF NWE S1 R5 EL'] = df_cost_nowe['ULSD 10 CIF NWE S1 R5 EL']

# DF AGG : aggregate prices series
df_agg = df_cost[['ULSD 10 FOB MED EL',
                  'ULSD 10 CIF NWE EL',
                  'ULSD 10 CIF NWE S1 R5 EL']]
df_agg['price_ht'] = df_prices_ht.mean(axis = 1)
df_agg['margin_a'] = df_agg['price_ht'] - df_agg['ULSD 10 CIF NWE EL']
df_agg['margin_b'] = df_agg['price_ht'] - df_agg['ULSD 10 CIF NWE S1 R5 EL']
# spaces in variable names seem not to be tolerated by formula
df_agg['cost_a'] = df_agg['ULSD 10 CIF NWE EL']
df_agg['cost_b'] = df_agg['ULSD 10 CIF NWE S1 R5 EL']
# dummy july + measure, dummy tax_cut
df_agg['dum_taxcut'] = 0
df_agg.loc['2012-08-31':'2013-01-11', 'dum_taxcut'] = 1
df_agg['dum_july_taxcut'] = 0
df_agg.loc['2012-07-31':'2013-01-11', 'dum_july_taxcut'] = 1

# Need to rationalize
ls_ls_reg_res = []
for cost in ['cost_a', 'cost_b']:
  ls_formulas = ['price_ht ~ %s' %cost,
                 'price_ht ~ %s + dum_taxcut' %cost,
                 'price_ht ~ %s + dum_july_taxcut' %cost]
  ls_reg_res = [smf.ols(str_formula, missing ='drop', data = df_agg).fit()\
                  for str_formula in ls_formulas]
  ls_ls_reg_res.append(ls_reg_res)

se_est_a = ls_ls_reg_res[0][-1].predict(sm.add_constant(df_agg[["cost_a",
                                                                "dum_july_taxcut"]]),
                                          transform=False)
se_est_b = ls_ls_reg_res[1][-1].predict(sm.add_constant(df_agg[["cost_b",
                                                                "dum_july_taxcut"]]),
                                          transform=False)
plt.plot(se_est_a)
plt.plot(se_est_b)
plt.plot(df_agg['price_ht'])
plt.show()

reg01 = smf.ols('price_ht ~ cost_a',
                missing = 'drop',
                data = df_agg[0:200]).fit().summary()

# brand (looks only at firm which don't change brand right now)
for brand in ['TOTAL', 'MOUSQUETAIRES', 'CARREFOUR', 'SYSTEMEU', 'ESSO']:
  ls_ind_brand = df_info.index[(df_info['brand_0'] == '%s' %brand) &\
                             (df_info['brand_0'] == '%s' %brand)]
  df_agg['price_ht_%s' %brand] = df_prices_ht[ls_ind_brand].mean(1)
  df_agg['margin_%s' %brand] = df_agg['price_ht_%s' %brand] - df_agg['cost_a']

# region

## Print prices and margin
#df_all.plot()
#plt.show()

## Graph with cost, average retail price, and margin
#
### Pb to get all 3 labels?
##ax = df_agg[['price_ht', 'ULSD 10 CIF NWE EL', 'margin_a']].plot(secondary_y = ['margin_a'])
##handles, labels = ax.get_legend_handles_labels()
##ax.legend(handles, ['Retail price before Tax', 'Rotterdam price', 'Retail margin'])
#
df_agg = df_agg[:'2012-06']

#import matplotlib as mpl
#mpl.rcParams['font.size'] = 10.
#mpl.rcParams['font.family'] = 'cursive'
#mpl.rcParams['font.cursive'] = 'Sand'
#mpl.rcParams['axes.labelsize'] = 8.
#mpl.rcParams['xtick.labelsize'] = 6.
#mpl.rcParams['ytick.labelsize'] = 6.

plt.rc('font', **{'serif': 'Computer Modern Roman'})

#http://damon-is-a-geek.com/publication-ready-the-first-time-beautiful-reproducible-plots-with-matplotlib.html
#from matplotlib import rcParams
#rcParams['font.family'] = 'serif'
#rcParams['font.serif'] = ['Computer Modern Roman']
#rcParams['text.usetex'] = True
#rcParams['pgf.texsystem'] = 'pdflatex'

from pylab import *
rcParams['figure.figsize'] = 16, 6

fig = plt.figure()
ax1 = fig.add_subplot(111)
# ax1 = plt.subplot(frameon=False)
line_1 = ax1.plot(df_agg.index, df_agg['price_ht'].values,
                  ls='--', c='b', label='Retail price before tax')
line_1[0].set_dashes([4,2])
line_2 = ax1.plot(df_agg.index, df_agg['ULSD 10 CIF NWE EL'].values,
                  ls='--', c= 'g', label=r'Rotterdam price')
line_2[0].set_dashes([8,2])
ax2 = ax1.twinx()
line_3 = ax2.plot(df_agg.index, df_agg['margin_a'].values,
                  ls='-', c='r', label=r'Retail gross margin (right axis)')

lns = line_1 + line_2 + line_3
labs = [l.get_label() for l in lns]
ax1.legend(lns, labs, loc=0)

ax1.grid()
#ax1.set_title(r"Daily diesel average prices and margin: September 2011 - July 2012")
ax1.set_ylabel(r"Price (euros)")
ax2.set_ylabel(r"Margin (euros)")
plt.tight_layout()
plt.show()

## Explore brand
#df_agg['cost_a_l4'] = df_agg['cost_a'].shift(4)
#df_agg['resid_ESSO'] = smf.ols('price_ht_ESSO ~ cost_a_l4',
#                               df_agg,
#                               missing='drop').fit().resid
#df_agg['pred_ESSO'] = df_agg['price_ht_ESSO'] - df_agg['resid_ESSO']
#df_agg[['pred_ESSO', 'price_ht_ESSO']].plot()
#plt.show()

## Explore groups
#df_info['brand_1_b'][df_info['brand_2_b'] == df_info['brand_2_e']].value_counts()

# Asymetry regressions

zero = 1e-10
df_agg = df_agg[:'2012-06']
#df_agg = df_agg['2012-08':]

# Pbm with missing data... need to fillna (or not necessarily if moving average)
df_agg['cost_a_f'] = df_agg['cost_a'].fillna(method='pad')
## Too volatile: can't proceed with raw cost => Moving averages... but then asymmetry?
#df_agg['cost_a_f'] = pd.rolling_mean(df_agg['cost_a'], 4, min_periods = 2)
# could do following step becore filling na...
df_agg['resid'] = smf.ols('price_ht ~ cost_a',
                          df_agg,
                          missing = 'drop').fit().resid
df_agg['cost_a_l3'] = df_agg['cost_a'].shift(3)
df_agg['resid_l3'] = smf.ols('price_ht ~ cost_a_l3',
                             df_agg,
                             missing='drop').fit().resid
# ok not error autocorrelation

# Cost variations only
ls_cost_d = []
ls_cost_d_sign = []
for i in range(1, 20):
  df_agg['cost_a_d%s' %(i-1)] = df_agg['cost_a_f'].shift(i-1) - df_agg['cost_a_f'].shift(i)
  ls_cost_d.append('cost_a_d%s' %(i-1))
  df_agg['cost_a_d%s_p' %(i-1)] = 0
  df_agg['cost_a_d%s_p' %(i-1)][df_agg['cost_a_d%s' %(i-1)] > zero]  = df_agg['cost_a_d%s' %(i-1)]
  df_agg['cost_a_d%s_n' %(i-1)] = 0
  df_agg['cost_a_d%s_n' %(i-1)][df_agg['cost_a_d%s' %(i-1)] < -zero] = df_agg['cost_a_d%s' %(i-1)]
  ls_cost_d_sign.append('cost_a_d%s_p' %(i-1))
  ls_cost_d_sign.append('cost_a_d%s_n' %(i-1))
df_agg['price_ht_d0' ] = df_agg['price_ht'] - df_agg['price_ht'].shift(1)
# or 4:30
reg0 = smf.ols('price_ht_d0 ~ resid + ' + '+'.join(ls_cost_d_sign[4:34]),
               df_agg, missing = 'drop').fit()
print reg0.summary()

import statsmodels.tsa.stattools as ts
# should improve nan treatment probably...
ts.adfuller(df_agg['resid'][~pd.isnull(df_agg['resid'])])

df_agg['price_ht_d0_res'] = reg0.resid
df_agg['price_ht_d0_pred'] = df_agg['price_ht_d0'] - df_agg['price_ht_d0_res']
df_agg[['price_ht_d0', 'price_ht_d0_pred']].plot()
plt.show()


se_params = reg0.params
se_params_p = se_params[se_params.index.map(lambda x: x[-1] == 'p')]
se_params_n = se_params[se_params.index.map(lambda x: x[-1] == 'n')]
df_adj = pd.DataFrame(zip(se_params_p.cumsum(), se_params_n.cumsum()),
                      columns = ['pos', 'neg'])
df_adj.plot()
plt.show()

# Cost and Retail variations
ls_cost_d = []
ls_retail_d = []
ls_cost_d_sign = []
ls_retail_d_sign = []
for i in range(1, 20):
  # Cost variations
  df_agg['cost_a_d%s' %(i-1)] = df_agg['cost_a_f'].shift(i-1) - df_agg['cost_a_f'].shift(i)
  ls_cost_d.append('cost_a_d%s' %(i-1))
  df_agg['cost_a_d%s_p' %(i-1)] = 0
  df_agg['cost_a_d%s_p' %(i-1)][df_agg['cost_a_d%s' %(i-1)] > zero]  = df_agg['cost_a_d%s' %(i-1)]
  df_agg['cost_a_d%s_n' %(i-1)] = 0
  df_agg['cost_a_d%s_n' %(i-1)][df_agg['cost_a_d%s' %(i-1)] < -zero] = df_agg['cost_a_d%s' %(i-1)]
  ls_cost_d_sign.append('cost_a_d%s_p' %(i-1))
  ls_cost_d_sign.append('cost_a_d%s_n' %(i-1))
  # Retail price variations
  df_agg['price_ht_d%s' %(i-1)] = df_agg['price_ht'].shift(i-1) - df_agg['price_ht'].shift(i)
  ls_retail_d.append('price_ht_d%s' %(i-1))
  df_agg['price_ht_d%s_p' %(i-1)] = 0
  df_agg['price_ht_d%s_p' %(i-1)][df_agg['price_ht_d%s' %(i-1)] > zero] = df_agg['price_ht_d%s' %(i-1)]
  df_agg['price_ht_d%s_n' %(i-1)] = 0
  df_agg['price_ht_d%s_n' %(i-1)][df_agg['price_ht_d%s' %(i-1)] < -zero] = df_agg['price_ht_d%s' %(i-1)]
  ls_retail_d_sign.append('price_ht_d%s_p' %(i-1))
  ls_retail_d_sign.append('price_ht_d%s_n' %(i-1))
df_agg['price_ht_d0' ] = df_agg['price_ht'] - df_agg['price_ht'].shift(1)
# or 4:30
reg1 = smf.ols('price_ht_d0 ~ resid + ' +\
               '+'.join(ls_cost_d_sign[0:28]) + '+' + \
               '+'.join(ls_retail_d_sign[2:6]),
               df_agg, missing = 'drop').fit()
print reg1.summary()
df_agg['price_ht_d0_res_2'] = reg1.resid
df_agg['price_ht_d0_pred_2'] = df_agg['price_ht_d0'] - df_agg['price_ht_d0_res_2']
df_agg[['price_ht_d0', 'price_ht_d0_pred_2']].plot()
plt.show() # print both residuals and prev vs. actual on graph

df_agg['price_ht_d0_res_2_l1']= df_agg['price_ht_d0_res_2'].shift(1)
print df_agg[['price_ht_d0_res_2_l1', 'price_ht_d0_res_2']].corr()
print smf.ols('price_ht_d0_res_2~price_ht_d0_res_2_l1', df_agg, missing='drop').fit().summary()

se_params = reg0.params
se_params_p = se_params[se_params.index.map(lambda x: x[-1] == 'p')]
se_params_n = se_params[se_params.index.map(lambda x: x[-1] == 'n')]
df_adj = pd.DataFrame(zip(se_params_p.cumsum(), se_params_n.cumsum()),
                      columns = ['pos', 'neg'])
df_adj.plot()
plt.show()

## ##########################
## TO BE MOVED SOMEWHERE ELSE
## ##########################
#
## Hist: all prices at day 0 (TODO: over time)
#min_x, max_x = 1.2, 1.6
#bins = np.linspace(min_x, max_x, (max_x - min_x) / 0.01 + 1)
#plt.hist(df_prices_ttc.ix[0][~pd.isnull(df_prices_ttc.ix[0])], bins = bins, alpha = 0.5)
#plt.show()
#
## Hist: supermarkets vs. oil (add ind?): first period
#
#ls_sup_ids = df_info.index[(df_info['brand_type_b'] == 'SUP') &\
#                           (df_info['brand_type_b'] == df_info['brand_type_e'])]
#ls_oil_ids = df_info.index[(df_info['brand_type_b'] == 'OIL') &\
#                           (df_info['brand_type_b'] == df_info['brand_type_e'])]
#
#plt.hist(df_prices_ttc[ls_sup_ids].ix[0][~pd.isnull(df_prices_ttc[ls_sup_ids].ix[0])],
#         bins = bins,
#         alpha = 0.5)
#plt.hist(df_prices_ttc[ls_oil_ids].ix[0][~pd.isnull(df_prices_ttc[ls_oil_ids].ix[0])],
#         bins = bins,
#         alpha = 0.5)
#plt.show()
#
## Hist: supermarkets vs. oil (add ind?): last period
#
#plt.hist(df_prices_ttc[ls_sup_ids].ix[-1][~pd.isnull(df_prices_ttc[ls_sup_ids].ix[0])],
#         bins = bins,
#         alpha = 0.5,
#         label = 'sup')
#plt.hist(df_prices_ttc[ls_oil_ids].ix[-1][~pd.isnull(df_prices_ttc[ls_oil_ids].ix[0])],
#         bins = bins,
#         alpha = 0.5,
#         label = 'oil')
#plt.show()
#
## Hist: oil companies
