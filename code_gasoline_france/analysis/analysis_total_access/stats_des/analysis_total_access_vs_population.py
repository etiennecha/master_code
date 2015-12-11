#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *

path_dir_built = os.path.join(path_data,
                              u'data_gasoline',
                              u'data_built',
                              u'data_scraped_2011_2014')
path_dir_built_csv = os.path.join(path_dir_built, u'data_csv')

path_dir_built_ta = os.path.join(path_data,
                                 u'data_gasoline',
                                 u'data_built',
                                 u'data_total_access')
path_dir_built_ta_csv = os.path.join(path_dir_built_ta, 'data_csv')
path_dir_built_ta_json = os.path.join(path_dir_built_ta, 'data_json')

# #########
# LOAD DATA
# #########

# DF STATION INFO

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
                               'dpt' : str},
                      parse_dates = [u'day_%s' %i for i in range(4)]) # fix
df_info.set_index('id_station', inplace = True)
df_info = df_info[df_info['highway'] != 1]

# DF PRICES

df_prices_ht = pd.read_csv(os.path.join(path_dir_built_csv,
                                        'df_prices_ht_final.csv'),
                           parse_dates = ['date'])
df_prices_ht.set_index('date', inplace = True)

df_prices_ttc = pd.read_csv(os.path.join(path_dir_built_csv,
                                        'df_prices_ttc_final.csv'),
                           parse_dates = ['date'])
df_prices_ttc.set_index('date', inplace = True)

ls_keep_ids = [id_station for id_station in df_prices.columns if\
                id_station in df_info.index]

df_prices = df_prices_ht[ls_keep_ids]

se_mean_prices = df_prices.mean(1)

# DF MARGIN CHGE

df_margin_chge = pd.read_csv(os.path.join(path_dir_built_csv,
                                          'df_margin_chge.csv'),
                             encoding = 'utf-8',
                             dtype = {'id_station' : str},
                             parse_dates = ['date'])
df_margin_chge.set_index('id_station', inplace = True)

# DICT TOTAL SA DATES

dict_ta_dates_str = dec_json(os.path.join(path_dir_built_ta_json))

## ##############################
## TOTAL ACCESS WITHIN INSEE AREA
## ##############################
#
#df_insee_areas = pd.read_csv(os.path.join(path_dir_insee_extracts,
#                                          'df_insee_areas.csv'),
#                             dtype = {'CODGEO' : str,
#                                      'AU2010': str,
#                                      'UU2010': str,
#                                      'BV' : str},
#                             encoding = 'utf-8')
#
#df_info = df_info.reset_index().merge(df_insee_areas[['CODGEO', 'AU2010', 'UU2010', 'BV']],
#                                      left_on = 'ci_1', right_on = 'CODGEO',
#                                      how = 'left').set_index('id_station')
#
#ls_areas = ['ci_1', 'AU2010', 'UU2010', 'BV']
#df_ta = df_info[ls_areas].copy()
#for area in ls_areas:
#  df_ta_area = df_info[[area, 'TA']].groupby(area).agg([sum])['TA']
#  #df_ta_area = df_info[[area, 'TA', 'TA_chge']].groupby(area).agg([sum])
#  #df_ta_area.columns = ['_'.join(col).strip() for col in df_ta_area.columns.values]
#  df_ta_area.rename(columns = {'sum': 'TA_%s' %area}, inplace = True)
#  df_ta = df_ta.reset_index().merge(df_ta_area,
#                                    left_on = area,
#                                    right_index = True,
#                                    how = 'left').set_index('id_station')
#  df_ta.drop(area, axis = 1, inplace = True)
#
#print '\nOverview of TAs within INSEE area', area
#
## Check % of TA within area
#df_ta_area['Nb_%s' %area] = df_info[area].value_counts() # keep active only...
#df_ta_area['Pct_TA'] = df_ta_area['TA_%s' %area] / df_ta_area['Nb_%s' %area]
#df_ta_area.sort('Nb_%s' %area, ascending = False, inplace = True)
#
#pd.set_option('float_format', '{:,.2f}'.format)
#ls_dpt_ta_col_disp = ['Nb_%s' %area, 'TA_%s' %area, 'Pct_TA']
#
#print '\nNb of areas:', len(df_ta_area)
#nb_areas_no_TA = len(df_ta_area[df_ta_area['TA_%s' %area] == 0])
#print 'Nb of areas with 0 TA:', nb_areas_no_TA
#
#if nb_areas_no_TA > 10:
#  #print '\nAreas with TA:'
#  #print df_ta_area[ls_dpt_ta_col_disp][df_ta_area['TA_%s' %area] != 0].to_string()
#  print '\nTop 20 biggest areas in terms of general count:'
#  print df_ta_area[ls_dpt_ta_col_disp][0:20].to_string()
#else:
#  print '\nAll areas:'
#  print df_ta_area[ls_dpt_ta_col_disp].to_string()
#
## Need ids of TAs within areas to find dates
#
## ################################
## TOTAL ACCESS WITHIN X KM RADIUS
## ################################
#
#dict_ls_comp = dec_json(os.path.join(path_dir_built_json,
#                                     'dict_ls_comp.json'))
#dict_ls_comp = {k: sorted(v, key=lambda tup: tup[1]) for k,v in dict_ls_comp.items()}
#ls_ta_ids = list(df_info.index[df_info['TA'] == 1])
#ls_rows_ta_around = []
#for id_station in df_info.index:
#  ls_comp = dict_ls_comp.get(id_station, [])
#  row_ta_around = [(id_comp, dist) for id_comp, dist in ls_comp\
#                      if id_comp in ls_ta_ids]
#  ls_rows_ta_around.append([x for ls_x in row_ta_around[0:2] for x in ls_x])
#df_ta_around = pd.DataFrame(ls_rows_ta_around,
#                            columns = ['id_cl_ta_0', 'dist_cl_ta_0',
#                                       'id_cl_ta_1', 'dist_cl_ta_1'],
#                            index = df_info.index)
#df_ta = pd.merge(df_ta, df_ta_around,
#                 left_index = True, right_index = True, how = 'left')
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
