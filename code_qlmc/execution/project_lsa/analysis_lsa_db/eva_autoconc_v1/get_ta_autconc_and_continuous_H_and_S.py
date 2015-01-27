#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
from functions_geocoding import *

path_dir_qlmc = os.path.join(path_data, 'data_qlmc')
path_dir_built_csv = os.path.join(path_dir_qlmc, 'data_built' , 'data_csv')
path_dir_built_png = os.path.join(path_dir_qlmc, 'data_built' , 'data_png')
path_dir_built_json = os.path.join(path_dir_qlmc, 'data_built' , 'data_json_qlmc')

pd.set_option('float_format', '{:10,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# #################
# LOAD DF EVAL COMP
# #################

df_hvh = pd.read_csv(os.path.join(path_dir_built_csv,
                                  'df_eval_compH_v_H.csv'),
                     dtype = {u'Code INSEE' : str,
                              u'Code INSEE ardt' : str,
                              u'N°Siren' : str,
                              u'N°Siret' : str},
                     parse_dates = [u'DATE ouv', u'DATE ferm', u'DATE réouv',
                                    u'DATE chg enseigne', u'DATE chgt surf'],
                     encoding = 'latin-1')

ls_disp_lsa = [u'Enseigne',
               u'ADRESSE1',
               u'Code postal',
               u'Ville'] # u'Latitude', u'Longitude']

ls_disp_lsa_comp = ls_disp_lsa + ['ac_nb_stores', 'ac_nb_chains', 'ac_nb_comp',
                                  'ac_store_share', 'store_share',
                                  'ac_group_share', 'group_share',
                                  'ac_hhi', 'hhi']

print df_hvh['ac_nb_chains'].describe()
print df_hvh['ac_group_share'].describe()
print len(df_hvh[(df_hvh['ac_nb_chains'] < 4) &\
                 (df_hvh['ac_group_share'] > 0.5)])
