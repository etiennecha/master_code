#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
import os, sys
import pandas as pd
import re

"""
From standardized txt files, output:
- basic utf-8 csv files (indiv + aggregated)
- excel-friendly latin-1 csv files (indiv + aggregated)
- excel files (aggregated only: one sheet per journal / university)
"""

# temp fix to use openpyxl
pd.core.format.header_style = None

path_source = os.path.join(path_data,
                           u'data_econ_academics',
                           u'data_source')
path_source_txt = os.path.join(path_source, u'data_txt')

path_built = os.path.join(path_data,
                           u'data_econ_academics',
                           u'data_built')
path_built_csv = os.path.join(path_built, u'data_csv')
path_built_xls = os.path.join(path_built, u'data_xls')

for dir_name in [u'publications', u'phd', 'literature']:
  
  path_dir_temp = os.path.join(path_source_txt, dir_name)
  ls_file_names = [x for x in os.listdir(path_dir_temp)]
  # if x[:4] == u'Econ'] # cannot use with phd hence no security
  
  # open excel writer: one sheet by iteration in file loop
  writer = pd.ExcelWriter(os.path.join(path_built_xls,
                                       u'{:s}.xlsx'.format(dir_name)))
  writer.date_format = None # Workaround for date formatting
  writer.datetime_format = None  # This one for datetime
  
  # create subfolders to output each subfile
  for path_subdir_temp in [path_built_csv]:
    if not os.path.exists(os.path.join(path_subdir_temp, dir_name)):
      os.mkdir(os.path.join(path_subdir_temp, dir_name))

  ls_df_econ = []
  for file_name in ls_file_names:
    journal_title = file_name.replace(u'.txt', u'').replace(u'Econ_', u'')
    path_input = os.path.join(path_source_txt, dir_name, file_name)
  
    econ = open(path_input, 'r').read()
    econ = econ.decode("utf-8-sig") #.encode("utf-8")
    #econ = econ.rstrip('\xef\xbb\xbf') # get rid of beginning of file
    ls_obs = econ.split('\n\n')
    ls_ls_obs = [x.split('\n') for x in ls_obs]
    # get rid of annoying 'This record' (could do it on first split btw...)
    ls_ls_obs = [[obs for obs in ls_obs if obs[:11] != u'This record']\
                   for ls_obs in ls_ls_obs]
    ls_dict_obs = [{obs[0:2]: obs[3:].strip() for obs in ls_obs} for ls_obs in ls_ls_obs]
    # get list of variables
    set_vars = set()
    for dict_obs in ls_dict_obs:
      set_vars.update(set(dict_obs.keys()))
    ls_vars = list(set_vars)
    ls_rows = [[dict_obs.get(var, '') for var in ls_vars] for dict_obs in ls_dict_obs]
    df_econ = pd.DataFrame(ls_rows,
                           columns = ls_vars)
  
    # basic csv
    df_econ.to_csv(os.path.join(path_built_csv,
                                dir_name,
                                u'df_{:s}.csv'.format(journal_title)),
                   index = False,
                   encoding = 'utf-8')
    
    # excel-friendly csv
    df_econ.to_csv(os.path.join(path_built_csv,
                                dir_name,
                                u'df_excel_{:s}.csv'.format(journal_title)),
                   index = False,
                   encoding = 'latin-1',
                   sep = ';',
                   escapechar = '\\',
                   quoting = 1) 
    
    # excel file: write journal or institution sheet
    # requires openpyxl (temp fix for some issues)
    df_econ.to_excel(writer, journal_title, index = False)
    
    if dir_name == 'publications':
      df_econ['JO'] =  journal_title
    elif dir_name == 'phd':
      df_econ['IN'] =  journal_title
    ls_df_econ.append(df_econ)
  
  df_econ_all = pd.concat(ls_df_econ)
  
  # excel file: write sheet with all info and close file
  df_econ_all.to_excel(writer, 'all', index = False)
  writer.save()
  
  # standard csv
  df_econ_all.to_csv(os.path.join(path_built_csv,
                                  u'{:s}.csv'.format(dir_name)),
                     index = False,
                     encoding = 'utf-8')
  
  # excel csv
  df_econ_all.to_csv(os.path.join(path_built_csv,
                                  u'excel_{:s}.csv'.format(dir_name)),
                     index = False,
                     encoding = 'latin-1',
                     sep = ';',
                     escapechar = '\\',
                     quoting = 1) 
