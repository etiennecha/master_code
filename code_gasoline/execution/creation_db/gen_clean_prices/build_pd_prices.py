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

#ls_columns = [pd.to_datetime(date) for date in master_price['dates']]
#df_price = pd.DataFrame(master_price['diesel_price'], master_price['ids'], ls_columns).T
#se_mean_price =  df_price.mean(1)

# ##########################
# DF PRICES BRANDS
# ##########################

# DF COST
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
# BeautifulSoup objs tend to be heavy (trees...)
del(soup)

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

# DF PRICES
ls_columns = [pd.to_datetime(date) for date in master_price['dates']]
df_prices_ttc = pd.DataFrame(master_price['diesel_price'], master_price['ids'], ls_columns).T
df_prices_ht = df_prices_ttc / 1.196 - 0.4419
#df_prices_ht = pd.DataFrame.copy(df_prices_ttc)
#df_prices_ht = df_prices_ht / 1.196 - 0.4419

# PrixHT = PrixTTC / 1.196 - 0.4419 
# 2011: http://www.developpement-durable.gouv.fr/La-fiscalite-des-produits,17899.html
# 2012: http://www.developpement-durable.gouv.fr/La-fiscalite-des-produits,26979.html
# 2013: http://www.developpement-durable.gouv.fr/La-fiscalite-des-produits,31455.html
ls_tax_11 = [(1,7,26,38,42,69,73,74,75,77,78,91,92,93,94,95,4,5,6,13,83,84), # PrixHT + 0.0135
              (16,17,79,86)] # PrixHT + 0.0250
ls_tax_12 = [(1,7,26,38,42,69,73,74), # PrixHT + 0.0135
              (16,17,79,86)] # PrixHT + 0.0250

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
df_prices_ht.ix['2012-12-01':'2012-12-11'] = df_prices_ht.ix['2012-12-11':'2012-12-11'] + 0.02
df_prices_ht.ix['2012-12-11':'2012-12-21'] = df_prices_ht.ix['2012-12-11':'2012-12-21'] + 0.015
df_prices_ht.ix['2012-12-21':'2013-01-11'] = df_prices_ht.ix['2012-12-21':'2013-01-11'] + 0.01

# BRANDS
ls_ls_ls_brands = []
for i in range(3):
  ls_ls_brands =  [[[dict_brands[get_str_no_accent_up(brand)][i], period]\
                        for brand, period in master_price['dict_info'][id_indiv]['brand']]\
                          for id_indiv in master_price['ids']]
  ls_ls_brands = [get_expanded_list(ls_brands, len(master_price['dates']))\
                    for ls_brands in ls_ls_brands]
  ls_ls_ls_brands.append(ls_ls_brands)

# ASSEMBLE PRICES/BRANDS INTO ONE DF (MI?) PRICES

## Pbms with Memory
#df_prices_ht = df_prices_ht.T.stack(dropna = False)
#df_brands_1 = pd.DataFrame(ls_ls_ls_brands[0], master_price['ids'], ls_columns).stack(dropna = False)
#df_mi_agg = pd.DataFrame({'price_ht' : df_prices_ht, 'brand_1': df_brands_1})
#del(ls_ls_ls_brands, df_prices_ttc, df_prices_ht, df_brands_1)
#df_mi_agg.rename(index={0:'id', 1:'date'}, inplace = True)

ls_all_prices = df_prices_ht.T.stack(dropna=False).values
ls_all_ids = [id_indiv for id_indiv in master_price['ids'] for x in range(len(master_price['dates']))]
ls_all_dates = [date for id_indiv in master_price['ids'] for date in master_price['dates']]
ls_ls_all_brands = [[brand for ls_brands in ls_ls_brands for brand in ls_brands]\
                      for ls_ls_brands in ls_ls_ls_brands]
index = pd.MultiIndex.from_tuples(zip(ls_all_ids, ls_all_dates), names= ['id','date'])
columns = ['price', 'brand_1', 'brand_2', 'brand_type']
df_mi_prices = pd.DataFrame(zip(*[ls_all_prices] + ls_ls_all_brands),
                            index = index,
                            columns = columns)

# ########
# DF INFO
# ########

# SERVICES (for INFO FILE)
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

