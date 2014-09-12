#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_ameli import *
import pprint
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Working with "old" (around 2012?) ameli files

# SHORT TERM
# todo: to be integrated with more recent data / specialist data (paris/idf only?)
# todo: lack of competition among ophtalmo/gyneco?

# MEDIUM TERM
# todo: integrate official stats by dpt to evaluate representativity / density
# todo: see if easy to assess where medecins missing (dpt with > 500: zip codes etc?)
# todo: medecins by insee code area (usual matching from commune + zip to insee code)
# todo: are prices useless ? only share or non conv etc? (btw salaries? location?)

path_folder_ameli = os.path.join(path_data, 'data_ameli', u'data_source', 'ameli_2012')

ls_ameli_file_names = [u'actes_medecins',
                       u'actes_medecins2',
                       u'actes_medecins3',
                       u'dbtoprint_json',
                       u'all_out']

ls_files_ameli = [dec_json(os.path.join(path_folder_ameli, file_name))\
                    for file_name in ls_ameli_file_names]

print u'\nRead and describe ameli files'
ls_indiv_ids =[]
for file_ameli in ls_files_ameli:
  print '\nFile type:', type(file_ameli), 'File length:', len(file_ameli)
  print file_ameli.keys()[0]
  pprint.pprint(file_ameli[file_ameli.keys()[0]])
  ls_indiv_ids += file_ameli.keys()
ls_unique_indiv_ids = list(set(ls_indiv_ids))

print u'\nPrint parsing exceptions'
ls_columns = ['name', 'zip_code', 'city', 'sector', 'card']
ls_indexes = []
ls_ls_df_indiv_info = []
for indiv_id, indiv_info in ls_files_ameli[0].items():
  ls_indexes.append(indiv_id)
  indiv_name = indiv_info['name']
  indiv_zip, indiv_city = None, None
  #for i in range(5):
  #  if (len(indiv_info['address']) > i) and\
  #     (re.match('([0-9]{5,5}) (.*)', indiv_info['address'][i])):
  #    indiv_zip = re.match('([0-9]{5,5}) (.*)', indiv_info['address'][i]).group(1)
  #    indiv_city = re.match('([0-9]{5,5}) (.*)', indiv_info['address'][i]).group(2)
  #    break
  #if not indiv_zip:
  #  print indiv_id, indiv_info['address']
  if re.match('([0-9]{5,5}) (.*)', indiv_info['address'][-2]):
    indiv_zip = re.match('([0-9]{5,5}) (.*)', indiv_info['address'][-2]).group(1)
    indiv_city = re.match('([0-9]{5,5}) (.*)', indiv_info['address'][-2]).group(2)
  else:
    print indiv_id, indiv_info['address']
  indiv_secteur = None
  indiv_carte_vitale = None
  if indiv_id in ls_files_ameli[4]:
    indiv_secteur = ls_files_ameli[4][indiv_id]['convention']
    indiv_carte_vitale = ls_files_ameli[4][indiv_id]['carte_vitale']
  ls_df_indiv_info = [indiv_name, indiv_zip, indiv_city, indiv_secteur, indiv_carte_vitale]
  ls_ls_df_indiv_info.append(ls_df_indiv_info)

df_ameli = pd.DataFrame(ls_ls_df_indiv_info, index = ls_indexes, columns = ls_columns)

# Number by sector
print u'\nNb of physicians by "secteur"'
print df_ameli['sector'].value_counts()

# Number by dpt and sector
print u'\nNb of physicians by "département" and "secteur"'
df_ameli['dpt'] = df_ameli['zip_code'].apply(lambda x: x[:2])
se_nb_by_dpt_and_sector = df_ameli.groupby(['sector', 'dpt']).size()
# print se_nb_by_dpt_and_sector.to_string()
ls_str_sectors = ('nonconv', 'secteur2', 'secteur1')
ls_se_sectors_by_dpt = []
for str_sector in ls_str_sectors:
  df_sector = df_ameli[df_ameli['sector'] == str_sector]
  ls_se_sectors_by_dpt.append(df_sector.groupby('dpt').size())
df_sectors_by_dpt = pd.concat(dict(zip(ls_str_sectors, ls_se_sectors_by_dpt)), axis= 1)
df_sectors_by_dpt = df_sectors_by_dpt.fillna(0)
df_sectors_by_dpt['total'] = df_sectors_by_dpt.sum(axis = 1)
#df_sectors_by_dpt['total'] = df_sectors_by_dpt['nonconv'] +\
#                             df_sectors_by_dpt['secteur2'] +\
#                             df_sectors_by_dpt['secteur1']
print df_sectors_by_dpt.to_string()

# plt.scatter(df_sectors_by_dpt['total'], df_sectors_by_dpt['secteur2'])
# plt.show()

# REMARKS:
# Paris 16: only zip 75116... not 75016
# Issue can be similar for other zip codes
# Can bias nb of competitors for a physician/within an area
# Still in any not too small area: should have a big enough sample of physicians (biases?)
