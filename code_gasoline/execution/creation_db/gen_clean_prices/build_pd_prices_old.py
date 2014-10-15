#!/usr/bin/python
# -*- coding: utf-8 -*-
import add_to_path_sub
from add_to_path_sub import path_data
from generic_master_price import *
from generic_master_info import *
from functions_string import *
from BeautifulSoup import BeautifulSoup
import xlrd
import itertools
import scipy
import pandas as pd
import patsy
import statsmodels.api as sm
import statsmodels.formula.api as smf
import time

path_dir_built_paper = os.path.join(path_data, 'data_gasoline', 'data_built', 'data_paper')

path_dir_built_json = os.path.join(path_dir_built_paper, 'data_json')
path_diesel_price = os.path.join(path_dir_built_json, 'master_price_diesel.json')
path_info = os.path.join(path_dir_built_json, 'master_info_diesel.json')
path_ls_ls_competitors = os.path.join(path_dir_built_json, 'ls_ls_competitors.json')
path_ls_tuple_competitors = os.path.join(path_dir_built_json, 'ls_tuple_competitors.json')

path_dir_built_graphs = os.path.join(path_dir_built_paper, 'data_graphs')
path_dir_brand_chges = os.path.join(path_dir_built_graphs, 'brand_changes')

path_dir_source = os.path.join(path_data, 'data_gasoline', 'data_source')
path_dict_brands = os.path.join(path_dir_source, 'data_other', 'dict_brands.json')
path_csv_insee_data = os.path.join(path_dir_source, 'data_other', 'data_insee_extract.csv')

path_dir_insee = os.path.join(path_data, 'data_insee')
path_dict_dpts_regions = os.path.join(path_dir_insee, 'dpts_regions', 'dict_dpts_regions.json')

path_dir_rotterdam = os.path.join(path_data, 'data_gasoline', 'data_source', 'data_rotterdam')
path_dir_reuters = os.path.join(path_dir_rotterdam, 'data_reuters')
path_xls_reuters_diesel = os.path.join(path_dir_reuters, 'diesel_data_to_import.xls')
path_xml_ecb = os.path.join(path_dir_rotterdam, 'usd.xml')

master_price = dec_json(path_diesel_price)
master_info = dec_json(path_info)
ls_ls_competitors = dec_json(path_ls_ls_competitors)
ls_tuple_competitors = dec_json(path_ls_tuple_competitors)
dict_brands = dec_json(path_dict_brands)
dict_dpts_regions = dec_json(path_dict_dpts_regions)

# GET AVERAGE PRICE
master_np_prices = np.array(master_price['diesel_price'], dtype = np.float32)
matrix_np_prices_ma = np.ma.masked_array(master_np_prices, np.isnan(master_np_prices))
ar_nb_valid_prices = np.ma.count(matrix_np_prices_ma, axis = 0) # would be safer to count nan..
ar_period_mean_prices = np.mean(matrix_np_prices_ma, axis = 0)
  
# #########################
# SERVICES (for INFO FILE)
# #########################

ls_listed_services = [service for indiv_id, indiv_info in master_info.items()\
                        if indiv_info['services'][-1] for service in indiv_info['services'][-1]]
ls_listed_services = list(set(ls_listed_services))
for indiv_id, indiv_info in master_info.items():
  if indiv_info['services'][-1] is not None:
    ls_station_services = [0 for i in ls_listed_services]
    for service in indiv_info['services'][-1]:
      service_ind = ls_listed_services.index(service)
      ls_station_services[service_ind] = 1
  else:
    ls_station_services = [None for i in ls_listed_services]
  master_info[indiv_id]['list_service_dummies'] = ls_station_services

# ######
# BRANDS
# ######
  
ls_ls_ls_brands = []
for i in range(3):
  ls_ls_brands =  [[[dict_brands[get_str_no_accent_up(brand)][i], period]\
                        for brand, period in master_price['dict_info'][id_indiv]['brand']]\
                          for id_indiv in master_price['ids']]
  ls_ls_brands = [get_expanded_list(ls_brands, len(master_price['dates'])) for ls_brands in ls_ls_brands]
  ls_ls_ls_brands.append(ls_ls_brands)
  
