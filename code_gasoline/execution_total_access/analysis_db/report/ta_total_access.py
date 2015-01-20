#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *

path_dir_built_paper = os.path.join(path_data,
                                    u'data_gasoline',
                                    u'data_built',
                                    u'data_paper_total_access')

path_dir_built_csv = os.path.join(path_dir_built_paper,
                                  u'data_csv')

path_dir_built_graphs = os.path.join(path_dir_built_paper,
                                     'data_graphs')

path_dir_insee = os.path.join(path_data, 'data_insee')
path_dir_insee_match = os.path.join(path_dir_insee, 'match_insee_codes')
path_dir_insee_extracts = os.path.join(path_dir_insee, 'data_extracts')

pd.set_option('float_format', '{:10,.0f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# #############
# READ INFO TA
# #############

df_info_ta = pd.read_csv(os.path.join(path_dir_built_csv,
                                      'df_info_ta_fixed.csv'),
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
                                       ['pp_chge_date', 'ta_chge_date'])
df_info_ta.set_index('id_station', inplace = True)

# ################
# LOAD INSEE DATA
# ################

# todo: fix pbms with num vs. string (CODEGEO in particular)

df_insee_areas = pd.read_csv(os.path.join(path_dir_insee_extracts,
                                          'df_insee_areas.csv'),
                             dtype = {'CODGEO' : str,
                                      'UU2010' : str,
                                      'AU2010' : str,
                                      'BV2010' : str},
                             encoding = 'UTF-8')

df_au_agg = pd.read_csv(os.path.join(path_dir_insee_extracts,
                                     'df_au_agg_final.csv'),
                        dtype = {'AU2010' : str,
                                 'CODGEO_CT' : str},
                        encoding = 'UTF-8')
df_au_agg.set_index('AU2010', inplace = True)

df_uu_agg = pd.read_csv(os.path.join(path_dir_insee_extracts,
                                     'df_uu_agg_final.csv'),
                        dtype = {'UU2010' : str,
                                 'CODGEO_CT' : str},
                        encoding = 'UTF-8')
df_uu_agg.set_index('UU2010', inplace = True)

#df_bv_agg = pd.read_csv(os.path.join(path_dir_insee_extracts,
#                                     'df_bv_agg_final.csv'),
#                        dtype = {'BV2010' : str,
#                                 'CODGEO_CT' : str},
#                        encoding = 'UTF-8')
#df_bv_agg.set_index('BV2010', inplace = True)


df_com = pd.read_csv(os.path.join(path_dir_insee_extracts,
                                  'data_insee_extract.csv'),
                     dtype = {'DEP': str,
                              'CODGEO' : str},
                     encoding = 'UTF-8')
df_com = df_com[~(df_com['DEP'].isin(['2A', '2B', '971', '972', '973', '974']))]
df_com.set_index('CODGEO', inplace = True)

# #######################
# ADD INSEE AREA CODES
# #######################

# i.e. Store viewpoint: add commune char

df_info_ta = pd.merge(df_insee_areas,
                      df_info_ta,
                      left_on = 'CODGEO',
                      right_on = 'ci_ardt_1',
                      how = 'right')

# ##########################
# ANALYSIS AT UU LEVEL
# ##########################

# Exclude rural areas etc.
df_uu_agg = df_uu_agg[~(df_uu_agg['LIBUU2010'].str.contains('rurales'))]
df_au_agg = df_au_agg[(df_au_agg.index != '000') &
                      (df_au_agg.index != '997') &
                      (df_au_agg.index != '998')]

ls_insee_area_loop = [[df_uu_agg, 'UU'],
                      [df_au_agg, 'AU']]

dict_rename_lib = {u'Marseille - Aix-en-Provence' : u'Marseille - Aix',
                   u'(partie française)' : u'(fr)',
                   u'Clermont-Ferrand' : u'Clermont-Fer.'}

def rename_field(some_str, dict_rename):
  for k,v in dict_rename.items():
    some_str = some_str.replace(k,v).strip()
  return some_str

for df_insee_areas, insee_area in ls_insee_area_loop:
  # avoid error message due to overwriting of dataframe
  df_insee_areas = df_insee_areas.copy()
  df_insee_areas.sort('P10_POP', ascending = False, inplace = True)
  df_insee_areas = df_insee_areas[~pd.isnull(df_insee_areas['P10_POP'])]
  
  # NB STORES BY AREA IN A GIVEN PERIOD
  se_ia_vc = df_info_ta['%s2010' %insee_area].value_counts()
  df_insee_areas['Nb TA'] = se_ia_vc
  
  # RENAME AREA FOR DISPLAY
  df_insee_areas['LIB%s2010' %insee_area] =\
     df_insee_areas['LIB%s2010' %insee_area].apply(\
        lambda x: rename_field(x, dict_rename_lib))
  
  ## todo: add pop by station and vehicle by station
  
  df_insee_areas.rename(columns = {'P10_POP' : 'Pop',
                                   'LIB%s2010' % insee_area : 'Area',
                                   'POPDENSITY10': 'Pop density',
                                   'QUAR2UC10' : 'Med rev'}, inplace = True)
  
  ls_disp = ['Area', 'Pop', 'Pop density', 'Med rev', 'Nb TA']
  
  df_insee_areas['Pop by TA'] = df_insee_areas['Pop'] / df_insee_areas['Nb TA']
  
  print u'\nTop 20 %s in terms of inhabitants:' %insee_area
  print df_insee_areas[ls_disp + ['Pop by TA']][0:20].to_string(index = False,
                                                              index_names = False)
  
  df_insee_areas.sort('Nb TA', inplace = True, ascending = False)
  print u'\nTop 20 %s in terms of TA count:' %insee_area
  print df_insee_areas[ls_disp + ['Pop by TA']][~pd.isnull(df_insee_areas['Nb TA'])][0:30].\
          to_string(index = False, index_names = False)
  
  print u'\nPopulation living in %s with at least one Total Access:' %insee_area
  print u'{:10,.0f}'.format(df_insee_areas['Pop'][~pd.isnull(df_insee_areas['Nb TA'])].sum())
