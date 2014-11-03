#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *

path_dir_built_paper = os.path.join(path_data, u'data_gasoline', u'data_built', u'data_paper')
path_dir_built_csv = os.path.join(path_dir_built_paper, u'data_csv')
path_dir_built_json = os.path.join(path_dir_built_paper, 'data_json')

path_dir_insee_extracts = os.path.join(path_data, 'data_insee', 'data_extracts')

# #########################
# LOAD INFO STATIONS
# #########################

df_info = pd.read_csv(os.path.join(path_dir_built_csv,
                                   'df_station_info_final.csv'),
                      encoding = 'utf-8',
                      dtype = {'id_station' : str,
                               'adr_zip' : str,
                               'adr_dpt' : str,
                               'ci_1' : str,
                               'ci_ardt_1' :str,
                               'ci_2' : str,
                               'ci_ardt_2' : str,
                               'dpt' : str})
df_info.set_index('id_station', inplace = True)

# Active gas stations? Pick arbitrary day for now
#df_info = df_info[(~pd.isnull(df_info['start'])) &\
#                  (~pd.isnull(df_info['end']))])
#df_info = df_info[(df_info['start'] <= '2012-06-01') &\
#                  (df_info['end'] >= '2012-06-01')]
df_info = df_info[df_info['highway'] != 1]

# Total Access in brands... but could no more be (check by concatenating)
df_info['TA'] = 0
df_info.loc[(df_info['brand_0'] == 'TOTAL_ACCESS') |\
            (df_info['brand_1'] == 'TOTAL_ACCESS') |\
            (df_info['brand_2'] == 'TOTAL_ACCESS'),
            'TA'] = 1
print u'Nb Total Access (assume no exit of brand nor dupl.):', df_info['TA'].sum()

# Chge to Total Access recorded
df_info['TA_chge'] = 0
df_info.loc[(df_info['brand_0'] != 'TOTAL_ACCESS') &\
            (df_info['brand_1'] == 'TOTAL_ACCESS'),
            'TA_chge'] = 1
df_info.loc[(df_info['brand_1'] != 'TOTAL_ACCESS') &\
            (df_info['brand_2'] == 'TOTAL_ACCESS'),
            'TA_chge'] = 1
print u'Chge to Total Access:', df_info['TA_chge'].sum()

# ##############################
# TOTAL ACCESS WITHIN INSEE AREA
# ##############################

df_insee_areas = pd.read_csv(os.path.join(path_dir_insee_extracts,
                                          'df_insee_areas.csv'),
                             dtype = {'CODGEO' : str,
                                      'AU2010': str,
                                      'UU2010': str,
                                      'BV' : str},
                             encoding = 'utf-8')

df_info = df_info.reset_index().merge(df_insee_areas[['CODGEO', 'AU2010', 'UU2010', 'BV']],
                                      left_on = 'ci_1', right_on = 'CODGEO',
                                      how = 'left').set_index('id_station')

ls_areas = ['ci_1', 'AU2010', 'UU2010', 'BV']
df_ta = df_info[ls_areas].copy()
for area in ls_areas:
  df_ta_area = df_info[[area, 'TA']].groupby(area).agg([sum])['TA']
  #df_ta_area = df_info[[area, 'TA', 'TA_chge']].groupby(area).agg([sum])
  #df_ta_area.columns = ['_'.join(col).strip() for col in df_ta_area.columns.values]
  df_ta_area.rename(columns = {'sum': 'TA_%s' %area}, inplace = True)
  df_ta = df_ta.reset_index().merge(df_ta_area,
                                    left_on = area,
                                    right_index = True,
                                    how = 'left').set_index('id_station')
  df_ta.drop(area, axis = 1, inplace = True)

print '\nOverview of TAs within INSEE area', area

# Check % of TA within area
df_ta_area['Nb_%s' %area] = df_info[area].value_counts() # keep active only...
df_ta_area['Pct_TA'] = df_ta_area['TA_%s' %area] / df_ta_area['Nb_%s' %area]
df_ta_area.sort('Nb_%s' %area, ascending = False, inplace = True)

pd.set_option('float_format', '{:,.2f}'.format)
ls_dpt_ta_col_disp = ['Nb_%s' %area, 'TA_%s' %area, 'Pct_TA']

