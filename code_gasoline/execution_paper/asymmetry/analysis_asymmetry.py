#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path_sub
from add_to_path_sub import path_data
from generic_master_price import *
from generic_master_info import *
import datetime, time
from BeautifulSoup import BeautifulSoup

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
df_reuters_diesel = reuters_diesel_excel_file.parse('Feuil1', skiprows = 0, header = 1, parse_dates = True)
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

df_cost['ULSD 10 FOB MED EL'] = df_cost['ULSD 10 FOB MED DT'] / litre_per_metric_tonne / df_cost['ECB Rate ED']
df_cost['ULSD 10 CIF NWE EL'] = df_cost['ULSD 10 CIF NWE DT'] / litre_per_metric_tonne / df_cost['ECB Rate ED']
df_cost['GASOIL 0.2 FOB ARA EL'] = df_cost['GASOIL 0.2 FOB ARA DT'] / 1183.5 / df_cost['ECB Rate ED']

# DF PRICES TTC

ar_diesel_price = np.array(master_price['diesel_price'], np.float64)
ls_index = [pd.to_datetime(date) for date in master_price['dates']]
df_prices_ttc = pd.DataFrame(ar_diesel_price.T, columns = master_price['ids'], index = ls_index)
# TODO: get rid of highway... single out Corsica?

# DF PRICES HT

df_prices_ht = pd.DataFrame.copy(df_prices_ttc)

ls_tax_11 = [(1,7,26,38,42,69,73,74,75,77,78,91,92,93,94,95,4,5,6,13,83,84), # (PrixTTC-0.4419+0.0135)/1.196
              (16,17,79,86)] # (PrixTTC-0.4419+0.0250)/1.196
# 2011 else: (PrixTTC-0.4419)/1.196
ls_tax_12 = [(1,7,26,38,42,69,73,74), # (PrixTTC-0.4419+0.0135)/1.196
              (16,17,79,86)] # (PrixTTC-0.4419+0.0250)/1.196
# 2012 - 2013 else: (PrixTTC-0.4419)/1.196 

df_prices_ht_2011 = df_prices_ht.ix[:'2011-12-31']
for indiv_id in df_prices_ht_2011.columns:
  if indiv_id[:-6] in ls_tax_11[0]:
    df_prices_ht_2011[indiv_id] = df_prices_ht_2011[indiv_id].apply(lambda x: (x-0.4419+0.0135)/1.196)
  elif indiv_id[:-6] in ls_tax_11[1]:
    df_prices_ht_2011[indiv_id] = df_prices_ht_2011[indiv_id].apply(lambda x: (x-0.4419+0.0250)/1.196)
  else:
    df_prices_ht_2011[indiv_id] = df_prices_ht_2011[indiv_id].apply(lambda x: (x-0.4419)/1.196)

df_prices_ht_2012 = df_prices_ht.ix['2012-01-01':]
for indiv_id in df_prices_ht_2012.columns:
  if indiv_id[:-6] in ls_tax_12[0]:
    df_prices_ht_2012[indiv_id] = df_prices_ht_2012[indiv_id].apply(lambda x: (x-0.4419+0.0135)/1.196)
  elif indiv_id[:-6] in ls_tax_12[1]:
    df_prices_ht_2012[indiv_id] = df_prices_ht_2012[indiv_id].apply(lambda x: (x-0.4419+0.0250)/1.196)
  else:
    df_prices_ht_2012[indiv_id] = df_prices_ht_2012[indiv_id].apply(lambda x: (x-0.4419)/1.196)

# DF ALL: MERGE DF PRICES HT AND DF REUTERS
df_all = df_cost[['ULSD 10 FOB MED EL', 'ULSD 10 CIF NWE EL']]
df_all['diesel_ht'] = df_prices_ht.mean(axis = 1)
df_all['margin'] = df_all['diesel_ht'] - df_all['ULSD 10 CIF NWE EL']

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

# Exclude highway and Corse
df_info = df_info[(df_info['highway'] != 1) &\
                  (df_info['region'] != 'Corse')]

# ########
# ANALYSIS
# ########

## Print prices and margin
#df_all.plot()
#plt.show()

# Hist: all prices at day 0 (TODO: over time)
min_x, max_x = 1.2, 1.6
bins = np.linspace(min_x, max_x, (max_x - min_x) / 0.01 + 1)
plt.hist(df_prices_ttc.ix[0][~pd.isnull(df_prices_ttc.ix[0])], bins = bins, alpha = 0.5)
plt.show()

# Hist: supermarkets vs. oil (add ind?): first period

ls_sup_ids = df_info.index[(df_info['brand_type_b'] == 'SUP') &\
                           (df_info['brand_type_b'] == df_info['brand_type_e'])]
ls_oil_ids = df_info.index[(df_info['brand_type_b'] == 'OIL') &\
                           (df_info['brand_type_b'] == df_info['brand_type_e'])]

plt.hist(df_prices_ttc[ls_sup_ids].ix[0][~pd.isnull(df_prices_ttc[ls_sup_ids].ix[0])],
         bins = bins,
         alpha = 0.5)
plt.hist(df_prices_ttc[ls_oil_ids].ix[0][~pd.isnull(df_prices_ttc[ls_oil_ids].ix[0])],
         bins = bins,
         alpha = 0.5)
plt.show()

# Hist: supermarkets vs. oil (add ind?): last period

plt.hist(df_prices_ttc[ls_sup_ids].ix[-1][~pd.isnull(df_prices_ttc[ls_sup_ids].ix[0])],
         bins = bins,
         alpha = 0.5,
         label = 'sup')
plt.hist(df_prices_ttc[ls_oil_ids].ix[-1][~pd.isnull(df_prices_ttc[ls_oil_ids].ix[0])],
         bins = bins,
         alpha = 0.5
         label = 'oil')
plt.show()

# Hist: oil companies
