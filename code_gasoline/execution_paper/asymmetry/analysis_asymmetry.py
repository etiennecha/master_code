#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path_sub
from add_to_path_sub import path_data
from generic_master_price import *
from generic_master_info import *
import datetime, time
from BeautifulSoup import BeautifulSoup
import statsmodels.api as sm
import statsmodels.formula.api as smf

path_dir_rotterdam = os.path.join(path_data, 'data_gasoline', 'data_source', 'data_rotterdam')
path_dir_reuters = os.path.join(path_dir_rotterdam, 'data_reuters')
path_xls_reuters_diesel = os.path.join(path_dir_reuters, 'diesel_data_to_import.xls')
path_xml_ecb = os.path.join(path_dir_rotterdam, 'usd.xml')

path_dir_built_paper = os.path.join(path_data, 'data_gasoline', 'data_built', 'data_paper')

path_dir_built_json = os.path.join(path_dir_built_paper, 'data_json')
path_diesel_price = os.path.join(path_dir_built_json, 'master_price_diesel.json')
path_info = os.path.join(path_dir_built_json, 'master_info_diesel.json')
path_ls_ls_competitors = os.path.join(path_dir_built_json, 'ls_ls_competitors.json')
path_ls_tuple_competitors = os.path.join(path_dir_built_json, 'ls_tuple_competitors.json')

path_dir_source = os.path.join(path_data, 'data_gasoline', 'data_source')
path_dict_brands = os.path.join(path_dir_source, 'data_other', 'dict_brands.json')
path_csv_insee_data = os.path.join(path_dir_source, 'data_other', 'data_insee_extract.csv')

path_dir_insee = os.path.join(path_data, 'data_insee')
path_dict_dpts_regions = os.path.join(path_dir_insee, 'dpts_regions', 'dict_dpts_regions.json')

master_price = dec_json(path_diesel_price)
master_info = dec_json(path_info)
ls_ls_competitors = dec_json(path_ls_ls_competitors)
ls_tuple_competitors = dec_json(path_ls_tuple_competitors)
dict_brands = dec_json(path_dict_brands)
dict_dpts_regions = dec_json(path_dict_dpts_regions)

# ################
# BUILD DATAFRAMES
# ################

# DF REUTERS

reuters_diesel_excel_file = pd.ExcelFile(path_xls_reuters_diesel)
print 'Reuters excel file sheets:', reuters_diesel_excel_file.sheet_names
df_reuters_diesel = reuters_diesel_excel_file.parse('Feuil1', skiprows = 0,
                                                    header = 1, parse_dates = True)
df_reuters_diesel.set_index('Date', inplace = True)

ecb_xml_file = open(path_xml_ecb, 'r').read()
soup = BeautifulSoup(ecb_xml_file)
print 'ECB xml file row content:', dict(soup.findAll('obs')[0].attrs)
ls_ecb = [[pd.to_datetime(dict(obs.attrs)[u'time_period']), float(dict(obs.attrs)[u'obs_value'])]\
            for obs in soup.findAll('obs')]
df_ecb = pd.DataFrame(ls_ecb, columns = ['Date', 'ECB Rate ED'])
df_ecb.set_index('Date', inplace = True)

print '\nReuters data and ECB US/EUR exchange rate'
index = pd.date_range(start = pd.to_datetime('20110904'),
                      end   = pd.to_datetime('20130604'), 
                      freq='D')
df_cost = pd.DataFrame(None, index = index)
for df_temp in [df_ecb, df_reuters_diesel]:
  for column in df_temp:
    df_cost[column] = df_temp[column]
print '\n', df_cost.info()

litre_per_us_gallon = 3.785411784
litre_per_barrel = 158.987295
litre_per_metric_tonne = 1183.5

df_cost['ULSD 10 FOB MED EL'] = df_cost['ULSD 10 FOB MED DT'] /\
                                  litre_per_metric_tonne / df_cost['ECB Rate ED']
df_cost['ULSD 10 CIF NWE EL'] = df_cost['ULSD 10 CIF NWE DT'] /\
                                  litre_per_metric_tonne / df_cost['ECB Rate ED']
df_cost['GASOIL 0.2 FOB ARA EL'] = df_cost['GASOIL 0.2 FOB ARA DT'] / 1183.5 /\
                                     df_cost['ECB Rate ED']

