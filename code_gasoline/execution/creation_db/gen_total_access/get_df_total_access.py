#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *

path_dir_built_paper = os.path.join(path_data, u'data_gasoline', u'data_built', u'data_paper')
path_dir_built_csv = os.path.join(path_dir_built_paper, u'data_csv')

df_info = pd.read_csv(os.path.join(path_dir_built_csv,
                                           'df_station_info.csv'),
                              encoding = 'utf-8',
                              dtype = {'id_station' : str,
                                       'adr_zip' : str,
                                       'adr_dpt' : str,
                                       'ci_1' : str,
                                       'ci_ardt_1' :str,
                                       'ci_2' : str,
                                       'ci_ardt_2' : str,
                                       'dpt' : str})

# Active gas stations? Pick arbitrary day for now
#df_info = df_info[(~pd.isnull(df_info['start'])) &\
#                  (~pd.isnull(df_info['end']))])
df_info = df_info[(df_info['start'] <= '2012-06-01') &\
                  (df_info['end'] >= '2012-06-01')]

# Total Access in brands... but could no more be (check by concatenating)
df_info['TA'] = 0
df_info['TA'][(df_info['brand_0'] == 'TOTAL_ACCESS') |\
              (df_info['brand_1'] == 'TOTAL_ACCESS') |\
              (df_info['brand_2'] == 'TOTAL_ACCESS')] = 1
print u'Nb Total Access (assume no exit of brand nor dupl.):', df_info['TA'].sum()

# Chge to Total Access recorded
df_info['TA_chge'] = 0
df_info['TA_chge'][(df_info['brand_0'] != 'TOTAL_ACCESS') &\
                   (df_info['brand_1'] == 'TOTAL_ACCESS')] = 1
df_info['TA_chge'][(df_info['brand_1'] != 'TOTAL_ACCESS') &\
                   (df_info['brand_2'] == 'TOTAL_ACCESS')] = 1
print u'Chge to Total Access:', df_info['TA_chge'].sum()

# Total Access within area
area = 'ci_1'
df_dpt_ta = df_info[[area, 'TA']].groupby(area).agg([sum])['TA']
df_dpt_ta.rename(columns = {'sum': 'TA_%s' %area}, inplace = True)

df_ta = pd.merge(df_dpt_ta, df_info,
                 left_index = True, right_on = area,
                 how = 'outer')

# Check % of TA within area
df_dpt_ta['Nb_%s' %area] = df_info[area].value_counts() # keep active only...
df_dpt_ta['Pct_TA'] = df_dpt_ta['TA_%s' %area] / df_dpt_ta['Nb_%s' %area]
df_dpt_ta.sort('Nb_%s' %area, ascending = False, inplace = True)

# Need to adapt if a lot of 0
pd.set_option('float_format', '{:,.2f}'.format)
ls_dpt_ta_col_disp = ['Nb_%s' %area, 'TA_%s' %area, 'Pct_TA']

print '\nNb of areas:', len(df_dpt_ta)
nb_areas_no_TA = len(df_dpt_ta[df_dpt_ta['TA_%s' %area] == 0])
print 'Nb of areas with 0 TA:', nb_areas_no_TA

if nb_areas_no_TA > 10:
  print '\nAreas with TA:'
  print df_dpt_ta[ls_dpt_ta_col_disp][df_dpt_ta['TA_%s' %area] != 0].to_string()
  print '\nTop 50 biggest areas in terms of general count:'
  print df_dpt_ta[ls_dpt_ta_col_disp][0:50].to_string()
else:
  print '\nAll areas:'
  print df_dpt_ta[ls_dpt_ta_col_disp].to_string()

# Need ids of TAs within areas to find dates