# #####################
# IMPORT INSEE DATA
# #####################

pd_df_insee = pd.read_csv(path_csv_insee_data, encoding = 'utf-8', dtype= str, tupleize_cols=False)
# exclude dom tom
pd_df_insee = pd_df_insee[~pd_df_insee[u'Département - Commune CODGEO'].str.contains('^97')]
pd_df_insee['Population municipale 2007 POP_MUN_2007'] =\
  pd_df_insee['Population municipale 2007 POP_MUN_2007'].apply(lambda x: float(x))

# ######################
# IMPORT UFIP DATA
# ######################

path_xlsx_ufip = os.path.join(path_dir_rotterdam, r'ufip-valeurs_2006-01-01_au_2013-12-31.xlsx')
ufip_excel_file = pd.ExcelFile(path_xlsx_ufip)
df_ufip = ufip_excel_file.parse('Worksheet')
df_ufip = df_ufip.set_index('Date')
# excel_file.sheet_names
print df_ufip.info()
df_ufip['date_str'] = map(lambda x: x.strftime('%Y%m%d'), df_ufip.index)
df_ufip.set_index('date_str', inplace=True)

# #######################
# TAXES
# #######################

# Base 2011-13: PrixTTC/1.196 - 0.4419
ls_tax_11 = [(1,7,26,38,42,69,73,74,75,77,78,91,92,93,94,95,4,5,6,13,83,84), # PrixTTC/1.196-0.4419+0.0135
              (16,17,79,86)] # PrixTTC/1.196-0.4419+0.0250
ls_tax_12 = [(1,7,26,38,42,69,73,74), # PrixTTC/1.196-0.4419+0.0135
              (16,17,79,86)] # PrixTTC/1.196-0.4419+0.0250

def get_tax_regime(dpt, ls_tup_regimes):
  dict_regime = dict(zip(range(96), [0 for i in range(96)]))
  for regime_ind, ls_regime_dpts in enumerate(ls_tup_regimes, start = 1):
    for regime in ls_regime_dpts:
      dict_regime[regime] = regime_ind
  return dict_regime[dpt] 

# ###########################################
# PRICE REGRESSION : ONE PERIOD CROSS SECTION
# ###########################################

#day_ind = 0
#ls_prices = [ls_prices[day_ind] for ls_prices in master_price['diesel_price']]
#ls_brands_std = [ls_brands[day_ind] for ls_brands in ls_ls_ls_brands[0]]
#ls_brands_gpd = [ls_brands[day_ind] for ls_brands in ls_ls_ls_brands[1]]
#ls_types      = [ls_brands[day_ind] for ls_brands in ls_ls_ls_brands[2]]
#dict_period = {'price' : ls_prices,
#               'brand' : ls_brands_gpd,
#               'type'  : ls_types}
#pd_period_prices = pd.DataFrame(dict_period, index = master_price['ids'])
#pd_period_prices['dpt'] =  pd_period_prices.index.map(lambda x: x[:-6])
#
#y,X = patsy.dmatrices('price ~ brand', pd_period_prices, return_type='dataframe')
#print sm.OLS(y, X, missing = 'drop').fit().summary()
#y,X = patsy.dmatrices('price ~ brand + C(dpt)', pd_period_prices, return_type='dataframe')
#print sm.OLS(y, X, missing = 'drop').fit().summary()
## TODO: read https://patsy.readthedocs.org/en/v0.1.0/categorical-coding.html
#
## stats des on brands / price quantiles per brands
#print pd_period_prices['brand'].describe()
#print pd_period_prices['brand'].value_counts()
#
## generate figure with price histograms per brand (?)
#ls_of_brands = np.unique(pd_period_prices['brand'])
## should take sqrt of list length rounded above to unit
#fig, axes = plt.subplots(nrows=5, ncols=5)
#list_axes = [j for i in axes for j in i][:len(ls_of_brands)]
## harmonize scales? (then need to impose categories)
#for i, ax in enumerate(list_axes):
#  brand_prices = pd_period_prices['price'][pd_period_prices['brand'] == ls_of_brands[i]]
#  test = ax.set_title('%s-%s'%(ls_of_brands[i], len(brand_prices[~np.isnan(brand_prices)])), fontsize=8)
#  # if brand_prices[~np.isnan(brand_prices)].tolist():
#  if len(brand_prices[~np.isnan(brand_prices)]) > 20:
#    test = ax.hist(brand_prices[~np.isnan(brand_prices)], bins = 20)
#plt.rcParams['font.size'] = 8
#plt.tight_layout()
#plt.show()

