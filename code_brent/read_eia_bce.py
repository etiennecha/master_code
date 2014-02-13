#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import os, sys, codecs
import datetime, time
import pandas as pd
import matplotlib.pyplot as plt
from BeautifulSoup import BeautifulSoup

# EIA: http://www.eia.gov/dnav/pet/pet_pri_spt_s1_d.htm
# ECB: http://www.ecb.europa.eu/stats/exchange/eurofxref/html/eurofxref-graph-usd.en.html 
# UFIP: http://www.ufip.fr/
path = os.path.abspath(os.path.dirname(sys.argv[0]))
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
               u'GAZOLE (Rotterdam)'      : 'UFIP RT Diesel EL',
               u'SP95 (Rotterdam)'        : 'UFIP RT SP95 EL',
               u'Brent ($ / baril)'       : 'UFIP Brent DB',
               u'Brent (€ / baril)'       : 'UFIP Brent EB',
               u'Parité (€/$)'            : 'UFIP Rate ED'}
df_ufip = df_ufip.rename(columns = dict_u_cols)
df_ufip.set_index('Date', inplace = True)

# REGROUP EIA + ECB (TODO +UFIP) IN ONE DATAFRAME
index = pd.date_range(start = pd.to_datetime('20121121'),
                      end   = pd.to_datetime('20140123'), 
                      freq='D')
df_all = pd.DataFrame(None, index = index)
for df_temp in [df_eia_brent, df_eia_diesel, df_ecb, df_ufip]:
  for column in df_temp:
    df_all[column] = df_temp[column]
print df_all.info()

se_temp = df_all['Europe Brent FOB DB'][~pd.isnull(df_all['Europe Brent FOB DB'])]
df_all['Europe Brent FOB R5 DB'] = pd.rolling_mean(se_temp, window = 5)

df_all[['ECB Rate ED', 'UFIP Rate ED']].plot()
df_all[['UFIP Brent DB', 'Europe Brent FOB DB', 'Europe Brent FOB R5 DB']].plot()
plt.show()

litre_per_us_gallon = 3.785411784
litre_per_barrel = 158.987295
df_all['NY Diesel EL'] = df_all['NY Diesel DG'] / litre_per_us_gallon / df_all['ECB Rate ED']
df_all['Gulf Diesel EL'] = df_all['Gulf Diesel DG'] / litre_per_us_gallon / df_all['ECB Rate ED']
df_all['LA Diesel EL'] = df_all['LA Diesel DG'] / litre_per_us_gallon / df_all['ECB Rate ED']

se_temp = df_all['NY Diesel EL'][~pd.isnull(df_all['NY Diesel EL'])]
df_all['NY Diesel R5 EL'] = pd.rolling_mean(se_temp, window = 5)

df_all[['UFIP RT Diesel EL', 'Gulf Diesel EL', 'LA Diesel EL', 'NY Diesel EL']].plot()
df_all[['UFIP RT Diesel EL', 'NY Diesel R5 EL']].plot()
plt.show()

#df_all[['OK WTI Brent FOB DB', 'Europe Brent FOB DB']].plot()
#plt.show()
#
#df_all[['NY Diesel DG', 'Gulf Diesel DG', 'LA Diesel DG']].plot()
#plt.show()
