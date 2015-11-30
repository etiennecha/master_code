#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
import datetime, time
from BeautifulSoup import BeautifulSoup

path_dir_rotterdam = os.path.join(path_data,
                                  'data_gasoline',
                                  'data_source',
                                  'data_rotterdam')

path_xls_reuters_diesel = os.path.join(path_dir_rotterdam,
                                       'data_reuters',
                                       'diesel_data_to_import.xls')

path_xls_eia = os.path.join(path_dir_rotterdam,
                            'PET_PRI_SPT_S1_D.xls')

# path_xlsx_ufip = os.path.join(path_dir_rotterdam,
#                               'ufip-valeurs_2006-01-01_au_2013-12-31.xlsx')
path_xlsx_ufip = os.path.join(path_dir_rotterdam,
                              'ufip-valeurs_2006-01-01_au_2015-06-30.xlsx')

path_xml_ecb = os.path.join(path_dir_rotterdam, 'usd.xml')

path_dir_built = os.path.join(path_data,
                              u'data_gasoline',
                              u'data_built')

# REUTERS FILE
reuters_diesel_excel_file = pd.ExcelFile(path_xls_reuters_diesel)
print 'Reuters excel file sheets:', reuters_diesel_excel_file.sheet_names
df_reuters_diesel = reuters_diesel_excel_file.parse('Feuil1',
                                                    header = 1,
                                                    parse_dates = True)
df_reuters_diesel.set_index('Date', inplace = True)
print df_reuters_diesel.info()

# EIA FILE
eia_excel_file = pd.ExcelFile(path_xls_eia)
print 'EIA excel file sheets:', eia_excel_file.sheet_names
# Brent price sheet
df_eia_brent = eia_excel_file.parse('Data 1',
                                    header = 2,
                                    parse_dates = True)
dict_brent_cols = {u'Cushing, OK WTI Spot Price FOB (Dollars per Barrel)' : u'OK WTI Brent FOB DB',
                   u'Europe Brent Spot Price FOB (Dollars per Barrel)' : 'Europe Brent FOB DB'}
df_eia_brent = df_eia_brent.rename(columns = dict_brent_cols)
df_eia_brent.set_index('Date', inplace = True)
# Diesel price sheet
df_eia_diesel = eia_excel_file.parse('Data 5',
                                     header = 2,
                                     parse_dates = True)
dict_d_cols = {u'New York Harbor Ultra-Low Sulfur No 2 Diesel Spot Price (Dollars per Gallon)':\
                   'NY Diesel DG',
               u'U.S. Gulf Coast Ultra-Low Sulfur No 2 Diesel Spot Price (Dollars per Gallon)':\
                   'Gulf Diesel DG',
               u'Los Angeles, CA Ultra-Low Sulfur CARB Diesel Spot Price (Dollars per Gallon)':\
                   'LA Diesel DG'}
df_eia_diesel = df_eia_diesel.rename(columns = dict_d_cols)
df_eia_diesel.set_index('Date', inplace = True)

# ECB FILE
ecb_xml_file = open(path_xml_ecb, 'r').read()
soup = BeautifulSoup(ecb_xml_file)
print 'ECB xml file row content:', dict(soup.findAll('obs')[0].attrs)
ls_ecb = [[pd.to_datetime(dict(obs.attrs)[u'time_period']), float(dict(obs.attrs)[u'obs_value'])]\
            for obs in soup.findAll('obs')]
df_ecb = pd.DataFrame(ls_ecb, columns = ['Date', 'ECB Rate ED'])
df_ecb.set_index('Date', inplace = True)

# UFIP FILE
ufip_excel_file = pd.ExcelFile(path_xlsx_ufip)
df_ufip = ufip_excel_file.parse('Worksheet')
ls_u_drop = ['GAZOLE TTC', 'GAZOLE HTT',
             'SP95 HTT', 'SP95 TTC',
             'FOD HTT', 'FOD TTC', 'FOD (Rotterdam)']
