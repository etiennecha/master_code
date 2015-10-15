#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *

path_dir_built_scraped = os.path.join(path_data,
                              u'data_gasoline',
                              u'data_built',
                              u'data_scraped_2011_2014')

path_dir_built_scraped_csv = os.path.join(path_dir_built_scraped,
                                          u'data_csv')

path_dir_built_scraped_json = os.path.join(path_dir_built_scraped,
                                           u'data_json')

path_dir_built_ta = os.path.join(path_data,
                                 u'data_gasoline',
                                 u'data_built',
                                 u'data_total_access')

path_dir_built_ta_csv = os.path.join(path_dir_built_ta, 
                                     'data_csv')

path_dir_built_graphs = os.path.join(path_dir_built_ta,
                                     'data_graphs')

# #########
# LOAD DATA
# #########

# DF STATION INFO

df_info = pd.read_csv(os.path.join(path_dir_built_scraped_csv,
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

# DF TOTAL ACCESS STATION INFO

df_info_ta = pd.read_csv(os.path.join(path_dir_built_ta_csv,
                                      'df_info_ta.csv'),
                         encoding = 'utf-8',
                         dtype = {'id_station' : str,
                                  'adr_zip' : str,
                                  'adr_dpt' : str,
                                  'ci_1' : str,
                                  'ci_ardt_1' :str,
                                  'ci_2' : str,
                                  'ci_ardt_2' : str,
                                  'dpt' : str},
                         parse_dates = [u'day_%s' %i for i in range(4)] +\
                                       ['pp_chge_date', 'ta_gov_date', 'ta_tot_date'])
df_info_ta.set_index('id_station', inplace = True)

# LOAD COMPETITION

dict_comp_dtype = {'id_ta_{:d}'.format(i) : str for i in range(23)}
dict_comp_dtype['id_station'] = str
df_comp = pd.read_csv(os.path.join(path_dir_built_scraped_csv,
                                   'df_comp.csv'),
                      dtype = dict_comp_dtype,
                      encoding = 'utf-8')
df_comp.set_index('id_station', inplace = True)

dict_close = dec_json(os.path.join(path_dir_built_scraped_json,
                                   'dict_ls_close.json'))

# LOAD PRICE STATS DES

df_price_stats = pd.read_csv(os.path.join(path_dir_built_scraped_csv,
                                          'df_station_stats.csv'),
                               dtype = {'id_station' : str},
                               encoding = 'utf-8')
df_price_stats.set_index('id_station', inplace = True)

# #################
# EXCLUDED STATIONS
# #################

# stations neither good for control nor for analysis

df_info['filter'] = 0

# exclude stations with insufficient (quality) price data
for df_temp in [df_price_stats[df_price_stats['nb_chge'] < 5],
                df_price_stats[df_price_stats['pct_chge'] < 0.03],
                df_price_stats[df_price_stats['nb_valid'] < 183]]:
  ls_exclude_temp = list(set(df_temp.index).intersection(set(df_info.index)))
  df_info.loc[ls_exclude_temp,
              'filter'] = 1

# exclude total access at beginning
ls_exclude_ta_beg = list(set(df_info_ta[df_info_ta['brand_0']  == 'TOTAL_ACCESS'].index)\
                                  .intersection(set(df_info.index)))
df_info.loc[df_info['brand_0'] == 'TOTAL_ACCESS',
            'filter'] = 1
# exclude total access ex total with small pp_chge
ls_exclude_ta_no_pp_chge = list(set(df_info_ta[(df_info_ta['brand_0'] == 'TOTAL') &\
                                               (df_info_ta['pp_chge'].abs() < 0.04)].index)\
                                  .intersection(set(df_info.index)))
df_info.loc[ls_exclude_ta_no_pp_chge,
            'filter'] = 2
# exclude total access previously non total
ls_exclude_ta_not_tot = list(set(df_info_ta[~df_info_ta['brand_0'].isin(['ELF', 'TOTAL'])].index)\
                                  .intersection(set(df_info.index)))
df_info.loc[ls_exclude_ta_not_tot,
            'filter'] = 3

# todo: exclude stations within 5 km of the last 3
ls_exclude_comp_of = ls_exclude_ta_beg +\
                       ls_exclude_ta_no_pp_chge +\
                         ls_exclude_ta_not_tot
ls_exclude_comp_of = list(set(ls_exclude_comp_of))

# ##############################
# COMPETITOR EXCLUSION
# ##############################

# todo: exclude competitors of ls_exclude_comp_of
ls_exclude_comp = []
for id_station in df_info.index:
  ls_close_temp = [x[0] for x in dict_close.get(id_station, []) if x[1] <= 5]
  if set(ls_close_temp).intersection(set(ls_exclude_comp_of)):
    ls_exclude_comp.append(id_station)
df_info.loc[ls_exclude_comp,
            'filter'] = 4

# #############################
# FINISH CLASSIFICATION
# #############################

df_ta_pp_chge = df_info_ta[(df_info_ta['brand_0'] == 'TOTAL') &\
                           (df_info_ta['pp_chge'].abs() >= 0.04)]
dict_ta_pp_chge = {row_i : list(row[['date_beg', 'date_end']].values)\
                     for row_i, row in df_ta_pp_chge.iterrows()}
df_info.loc[dict_ta_pp_chge.keys(),
            'filter'] = 5

df_ta_elf = df_info_ta[(df_info_ta['brand_0'] == 'ELF')]
dict_ta_elf = {row_i : list(row[['date_beg', 'date_end']].values)\
                 for row_i, row in df_ta_elf.iterrows()}
df_info.loc[dict_ta_pp_chge.keys(),
            'filter'] = 6

df_info.loc[(df_info['filter'] == 0) &\
            (df_info['brand_last'] == 'TOTAL'),
            'filter'] = 7

df_info.loc[(df_info['filter'] == 0) &\
            (df_info['brand_last'] == 'ELF'),
            'filter'] = 8

df_info.loc[(df_info['filter'] == 0) &\
            (df_info['brand_last'] == 'ELAN'),
            'filter'] = 9

df_info.loc[(df_info['filter'] == 0) &\
            (df_info['group_type_last'] == 'SUP'),
            'filter'] = 10

df_info.loc[(df_info['filter'] == 0) &\
            (df_info['group_type_last'] == 'OIL'),
            'filter'] = 11

# ##############################
# TREATED TA (W/ CHANGE) AND ELF
# ##############################

df_info['treatment_0'] = 0

# Caution: total access are also looped on here (got to exclude later)

# TOTAL W/ PP CHGE => TA treatment
# pick most recent date(s) (w/ id) if within X km

# ELF => TA treatment
# pick most recent date(s) (w/ id) within X km and no TA within 10 km


# todo: fill date_beg and date_end using some timedelta

ls_out_ids = []
ls_control_ids = []
ls_ta_pp_chge_treated = []
ls_ta_elf_treated = []
for row_i, row in df_comp.iterrows():
  ls_ta_temp = [[row['id_ta_{:d}'.format(i)], row['dist_ta_{:d}'.format(i)]]\
                  for i in range(23)]
  # ordered on distance: control if ta within 10 km else out of market
  # ls_ta_temp assumed to be ordered on distance
  if (pd.isnull(ls_ta_temp[0][1])) or (ls_ta_temp[0][1] > 10):
    ls_out_ids.append(row_i)
  elif ls_ta_temp[0][1] > 5:
    ls_control_ids.append(row_i)
  # ta and elf treatment
  ls_ta_pp_chge_temp = [x for x in ls_ta_temp if x[1] <= 5 and x[0] in dict_ta_pp_chge]
  ls_ta_elf_temp = [x for x in ls_ta_temp if x[1] <= 5 and x[0] in dict_ta_elf]
  if ls_ta_pp_chge_temp:
    ls_ta_pp_chge_temp = [tuple(x + dict_ta_pp_chge[x[0]]) for x in ls_ta_pp_chge_temp]
    ls_ta_pp_chge_temp = sorted(ls_ta_pp_chge_temp, key = lambda x: x[2])
    ls_ta_pp_chge_treated.append([row_i] + list(ls_ta_pp_chge_temp[0]))
  elif ls_ta_elf_temp:
    ls_ta_elf_temp = [x + dict_ta_elf[x[0]] for x in ls_ta_elf_temp]
    ls_ta_elf_temp = sorted(ls_ta_elf_temp, key = lambda x: x[2])
    ls_ta_elf_treated.append([row_i] + list(ls_ta_elf_temp[0]))

# TOTAL W/ PP CHGE => TA

# Add dates of relevant pp_chge in df_info (also value of pp_chge?)
df_info['id_total_ta'] = None
df_info['dist_total_ta'] = np.nan
df_info['pp_chge_total_ta'] = np.nan
df_info['date_min_total_ta'] = None # or pd.NaT
df_info['date_max_total_ta'] = None # or pd.NaT
for id_station, id_ta, dist, date_beg, date_end in ls_ta_pp_chge_treated:
  df_info.loc[id_station,
              ['id_total_ta',
               'dist_total_ta',
               'pp_chge_total_ta',
               'date_min_total_ta',
               'date_max_total_ta']] = [id_ta,
                                        dist,
                                        df_info_ta.ix[id_ta]['pp_chge'],
                                        date_beg,
                                        date_end]

# includes Total group stations (and possibly Total Access)
df_info.loc[(~pd.isnull(df_info['id_total_ta'])),
            'treatment_0'] = 1

# ELF => TA

# Add dates of relevant elf rebranding in df_info
df_info['id_elf_ta'] = None
df_info['dist_elf_ta'] = np.nan
df_info['date_min_elf_ta'] = None # or pd.NaT
df_info['date_max_elf_ta'] = None # or pd.NaT
for id_station, id_ta, dist, date_beg, date_end in ls_ta_elf_treated:
  df_info.loc[id_station,
              ['id_elf_ta',
               'dist_elf_ta',
               'date_min_elf_ta',
               'date_max_elf_ta']] = [id_ta,
                                      dist,
                                      date_beg,
                                      date_end]

df_info.loc[(~pd.isnull(df_info['id_elf_ta'])),
            'treatment_0'] = 2

# Control
df_info['control'] = 0
df_info.loc[ls_control_ids,
            'control'] = 1

df_info.loc[(df_info['control'] == 1),
            'treatment'] = 3

# Out of market(s): may miss those with no competitors
df_info['out'] = 0
df_info.loc[ls_out_ids,
            'out'] = 1
df_info.loc[(df_info['control'] == 1),
            'treatment'] = 4

# Not sure about those
df_info.loc[dict_ta_pp_chge.keys(),
            'treatment'] = 5

df_info.loc[dict_ta_elf.keys(),
            'treatment'] = 6

# ##########
# STATS DES
# ##########

print u'\nOverview of filter categorial variable:'
print df_info['filter'].value_counts().to_string()

print u'\nOverview of treatment categorical variable:'
print df_info['treatment'].value_counts().to_string()

# Caution: not done in treatment:
# - excluding station with incorrect data (filter 1)
# - excluding uncertain situations (filter 2:4)
# - distinguishing TOTAL group station (filter 7:9)
# - distinguishing non TOTAL group station (not in 1:9)

# #######
# OUTPUT
# #######
