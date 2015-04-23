#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import os, sys, codecs
import datetime, time
import pandas as pd
import matplotlib.pyplot as plt
from BeautifulSoup import BeautifulSoup

path = os.path.abspath(os.path.dirname(sys.argv[0]))
file_reuters_diesel = 'diesel_data_to_import.xls'
path_reuters_diesel = os.path.join(path, file_reuters_diesel)

reuters_diesel_excel_file = pd.ExcelFile(path_reuters_diesel)
print 'Reuters excel file sheets:', reuters_diesel_excel_file.sheet_names
df_diesel_reuters = reuters_diesel_excel_file.parse('Feuil1', skiprows = 0, header = 1, parse_dates = True)
df_diesel_reuters.set_index('Date', inplace = True)
print df_diesel_reuters.info()

file_ecb = 'usd.xml'
file_eia = 'PET_PRI_SPT_S1_D.xls'
file_ufip = 'ufip-valeurs_2006-01-01_au_2013-12-31.xlsx'
path_ecb = os.path.join(path, file_ecb)
path_eia = os.path.join(path, file_eia)
path_ufip = os.path.join(path, file_ufip)

# EIA FILE
eia_excel_file = pd.ExcelFile(path_eia)
print 'EIA excel file sheets:', eia_excel_file.sheet_names
# Brent price sheet
df_eia_brent = eia_excel_file.parse('Data 1', skiprows = 1, header = 2, parse_dates = True)
dict_brent_cols = {u'Cushing, OK WTI Spot Price FOB (Dollars per Barrel)' : u'OK WTI Brent FOB DB',
                   u'Europe Brent Spot Price FOB (Dollars per Barrel)' : 'Europe Brent FOB DB'}
df_eia_brent = df_eia_brent.rename(columns = dict_brent_cols)
df_eia_brent.set_index('Date', inplace = True)
# Diesel price sheet
df_eia_diesel = eia_excel_file.parse('Data 5', skiprows = 1, header = 2, parse_dates = True)
dict_d_cols = {u'New York Harbor Ultra-Low Sulfur No 2 Diesel Spot Price (Dollars per Gallon)':\
                   'NY Diesel DG',
               u'U.S. Gulf Coast Ultra-Low Sulfur No 2 Diesel Spot Price (Dollars per Gallon)':\
                   'Gulf Diesel DG',
               u'Los Angeles, CA Ultra-Low Sulfur CARB Diesel Spot Price (Dollars per Gallon)':\
                   'LA Diesel DG'}
df_eia_diesel = df_eia_diesel.rename(columns = dict_d_cols)
df_eia_diesel.set_index('Date', inplace = True)

# ECB FILE
ecb_xml_file = open(path_ecb, 'r').read()
soup = BeautifulSoup(ecb_xml_file)
print 'ECB xml file row content:', dict(soup.findAll('obs')[0].attrs)
ls_ecb = [[pd.to_datetime(dict(obs.attrs)[u'time_period']), float(dict(obs.attrs)[u'obs_value'])]\
            for obs in soup.findAll('obs')]
df_ecb = pd.DataFrame(ls_ecb, columns = ['Date', 'ECB Rate ED'])
df_ecb.set_index('Date', inplace = True)

# UFIP FILE
ufip_excel_file = pd.ExcelFile(path_ufip)
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

# REGROUP EIA,ECB and UFIP IN ONE DATAFRAME (arbitrary date range)
index = pd.date_range(start = pd.to_datetime('20121121'),
                      end   = pd.to_datetime('20140123'), 
                      freq='D')
df_all = pd.DataFrame(None, index = index)
for df_temp in [df_eia_brent, df_eia_diesel, df_ecb, df_ufip, df_diesel_reuters]:
  for column in df_temp:
    df_all[column] = df_temp[column]
print df_all.info()


litre_per_us_gallon = 3.785411784
litre_per_barrel = 158.987295
litre_per_metric_tonne = 1183.5

df_all['Europe Brent FOB EL'] = df_all['Europe Brent FOB DB'] / litre_per_barrel / df_all['ECB Rate ED'] 
df_all['NY Diesel EL'] = df_all['NY Diesel DG'] / litre_per_us_gallon / df_all['ECB Rate ED']

# ULSD: 100 Metric Tonnes = 118.35 Cubic Metres = 118 350 Litres => divide by 1183.5
df_all['ULSD 10 FOB MED EL'] = df_all['ULSD 10 FOB MED DT'] / litre_per_metric_tonne / df_all['ECB Rate ED']
df_all['ULSD 10 CIF NWE EL'] = df_all['ULSD 10 CIF NWE DT'] / litre_per_metric_tonne / df_all['ECB Rate ED']
df_all['GASOIL 0.2 FOB ARA EL'] = df_all['GASOIL 0.2 FOB ARA DT'] / 1183.5 / df_all['ECB Rate ED']

#df_all[['ULSD 10 FOB MED EL', 'ULSD 10 CIF NWE EL',
#        'NY Diesel EL', 'UFIP RT Diesel R5 EL']].plot()
#plt.show()

# CIF NWE looks good
se_temp = df_all['ULSD 10 CIF NWE EL'][~pd.isnull(df_all['ULSD 10 CIF NWE EL'])]
df_all['ULSD 10 CIF NWE R5 EL'] = pd.rolling_mean(se_temp, window = 5)

df_all[['ULSD 10 CIF NWE EL', 'ULSD 10 CIF NWE R5 EL', 'UFIP RT Diesel R5 EL']].plot()
plt.show()