df_ufip.drop(ls_u_drop, inplace = True, axis = 1)
dict_u_cols = {u'Marge de raffinage (€/t)': 'UFIP Ref margin ET',
               u'GAZOLE (Rotterdam)'      : 'UFIP RT Diesel R5 EL',
               u'SP95 (Rotterdam)'        : 'UFIP RT SP95 R5 EL',
               u'Brent ($ / baril)'       : 'UFIP Brent R5 DB',
               u'Brent (€ / baril)'       : 'UFIP Brent R5 EB',
               u'Parité (€/$)'            : 'UFIP Rate ED'}
df_ufip = df_ufip.rename(columns = dict_u_cols)
df_ufip.set_index('Date', inplace = True)

# REGROUP EIA, ECB UFIP and REUTERS IN ONE DATAFRAME (arbitrary date range)
index = pd.date_range(start = pd.to_datetime('20110904'),
                      end   = pd.to_datetime('20150630'), 
                      freq='D')
df_all = pd.DataFrame(None, index = index)
for df_temp in [df_eia_brent, df_eia_diesel, df_ecb, df_ufip, df_reuters_diesel]:
  for column in df_temp:
    df_all[column] = df_temp[column]
print df_all.info()

# Fill ECB rate with previously avail value
df_all['ECB Rate ED'].fillna(method='pad', limit=5, inplace = True)
# Keep only lines where usefull for aesthetic reasons?
df_all.loc[pd.isnull(df_all['ULSD 10 CIF NWE DT']), 'ECB Rate ED'] = np.nan

# Exogeneous params
litre_per_us_gallon = 3.785411784
litre_per_barrel = 158.987295
litre_per_metric_tonne = 1183.5

df_all['Europe Brent FOB EL'] = df_all['Europe Brent FOB DB'] / litre_per_barrel / df_all['ECB Rate ED'] 

df_all['NY Diesel EL'] = df_all['NY Diesel DG'] / litre_per_us_gallon / df_all['ECB Rate ED']

# ULSD: 100 Metric Tonnes = 118.35 Cubic Metres = 118 350 Litres => divide by 1183.5
df_all['ULSD 10 FOB MED EL'] = df_all['ULSD 10 FOB MED DT'] /\
                                 litre_per_metric_tonne / df_all['ECB Rate ED']
df_all['ULSD 10 CIF NWE EL'] = df_all['ULSD 10 CIF NWE DT'] /\
                                 litre_per_metric_tonne / df_all['ECB Rate ED']
df_all['GASOIL 0.2 FOB ARA EL'] = df_all['GASOIL 0.2 FOB ARA DT'] /\
                                   litre_per_metric_tonne / df_all['ECB Rate ED']

#df_all[['ULSD 10 FOB MED EL', 'ULSD 10 CIF NWE EL',
#        'NY Diesel EL', 'UFIP RT Diesel R5 EL']].plot()
#plt.show()

# CIF NWE looks good
se_temp = df_all['ULSD 10 CIF NWE EL'][~pd.isnull(df_all['ULSD 10 CIF NWE EL'])]
df_all['ULSD 10 CIF NWE R5 EL'] = pd.rolling_mean(se_temp, window = 5)

df_all[['ULSD 10 CIF NWE EL', 'ULSD 10 CIF NWE R5 EL', 'UFIP RT Diesel R5 EL']].plot()
plt.show()

# ####################
# UFIP COMPARISON
# ####################

# todo: take into account week end properly with shift
# think it was done with excel and there was no line for week end
# shift must a.s. intervene before moving average

# nb: same to shift by 1 then moving average 5 or converse
# pbm with WE doing it this way...
df_all['ULSD 10 CIF NWE S1 EL'] = df_all['ULSD 10 CIF NWE EL'].shift(1)
df_all['ULSD 10 CIF NWE R5 S1 EL'] = df_all['ULSD 10 CIF NWE R5 EL'].shift(1)

