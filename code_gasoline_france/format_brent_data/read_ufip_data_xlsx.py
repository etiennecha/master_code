#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import os, sys, codecs
import datetime, time
import pandas as pd
import matplotlib.pyplot as plt

path = os.path.abspath(os.path.dirname(sys.argv[0]))
path_excel_file = path + r'\ufip-valeurs_2006-01-01_au_2013-12-31.xlsx'
excel_file = pd.ExcelFile(path_excel_file)
df = excel_file.parse('Worksheet')
df = df.set_index('Date')
# excel_file.sheet_names
print df.info()

# df[['SP95 (Rotterdam)','GAZOLE (Rotterdam)']].plot()
# plt.show()

# df[['GAZOLE TTC', 'GAZOLE HTT']].plot(style='o')
# plt.show()

df['margin_gazole'] = df['GAZOLE HTT'] - df['GAZOLE (Rotterdam)']
# df['margin_gazole'].plot(style='o')

df['margin_gazole_filled'] = df['margin_gazole'].interpolate()

df_margin = df[['margin_gazole', 'GAZOLE (Rotterdam)']][pd.notnull(df['margin_gazole'])]
print df_margin.corr()

# df_margin[['margin_gazole', 'GAZOLE (Rotterdam)']][0:100].plot()
# plt.show()

# CORRELATION BETWEEN MARGIN AND PRICE CHANGES: STRONGLY NEGATIVE

df_margin['margin_gazole_var'] = df_margin['margin_gazole'] - df_margin['margin_gazole'].shift(1)
df_margin['GAZOLE (Rotterdam)_var'] = df_margin['GAZOLE (Rotterdam)'] - df_margin['GAZOLE (Rotterdam)'].shift(1)

# df_margin[['margin_gazole_var', 'GAZOLE (Rotterdam)_var']][0:172].plot()
# df_margin[['margin_gazole_var', 'GAZOLE (Rotterdam)_var']][172:].plot()

print df_margin[['margin_gazole_var', 'GAZOLE (Rotterdam)_var']][:172].corr()
print df_margin[['margin_gazole_var', 'GAZOLE (Rotterdam)_var']][172:].corr()
print df_margin[['margin_gazole_var', 'GAZOLE (Rotterdam)_var']].corr()

# WITH "ONE WEEK" SHIFT (APPROXIMATE DUE TO AVAIL. DATES): STRONGLY POSITIVE

df_margin['GAZOLE (Rotterdam)_var_sh'] = df_margin['GAZOLE (Rotterdam)_var'].shift(1)

# df_margin[['margin_gazole_var', 'GAZOLE (Rotterdam)_var_sh']][:172].plot()
# df_margin[['margin_gazole_var', 'GAZOLE (Rotterdam)_var_sh']][172:].plot()

print df_margin[['margin_gazole_var', 'GAZOLE (Rotterdam)_var_sh']][:172].corr()
print df_margin[['margin_gazole_var', 'GAZOLE (Rotterdam)_var_sh']][172:].corr()
print df_margin[['margin_gazole_var', 'GAZOLE (Rotterdam)_var_sh']].corr()
