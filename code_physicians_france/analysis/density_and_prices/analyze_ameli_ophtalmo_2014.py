#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_ameli import *
import numpy as np
import pandas as pd
import pprint
import matplotlib.pyplot as plt
import matplotlib.ticker as tkr
import statsmodels.formula.api as smf

path_built = os.path.join(path_data,
                          u'data_ameli',
                          u'data_built')

path_built_csv = os.path.join(path_built, 'data_csv')
path_built_json = os.path.join(path_built, u'data_json')
path_built_graphs = os.path.join(path_built, u'data_graphs')

path_dir_insee = os.path.join(path_data, u'data_insee')
path_dir_insee_extracts = os.path.join(path_dir_insee, 'data_extracts')

pd.set_option('float_format', '{:,.0f}'.format)

# ############
# LOAD DATA
# ############

# LOAD DF PHYSICIANS
file_extension = u'df_ophtalmo_75_2014'
df_physicians = pd.read_csv(os.path.join(path_built_csv,
                                         '%s.csv' %file_extension),
                            dtype = {'zip': str,
                                     'CODGEO' : str},
                            encoding = 'utf-8')

lsd0 = ['gender','name', 'surname', 'zip_city',
        'convention', 'carte_vitale', 'status', 'spe', 'nb_loc']

## BIAS?
for field in ['c_base', 'c_proba', 'c_min', 'c_max']:
  df_physicians.loc[df_physicians['status'] == 'Hopital L',
                    field] = np.nan
df_physicians = df_physicians[df_physicians['status'] != 'Hopital L']

# LOAD INSEE DATA
df_inscom = pd.read_csv(os.path.join(path_dir_insee_extracts,
                                     'df_communes.csv'),
                        dtype = {'CODGEO': str,
                                 'LIBGEO': str,
                                 'REG': str,
                                 'DEP': str},
                        encoding = 'utf-8')

df_inscom['PCT_65P'] = df_inscom[['P10_POP6074', 'P10_POP75P']].sum(1) /\
                         df_inscom['P10_POP'].astype(float) * 100
df_inscom['PCT_75P'] = df_inscom['P10_POP75P'] /\
                         df_inscom['P10_POP'].astype(float) * 100
df_inscom['PCT_14M'] = df_inscom['P10_POP0014'] /\
                         df_inscom['P10_POP'].astype(float) * 100

# Pop and Revenue: thousand inhabitants / euros
df_inscom['P10_POP'] = df_inscom['P10_POP'] / 1000.0
df_inscom['QUAR2UC10'] = df_inscom['QUAR2UC10'] / 1000.0

# AGGREGATE BY AREA
col_area = 'CODGEO'
ls_area_rows = []
for area in df_physicians[col_area].unique():
  df_area = df_physicians[df_physicians[col_area] == area]
  df_area_s1 = df_area[df_area['convention'].str.contains('1', na = False)]
  df_area_s2 = df_area[df_area['convention'].str.contains('2', na = False)]
  df_s2_desc = df_area_s2['c_base'].describe()
  ls_s2_desc_val = list(df_s2_desc.values)
  ls_area_rows.append([area,
                       len(df_area),
                       len(df_area_s1),
                       len(df_area_s2)] +\
                       ls_s2_desc_val)

ls_s2_desc_cols = ['c_base_%s' %x for x in list(df_s2_desc.index)]
ls_columns = [col_area, 'nb_tot', 'nb_s1', 'nb_s2'] + ls_s2_desc_cols
df_agg = pd.DataFrame(ls_area_rows, columns = ls_columns)

df_agg = pd.merge(df_agg,
                  df_inscom,
                  left_on = col_area,
                  right_on = col_area)

# Density per 100,000 inhabitant
df_agg['density_tot'] = df_agg['nb_tot'] * 100 / df_agg['P10_POP'].astype(float)
df_agg['density_s1'] = df_agg['nb_s1'] * 100 / df_agg['P10_POP'].astype(float)
df_agg['density_s2'] = df_agg['nb_s2'] * 100 / df_agg['P10_POP'].astype(float)

# ADHOC FOR GRAPHS: get arrondissement from CODGEO
df_ardts = df_agg.copy()
df_ardts['ardt'] = df_ardts['CODGEO'].str.slice(start = 3)

# ############
# STATS DES
# ############

df_ardts.sort(col_area, ascending = True, inplace = True)

# nb: count gives number of prices known for physicians in sector 2
print ''
print df_ardts[[col_area, 'P10_POP', 'PCT_65P', 'QUAR2UC10',
                'density_tot', 'density_s2',
                'c_base_count', 'c_base_mean', 'c_base_std', ]].to_string()

