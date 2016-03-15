#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import add_to_path
from add_to_path import *
from functions_generic_qlmc import *
from functions_maps import *
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import textwrap

path_built_csv = os.path.join(path_data,
                              'data_supermarkets',
                              'data_built',
                              'data_qlmc_2015',
                              'data_csv_201503')

path_lsa_csv = os.path.join(path_data,
                            'data_supermarkets',
                            'data_built',
                            'data_lsa',
                            'data_csv')

path_maps = os.path.join(path_data, 'data_maps')
path_geo_dpt = os.path.join(path_maps, 'GEOFLA_DPT_WGS84', 'DEPARTEMENT')
path_geo_com = os.path.join(path_maps, 'GEOFLA_COM_WGS84', 'COMMUNE')

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# ############
# LOAD DATA
# ############

# LOAD DF PRICES
df_prices = pd.read_csv(os.path.join(path_built_csv,
                                     'df_prices.csv'),
                        encoding = 'utf-8')


# LOAD DF STORES (INCLUDING LSA INFO)
df_stores = pd.read_csv(os.path.join(path_built_csv,
                                     'df_stores_final.csv'),
                        dtype = {'c_insee' : str,
                                 'id_lsa' : str},
                        encoding = 'utf-8')

df_lsa = pd.read_csv(os.path.join(path_lsa_csv,
                                  'df_lsa_active.csv'),
                     dtype = {u'id_lsa' : str,
                              u'c_insee' : str,
                              u'c_insee_ardt' : str,
                              u'c_postal' : str,
                              u'c_siren' : str,
                              u'c_nic' : str,
                              u'c_siret' : str},
                     parse_dates = [u'date_ouv', u'date_fer', u'date_reouv',
                                    u'date_chg_enseigne', u'date_chg_surface'],
                     encoding = 'utf-8')

df_stores = pd.merge(df_stores,
                     df_lsa[['id_lsa', 'enseigne_alt', 'groupe',
                            'surface', 'region',
                            'longitude', 'latitude']],
                     on = 'id_lsa',
                     how = 'left')

# BUILD DF QLMC WITH PRICE AND STORE INFO
# Restrict to leclerc (could drop rest?)
df_prices = df_prices[df_prices['store_chain'] == 'LECLERC'].copy()
df_prices.drop(['store_chain'], axis = 1, inplace = True) # in df_stores too
df_qlmc = pd.merge(df_prices,
                   df_stores,
                   left_on = 'store_id',
                   right_on = 'store_id',
                   how = 'left')
df_qlmc = df_qlmc[~df_qlmc['id_lsa'].isnull()]

# Avoid error msg on condition number
df_qlmc['surface'] = df_qlmc['surface'].apply(lambda x: x/1000.0)
# df_qlmc_prod['ac_hhi'] = df_qlmc_prod['ac_hhi'] * 10000
# Try with log of price (semi elasticity)
df_qlmc['ln_price'] = np.log(df_qlmc['price'])
# Control for dpt (region?)
df_qlmc['dpt'] = df_qlmc['c_insee'].str.slice(stop = 2)
pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# LOAD GEOGRAPHY
geo_france = GeoFrance(path_dpt = path_geo_dpt,
                       path_com = path_geo_com,
                       corse = True)
df_dpt = geo_france.df_dpt
df_com = geo_france.df_com

df_stores['point'] = df_stores[['longitude', 'latitude']].apply(\
                       lambda x: Point(geo_france.m_fra(x[0], x[1])), axis = 1)

# ADD STORE PRICE FREQUENCIES
df_store_fq = pd.read_csv(os.path.join(path_built_csv,
                                       'df_chain_store_price_freq.csv'),
                          encoding = 'utf-8')

df_store_fq.drop('store_chain', axis = 1, inplace = True)

df_stores = pd.merge(df_stores,
                     df_store_fq,
                     on = 'store_id',
                     how = 'left')

## ########
## BOX PLOT
## ########
#
#se_prod_vc = df_qlmc['product'].value_counts()
#df_prod_prices = df_qlmc[df_qlmc['product'].isin(se_prod_vc[0:1].index)]\
#                   [['product', 'price', 'store_id']].copy()
#df_prod_prices = df_prod_prices.pivot(index='store_id', columns='product', values='price')
## improve boxplot display
## http://matplotlib.org/examples/pylab_examples/boxplot_demo2.html
## todo: update matplotlib http://stackoverflow.com/questions/21997897/ (ctd)
## changing-what-the-ends-of-whiskers-represent-in-matplotlibs-boxplot-function
#ax = df_prod_prices.plot(kind = 'box') #, whis = [0.10, 0.90])
## ax.get_xticklabels()[0].get_text()
## textwrap.fill(ax.get_xticklabels()[0].get_text(), width = 20)
#ax.set_xticklabels([textwrap.fill(x.get_text(), 20) for x in ax.get_xticklabels()])
#plt.show()

# ########
# MAPS
# ########

# http://stackoverflow.com/questions/11885060/how-to-shade-points-in-scatter-based-on-colormap-in-matplotlib

# LECLERC: frequency of most common price

chain = 'LECLERC'
df_chain = df_stores[(df_stores['store_chain'] == chain) &\
                     (~df_stores['latitude'].isnull()) &\
                     (~df_stores['price_1'].isnull())].copy()

#df_dpt['patches'] = df_dpt['poly'].map(\
#                      lambda x: PolygonPatch(x,
#                                             facecolor='#FFFFFF', # '#555555'
#                                             edgecolor='#787878', # '#787878'
#                                             lw=.2,
#                                             alpha=.3,
#                                             zorder=1))
#fig = plt.figure()
#ax = fig.add_subplot(111, aspect = 'equal') #, frame_on = False)
#p = PatchCollection(df_dpt['patches'].values, match_original = True)
#ax.add_collection(p)
##geo_france.m_fra.drawcountries()
##geo_france.m_fra.drawcoastlines()
#ax.autoscale_view(True, True, True)
#ax.axis('off')
#plt.tight_layout()
#colors = df_chain['price_1'].values
#mymap = plt.get_cmap("Reds")
#my_colors = mymap(colors)
#ax.scatter([pt.x for pt in df_chain['point'].values],
#           [pt.y for pt in df_chain['point'].values],
#           s=30,
#           c=colors,
#           edgecolors='None',
#           cmap=mymap)
## plt.legend(scatterpoints=1)
#plt.tight_layout()
#plt.show()

df_chain.sort('price_1', ascending = False, inplace = True)
print(df_chain[['store_id', 'region', 'price_1', 'price_2', 'diff', 'no_ref']][0:20].to_string())
