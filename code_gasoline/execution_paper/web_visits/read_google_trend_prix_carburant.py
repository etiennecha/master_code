#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import add_to_path_sub
from add_to_path_sub import path_data
from generic_master_price import *
from generic_master_info import *

path_dir_source = os.path.join(path_data, 'data_gasoline', 'data_source')

path_dir_web_visits = os.path.join(path_dir_source, 'data_web_visits')
path_csv_google_trend = os.path.join(path_dir_web_visits, u'20140422_google_trend_prix_carburant.csv')
path_dir_rotterdam = os.path.join(path_dir_source, 'data_rotterdam')
path_xlsx_ufip = os.path.join(path_dir_rotterdam, 'ufip-valeurs_2006-01-01_au_2013-12-31.xlsx')

# Google Trend File
str_file = open(path_csv_google_trend, 'r').read()
ls_rows = [row.split(',') for row in str_file.split('\n')[4:543]]
df_trend = pd.DataFrame(ls_rows[1:], columns = ls_rows[0])

df_trend.index = df_trend['Semaine'].apply(lambda x: pd.to_datetime(x[0:10]))
df_trend.rename(columns = {'prix carburant' : 'prix_carburant',
                           'prix essence' : 'prix_essence',
                           'prix diesel' : 'prix_diesel'}, inplace = True)
for col in ['prix_carburant', 'prix_essence', 'prix_diesel']:
  df_trend[col] = df_trend[col].apply(lambda x: float(x))

#df_trend[['prix_carburant', 'prix_essence', 'prix_diesel']].plot()
#df_trend['prix_carburant']['2010':].plot()
## todo: output?

# Ufip file
ufip_excel_file = pd.ExcelFile(path_xlsx_ufip)
df_ufip = ufip_excel_file.parse('Worksheet')
#ls_u_drop = ['GAZOLE TTC', 'GAZOLE HTT',
#             'SP95 HTT', 'SP95 TTC',
#             'FOD HTT', 'FOD TTC', 'FOD (Rotterdam)']
#df_ufip.drop(ls_u_drop, inplace = True, axis = 1)
dict_u_cols = {u'Marge de raffinage (€/t)': 'UFIP Ref margin ET',
               u'GAZOLE (Rotterdam)'      : 'UFIP RT Diesel R5 EL',
               u'SP95 (Rotterdam)'        : 'UFIP RT SP95 R5 EL',
               u'Brent ($ / baril)'       : 'UFIP Brent R5 DB',
               u'Brent (€ / baril)'       : 'UFIP Brent R5 EB',
               u'Parité (€/$)'            : 'UFIP Rate ED'}
df_ufip = df_ufip.rename(columns = dict_u_cols)
df_ufip.set_index('Date', inplace = True)

df_weekly_prices = df_ufip[df_ufip.columns[:4]][~pd.isnull(df_ufip['GAZOLE TTC'])]
df_weekly_prices.index = pd.Series(df_weekly_prices.index).apply(lambda x: \
                           x + pd.tseries.offsets.timedelta(days=2))
df_weekly_prices['trend'] = df_trend['prix_carburant']/100 + 0.9

df_weekly_prices[['trend', 'GAZOLE TTC']].plot()
plt.show()