# Paris overall
print ''
print 'Stats Paris Overall'
print df_inscom[df_inscom['CODGEO'] == '75056'].T
print df_ardts['nb_tot'].sum() / df_inscom[df_inscom['CODGEO'] == '75056']\
                                          ['P10_POP'].astype(float) * 100
print df_ardts['nb_s2'].sum() / df_inscom[df_inscom['CODGEO'] == '75056']\
                                          ['P10_POP'].astype(float) * 100
print df_physicians['c_base'].describe()

phy = 'ophtalmologists'

dpi = 300
width, height = 12, 5

# Scatter: Density of GPs vs. Median revenue
df_ardts['ardt'] = df_ardts['CODGEO'].str.slice(start = 3)
fig, ax = plt.subplots()
ax.scatter(df_ardts['QUAR2UC10'], df_ardts['density_tot'])
for row_i, row in df_ardts.iterrows():
  ax.annotate(row['ardt'], (row['QUAR2UC10'], row['density_tot'] + 1))
x_format = tkr.FuncFormatter('{:,.0f}'.format)
ax.xaxis.set_major_formatter(x_format)
plt.xlabel('Median fiscal revenue by household (euros)')
plt.ylabel('Nb of %s per 100,000 inhab.' %phy)
ax.grid(True)
#plt.title('Density of %s vs. revenue by district' %phy)
plt.tight_layout() 
fig.set_size_inches(width, height)
plt.savefig(os.path.join(path_built_graphs, 'Ophtalmo_Ardt_DensityVsRevenue.png'),
            dpi = dpi)
plt.close()
#plt.show()

# Scatter: Density of Sector 1 GPs vs. Median revenue
df_ardts['ardt'] = df_ardts['CODGEO'].str.slice(start = 3)
fig, ax = plt.subplots()
ax.scatter(df_ardts['QUAR2UC10'], df_ardts['density_s1'], clip_on = False, zorder = 100)
for row_i, row in df_ardts.iterrows():
  ax.annotate(row['ardt'], (row['QUAR2UC10'], row['density_s1'] + 0.3))
x_format = tkr.FuncFormatter('{:,.0f}'.format)
ax.xaxis.set_major_formatter(x_format)
plt.xlabel('Median fiscal revenue by household (euros)')
plt.ylabel('Nb of Sector 1 %s per 100,000 inhab.' %phy)
plt.ylim(0, plt.ylim()[1])
ax.grid(True)
#plt.title('Density of Sector 1 %s vs. revenue by district' %phy)
plt.tight_layout() 
fig.set_size_inches(width, height)
plt.savefig(os.path.join(path_built_graphs, 'Ophtalmo_Ardt_DensityS1VsRevenue.png'),
            dpi = dpi)
plt.close()
#plt.show()

# Scatter: Density of Sector 2 GPs vs. Median revenue
df_ardts['ardt'] = df_ardts['CODGEO'].str.slice(start = 3)
fig, ax = plt.subplots()
ax.scatter(df_ardts['QUAR2UC10'], df_ardts['density_s2'], clip_on = False, zorder = 100)
for row_i, row in df_ardts.iterrows():
  ax.annotate(row['ardt'], (row['QUAR2UC10'], row['density_s2'] + 1))
x_format = tkr.FuncFormatter('{:,.0f}'.format)
ax.xaxis.set_major_formatter(x_format)
plt.xlabel('Median fiscal revenue by household (euros)')
# Add precision about households
plt.ylabel('Nb of Sector 2 %s per 100,000 inhab.' %phy)
#plt.title('Density of Sector 2 %s vs. revenue by district' %phy)
plt.ylim(0, plt.ylim()[1])
ax.grid(True)
plt.tight_layout() 
fig.set_size_inches(width, height)
plt.savefig(os.path.join(path_built_graphs, 'Ophtalmo_Ardt_DensityS2VsRevenue.png'),
            dpi = dpi)
plt.close()
plt.show()

# Scatter: Average consultation price vs. Median revenue
df_ardts['ardt'] = df_ardts['CODGEO'].str.slice(start = 3)
fig, ax = plt.subplots()
ax.scatter(df_ardts['QUAR2UC10'], df_ardts['c_base_mean']) # ,s=(df_ardts['c_base_count']*16))
for row_i, row in df_ardts.iterrows():
  ax.annotate(row['ardt'], (row['QUAR2UC10'], row['c_base_mean'] + 2))
x_format = tkr.FuncFormatter('{:,.0f}'.format)
ax.xaxis.set_major_formatter(x_format)
plt.xlabel('Median fiscal revenue by household (euros)')
plt.ylabel('Average sector 2 consultation price (euros)')
#plt.title('Average consultation price vs. revenue by district')
ax.grid(True)
plt.tight_layout() 
fig.set_size_inches(width, height)