print (df_all['UFIP RT Diesel R5 EL'] - df_all['ULSD 10 CIF NWE R5 EL']).mean()
print (df_all['UFIP RT Diesel R5 EL'] - df_all['ULSD 10 CIF NWE R5 S1 EL']).mean()

df_all['UFIP_diff'] = df_all['UFIP RT Diesel R5 EL'] - df_all['ULSD 10 CIF NWE R5 S1 EL']
print np.argmax(df_all['UFIP_diff']), np.max(df_all['UFIP_diff'])
print df_all[['UFIP RT Diesel R5 EL', 'ULSD 10 CIF NWE R5 S1 EL',
              'ULSD 10 CIF NWE S1 EL', 'UFIP_diff']].ix['2013-03-20':'2013-04-20'].to_string()
# obs: though WE prices are filled with previous prices by UFIP, other missing seem not to be

#plt.plot(df_all['UFIP RT Diesel R5 EL'] - df_all['ULSD 10 CIF NWE R5 EL'])
#plt.plot(df_all['UFIP RT Diesel R5 EL'] - df_all['ULSD 10 CIF NWE R5 S1 EL'])
#plt.show()

# todo: check: not ok because time stamps are kept... so then week end are still there as nan
df_all_nowe = df_all[~((df_all.index.weekday == 5) | (df_all.index.weekday == 6))].copy()
df_all_nowe['ULSD 10 CIF NWE S1b EL'] = df_all_nowe['ULSD 10 CIF NWE EL'].shift(1)
df_all_nowe['ULSD 10 CIF NWE S1b R5b EL'] = pd.stats.moments.rolling_apply(
                                              df_all_nowe['ULSD 10 CIF NWE S1b EL'], 5,
                                              lambda x: x[~pd.isnull(x)].mean(),2)
df_all_nowe['UFIP_diff_b'] = df_all_nowe['UFIP RT Diesel R5 EL'] -\
                               df_all_nowe['ULSD 10 CIF NWE S1b R5b EL']
df_all_nowe['UFIP_diff_b'].plot()
plt.show()
# not good
print df_all_nowe[['UFIP RT Diesel R5 EL',
                   'ULSD 10 CIF NWE S1b R5b EL',
                   'ULSD 10 CIF NWE S1b EL',
                   'UFIP_diff_b']].ix['2013-03-20':'2013-04-20'].to_string()

df_all['ULSD 10 CIF NWE S1b R5b EL'] = df_all_nowe['ULSD 10 CIF NWE S1b R5b EL']

# #############
# OUTPUT
# #############

ls_output_columns = ['UFIP RT Diesel R5 EL',
                     'UFIP RT SP95 R5 EL',
                     'UFIP Brent R5 DB',
                     'UFIP Brent R5 EB',
                     'UFIP Ref margin ET',
                     'UFIP Rate ED',
                     'ECB Rate ED', # same?
                     'Europe Brent FOB DB',
                     'Europe Brent FOB EL',
                     'NY Diesel DG',
                     'NY Diesel EL',
                     'ULSD 10 FOB MED DT',
                     'ULSD 10 CIF NWE DT',
                     'ULSD 10 FOB MED EL',
                     'ULSD 10 CIF NWE EL',
                     'ULSD 10 CIF NWE R5 EL',
                     'ULSD 10 CIF NWE R5 S1 EL',
                     'UFIP_diff']

df_all[ls_output_columns].to_csv(os.path.join(path_dir_built,
                                              'data_paper_dispersion',
                                              'data_csv',
                                              'df_quotations.csv'),
                                 index_label = 'date',
                                 float_format= '%.3f',
                                 encoding = 'utf-8')

df_all[ls_output_columns].to_csv(os.path.join(path_dir_built,
                                              'data_paper_total_access',
                                              'data_csv',
                                              'df_quotations.csv'),
                                 index_label = 'date',
                                 float_format= '%.3f',
                                 encoding = 'utf-8')
