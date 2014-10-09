#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_ameli import *
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as tkr

# ############
# LOAD DATA
# ############

# LOAD AMELI DATA
path_dir_ameli = os.path.join(path_data, u'data_ameli', 'data_source', 'ameli_2014')
path_dir_built_csv= os.path.join(path_data, u'data_ameli', 'data_built', 'csv')
path_dir_built_json = os.path.join(path_data, u'data_ameli', 'data_built', 'json')
path_dir_built_png = os.path.join(path_data, u'data_ameli', 'data_built', 'png')
#path_dir_built_hdf5 = os.path.join(path_data, u'data_ameli', 'data_built', 'hdf5')
#ameli_data = pd.HDFStore(os.path.join(path_dir_built_hdf5, 'ameli_data.h5'))

file_extension = u'generaliste_75_2014'
df_physicians = pd.read_csv(os.path.join(path_dir_built_csv, '%s.csv' %file_extension),
                            encoding = 'utf-8')

## todo: geog and distance in other script (try to separate creation vs. analysis)
#dict_gps = dec_json(os.path.join(path_dir_built_json, 'dict_gps_%s.json' %file_extension))

# LOAD INSEE DATA
path_dir_insee = os.path.join(path_data, u'data_insee')
path_dir_insee_extracts = os.path.join(path_dir_insee, 'data_extracts')
df_inscom = pd.read_csv(os.path.join(path_dir_insee_extracts, 'df_communes.csv'),
                        dtype = {'CODGEO': np.object_,
                                 'LIBGEO': np.object_,
                                 'REG': np.object_,
                                 'DEP': np.object_})

ls_disp_base = ['gender','name', 'surname', 'zip_city',
                'convention', 'carte_vitale', 'status', 'spe', 'nb_loc']

# ############
# STATS DES
# ############
pd.set_option('float_format', '{:,.1f}'.format)

# ARDT

df_physicians['zip'] = df_physicians['zip_city'].str.slice(stop = 5)
df_physicians['CODGEO'] = df_physicians['zip'].apply(\
                            lambda x: re.sub(u'750([0-9]{2})', u'751\\1', x))

## DF ARDT ALL
#gb_ardt = df_physicians[['CODGEO', 'c_base']].groupby('CODGEO')
#df_ardts = gb_ardt.agg([len, np.mean, np.median])['c_base']
#df_ardts['len'] = df_ardts['len'].astype(int)
#print df_ardts.to_string()
#df_ardts.reset_index(inplace = True)
#df_ardts = pd.merge(df_ardts, df_inscom, left_on = 'CODGEO', right_on = 'CODGEO')
#df_ardts['phys_density'] = df_ardts['len'] / df_ardts['P10_POP'].astype(float)

# DF ARDT COMPREHENSIVE
# todo: try also with min and max price (then may want to restrict), also spread?
ls_ardt_rows = []
for ardt in df_physicians['CODGEO'].unique():
  df_ardt = df_physicians[df_physicians['CODGEO'] == ardt]
  nb_phy = len(df_ardt)
  nb_phy_s1 = len(df_ardt[df_ardt['convention'].isin(['1', '1 AS', '1 DPD'])])
  nb_phy_s2 = len(df_ardt[df_ardt['convention'].isin(['2', '2 AS'])])
  df_ardt_s2 = df_ardt[df_ardt['convention'].isin(['2', '2 AS'])]
  des_c_base_s2 = df_ardt_s2['c_base'].describe()
  ls_c_base_s2_val = list(des_c_base_s2.values)
  ls_ardt_rows.append([ardt, nb_phy, nb_phy_s1, nb_phy_s2] + ls_c_base_s2_val)

ls_des_cols = ['c_base_%s' %x for x in list(des_c_base_s2.index)]

ls_columns = ['CODGEO', 'nb_phy', 'nb_phy_s1', 'nb_phy_s2'] + ls_des_cols
             
df_ardts = pd.DataFrame(ls_ardt_rows, columns = ls_columns)

df_ardts = pd.merge(df_ardts, df_inscom, left_on = 'CODGEO', right_on = 'CODGEO')
df_ardts['phy_density'] = df_ardts['nb_phy'] * 100000 / df_ardts['P10_POP'].astype(float)
df_ardts['phy_s1_density'] = df_ardts['nb_phy_s1'] * 100000 / df_ardts['P10_POP'].astype(float)
df_ardts['phy_s2_density'] = df_ardts['nb_phy_s2'] * 100000 / df_ardts['P10_POP'].astype(float)

# nb: count gives number of prices known for physicians in sector 2
print df_ardts[['CODGEO', 'phy_density', 'phy_s2_density'] +\
               ls_des_cols].to_string()

dpi = 300
width, height = 12, 5

