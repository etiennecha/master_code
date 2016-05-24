#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_ameli import *
from matching_insee import *
import numpy as np
import pandas as pd
import pprint
import matplotlib.pyplot as plt
import matplotlib.ticker as tkr
import matplotlib

matplotlib.rcParams.update({'font.size': 4})
pd.set_option('float_format', '{:,.1f}'.format)

path_built = os.path.join(path_data,
                          u'data_ameli',
                          u'data_built')

path_built_csv = os.path.join(path_built, 'data_csv')
path_built_json = os.path.join(path_built, u'data_json')
path_built_graphs = os.path.join(path_built, u'data_graphs')

path_dir_insee = os.path.join(path_data, u'data_insee')
path_dir_insee_extracts = os.path.join(path_dir_insee, 'data_extracts')

pd.set_option('float_format', '{:,.1f}'.format)

# ############
# LOAD DATA
# ############

# LOAD DF PHYSICIANS
file_extension = u'df_ophtalmo_suburb_2014'
df_physicians = pd.read_csv(os.path.join(path_built_csv,
                                         '{:s}.csv'.format(file_extension)),
                            dtype = {'zip': str,
                                     'CODGEO' : str},
                            encoding = 'utf-8')

## BIAS?
for field in ['c_base', 'c_proba', 'c_min', 'c_max']:
  df_physicians.loc[df_physicians['status'] == 'Hopital L',
                    field] = np.nan
df_physicians = df_physicians[df_physicians['status'] != 'Hopital L']

## todo: geog and distance in other script (try to separate creation vs. analysis)
#dict_gps = dec_json(os.path.join(path_dir_built_json, 'dict_gps_%s.json' %file_extension))

# LOAD INSEE DATA
df_inscom = pd.read_csv(os.path.join(path_dir_insee_extracts,
                                     'df_communes.csv'),
                        dtype = {'CODGEO': str,
                                 'LIBGEO': str,
                                 'REG': str,
                                 'DEP': str},
                        encoding = 'utf-8')

ls_disp_base = ['gender','name', 'surname', 'zip_city',
                'convention', 'carte_vitale', 'status', 'spe', 'nb_loc']

# DF AREA ALL
gb_area = df_physicians[['CODGEO', 'c_base']].groupby('CODGEO')
df_areas = gb_area.agg([len, np.mean, np.median])['c_base']
df_areas['len'] = df_areas['len'].astype(int)

# print df_areas.to_string()

df_areas.reset_index(inplace = True)
df_areas = pd.merge(df_areas,
                    df_inscom,
                    left_on = 'CODGEO',
                    right_on = 'CODGEO')
df_areas['phys_density'] = df_areas['len'] / df_areas['P10_POP'].astype(float)

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
print df_ardts[['CODGEO', 'LIBGEO', 'P10_POP',
                'nb_phy', 'phy_density', 'phy_s2_density'] +\
                ls_des_cols][df_ardts['P10_POP'] >= 20000].to_string()

phy = 'ophtalmologists'

dpi = 300
width, height = 12, 5
df_draw = df_ardts[df_ardts['P10_POP'] >= 30000].copy()
df_draw['ardt'] = df_draw['LIBGEO']

df_draw = df_draw[(~df_draw['QUAR2UC10'].isnull()) &\
                  (~df_draw['c_base_mean'].isnull()) &\
                  (~df_draw['ardt'].isnull()) &\
                  (~df_draw['P10_POP'].isnull())]

# exclude outlier neuilly sur seine (although favorable to story)
df_draw = df_draw[df_draw['ardt'] != u'Neuilly-sur-Seine']

#matplotlib.rcParams['axes.titlesize'] = 12
matplotlib.rcParams['axes.labelsize'] = 12

# Scatter: Density of GPs vs. Median revenue
fig, ax = plt.subplots()
ax.scatter(df_draw['QUAR2UC10'], df_draw['phy_density'], s=(df_draw['P10_POP']/1000.0))
for row_i, row in df_draw.iterrows():
  ax.annotate(row['ardt'], (row['QUAR2UC10'] - 300, row['phy_density'] + 0.8), size = 6)
x_format = tkr.FuncFormatter('{:,.0f}'.format)
ax.xaxis.set_major_formatter(x_format)
plt.xlabel('Median fiscal revenue by household (euros)')
plt.ylabel('Nb of %s per 100,000 inhab.' %phy)
plt.setp(ax.get_xticklabels(), fontsize=12)
plt.setp(ax.get_yticklabels(), fontsize=12)
#plt.title('Density of %s vs. revenue by district' %phy)
plt.tight_layout() 
ax.grid(True)
fig.set_size_inches(width, height)
plt.savefig(os.path.join(path_built_graphs, 'Ophtalmo_Idf_DensityVsRevenue.png'),
            dpi = dpi)
plt.close()
#plt.show()

