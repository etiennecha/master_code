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

file_ecb = r'usd.xml'
file_eia = r'PET_PRI_SPT_S1_D.xls'
path = os.path.abspath(os.path.dirname(sys.argv[0]))
path_ecb = os.path.join(path, file_ecb)
path_eia = os.path.join(path, file_eia)

# EIA FILE
excel_file = pd.ExcelFile(path_eia)
print 'EIA excel file sheets:', excel_file.sheet_names
# Brent price sheet
df_eia_brent = excel_file.parse('Data 1', skiprows = 1, header = 2, parse_dates = True)
dict_brent_cols = {u'Cushing, OK WTI Spot Price FOB (Dollars per Barrel)' : u'OK WTI Brent FOB DB',
                   u'Europe Brent Spot Price FOB (Dollars per Barrel)' : 'Europe Brent FOB DB'}
df_eia_brent = df_eia_brent.rename(columns = dict_brent_cols)
df_eia_brent.set_index('Date', inplace = True)
# Diesel price sheet
df_eia_diesel = excel_file.parse('Data 5', skiprows = 1, header = 2, parse_dates = True)
dict_d_cols = {u'New York Harbor Ultra-Low Sulfur No 2 Diesel Spot Price (Dollars per Gallon)':\
                   'NY Diesel DG',
               u'U.S. Gulf Coast Ultra-Low Sulfur No 2 Diesel Spot Price (Dollars per Gallon)':\
                  'Gulf Diesel DG',
               u'Los Angeles, CA Ultra-Low Sulfur CARB Diesel Spot Price (Dollars per Gallon)':\
                  'LA Diesel DG'}
df_eia_diesel = df_eia_diesel.rename(columns = dict_d_cols)
df_eia_diesel.set_index('Date', inplace = True)

# ECB FILE
ecb_file = open(path_ecb, 'r').read()
soup = BeautifulSoup(ecb_file)
print 'ECB xml file row content:', dict(soup.findAll('obs')[0].attrs)
ls_ecb = [[pd.to_datetime(dict(obs.attrs)[u'time_period']), dict(obs.attrs)[u'obs_value']]\
            for obs in soup.findAll('obs')]
df_ecb = pd.DataFrame(ls_ecb, columns = ['Date', 'Rate ECB ED'])
df_ecb.set_index('Date', inplace = True)

# REGROUP EIA + ECB IN ONE DATAFRAME
index = pd.date_range(start = pd.to_datetime('20121121'),
                      end   = pd.to_datetime('20140123'), 
                      freq='D')
df_all = pd.DataFrame(None, index = index)
for df_temp in [df_eia_brent, df_eia_diesel, df_ecb]:
  for column in df_temp:
    df_all[column] = df_temp[column]
print df_all.info()

df_all[['OK WTI Brent FOB DB', 'Europe Brent FOB DB']].plot()
plt.show()

df_all[['NY Diesel DG', 'Gulf Diesel DG', 'LA Diesel DG']].plot()
plt.show()