plt.savefig(os.path.join(path_built_graphs, 'Ophtalmo_Ardt_ConsultationS2VsRevenue.png'),
            dpi = dpi)
plt.close()
#plt.show()

# REGRESSIONS
df_ardts = df_ardts[df_ardts['c_base_count'] >= 5] # not enough obs
for formula in ['c_base_mean ~  QUAR2UC10',
                'density_s2 ~ QUAR2UC10',
                'c_base_mean ~ PCT_65P',
                'c_base_mean ~ PCT_65P + QUAR2UC10',
                'density_s2 ~ PCT_65P + QUAR2UC10']:
  res02 = smf.ols(formula = formula,
                  data = df_ardts,
                  missing= 'drop').fit()
  print ''
  print res02.summary()

## Check spread (s2 only... investigate status differences)
#df_physicians_s2['spread'] = df_physicians_s2['c_max'] - df_physicians_s2['c_base']
#ls_spread = []
#for ardt in df_physicians_s2['CODGEO'].unique():
#	ls_spread.append(df_physicians_s2['spread'][df_physicians_s2['CODGEO'] == ardt].describe())
#df_spread = pd.concat(ls_spread, axis = 1, keys = df_physicians_s2['CODGEO'].unique()).T
#df_spread.sort('count', ascending = False, inplace = True)
#print df_spread.to_string()
#
#plt.scatter(df_physicians_s2['spread'], df_physicians_s2['c_proba'])
#plt.show()

## INDIV REGS
#df_physicians_s2 = df_physicians[df_physicians['convention'] == '2'].copy()
#df_physicians_s2 = pd.merge(df_physicians_s2,
#                            df_ardts,
#                            left_on = col_area,
#                            right_on = col_area)
#formula = 'c_base ~ C(status) + density_tot + QUAR2UC10'
#res01 = smf.ols(formula = formula, data = df_physicians_s2, missing= 'drop').fit()
#print ''
#print res01.summary()

# #################
# UPDATE FOLLOWING
# #################

## COMPANY CREATION DATE
#path_dir_societe = os.path.join(path_data, u'data_ameli', 'data_source', u'societe')
#dict_results = dec_json(os.path.join(path_dir_societe, u'societe_dict_ophtalmo'))
#ls_no_result = dec_json(os.path.join(path_dir_societe, u'societe_ls_no_result_ophtalmo'))
#
#dict_ste_physicians = {}
#for id_physician, info_physician in dict_results.items():
#  if u'médecin' in info_physician[2][0]:
#    dict_ste_physicians[id_physician] = info_physician[:2] +\
#                                        [[elt.strip() if elt else elt\
#                                           for elt in info_physician[3]]]
#  else:
#    dict_results[id_physician][2] =\
#      [elt.strip() if elt else elt\
#        for elt in info_physician[2][0].replace('\n', '').split(';')]
#    dict_results[id_physician][3] =\
#      [elt.strip() if elt else elt for elt in info_physician[3]]
#    print '\n', id_physician
#    pprint.pprint(dict_results[id_physician])
#
#df_physicians['immatriculation'] = None
#for id_physician, info_physician in dict_ste_physicians.items():
#  len_info_ste = len(info_physician[2])
#  ls_titles = [info_physician[2][i] for i in range(len_info_ste) if i%2 == 0]
#  ls_contents = [info_physician[2][i] for i in range(len_info_ste) if i%2 != 0]
#  dict_info_ste = dict(zip(ls_titles, ls_contents))
#  dict_ste_physicians[id_physician][2] = dict_info_ste 
#  # print id_physician, dict_info_ste.get('Immatriculation')
#  df_physicians.ix[id_physician, 'immatriculation'] = dict_info_ste.get('Immatriculation')
#df_physicians['immatriculation'] =\
#  df_physicians['immatriculation'].apply(lambda x: float(x[-4:]) if x else None)
#
## Some info wrong: 1900 => 2000 after verification with other site
#df_physicians['immatriculation'][df_physicians['immatriculation'] == 1900] = 2000
## Misses 5
## df_physicians['zip_city'][df_physicians['zip_city'].str.startswith('75116')] = '75016 PARIS'
#df_temp = df_physicians[(df_physicians['convention'] == '1') |\
#                        (df_physicians['convention'] == '2')]
#import statsmodels.formula.api as smf
#formula = 'consultation ~ C(zip_city) + immatriculation + C(convention)'
#res01 = smf.ols(formula = formula, data = df_temp, missing= 'drop').fit()
#print res01.summary()
#
## todo: investigate immatriculation... might be better to use age
## todo: represent nb of immatriculation (& status) per year (cf zagaz registrations)
## todo: represent tarif by year of immatriculation...
#
## CHECK OSM ROUTE SERVICE : http://wiki.openstreetmap.org/wiki/OpenRouteService