# Scatter: Density of GPs vs. Median revenue
df_ardts['ardt'] = df_ardts['CODGEO'].str.slice(start = 3)
fig, ax = plt.subplots()
ax.scatter(df_ardts['QUAR2UC10'], df_ardts['phy_density'])
for row_i, row in df_ardts.iterrows():
  ax.annotate(row['ardt'], (row['QUAR2UC10'], row['phy_density'] + 3))
x_format = tkr.FuncFormatter('{:,.0f}'.format)
ax.xaxis.set_major_formatter(x_format)
plt.xlabel('Median fiscal revenue by household (euros)')
plt.ylabel('Nb of GPs per 100,000 inhab.')
#plt.title('Density of GPs vs. revenue by district')
plt.tight_layout() 
fig.set_size_inches(width, height)
plt.savefig(os.path.join(path_dir_built_png, 'GP_Ardt_DensityVsRevenue.png'),
            dpi = dpi)
#plt.show()

# Scatter: Density of Sector 1 GPs vs. Median revenue
df_ardts['ardt'] = df_ardts['CODGEO'].str.slice(start = 3)
fig, ax = plt.subplots()
ax.scatter(df_ardts['QUAR2UC10'], df_ardts['phy_s1_density'])
for row_i, row in df_ardts.iterrows():
  ax.annotate(row['ardt'], (row['QUAR2UC10'], row['phy_s1_density'] + 2))
x_format = tkr.FuncFormatter('{:,.0f}'.format)
ax.xaxis.set_major_formatter(x_format)
plt.xlabel('Median fiscal revenue by household (euros)')
plt.ylabel('Nb of Sector 1 GPs per 100,000 inhab.')
#plt.title('Density of Sector 1 GPs vs. revenue by district')
plt.tight_layout()
fig.set_size_inches(width, height)
plt.savefig(os.path.join(path_dir_built_png, 'GP_Ardt_DensityS1VsRevenue.png'),
            dpi = dpi)
#plt.show()

# Scatter: Density of Sector 2 GPs vs. Median revenue
df_ardts['ardt'] = df_ardts['CODGEO'].str.slice(start = 3)
fig, ax = plt.subplots()
ax.scatter(df_ardts['QUAR2UC10'], df_ardts['phy_s2_density'])
for row_i, row in df_ardts.iterrows():
  ax.annotate(row['ardt'], (row['QUAR2UC10'], row['phy_s2_density'] + 2))
x_format = tkr.FuncFormatter('{:,.0f}'.format)
ax.xaxis.set_major_formatter(x_format)
plt.xlabel('Median fiscal revenue by household (euros)')
plt.ylabel('Nb of Sector 2 GPs per 100,000 inhab.')
#plt.title('Density of Sector 2 GPs vs. revenue by district')
plt.tight_layout()
fig.set_size_inches(width, height)
plt.savefig(os.path.join(path_dir_built_png, 'GP_Ardt_DensityS2VsRevenue.png'),
            dpi = dpi)
#plt.show()

# Scatter: Average consultation price vs. Median revenue
df_ardts['ardt'] = df_ardts['CODGEO'].str.slice(start = 3)
fig, ax = plt.subplots()
ax.scatter(df_ardts['QUAR2UC10'], df_ardts['c_base_mean'])
for row_i, row in df_ardts.iterrows():
  ax.annotate(row['ardt'], (row['QUAR2UC10'], row['c_base_mean'] + 1))
x_format = tkr.FuncFormatter('{:,.0f}'.format)
ax.xaxis.set_major_formatter(x_format)
plt.xlabel('Median fiscal revenue by household (euros)')
plt.ylabel('Average sector 2 consultation price (euros)')
#plt.title('Average sector 2 consultation price vs. revenue by district')
plt.tight_layout()
fig.set_size_inches(width, height)
plt.savefig(os.path.join(path_dir_built_png, 'GP_Ardt_ConsultationS2VsRevenue.png'),
            dpi = dpi)
#plt.show()

# Seems differences linked largely to status / convention

import statsmodels.formula.api as smf
df_physicians_s2 = df_physicians[df_physicians['convention'] == '2'].copy()
df_physicians_s2 = pd.merge(df_physicians_s2, df_ardts, left_on = 'CODGEO', right_on = 'CODGEO')

formula = 'c_base ~ C(status) + phy_density + QUAR2UC10'
res01 = smf.ols(formula = formula, data = df_physicians_s2, missing= 'drop').fit()
print res01.summary()

# ADD age

# Check spread (s2 only... investigate status differences)
df_physicians_s2['spread'] = df_physicians_s2['c_max'] - df_physicians_s2['c_base']
ls_spread = []
for ardt in df_physicians_s2['CODGEO'].unique():
	ls_spread.append(df_physicians_s2['spread'][df_physicians_s2['CODGEO'] == ardt].describe())
df_spread = pd.concat(ls_spread, axis = 1, keys = df_physicians_s2['CODGEO'].unique()).T
df_spread.sort('count', ascending = False, inplace = True)
print df_spread.to_string()