print '\nNb of areas:', len(df_ta_area)
nb_areas_no_TA = len(df_ta_area[df_ta_area['TA_%s' %area] == 0])
print 'Nb of areas with 0 TA:', nb_areas_no_TA

if nb_areas_no_TA > 10:
  #print '\nAreas with TA:'
  #print df_ta_area[ls_dpt_ta_col_disp][df_ta_area['TA_%s' %area] != 0].to_string()
  print '\nTop 50 biggest areas in terms of general count:'
  print df_ta_area[ls_dpt_ta_col_disp][0:50].to_string()
else:
  print '\nAll areas:'
  print df_ta_area[ls_dpt_ta_col_disp].to_string()

# Need ids of TAs within areas to find dates

# ################################
# TOTAL ACCESS WITHIN X KM RADIUS
# ################################

dict_ls_comp = dec_json(os.path.join(path_dir_built_json,
                                     'dict_ls_comp.json'))
dict_ls_comp = {k: sorted(v, key=lambda tup: tup[1]) for k,v in dict_ls_comp.items()}
ls_ta_ids = list(df_info.index[df_info['TA'] == 1])
ls_rows_ta_around = []
for id_station in df_info.index:
  ls_comp = dict_ls_comp.get(id_station, [])
  row_ta_around = [(id_comp, dist) for id_comp, dist in ls_comp\
                      if id_comp in ls_ta_ids]
  ls_rows_ta_around.append([x for ls_x in row_ta_around[0:2] for x in ls_x])
df_ta_around = pd.DataFrame(ls_rows_ta_around,
                            columns = ['id_cl_ta_0', 'dist_cl_ta_0',
                                       'id_cl_ta_1', 'dist_cl_ta_1'],
                            index = df_info.index)
df_ta = pd.merge(df_ta, df_ta_around,
                 left_index = True, right_index = True, how = 'left')

# #####################################
# POLICY PRICE CHANGE
# #####################################

df_prices = pd.read_csv(os.path.join(path_dir_built_csv, 'df_prices_ht_final.csv'),
                        parse_dates = ['date'])
df_prices.set_index('date', inplace = True)
ls_keep_ids = [id_station for id_station in df_prices.columns if\
                id_station in df_info.index]
df_prices = df_prices[ls_keep_ids]

se_mean_prices = df_prices.mean(1)
df_diff = df_prices.apply(lambda x: x - se_mean_prices, axis = 0)

# FIND BIG DIFFERENCE IN DIFF VS. NATIONAL PRICE (BEFORE TAX)
# TODO: robustness checks around 0.04

window_lim = 20
ls_mean_diffs, ls_index = [], []
for per_ind in range(window_lim, len(df_diff) - window_lim):
  ls_index.append(df_diff.index[per_ind]) # todo better
  mean_diff = df_diff.ix[:per_ind].mean(0) - df_diff[per_ind:].mean(0)
  ls_mean_diffs.append(mean_diff)
df_res = pd.concat(ls_mean_diffs, axis=1, keys =ls_index).T
se_res_max = df_res.max(0)
se_res_argmax = df_res.idxmax(0)
print '\nNb of detected price policy chges', len(se_res_max[se_res_max.abs() > 0.04])

df_ta['pp_chge'] = 0
df_ta.loc[list(se_res_max.index[se_res_max.abs() > 0.04]), 'pp_chge'] = 1
df_ta.loc[list(se_res_argmax.index[se_res_max.abs() > 0.04]), 'pp_chge_date'] = se_res_argmax

# check chge in policy not TA
df_info = pd.merge(df_info, df_ta,
                   left_index = True, right_index = True, how = 'left')
ls_disp = ['name', 'adr_city', 'adr_dpt', 'brand_0', 'brand_1', 'brand_2',
           'pp_chge_date', 'id_cl_ta_0', 'dist_cl_ta_0']
print df_info[ls_disp][(df_info['pp_chge'] == 1) & (df_info['TA'] != 1)].to_string()

## Not TA => Gvt announces?
#ax = df_prices[['93420001', '93420006']].plot()
#ax.axvline(x = pd.to_datetime('2012-10-15'), color = 'k', ls = 'dashed')
#ax.axvline(x = pd.to_datetime('2012-10-26'), color = 'k', ls = 'dashed')
#df_prices.mean(1).plot(ax = ax)
#plt.show()