# Scatter: Density of Sector 1 GPs vs. Median revenue
fig, ax = plt.subplots()
ax.scatter(df_draw['QUAR2UC10'], df_draw['phy_s1_density'], clip_on = False, zorder = 100)
for row_i, row in df_draw.iterrows():
  ax.annotate(row['ardt'], (row['QUAR2UC10'] - 300, row['phy_s1_density'] + 0.8), size = 6)
x_format = tkr.FuncFormatter('{:,.0f}'.format)
ax.xaxis.set_major_formatter(x_format)
plt.xlabel('Median fiscal revenue by household (euros)')
plt.ylabel('Nb of Sector 1 %s per 100,000 inhab.' %phy)
plt.setp(ax.get_xticklabels(), fontsize=12)
plt.setp(ax.get_yticklabels(), fontsize=12)
#plt.title('Density of Sector 1 %s vs. revenue by district' %phy)
plt.tight_layout() 
plt.ylim(0, plt.ylim()[1])
ax.grid(True)
fig.set_size_inches(width, height)
plt.savefig(os.path.join(path_built_graphs, 'Ophtalmo_Idf_DensityS1VsRevenue.png'),
            dpi = dpi)
plt.close()
#plt.show()

# Scatter: Density of Sector 2 GPs vs. Median revenue
fig, ax = plt.subplots()
ax.scatter(df_draw['QUAR2UC10'], df_draw['phy_s2_density'])
for row_i, row in df_draw.iterrows():
  ax.annotate(row['ardt'], (row['QUAR2UC10'] - 300, row['phy_s2_density'] + 0.8), size=6)
x_format = tkr.FuncFormatter('{:,.0f}'.format)
ax.xaxis.set_major_formatter(x_format)
plt.xlabel('Median fiscal revenue by household (euros)')
# Add precision about households
plt.ylabel('Nb of Sector 2 %s per 100,000 inhab.' %phy)
plt.setp(ax.get_xticklabels(), fontsize=12)
plt.setp(ax.get_yticklabels(), fontsize=12)
#plt.title('Density of Sector 2 %s vs. revenue by district' %phy)
plt.tight_layout() 
ax.grid(True)
fig.set_size_inches(width, height)
plt.savefig(os.path.join(path_built_graphs, 'Ophtalmo_Idf_DensityS2VsRevenue.png'),
            dpi = dpi)
plt.close()
#plt.show()

# Scatter: Average consultation price vs. Median revenue
fig, ax = plt.subplots()
# s=(df_draw['c_base_count']*16)
ax.scatter(df_draw['QUAR2UC10'], df_draw['c_base_mean'], s=(df_draw['P10_POP']/1000.0))
for row_i, row in df_draw.iterrows():
  ax.annotate(row['ardt'], (row['QUAR2UC10'] - 300, row['c_base_mean'] + 0.8), size = 6)
x_format = tkr.FuncFormatter('{:,.0f}'.format)
ax.xaxis.set_major_formatter(x_format)
plt.xlabel('Median fiscal revenue by household (euros)')
plt.ylabel('Average sector 2 consultation price (euros)')
plt.setp(ax.get_xticklabels(), fontsize=12)
plt.setp(ax.get_yticklabels(), fontsize=12)
#plt.title('Average consultation price vs. revenue by district')
plt.tight_layout()
ax.grid(True)
fig.set_size_inches(width, height)
plt.savefig(os.path.join(path_built_graphs, 'Ophtalmo_Idf_ConsultationS2VsRevenue.png'),
            dpi = dpi)
plt.close()
#plt.show()

# Scatter: improve label display locations

def get_text_positions(x_data, y_data, txt_width, txt_height):
  a = zip(y_data, x_data)
  text_positions = list(y_data)
  for index, (y, x) in enumerate(a):
    local_text_positions = [i for i in a if i[0] > (y - txt_height) 
                              and (abs(i[1] - x) < txt_width * 2) and i != (y,x)]
    if local_text_positions:
      sorted_ltp = sorted(local_text_positions)
      if abs(sorted_ltp[0][0] - y) < txt_height: #True == collision
        differ = np.diff(sorted_ltp, axis=0)
        a[index] = (sorted_ltp[-1][0] + txt_height, a[index][1])
        text_positions[index] = sorted_ltp[-1][0] + txt_height*1.01
        for k, (j, m) in enumerate(differ):
          #j is the vertical distance between words
          if j > txt_height * 2: #if True then room to fit a word in
            a[index] = (sorted_ltp[k][0] + txt_height, a[index][1])
            text_positions[index] = sorted_ltp[k][0] + txt_height
            break
  return text_positions

def text_plotter(text, x_data, y_data, text_positions, txt_width,txt_height):
  for z,x,y,t in zip(text, x_data, y_data, text_positions):
    plt.annotate(z, xy=(x-txt_width/2, t + 0.5), size=6)
    if y != t:
      plt.arrow(x, t,0,y-t, color='red',alpha=0.3, width=txt_width*0.05, 
          head_width=txt_width/2,
          head_length=txt_height*0.5, 
          zorder=0,
          length_includes_head=True)


