import os, sys
import json
import itertools
import math
import copy
import random
import pprint
import numpy as np
import scipy
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
import patsy
import xlrd
from generic_master_price import *

# PRICE CHANGE VALUE AND FREQUENCY ANALYSIS FUNCTIONS

if __name__=="__main__":
  if os.path.exists(r'W:\Bureau\Etienne_work\Data'):
    path_data = r'W:\Bureau\Etienne_work\Data'
  else:
    path_data = r'C:\Users\etna\Desktop\Etienne_work\Data'
  
  folder_built_master_json = r'\data_gasoline\data_built\data_json_gasoline'
  folder_source_brand = r'\data_gasoline\data_source\data_stations\data_brands'
  folder_dpts_regions = r'\data_insee\Regions_departements'
  folder_built_csv = r'\data_gasoline\data_built\data_csv_gasoline'
  folder_ufip = r'\data_ufip'

  master_price = dec_json(path_data + folder_built_master_json + r'\master_diesel\master_price_diesel')
  master_info = dec_json(path_data + folder_built_master_json + r'\master_diesel\master_info_diesel')
  ls_ls_competitors = dec_json(path_data + folder_built_master_json + r'\master_diesel\list_list_competitors')
  ls_tuple_competitors = dec_json(path_data + folder_built_master_json + r'\master_diesel\list_tuple_competitors') 
  dict_brands = dec_json(path_data + folder_source_brand + r'\dict_brands') 
  dict_dpts_regions = dec_json(path_data + folder_dpts_regions + r'\dict_dpts_regions') 

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
  
  pd_df_insee = pd.read_csv(path_data + folder_built_csv + r'/master_insee_output.csv',\
                              encoding = 'utf-8', dtype= str, tupleize_cols=False)
  # exclude dom tom
  pd_df_insee = pd_df_insee[~pd_df_insee[u'Département - Commune CODGEO'].str.contains('^97')]
  pd_df_insee['Population municipale 2007 POP_MUN_2007'] =\
    pd_df_insee['Population municipale 2007 POP_MUN_2007'].apply(lambda x: float(x))
  
  # ######################
  # IMPORT UFIP DATA
  # ######################

  path_ufip_excel_file = path_data + folder_ufip + r'\ufip-valeurs_2006-01-01_au_2013-12-31.xlsx'
  ufip_excel_file = pd.ExcelFile(path_ufip_excel_file)
  df_ufip = ufip_excel_file.parse('Worksheet')
  df_ufip = df_ufip.set_index('Date')
  # excel_file.sheet_names
  print df_ufip.info()
  df_ufip['date_str'] = map(lambda x: x.strftime('%Y%m%d'), df_ufip.index)
  df_ufip.set_index('date_str', inplace=True)
 
  # #######################
  # TAXES
  # #######################

  ls_tax_11 = [(1,7,26,38,42,69,73,74,75,77,78,91,92,93,94,95,4,5,6,13,83,84), # (PrixTTC-0.4419+0.0135)/1.196
                (16,17,79,86)] # (PrixTTC-0.4419+0.0250)/1.196
  # 2011 else: (PrixTTC-0.4419)/1.196
  ls_tax_12 = [(1,7,26,38,42,69,73,74), # (PrixTTC-0.4419+0.0135)/1.196
                (16,17,79,86)] # (PrixTTC-0.4419+0.0250)/1.196
  # 2012 - 2013 else: (PrixTTC-0.4419)/1.196 
  
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
  
  ls_all_prices = [price for ls_prices in master_price['diesel_price'] for price in ls_prices]
  ls_all_ids = [id_indiv for id_indiv in master_price['ids'] for x in range(len(master_price['dates']))]
  ls_all_dates = [date for id_indiv in master_price['ids'] for date in master_price['dates']]
  ls_ls_all_brands = [[brand for ls_brands in ls_ls_brands for brand in ls_brands]\
                        for ls_ls_brands in ls_ls_ls_brands]
  index = pd.MultiIndex.from_tuples(zip(ls_all_ids, ls_all_dates), names= ['id','date'])
  columns = ['price', 'brand_1', 'brand_2', 'brand_type']
  pd_mi_prices = pd.DataFrame(zip(*[ls_all_prices] + ls_ls_all_brands), index = index, columns = columns)
  pd_pd_prices = pd_mi_prices.to_panel()
  # build pd_df_info (simple info dataframe)
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
    row = [indiv_id, city, zip_code, code_geo, code_geo_ardts, tax_11, tax_12, highway, region]
    ls_rows.append(row)
  header = ['id', 'city', 'zip_code', 'code_geo', 'code_geo_ardts', 'tax_11', 'tax_12', 'highway', 'region']
  pd_df_master_info = pd.DataFrame(zip(*ls_rows), header).T
  # merge info and prices
  pd_df_master_info = pd_df_master_info.set_index('id')
  pd_mi_prices = pd_mi_prices.reset_index()
  pd_mi_final = pd_mi_prices.join(pd_df_master_info, on = 'id')
  # add price before tax before setting index (less clear how to select then)
  # 2011: http://www.developpement-durable.gouv.fr/La-fiscalite-des-produits,17899.html
  # 2012: http://www.developpement-durable.gouv.fr/La-fiscalite-des-produits,26979.html
  # 2013: http://www.developpement-durable.gouv.fr/La-fiscalite-des-produits,31455.html
  pd_mi_final['price_ht'] = (pd_mi_final['price'][(pd_mi_final['date'].str.startswith('2011')) &\
                                                  (pd_mi_final['tax_11'] == 0)]-0.4419)/1.196
  pd_mi_final['price_ht'] = np.where((pd_mi_final['date'].str.startswith('2011')) &\
                                     (pd_mi_final['tax_11'] == 1),
                                     (pd_mi_final['price']+0.0135-0.4419)/1.196, pd_mi_final['price_ht'])
  pd_mi_final['price_ht'] = np.where((pd_mi_final['date'].str.startswith('2011')) &\
                                     (pd_mi_final['tax_11'] == 2),
                                     (pd_mi_final['price']+0.0250-0.4419)/1.196, pd_mi_final['price_ht'])
  pd_mi_final['price_ht'] = np.where((pd_mi_final['date'].str.match('2012|2013.*')) &\
                                     (pd_mi_final['tax_12'] == 0),
                                     (pd_mi_final['price']-0.4419)/1.196, pd_mi_final['price_ht']) 
  pd_mi_final['price_ht'] = np.where((pd_mi_final['date'].str.match('2012|2013.*')) &\
                                     (pd_mi_final['tax_12'] == 1),
                                     (pd_mi_final['price']+0.0135-0.4419)/1.196, pd_mi_final['price_ht'])
  pd_mi_final['price_ht'] = np.where((pd_mi_final['date'].str.match('2012|2013.*')) &\
                                     (pd_mi_final['tax_12'] == 2),
                                     (pd_mi_final['price']+0.0250-0.4419)/1.196, pd_mi_final['price_ht'])
  pd_mi_final = pd_mi_final.set_index(['id','date'])
   
  # TODO: restrict size to begin with (time/location)
  # pd_mi_final.ix['1500007',:] # based on id
  # pd_mi_final[pd_mi_final['code_geo'].str.startswith('01', na=False)] # based on insee
  # http://stackoverflow.com/questions/17242970/multi-index-sorting-in-pandas
  pd_mi_final_alt = pd_mi_final.swaplevel('id', 'date')
  pd_mi_final_alt = pd_mi_final_alt.sort()
  pd_mi_final_extract = pd_mi_final_alt.ix['20110904':'20111004']
    
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
  
  # AGGREGATE LEVEL
  df_mean = pd_mi_final.mean(level=1)
  df_mean['Rotterdam'] = df_ufip['GAZOLE (Rotterdam)']
  df_mean['UFIP_ht'] = df_ufip['GAZOLE HTT']
  df_mean['price_ht_bis'] = df_mean['price_ht'] - (df_mean['price_ht'] - df_mean['Rotterdam']).mean()
  #df_mean[['Rotterdam', 'price_ht_bis']].plot()
  #plt.plot()
  df_mean['OIL_ht'] = pd_mi_final['price_ht'][pd_mi_final['brand_type'] == 'OIL'].mean(level=1)
  df_mean['SUP_ht'] = pd_mi_final['price_ht'][pd_mi_final['brand_type'] == 'SUP'].mean(level=1)
  df_mean['OIL_norm'] = df_mean['OIL_ht'] - (df_mean['OIL_ht'] - df_mean['Rotterdam']).mean()
  df_mean['SUP_norm'] = df_mean['SUP_ht'] - (df_mean['SUP_ht'] - df_mean['Rotterdam']).mean()

  df_mean['OIL_norm_per1'] = df_mean['OIL_ht'] - (df_mean['OIL_ht'] - df_mean['Rotterdam'])[0:360].mean()
  df_mean['SUP_norm_per1'] = df_mean['SUP_ht'] - (df_mean['SUP_ht'] - df_mean['Rotterdam'])[0:360].mean()
  
  df_mean['price_ht_d1'] = df_mean['price_ht'] - df_mean['price_ht'].shift(1)
  df_mean['OIL_ht_d1'] = df_mean['OIL_ht'] - df_mean['OIL_ht'].shift(1)
  df_mean['Rotterdam_d1'] = df_mean['Rotterdam'] - df_mean['Rotterdam'].shift(1)

  # STATION LEVEL REGRESSION
  
  df_station = pd_mi_final.ix['1500007']
  df_station['Rotterdam'] = df_ufip['GAZOLE (Rotterdam)']
  #df_station['price_ht'] = (df_station['price']-0.4419)/1.196
  df_station['gross_margin'] = df_station['price_ht'] - df_station['Rotterdam']
  # restrict to period before price policy
  df_station['price_ht_bis'] = df_station['price_ht']-df_station['gross_margin'][0:360].mean()
  df_station[['Rotterdam', 'price_ht_bis']][0:360].plot()

  ls_display = []
  for id_sta in master_price['ids'][1:10]:
    df_station[id_sta] = pd_mi_final.ix[id_sta]['price_ht']
    df_station['%s_gm' %id_sta] = df_station[id_sta] - df_station['Rotterdam']
    ls_display.append('%s_gm' %id_sta)
  
  # before 0:360, while 361:506, after 507:
  # dataframe with all prices as columns
  df_all_station_prices = pd_mi_final['price_ht'].unstack('id')
  ls_col_titles = list(df_all_station_prices.columns)
  df_all_station_prices['Rotterdam'] = df_ufip['GAZOLE (Rotterdam)']a
  for col_title in ls_col_titles:
    df_all_station_prices[col_title] = df_all_station_prices[col_title] - df_all_station_prices['Rotterdam']
  del(df_all_station_prices['Rotterdam'])
  se_measure = df_all_station_prices[0:360].mean() - df_all_station_prices[361:506].mean()
  se_backlash = df_all_station_prices[507:].mean() - df_all_station_prices[0:360].mean()
  # TODO: merge with info to which brands added (also mark brand chges to exclude Total Access)
  df_brand = pd.DataFrame([ls_brand[-1] for ls_brand in ls_ls_ls_brands[0]], index = master_price['ids'])
  pd_df_master_info['brand_1'] = df_brand[0]
  pd_df_master_info['measure'] = se_measure
   
  # ###########
  # DEPRECATED
  # ###########
  
  # # SMALL REMINDER ON PANDAS COMMANDS
  # pd_multi_index_master['price']
  # pd_multi_index_master.ix['10000001']
  # print X[u'brand[T.TOTAL_ACCESS]'].ix['10000001']
  # # Reorder columns
  # cols = X.columns.tolist()
  # cols = cols[:-2] + cols[-1:] + cols[-2:-1]
  # X = X[cols]
  
  # # Creates a dict: keys = station ids, contents = DataFrame with gas station prices and info etc
  # # e.g. data = {'Item1' : pd.DataFrame(np.random.randn(4,3)), 'Item2' : pd.DataFrame(np.random.randn(4,2))}
  # # e.g. panel_data = pd.Panel(data)
  # # list_formatted_dates = ['%s/%s/%s' %(elt[:4], elt[4:6], elt[6:]) for elt in master_price['dates']]
  # # index_formatted_dates = pd.to_datetime(list_formatted_dates)
  
  # # TODO: try station FE regression within a dpt and with 300 periods
  # # UGLY... PROBLEM SOLVED (TEMP)
  # dict_panel_data_master_temp = {}
  # for i, id in enumerate(master_price['ids']):
    # if 'code_geo' in master_price['dict_info'][id]: # temp: TODO: complete master_info
      # list_station_prices = master_price['diesel_price'][i]
      # list_station_brands = [dict_brands[get_str_no_accent_up(brand)][1] if brand else brand\
                              # for brand in get_field_as_list(id, 'brand', master_price)]
      # zip_code = '%05d' %int(id[:-3])
      # dict_station = {'price' : np.array(list_station_prices, dtype = np.float32),
                      # 'brand' : np.array(list_station_brands),
                      # 'zip_code' : zip_code,
                      # 'department' : zip_code[:2],
                      # 'region' : dict_dpts_regions[zip_code[:2]],
                      # 'insee_code' : master_price['dict_info'][id]['code_geo'],
                      # 'id' : id}
      # pd_df_station_temp = pd.DataFrame(dict_station, index = master_price['dates'])
      # dict_panel_data_master_temp[id] = pd_df_station_temp[0:300]
  # pd_pd_master_temp = pd.Panel(dict_panel_data_master_temp)
  # pd_pd_master_temp = pd_pd_master_temp.transpose('minor', 'items', 'major')
  # pd_mi_master_temp = pd_pd_master_temp.to_frame(filter_observations=False)
  # pd_mi_master_temp['price'] = pd_mi_master_temp['price'].astype(np.float32)
  # pd_dpt_01['date'] = pd_dpt_01.index.get_level_values(1)
  # pd_dpt_01 = pd_mi_master_temp[pd_mi_master_temp['department'] == '01']
  # res01 = smf.ols(formula = 'price ~ C(id) + C(date)', data = pd_dpt_01).fit()
  # # X = pd.DataFrame(pd_dpt_01[['id', 'date']], columns=["id", "date"])
  # # y_prediction = res01.predict(X)