# DF PRICES TTC

ar_diesel_price = np.array(master_price['diesel_price'], np.float64)
ls_index = [pd.to_datetime(date) for date in master_price['dates']]
df_prices_ttc = pd.DataFrame(ar_diesel_price.T, columns = master_price['ids'], index = ls_index)

# DF PRICES HT

df_prices_ht = pd.DataFrame.copy(df_prices_ttc)
# TODO: Corsica: VAT is 13% ? 
df_prices_ht = df_prices_ht / 1.196 - 0.4419

ls_tax_11 = [(1,7,26,38,42,69,73,74,75,77,78,91,92,93,94,95,4,5,6,13,83,84), # (PrixTTC-0.4419+0.0135)/1.196
              (16,17,79,86)] # (PrixTTC-0.4419+0.0250)/1.196
# 2011 else: (PrixTTC-0.4419)/1.196
ls_tax_12 = [(1,7,26,38,42,69,73,74), # (PrixTTC-0.4419+0.0135)/1.196
              (16,17,79,86)] # (PrixTTC-0.4419+0.0250)/1.196
# 2012 - 2013 else: (PrixTTC-0.4419)/1.196
# All: VAT ... but temporary tax cut

df_prices_ht_2011 = df_prices_ht.ix[:'2011-12-31']
for indiv_id in df_prices_ht_2011.columns:
  if indiv_id[:-6] in ls_tax_11[0]:
    df_prices_ht_2011[indiv_id] = df_prices_ht_2011[indiv_id].apply(lambda x: x + 0.0135)
  elif indiv_id[:-6] in ls_tax_11[1]:
    df_prices_ht_2011[indiv_id] = df_prices_ht_2011[indiv_id].apply(lambda x: x + 0.0250)

df_prices_ht_2012 = df_prices_ht.ix['2012-01-01':]
for indiv_id in df_prices_ht_2012.columns:
  if indiv_id[:-6] in ls_tax_12[0]:
    df_prices_ht_2012[indiv_id] = df_prices_ht_2012[indiv_id].apply(lambda x: x + 0.0135)
  elif indiv_id[:-6] in ls_tax_12[1]:
    df_prices_ht_2012[indiv_id] = df_prices_ht_2012[indiv_id].apply(lambda x: x + 0.0250)

df_prices_ht.ix['2012-08-31':'2012-11-30'] = df_prices_ht.ix['2012-08-31':'2012-11-30'] + 0.03
df_prices_ht.ix['2012-12-01':'2012-12-11'] = df_prices_ht.ix['2012-12-01':'2012-12-11'] + 0.02
df_prices_ht.ix['2012-12-11':'2012-12-21'] = df_prices_ht.ix['2012-12-11':'2012-12-21'] + 0.015
df_prices_ht.ix['2012-12-21':'2013-01-11'] = df_prices_ht.ix['2012-12-21':'2013-01-11'] + 0.01

# DF INFO

dict_std_brands = {v[0]: v for k, v in dict_brands.items()}

ls_services = [service for indiv_id, indiv_info in master_info.items()\
                 if indiv_info['services'][-1] for service in indiv_info['services'][-1]]
ls_services = list(set(ls_services))
for indiv_id, indiv_info in master_info.items():
  # Caution [] and None are false but different here
  if indiv_info['services'][-1] is not None:
    ls_station_services = [0 for i in ls_services]
    for service in indiv_info['services'][-1]:
      service_ind = ls_services.index(service)
      ls_station_services[service_ind] = 1
  else:
    ls_station_services = [None for i in ls_services]
  master_info[indiv_id]['list_service_dummies'] = ls_station_services