# #########################################
# PRICE REGRESSIONS : ALL PERIOD PANEL DATA
# #########################################

# Build pd_pd_prices
ls_all_prices = [price for ls_prices in master_price['diesel_price'] for price in ls_prices]
ls_all_ids = [id_indiv for id_indiv in master_price['ids'] for x in range(len(master_price['dates']))]
ls_all_dates = [date for id_indiv in master_price['ids'] for date in master_price['dates']]
ls_ls_all_brands = [[brand for ls_brands in ls_ls_brands for brand in ls_brands]\
                      for ls_ls_brands in ls_ls_ls_brands]
index = pd.MultiIndex.from_tuples(zip(ls_all_ids, ls_all_dates), names= ['id', 'date'])
columns = ['price', 'brand_1', 'brand_2', 'brand_type']

pd_mi_prices = pd.DataFrame(zip(*[ls_all_prices] + ls_ls_all_brands), index = index, columns = columns)

## Too slow...
#df_prices = pd.DataFrame(zip(*[ls_all_prices] + ls_ls_all_brands), index = index, columns = columns)
#df_prices = df_prices.reset_index(0)
#df_prices = df_prices.sort()
#df_prices_2011 = df_prices.ix['20110904':'20120905']
#for dpt in ls_tax_11[0]:
#  dpt = str(dpt)
#  df_prices_2011['price'][df_prices_2011['id'].str.slice(stop = -6) == dpt] =\
#    df_prices_2011['price'][df_prices_2011['id'].str.slice(stop = -6) == dpt] + 0.4419 + 0.0135

# Build pd_df_info (simple info dataframe)
ls_rows = []
for indiv_ind, indiv_id in enumerate(master_price['ids']):
  city = master_price['dict_info'][indiv_id]['city']
  if city:
    city = city.replace(',',' ')
  zip_code = '%05d' %int(indiv_id[:-3])
  code_geo = master_price['dict_info'][indiv_id].get('code_geo')
  code_geo_ardts = master_price['dict_info'][indiv_id].get('code_geo_ardts')
  tax_11 = get_tax_regime(int(zip_code[0:2]), ls_tax_11)
  tax_12 = get_tax_regime(int(zip_code[0:2]), ls_tax_12)
  highway = None
  if master_info.get(indiv_id):
    highway = master_info[indiv_id]['highway'][3]
  region = dict_dpts_regions[zip_code[:2]]
  row = [indiv_id, city, zip_code, code_geo, code_geo_ardts,
         tax_11, tax_12, highway, region]
  ls_rows.append(row)
ls_columns = ['id', 'city', 'zip_code', 'code_geo', 'code_geo_ardts',
              'tax_11', 'tax_12', 'highway', 'region']
pd_df_master_info = pd.DataFrame(zip(*ls_rows), ls_columns).T

# Merge info and prices
pd_df_master_info = pd_df_master_info.set_index('id')
pd_mi_prices = pd_mi_prices.reset_index()
pd_mi_final = pd_mi_prices.join(pd_df_master_info, on = 'id')
# add price before tax before setting index (less clear how to select then)
# 2011: http://www.developpement-durable.gouv.fr/La-fiscalite-des-produits,17899.html
# 2012: http://www.developpement-durable.gouv.fr/La-fiscalite-des-produits,26979.html
# 2013: http://www.developpement-durable.gouv.fr/La-fiscalite-des-produits,31455.html
pd_mi_final['price_ht'] = pd_mi_final['price'] / 1.196 - 0.4419

