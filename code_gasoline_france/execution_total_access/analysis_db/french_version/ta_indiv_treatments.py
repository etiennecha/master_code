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

dist = 5
diff = 0.02

df_tta_dist = df_tta_res[df_tta_res['distance'] <= dist]
df_tta_dist_sup = df_tta_dist[df_tta_dist['group_type'] == 'SUP']
df_tta_dist_oth = df_tta_dist[df_tta_dist['group_type'] != 'SUP']

df_elfta_dist     = df_elfta_res[df_elfta_res['distance'] <= dist]
df_elfta_dist_sup = df_elfta_dist[df_elfta_dist['group_type'] == 'SUP']
df_elfta_dist_oth = df_elfta_dist[df_elfta_dist['group_type'] != 'SUP']

# OVERVIEW QUANTILES

ls_loop_overview = [['T-TA', 'All', df_tta_dist],
                    ['T-TA', 'Sup', df_tta_dist_sup],
                    ['T-TA', 'Oth', df_tta_dist_oth],
                    ['E-TA', 'All', df_elfta_dist],
                    ['E-TA', 'Sup', df_elfta_dist_sup],
                    ['E-TA', 'Oth', df_elfta_dist_oth]]

ls_percentiles = [0.1, 0.25, 0.5, 0.75, 0.9]

print 'Max distance: {:.2f} km'.format(dist)
print 'Value threshold: {:.3f} euros'.format(diff)

for pop, pop_type, df_temp in ls_loop_overview:
  print u'\nOverview {:s} ({:s}):'.format(pop, pop_type)
  print df_temp.describe(percentiles = ls_percentiles)
  print u'Less than -{:.3f} : {:.2f} %'.format(diff,
          100 * len(df_temp[df_temp['coeff'] <= - diff]) / float(len(df_temp)))
  print u'More than  {:.3f} : {:.2f} %'.format(diff,\
          100 * len(df_temp[df_temp['coeff'] >= diff]) / float(len(df_temp)))
  print u'In bewteen       : {:.2f} %'.format(\
          100 * len(df_temp[df_temp['coeff'].abs() < diff]) / float(len(df_temp)))