# INSEE DATA
df_insee = pd.read_csv(path_csv_insee_data, encoding = 'utf-8', dtype= str, tupleize_cols=False)
# exclude dom tom
df_insee = df_insee[~df_insee[u'Département - Commune CODGEO'].str.contains('^97')]
df_insee['Population municipale 2007 POP_MUN_2007'] =\
  df_insee['Population municipale 2007 POP_MUN_2007'].apply(lambda x: float(x))

# build df_info (simple info dataframe)
ls_rows = []
for indiv_ind, indiv_id in enumerate(master_price['ids']):
  city = master_price['dict_info'][indiv_id]['city']
  if city:
    city = city.replace(',',' ')
  zip_code = '%05d' %int(indiv_id[:-3])
  code_geo = master_price['dict_info'][indiv_id].get('code_geo')
  code_geo_ardts = master_price['dict_info'][indiv_id].get('code_geo_ardts')
  highway = None
  if master_info.get(indiv_id):
    highway = master_info[indiv_id]['highway'][3]
  region = dict_dpts_regions[zip_code[:2]]
  row = [indiv_id, city, zip_code, code_geo, code_geo_ardts, highway, region]
  ls_rows.append(row)
ls_columns = ['id', 'city', 'zip_code', 'code_geo', 'code_geo_ardts', 'highway', 'region']
df_info = pd.DataFrame(ls_rows, master_price['ids'], ls_columns)

#TODO: check no codegeo...

# ############
# FINAL MERGE
# ############
# (check that) both df are sorted
df_mi_prices = df_mi_prices.reset_index()
df_final = df_mi_prices.join(df_info, on = 'id', lsuffix = '_a')

path_dir_built_csv = os.path.join(path_dir_built_paper, 'data_csv')
df_final.to_csv(os.path.join(path_dir_built_csv, 'price_panel_data.csv'),
                float_format='%.4f',
                encoding='utf-8')

# ############
# REGRESSIONS
# ############

# Restrict df_final...
df_final['code_geo'][pd.isnull(df_final['code_geo'])] =  ''
df_final = df_final[~(df_final['highway'] == 1) &\
                    ~(df_final['code_geo'].str.startswith('2A')) &\
                    ~(df_final['code_geo'].str.startswith('2B'))]

#http://nbviewer.ipython.org/urls/s3.amazonaws.com/datarobotblog/notebooks/multiple_regression_in_python.ipynb

## General price cleaning .. Memory error at work
#res01 = smf.ols('price ~ C(date) + C(id)', data = df_final, missing = 'drop').fit()

## Try with 2011 only... memory error at work too
#res02 = smf.ols('price ~ C(date) + C(id)',\
#                data = df_final[df_final['date'].str.startswith('2011')],\
#                missing = 'drop').fit()

# Subset dpt 92 (exclude null code_geo so far: should exclude only full series)
#df_final = df_final[~pd.isnull(df_final['code_geo'])]
#res03 = smf.ols('price ~ C(date) + C(id)',\
#                data = df_final[df_final['code_geo'].str.startswith('92')],\
#                missing = 'drop').fit()
#df_final['cleaned_price'] = np.nan
#df_final['cleaned_price'][(df_final['code_geo'].str.startswith('92')) &\
#                          (~pd.isnull(df_final['price']))] = res03.fittedvalues
# df_final[['price', 'cleaned_price']][df_final['id'] == '92160003'].plot()

# (check that) all ids are matched (generalize...)

## With Panel data
#df_mi_final = df_final.set_index(['id', 'date'])
#
#from patsy import dmatrices
#from panel import *
#import pprint
#f = 'price~brand_2'
#y, X = dmatrices(f, df_mi_final, return_type='dataframe')
#mod1 = PanelLM(y, X, method='pooling').fit()
#pprint.pprint(zip(X.columns, mod1.params, mod1.bse))

# FOR UPDATE...

## TODO: restrict size to begin with (time/location)
## pd_mi_final.ix['1500007',:] # based on id
## pd_mi_final[pd_mi_final['code_geo'].str.startswith('01', na=False)] # based on insee
## http://stackoverflow.com/questions/17242970/multi-index-sorting-in-pandas
#pd_mi_final_alt = pd_mi_final.swaplevel('id', 'date')
#pd_mi_final_alt = pd_mi_final_alt.sort()
#pd_mi_final_extract = pd_mi_final_alt.ix['20110904':'20111004']
  
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