ls_ls_info = []
for indiv_ind, indiv_id in enumerate(master_price['ids']):
  # from master_price
  indiv_dict_info = master_price['dict_info'][indiv_id]
  city = indiv_dict_info['city']
  zip_code = '%05d' %int(indiv_id[:-3]) # TODO: improve if must be used alone
  region = dict_dpts_regions[zip_code[:2]]
  code_geo = indiv_dict_info.get('code_geo')
  code_geo_ardts = indiv_dict_info.get('code_geo_ardts')
  brand_1_b = indiv_dict_info['brand_std'][0][0]
  brand_2_b = dict_std_brands[indiv_dict_info['brand_std'][0][0]][1]
  brand_type_b = dict_std_brands[indiv_dict_info['brand_std'][0][0]][2]
  brand_1_e = indiv_dict_info['brand_std'][-1][0]
  brand_2_e = dict_std_brands[indiv_dict_info['brand_std'][-1][0]][1]
  brand_type_e = dict_std_brands[indiv_dict_info['brand_std'][-1][0]][2]
  # from master_info
  highway, hours = None, None
  ls_service_dummies = [None for i in ls_services]
  if master_info.get(indiv_id):
    highway = master_info[indiv_id]['highway'][3]
    hours = master_info[indiv_id]['hours'][-1]
    ls_service_dummies = master_info[indiv_id]['list_service_dummies']
  ls_ls_info.append([city, zip_code, code_geo, code_geo_ardts, region,
                     brand_1_b, brand_2_b, brand_type_b,
                     brand_1_e, brand_2_e, brand_type_e,
                     highway, hours] + ls_service_dummies)
ls_columns = ['city', 'zip_code', 'code_geo', 'code_geo_ardts', 'region',
              'brand_1_b', 'brand_2_b', 'brand_type_b',
              'brand_1_e', 'brand_2_e', 'brand_type_e',
              'highway', 'hours'] + ls_services
df_info = pd.DataFrame(ls_ls_info, master_price['ids'], ls_columns)
print '\n', df_info.info()

df_info['dpt'] = df_info['code_geo'].map(lambda x: x[:2] if x else None)

# Exclude highway and Corse from df_info, df_prices_ttc, df_prices_ht
df_info = df_info[(df_info['highway'] != 1) &\
                  (df_info['region'] != 'Corse')]

df_prices_ttc = df_prices_ttc[df_info.index]
df_prices_ht = df_prices_ht[df_info.index]

# ########
# ANALYSIS
# ########

# not sure if need to keep this... compare UFIP for robustness if needed
df_cost_nowe = df_cost[~((df_cost.index.weekday == 5) | (df_cost.index.weekday == 6))]
df_cost_nowe['ULSD 10 CIF NWE S1 EL'] = df_cost_nowe['ULSD 10 CIF NWE EL'].shift(1)
df_cost_nowe['ULSD 10 CIF NWE S1 R5 EL'] = pd.stats.moments.rolling_apply(
                                             df_cost_nowe['ULSD 10 CIF NWE S1 EL'], 5,
                                             lambda x: x[~pd.isnull(x)].mean(), 2)
df_cost['ULSD 10 CIF NWE S1 R5 EL'] = df_cost_nowe['ULSD 10 CIF NWE S1 R5 EL']

# DF AGG : aggregate prices series
df_agg = df_cost[['ULSD 10 FOB MED EL', 'ULSD 10 CIF NWE EL', 'ULSD 10 CIF NWE S1 R5 EL']]
df_agg['price_ht'] = df_prices_ht.mean(axis = 1)
df_agg['margin_a'] = df_agg['price_ht'] - df_agg['ULSD 10 CIF NWE EL']
df_agg['margin_b'] = df_agg['price_ht'] - df_agg['ULSD 10 CIF NWE S1 R5 EL']
# spaces in variable names seem not to be tolerated by formula
df_agg['cost_a'] = df_agg['ULSD 10 CIF NWE EL']
df_agg['cost_b'] = df_agg['ULSD 10 CIF NWE S1 R5 EL']
# dummy july + measure, dummy tax_cut
df_agg['dum_taxcut'] = 0
df_agg['dum_taxcut'].ix['2012-08-31':'2013-01-11'] = 1
df_agg['dum_july_taxcut'] = 0
df_agg['dum_july_taxcut'].ix['2012-07-31':'2013-01-11'] = 1

# Need to rationalize
ls_ls_reg_res = []
for cost in ['cost_a', 'cost_b']:
  ls_formulas = ['price_ht ~ %s' %cost,
                 'price_ht ~ %s + dum_taxcut' %cost,
                 'price_ht ~ %s + dum_july_taxcut' %cost]
  ls_reg_res = [smf.ols(str_formula, missing ='drop', data = df_agg).fit()\
                  for str_formula in ls_formulas]
  ls_ls_reg_res.append(ls_reg_res)

