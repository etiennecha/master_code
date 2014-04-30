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

path_dir_source = os.path.join(path_data, 'data_gasoline', 'data_source')
path_dict_brands = os.path.join(path_dir_source, 'data_other', 'dict_brands.json')

path_dir_insee = os.path.join(path_data, 'data_insee')
path_dict_dpts_regions = os.path.join(path_dir_insee, 'dpts_regions', 'dict_dpts_regions.json')

master_price = dec_json(path_diesel_price)
master_info = dec_json(path_info)
dict_brands = dec_json(path_dict_brands)
dict_dpts_regions = dec_json(path_dict_dpts_regions)

# ################
# BUILD DATAFRAMES
# ################

# DF REUTERS

reuters_diesel_excel_file = pd.ExcelFile(path_xls_reuters_diesel)
df_reuters_diesel = reuters_diesel_excel_file.parse('Feuil1', skiprows = 0, header = 1, parse_dates = True)
df_reuters_diesel.set_index('Date', inplace = True)

ecb_xml_file = open(path_xml_ecb, 'r').read()
soup = BeautifulSoup(ecb_xml_file)
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

litre_per_us_gallon = 3.785411784
litre_per_barrel = 158.987295
litre_per_metric_tonne = 1183.5

df_cost['ULSD 10 FOB MED EL'] =\
  df_cost['ULSD 10 FOB MED DT'] / litre_per_metric_tonne / df_cost['ECB Rate ED']
df_cost['ULSD 10 CIF NWE EL'] =\
  df_cost['ULSD 10 CIF NWE DT'] / litre_per_metric_tonne / df_cost['ECB Rate ED']
df_cost['GASOIL 0.2 FOB ARA EL'] =\
  df_cost['GASOIL 0.2 FOB ARA DT'] / litre_per_metric_tonne / df_cost['ECB Rate ED']

# DF PRICES TTC

ar_diesel_price = np.array(master_price['diesel_price'], np.float64)
ls_index = [pd.to_datetime(date) for date in master_price['dates']]
df_prices_ttc = pd.DataFrame(ar_diesel_price.T, columns = master_price['ids'], index = ls_index)

# DF PRICES HT

df_prices_ht = pd.DataFrame.copy(df_prices_ttc)
df_prices_ht = df_prices_ht / 1.196 - 0.4419

# PrixHT = PrixTTC / 1.196 - 0.4419 
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

df_info['dpt'] = df_info['code_geo'].map(lambda x: x[:2] if x else None)

# Exclude highway and Corse
df_info = df_info[(df_info['highway'] != 1) &\
                  (df_info['region'] != 'Corse')]

## Margin
#df_agg = df_cost[['ULSD 10 FOB MED EL', 'ULSD 10 CIF NWE EL']]
#df_agg['diesel_ht'] = df_prices_ht.mean(axis = 1)
#df_agg['margin'] = df_agg['diesel_ht'] - df_agg['ULSD 10 CIF NWE EL']
#
#dict_cat_ids = {}
#for cat in ['SUP', 'OIL', 'IND']:
#  ls_cat_ids = df_info.index[(df_info['brand_type_b'] == '%s'%cat) &\
#                             (df_info['brand_type_b'] == df_info['brand_type_e'])]
#  dict_cat_ids[cat] = ls_cat_ids
#  df_agg['diesel_ht_%s' %cat] = df_prices_ht[ls_cat_ids].mean(axis=1)
#  df_agg['margin_%s' %cat] = df_agg['diesel_ht_%s' %cat] - df_agg['ULSD 10 CIF NWE EL']
#
#df_agg[['diesel_ht', 'ULSD 10 FOB MED EL', 'ULSD 10 CIF NWE EL']].plot()
#plt.show()

# INSPECT EFFECT OF TAX CUT: DECREASE IN MARGIN?
df_cost['avg_diesel_ttc'] = df_prices_ttc.mean(1)
df_cost['avg_diesel_ht'] = df_prices_ht.mean(1)
df_cost['avg_diesel_margin'] = df_cost['avg_diesel_ht'] -  df_cost['ULSD 10 CIF NWE EL']

ax = df_cost['avg_diesel_margin'].plot()
ax.axvline(x=pd.to_datetime('2012-08-31'), linewidth=1, color='r')
ax.axvline(x=pd.to_datetime('2013-01-11'), linewidth=1, color='r')

df_cost['avg_diesel_margin'][:'2012-06-28'].mean()
df_cost['avg_diesel_margin'][:'2013-01-11'].mean()

# TOTAL?
ls_total_ind = df_info.index[(df_info['brand_1_b'] == 'TOTAL') & (df_info['brand_1_e'] == 'TOTAL')]
df_cost['avg_diesel_margin_total'] = df_prices_ht[ls_total_ind].mean(1) -\
                                       df_cost['ULSD 10 CIF NWE EL']
df_cost['avg_diesel_margin_total'].plot()
plt.show()

# Check variations frequent changers vs. prices