# ###############
# OUTPUT
# ################

df_ta.to_csv(os.path.join(path_dir_built_csv,
                          'df_ta.csv'),
                          encoding = 'utf-8')

## ###############
## CHECK RESULTS
## ###############
#
## 94140002 (too few prices... inactive in the end with gap, sux)
#
## 95180001, 95180001: bad luck, supermarkets with play with prices
## 93120003: unsure why captured? bad luck?
#
## 93300008, 93420001, 93100006: seem legit (adjustment to competition?)
#
## EXAMPLE
#ls_ids_ta_check = [x for x in se_res_max.index[se_res_max.abs() > 0.04]\
#                     if x in df_info.index[df_info['TA'] == 1]]
#
#indiv_id = ls_ids_ta_check[0]
#
#plt.rcParams['figure.figsize'] = 16, 6
#ax = df_prices[indiv_id].plot()
#se_mean_prices.plot(ax=ax)
#handles, labels = ax.get_legend_handles_labels()
#ax.legend(handles, [indiv_id, u'mean price'], loc = 1)
#ax.axvline(x = se_res_argmax.ix[indiv_id], color = 'k', ls = 'dashed')
#plt.tight_layout()
#plt.show()
#
#
## ########
## MARGIN
## ########
#
#df_quotations = pd.read_csv(os.path.join(path_dir_built_csv, 'df_quotations.csv'),
#                        parse_dates = ['date'])
#df_quotations.set_index('date', inplace = True)
#df_quotations = df_quotations.ix[:'2013-06-04']
#
## Check graph 1
#ax = df_prices[indiv_id].plot()
#df_quotations['ULSD 10 CIF NWE R5 EL'].plot(ax=ax)
#plt.plot()
#
## Check graph 2
#df_quotations['france_prices'] = df_prices.mean(1)
#df_quotations['temp_prices'] = df_prices[indiv_id]
#df_quotations['temp_margin'] = df_quotations['temp_prices'] -\
#                                 df_quotations['ULSD 10 CIF NWE R5 EL']
#df_quotations['temp_margin'].plot()
#plt.show()
#
## Check graph 3
#from pylab import *
#rcParams['figure.figsize'] = 16, 6
#
#fig = plt.figure()
#ax1 = fig.add_subplot(111)
## ax1 = plt.subplot(frameon=False)
#line_1 = ax1.plot(df_quotations.index, df_quotations['temp_prices'].values,
#                  ls='--', c='b', label='Station price before tax')
#line_1[0].set_dashes([4,2])
#line_2 = ax1.plot(df_quotations.index, df_quotations['ULSD 10 CIF NWE R5 EL'].values,
#                  ls='--', c= 'g', label=r'Diesel cost')
#line_2[0].set_dashes([8,2])
#ax2 = ax1.twinx()
#line_3 = ax2.plot(df_quotations.index, df_quotations['temp_margin'].values,
#                  ls='-', c='r', label=r'Staton retail gross margin')
#
#lns = line_1 + line_2 + line_3
#labs = [l.get_label() for l in lns]
#ax1.legend(lns, labs, loc=0)
#
#ax1.grid()
##ax1.set_title(r"Title here")
#ax1.set_ylabel(r"Price and Cost (euros)")
#ax2.set_ylabel(r"Margin (euros)")
#plt.tight_layout()
#plt.show()

# #####################
# ARCHIVE: GRAPH SYNTAX
# #####################

#ax = df_price[['51520001','51000009', '51000007']].plot()
#handles, labels = ax.get_legend_handles_labels()
#ax.legend(handles, [u'Total Access', u'Intermarché', 'Esso'], loc = 1)
#plt.tight_layout()
#plt.show()

#ax = df_price[['avg_price', indiv_id]].plot(xlim = (df_price.index[0], df_price.index[-1]),
#                                            ylim=(1.2, 1.6))
#ax.axvline(x = se_argmax[indiv_id], color='k', ls='dashed')
#plt.savefig(os.path.join(path_dir_temp, 'chge_id_%s' %indiv_id))
#plt.close()