se_est_a = ls_ls_reg_res[0][-1].predict(sm.add_constant(df_agg[["cost_a", "dum_july_taxcut"]]),
                                          transform=False)
se_est_b = ls_ls_reg_res[1][-1].predict(sm.add_constant(df_agg[["cost_b", "dum_july_taxcut"]]),
                                          transform=False)
plt.plot(se_est_a)
plt.plot(se_est_b)
plt.plot(df_agg['price_ht'])
plt.show()

reg01 = smf.ols('price_ht ~ cost_a', missing = 'drop', data = df_agg[0:200]).fit().summary()

# brand (looks only at firm which don't change brand right now)
for brand in ['TOTAL', 'MOUSQUETAIRES', 'CARREFOUR', 'SYSTEMEU', 'ESSO']:
  ls_ind_brand = df_info.index[(df_info['brand_2_e'] == '%s' %brand) &\
                             (df_info['brand_2_b'] == '%s' %brand)]
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
from matplotlib import rcParams
rcParams['font.family'] = 'serif'
rcParams['font.serif'] = ['Computer Modern Roman']
rcParams['text.usetex'] = True
rcParams['pgf.texsystem'] = 'pdflatex'

#from pylab import *
#rcParams['figure.figsize'] = 16, 6

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
#df_agg['resid_ESSO'] = smf.ols('price_ht_ESSO~cost_a_l4', df_agg, missing='drop').fit().resid
#df_agg['pred_ESSO'] = df_agg['price_ht_ESSO'] - df_agg['resid_ESSO']
#df_agg[['pred_ESSO', 'price_ht_ESSO']].plot()
#plt.show()

## Explore groups
#df_info['brand_1_b'][df_info['brand_2_b'] == df_info['brand_2_e']].value_counts()

# Asymetry regressions

zero = 0.00000000001
df_agg = df_agg[:'2012-06']
#df_agg = df_agg['2012-08':]

# Pbm with missing data... need to fillna (or not necessarily if moving average)
df_agg['cost_a_f'] = df_agg['cost_a'].fillna(method='pad')
## Too volatile: can't proceed with raw cost => Moving averages... but then asymmetry?
#df_agg['cost_a_f'] = pd.rolling_mean(df_agg['cost_a'], 4, min_periods = 2)
# could do following step becore filling na...
df_agg['resid'] = smf.ols('price_ht~cost_a', df_agg, missing='drop').fit().resid
df_agg['cost_a_l3'] = df_agg['cost_a'].shift(3)
df_agg['resid_l3'] = smf.ols('price_ht~cost_a_l3', df_agg, missing='drop').fit().resid
# ok not error autocorrelation

## Cost variations only
#ls_cost_d = []
#ls_cost_d_sign = []
#for i in range(1, 20):
#  df_agg['cost_a_d%s' %(i-1)] = df_agg['cost_a_f'].shift(i-1) - df_agg['cost_a_f'].shift(i)
#  ls_cost_d.append('cost_a_d%s' %(i-1))
#  df_agg['cost_a_d%s_p' %(i-1)] = 0
#  df_agg['cost_a_d%s_p' %(i-1)][df_agg['cost_a_d%s' %(i-1)] > 0 + 0.000000001]  = df_agg['cost_a_d%s' %(i-1)]
#  df_agg['cost_a_d%s_n' %(i-1)] = 0
#  df_agg['cost_a_d%s_n' %(i-1)][df_agg['cost_a_d%s' %(i-1)] < 0 - 0.000000001] = df_agg['cost_a_d%s' %(i-1)]
#  ls_cost_d_sign.append('cost_a_d%s_p' %(i-1))
#  ls_cost_d_sign.append('cost_a_d%s_n' %(i-1))
#df_agg['price_ht_d0' ] = df_agg['price_ht'] - df_agg['price_ht'].shift(1)
## or 4:30
#reg0 = smf.ols('price_ht_d0 ~ resid + ' + '+'.join(ls_cost_d_sign[4:34]),
#               df_agg, missing = 'drop').fit()
#print reg0.summary()
#
#import statsmodels.tsa.stattools as ts
## should improve nan treatment probably...
#ts.adfuller(df_agg['resid'][~pd.isnull(df_agg['resid'])])
#
#df_agg['price_ht_d0_res'] = reg0.resid
#df_agg['price_ht_d0_pred'] = df_agg['price_ht_d0'] - df_agg['price_ht_d0_res']
#df_agg[['price_ht_d0', 'price_ht_d0_pred']].plot()
#plt.show()

