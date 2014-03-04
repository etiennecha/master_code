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

# DF REUTERS

reuters_diesel_excel_file = pd.ExcelFile(path_xls_reuters_diesel)
print 'Reuters excel file sheets:', reuters_diesel_excel_file.sheet_names
df_reuters_diesel = reuters_diesel_excel_file.parse('Feuil1', skiprows = 0, header = 1, parse_dates = True)
df_reuters_diesel.set_index('Date', inplace = True)
print df_reuters_diesel.info()

ecb_xml_file = open(path_xml_ecb, 'r').read()
soup = BeautifulSoup(ecb_xml_file)
print 'ECB xml file row content:', dict(soup.findAll('obs')[0].attrs)
ls_ecb = [[pd.to_datetime(dict(obs.attrs)[u'time_period']), float(dict(obs.attrs)[u'obs_value'])]\
            for obs in soup.findAll('obs')]
df_ecb = pd.DataFrame(ls_ecb, columns = ['Date', 'ECB Rate ED'])
df_ecb.set_index('Date', inplace = True)

index = pd.date_range(start = pd.to_datetime('20110904'),
                      end   = pd.to_datetime('20130604'), 
                      freq='D')
df_cost = pd.DataFrame(None, index = index)
for df_temp in [df_ecb, df_reuters_diesel]:
  for column in df_temp:
    df_cost[column] = df_temp[column]
print df_cost.info()

litre_per_us_gallon = 3.785411784
litre_per_barrel = 158.987295
litre_per_metric_tonne = 1183.5

df_cost['ULSD 10 FOB MED EL'] = df_cost['ULSD 10 FOB MED DT'] / litre_per_metric_tonne / df_cost['ECB Rate ED']
df_cost['ULSD 10 CIF NWE EL'] = df_cost['ULSD 10 CIF NWE DT'] / litre_per_metric_tonne / df_cost['ECB Rate ED']
df_cost['GASOIL 0.2 FOB ARA EL'] = df_cost['GASOIL 0.2 FOB ARA DT'] / 1183.5 / df_cost['ECB Rate ED']

# DF PRICES

ar_diesel_price = np.array(master_price['diesel_price'], np.float64)
ls_index = [pd.to_datetime(date) for date in master_price['dates']]
df_prices = pd.DataFrame(ar_diesel_price.T, columns = master_price['ids'], index = ls_index)

# TAXES
ls_tax_11 = [(1,7,26,38,42,69,73,74,75,77,78,91,92,93,94,95,4,5,6,13,83,84), # (PrixTTC-0.4419+0.0135)/1.196
              (16,17,79,86)] # (PrixTTC-0.4419+0.0250)/1.196
# 2011 else: (PrixTTC-0.4419)/1.196
ls_tax_12 = [(1,7,26,38,42,69,73,74), # (PrixTTC-0.4419+0.0135)/1.196
              (16,17,79,86)] # (PrixTTC-0.4419+0.0250)/1.196
# 2012 - 2013 else: (PrixTTC-0.4419)/1.196 

df_prices_2011 = df_prices.ix[:'2011-12-31']
for indiv_id in df_prices_2011.columns:
  if indiv_id[:-6] in ls_tax_11[0]:
    df_prices_2011[indiv_id] = df_prices_2011[indiv_id].apply(lambda x: (x-0.4419+0.0135)/1.196)
  elif indiv_id[:-6] in ls_tax_11[1]:
    df_prices_2011[indiv_id] = df_prices_2011[indiv_id].apply(lambda x: (x-0.4419+0.0250)/1.196)
  else:
    df_prices_2011[indiv_id] = df_prices_2011[indiv_id].apply(lambda x: (x-0.4419)/1.196)

df_prices_2012 = df_prices.ix['2012-01-01':]
for indiv_id in df_prices_2012.columns:
  if indiv_id[:-6] in ls_tax_12[0]:
    df_prices_2012[indiv_id] = df_prices_2012[indiv_id].apply(lambda x: (x-0.4419+0.0135)/1.196)
  elif indiv_id[:-6] in ls_tax_12[1]:
    df_prices_2012[indiv_id] = df_prices_2012[indiv_id].apply(lambda x: (x-0.4419+0.0250)/1.196)
  else:
    df_prices_2012[indiv_id] = df_prices_2012[indiv_id].apply(lambda x: (x-0.4419)/1.196)

# MERGE
df_all = df_cost[['ULSD 10 FOB MED EL', 'ULSD 10 CIF NWE EL']]
df_all['diesel_ttc'] = df_prices.mean(axis = 1) - 0.1

df_all.plot()
plt.show()

  
