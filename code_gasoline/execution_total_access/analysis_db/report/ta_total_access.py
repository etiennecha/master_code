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

df_insee_areas = pd.read_csv(os.path.join(path_dir_insee_extracts, 'df_insee_areas.csv'),
                             encoding = 'UTF-8')
df_au_agg = pd.read_csv(os.path.join(path_dir_insee_extracts, 'df_au_agg_final.csv'),
                        encoding = 'UTF-8')
df_uu_agg = pd.read_csv(os.path.join(path_dir_insee_extracts, 'df_uu_agg_final.csv'),
                        encoding = 'UTF-8')
df_com = pd.read_csv(os.path.join(path_dir_insee_extracts, 'data_insee_extract.csv'),
                     encoding = 'UTF-8', dtype = {'DEP': str, 'CODGEO' : str})

# GET RID OF DOMTOM AND CORSICA
df_com = df_com[~(df_com['DEP'].isin(['2A', '2B', '971', '972', '973', '974']))]

df_com['CODGEO'] = df_com['CODGEO'].apply(\
                         lambda x: "{:05d}".format(x)\
                           if (type(x) == np.int64 or type(x) == long) else x)

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

dict_rename_lib = {u'Marseille - Aix-en-Provence' : u'Marseille - Aix',
                   u'(partie française)' : u'(fr)',
                   u'Clermont-Ferrand' : u'Clermont-Fer.'}

def rename_field(some_str, dict_rename):
  for k,v in dict_rename.items():
    some_str = some_str.replace(k,v).strip()
  return some_str

# Same except: 'AU2010' / 'UU2010', 'LIBAU2010' / 'LIBUU2010'
# Also need to sort and drop nan
df_uu_agg.sort('P10_POP', ascending = False, inplace = True)
df_uu_agg = df_uu_agg[~pd.isnull(df_uu_agg['P10_POP'])]

# NB STORES BY UU IN A GIVEN PERIOD
df_uu_agg.set_index('UU2010', inplace = True)
se_au_vc = df_info_ta['UU2010'].value_counts()
df_uu_agg['Nb TA'] = se_au_vc

# RENAME AU2010 FOR OUTPUT
df_uu_agg['LIBUU2010'] = df_uu_agg['LIBUU2010'].apply(\
                           lambda x: rename_field(x, dict_rename_lib))

## TODO: add pop by station and vehicle by station

df_uu_agg.rename(columns = {'P10_POP' : 'Pop',
                            'LIBUU2010': 'Area',
                            'POPDENSITY10': 'Pop density',
                            'QUAR2UC10' : 'Med rev'}, inplace = True)

ls_disp_au = ['Area', 'Pop', 'Pop density', 'Med rev', 'Nb TA']

print u'\nTop 20 Aires Urbaines in terms of inhabitants'
print df_uu_agg[ls_disp_au][0:20].to_string(index = False,
                                            index_names = False)

print df_uu_agg[ls_disp_au][~pd.isnull(df_uu_agg['Nb TA'])].to_string(index = False,
                                                                      index_names = False)