pd_mi_final['price_ht'] = np.where((pd_mi_final['date'].str.startswith('2011')) &\
                                     (pd_mi_final['tax_11'] == 1),
                                   pd_mi_final['price_ht'] + 0.0135,
                                   pd_mi_final['price_ht'])
pd_mi_final['price_ht'] = np.where((pd_mi_final['date'].str.startswith('2011')) &\
                                     (pd_mi_final['tax_11'] == 2),
                                   pd_mi_final['price_ht'] + 0.0250,
                                   pd_mi_final['price_ht'])

pd_mi_final['price_ht'] = np.where((pd_mi_final['date'].str.match('2012|2013.*')) &\
                                     (pd_mi_final['tax_12'] == 1),
                                   pd_mi_final['price_ht'] + 0.0135,
                                   pd_mi_final['price_ht'])
pd_mi_final['price_ht'] = np.where((pd_mi_final['date'].str.match('2012|2013.*')) &\
                                     (pd_mi_final['tax_12'] == 2),
                                   pd_mi_final['price_ht'] + 0.0250,
                                   pd_mi_final['price_ht'])

pd_mi_final = pd_mi_final.set_index(['id','date'])
# Tax cut and progressive exit
pd_mi_final = pd_mi_final.reset_index(0)
pd_mi_final = pd_mi_final.sort()
pd_mi_final.ix['20120831':'20121130']['price'] = pd_mi_final.ix['20120831':'20121130']['price'] + 0.03
pd_mi_final.ix['20121201':'20121211']['price'] = pd_mi_final.ix['20121201':'20121211']['price'] + 0.02
pd_mi_final.ix['20121211':'20121221']['price'] = pd_mi_final.ix['20121211':'20121221']['price'] + 0.015
pd_mi_final.ix['20121221':'20130111']['price'] = pd_mi_final.ix['20121221':'20130111']['price'] + 0.01

pd_mi_final = pd_mi_final.set_index(['id'], append = True)
pd_mi_final = pd_mi_final.swaplevel('id', 'date')
pd_mi_final = pd_mi_final.sort()
#pd_pd_prices = pd_mi_prices.to_panel()

## pd_mi_final.ix['1500007',:] # based on id
## http://stackoverflow.com/questions/17242970/multi-index-sorting-in-pandas
  
# # EXAMPLE PANEL DATA REGRESSIONS
# from patsy import dmatrices
# f = 'price~brand_2'
# y, X = dmatrices(f, pd_mi_final_extract, return_type='dataframe')
# sys.path.append(r'W:\Bureau\Etienne_work\Code\code_gasoline\code_gasoline_db_analysis\code_panel_regressions')
# from panel import *
# mod1 = PanelLM(y, X, method='pooling').fit()
# mod2 = PanelLM(y, X, method='between').fit()
# mod3 = PanelLM(y, X.ix[:,1:], method='within').fit()
# mod4 = PanelLM(y, X.ix[:,1:], method='within', effects='time').fit()
# mod5 = PanelLM(y, X.ix[:,1:], method='within', effects='twoways').fit()
# mod6 = PanelLM(y, X, 'swar').fit()
# mn = ['OLS', 'Between', 'Within N', 'Within T', 'Within 2w', 'RE-SWAR']
# results = [mod1, mod2, mod3, mod4, mod5, mod6]
# # Base group: Agip
# # Equivalent to Stata FE is Within N (Within T: time effect...)
# for i, result in enumerate(results):
  # print mn[i]
  # if len(X.columns) == len(result.params):
    # pprint.pprint(zip(X.columns, result.params, result.bse))
  # else:
    # pprint.pprint(zip(X.columns[1:], result.params, result.bse))

# pprint.pprint(zip(map(lambda x: '{:<28}'.format(x[:25]), X.columns),
                  # map(lambda x: '{:8.3f}'.format(x), np.round(mod1.params,3).tolist()),
                  # map(lambda x: '{:8.3f}'.format(x), np.round(mod1.bse,3).tolist())))

# TODO: compute price_ht based on dpt... (add categorical variable in df_info)
