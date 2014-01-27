#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import os, sys, codecs
import datetime, time
import pandas as pd
import matplotlib.pyplot as plt

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

path = os.path.abspath(os.path.dirname(sys.argv[0]))

dict_prices = dec_json(path + r'\20140124_ufip_data')

def convert_to_date(date_num):
  reference_date = datetime.datetime(1970,01,01)
  date = reference_date + datetime.timedelta(seconds=date_num/1000)
  return date.strftime('%Y%m%d')

for product, ls_ls_product_prices in dict_prices.items():
  ls_ls_product_prices = [[convert_to_date(date_num), price] for date_num, price in ls_ls_product_prices]
  dict_prices[product] = ls_ls_product_prices
  print '{:<20}'.format(product[0:20]), 'starts:', ls_ls_product_prices[0][0], ' ends:', ls_ls_product_prices[-1][0]

# Create empty DataFrame with full date range (daily)
index = pd.date_range(start = pd.to_datetime('20121121'),
                      end   = pd.to_datetime('20140123'), 
                      freq='D')
pd_df_all = pd.DataFrame(None, index = index)
# Add each series (could use join etc. but be cautious upon mergin not to lose data)
for product, ls_ls_product_prices in dict_prices.items():
  pd_df_all[product] = pd.Series([price for date_str, price in ls_ls_product_prices],
                             index = [pd.to_datetime(date_str) for date_str, price in ls_ls_product_prices])

print pd_df_all

# pd_df_all[['gazole_ttc', 'gazole_htt']].plot(style='o')
# plt.show()
# pd_df_all[['gazole','sp95']].plot()
# plt.show()
# # TODO: use matplotlib to have all on same graph

pd_df_all['spread'] = pd_df_all['gazole'] - pd_df_all['sp95']
pd_df_all['spread'].plot()