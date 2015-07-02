#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *

pd.set_option('float_format', '{:,.3f}'.format)

path_dir_built_paper = os.path.join(path_data,
                                    u'data_gasoline',
                                    u'data_built',
                                    u'data_paper_total_access')


path_dir_built_csv = os.path.join(path_dir_built_paper,
                                  u'data_csv')

df_tta_res = pd.read_csv(os.path.join(path_dir_built_csv,
                                      'df_tta_by_dpt_final.csv'),
                         dtype = {'id_ta' : str},
                         encoding = 'utf-8')

df_elfta_res = pd.read_csv(os.path.join(path_dir_built_csv,
                                        'df_elfta_by_dpt_final.csv'),
                           dtype = {'id_ta' : str},
                           encoding = 'utf-8')