#
#se_params = reg0.params
#se_params_p = se_params[se_params.index.map(lambda x: x[-1] == 'p')]
#se_params_n = se_params[se_params.index.map(lambda x: x[-1] == 'n')]
#df_adj = pd.DataFrame(zip(se_params_p.cumsum(), se_params_n.cumsum()),
#                      columns = ['pos', 'neg'])
#df_adj.plot()
#plt.show()

## Cost and Retail variations
#ls_cost_d = []
#ls_retail_d = []
#ls_cost_d_sign = []
#ls_retail_d_sign = []
#for i in range(1, 20):
#  # Cost variations
#  df_agg['cost_a_d%s' %(i-1)] = df_agg['cost_a_f'].shift(i-1) - df_agg['cost_a_f'].shift(i)
#  ls_cost_d.append('cost_a_d%s' %(i-1))
#  df_agg['cost_a_d%s_p' %(i-1)] = 0
#  df_agg['cost_a_d%s_p' %(i-1)][df_agg['cost_a_d%s' %(i-1)] > zero]  = df_agg['cost_a_d%s' %(i-1)]
#  df_agg['cost_a_d%s_n' %(i-1)] = 0
#  df_agg['cost_a_d%s_n' %(i-1)][df_agg['cost_a_d%s' %(i-1)] < -zero] = df_agg['cost_a_d%s' %(i-1)]
#  ls_cost_d_sign.append('cost_a_d%s_p' %(i-1))
#  ls_cost_d_sign.append('cost_a_d%s_n' %(i-1))
#  # Retail price variations
#  df_agg['price_ht_d%s' %(i-1)] = df_agg['price_ht'].shift(i-1) - df_agg['price_ht'].shift(i)
#  ls_retail_d.append('price_ht_d%s' %(i-1))
#  df_agg['price_ht_d%s_p' %(i-1)] = 0
#  df_agg['price_ht_d%s_p' %(i-1)][df_agg['price_ht_d%s' %(i-1)] > zero] = df_agg['price_ht_d%s' %(i-1)]
#  df_agg['price_ht_d%s_n' %(i-1)] = 0
#  df_agg['price_ht_d%s_n' %(i-1)][df_agg['price_ht_d%s' %(i-1)] < -zero] = df_agg['price_ht_d%s' %(i-1)]
#  ls_retail_d_sign.append('price_ht_d%s_p' %(i-1))
#  ls_retail_d_sign.append('price_ht_d%s_n' %(i-1))
#df_agg['price_ht_d0' ] = df_agg['price_ht'] - df_agg['price_ht'].shift(1)
## or 4:30
#reg1 = smf.ols('price_ht_d0 ~ resid + ' +\
#               '+'.join(ls_cost_d_sign[0:28]) + '+' + \
#               '+'.join(ls_retail_d_sign[2:6]),
#               df_agg, missing = 'drop').fit()
#print reg1.summary()
#df_agg['price_ht_d0_res_2'] = reg1.resid
#df_agg['price_ht_d0_pred_2'] = df_agg['price_ht_d0'] - df_agg['price_ht_d0_res_2']
#df_agg[['price_ht_d0', 'price_ht_d0_pred_2']].plot()
#plt.show() # print both residuals and prev vs. actual on graph
#
#df_agg['price_ht_d0_res_2_l1']= df_agg['price_ht_d0_res_2'].shift(1)
#print df_agg[['price_ht_d0_res_2_l1', 'price_ht_d0_res_2']].corr()
#print smf.ols('price_ht_d0_res_2~price_ht_d0_res_2_l1', df_agg, missing='drop').fit().summary()

#se_params = reg0.params
#se_params_p = se_params[se_params.index.map(lambda x: x[-1] == 'p')]
#se_params_n = se_params[se_params.index.map(lambda x: x[-1] == 'n')]
#df_adj = pd.DataFrame(zip(se_params_p.cumsum(), se_params_n.cumsum()),
#                      columns = ['pos', 'neg'])
#df_adj.plot()
#plt.show()

# ##########################
# TO BE MOVED SOMEWHERE ELSE
# ##########################

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