fig, ax = plt.subplots()
p1 = ax.scatter(df_draw['QUAR2UC10'], df_draw['c_base_mean'], s=(df_draw['P10_POP']/1000.0))
txt_height = 0.04*(plt.ylim()[1] - plt.ylim()[0])
txt_width = 0.02*(plt.xlim()[1] - plt.xlim()[0])
text_positions = get_text_positions(df_draw['QUAR2UC10'].values,
                                    df_draw['c_base_mean'].values,
                                    txt_width,
                                    txt_height)
text_plotter(df_draw['ardt'].values,
             df_draw['QUAR2UC10'].values,
             df_draw['c_base_mean'].values,
             text_positions,
             txt_width,
             txt_height)
plt.xlabel('Median fiscal revenue by household (euros)')
plt.ylabel('Average sector 2 consultation price (euros)')
plt.setp(ax.get_xticklabels(), fontsize=12)
plt.setp(ax.get_yticklabels(), fontsize=12)
ax.grid(True)
fig.set_size_inches(width, height)
plt.savefig(os.path.join(path_built_graphs, 'Ophtalmo_Idf_ConsultationS2VsRevenue_alt.png'),
            dpi = dpi)
plt.close()

# ############
# TODO: UPDATE
# ############

## Seems differences linked largely to status / convention
#
#import statsmodels.formula.api as smf
#df_physicians_s2 = df_physicians[df_physicians['convention'] == '2'].copy()
#df_physicians_s2 = pd.merge(df_physicians_s2, df_ardts, left_on = 'CODGEO', right_on = 'CODGEO')
#
#formula = 'c_base ~ C(status) + phy_density + QUAR2UC10'
#res01 = smf.ols(formula = formula, data = df_physicians_s2, missing= 'drop').fit()
#print res01.summary()
#
## ADD age
#
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
#
## UPDATE FOLLOWING
#
### COMPANY CREATION DATE
##path_dir_societe = os.path.join(path_data, u'data_ameli', 'data_source', u'societe')
##dict_results = dec_json(os.path.join(path_dir_societe, u'societe_dict_ophtalmo'))
##ls_no_result = dec_json(os.path.join(path_dir_societe, u'societe_ls_no_result_ophtalmo'))
##
##dict_ste_physicians = {}
##for id_physician, info_physician in dict_results.items():
##  if u'médecin' in info_physician[2][0]:
##    dict_ste_physicians[id_physician] = info_physician[:2] +\
##                                        [[elt.strip() if elt else elt\
##                                           for elt in info_physician[3]]]
##  else:
##    dict_results[id_physician][2] =\
##      [elt.strip() if elt else elt\
##        for elt in info_physician[2][0].replace('\n', '').split(';')]
##    dict_results[id_physician][3] =\
##      [elt.strip() if elt else elt for elt in info_physician[3]]
##    print '\n', id_physician
##    pprint.pprint(dict_results[id_physician])
##
##df_physicians['immatriculation'] = None
##for id_physician, info_physician in dict_ste_physicians.items():
##  len_info_ste = len(info_physician[2])
##  ls_titles = [info_physician[2][i] for i in range(len_info_ste) if i%2 == 0]
##  ls_contents = [info_physician[2][i] for i in range(len_info_ste) if i%2 != 0]
##  dict_info_ste = dict(zip(ls_titles, ls_contents))
##  dict_ste_physicians[id_physician][2] = dict_info_ste 
##  # print id_physician, dict_info_ste.get('Immatriculation')
##  df_physicians.ix[id_physician, 'immatriculation'] = dict_info_ste.get('Immatriculation')
##df_physicians['immatriculation'] =\
##  df_physicians['immatriculation'].apply(lambda x: float(x[-4:]) if x else None)
##
### Some info wrong: 1900 => 2000 after verification with other site
##df_physicians['immatriculation'][df_physicians['immatriculation'] == 1900] = 2000
### Misses 5
### df_physicians['zip_city'][df_physicians['zip_city'].str.startswith('75116')] = '75016 PARIS'
##df_temp = df_physicians[(df_physicians['convention'] == '1') |\
##                        (df_physicians['convention'] == '2')]
##import statsmodels.formula.api as smf
##formula = 'consultation ~ C(zip_city) + immatriculation + C(convention)'
##res01 = smf.ols(formula = formula, data = df_temp, missing= 'drop').fit()
##print res01.summary()
##
### todo: investigate immatriculation... might be better to use age
### todo: represent nb of immatriculation (& status) per year (cf zagaz registrations)
### todo: represent tarif by year of immatriculation...
##
### CHECK OSM ROUTE SERVICE : http://wiki.openstreetmap.org/wiki/OpenRouteService
