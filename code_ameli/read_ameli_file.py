#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import os, sys, codecs
import re
import pprint
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

if __name__=="__main__":
  if os.path.exists(r'W:\Bureau\Etienne_work\Data'):
    path_data = r'W:\Bureau\Etienne_work\Data'
  else:
    path_data = r'C:\Users\etna\Desktop\Etienne_work\Data'
  folder_ameli = r'\data_ameli'
  
  ls_files_ameli_names = [r'\actes_medecins',
                          r'\actes_medecins2',
                          r'\actes_medecins3',
                          r'\dbtoprint_json',
                          r'\all_out']
  
  ls_files_ameli = [dec_json(path_data + folder_ameli + file_ameli_name) for file_ameli_name in ls_files_ameli_names]
  
  ls_indiv_ids =[]
  for file_ameli in ls_files_ameli:
    print '\nFile type:', type(file_ameli), 'File length:', len(file_ameli)
    print file_ameli.keys()[0]
    pprint.pprint(file_ameli[file_ameli.keys()[0]])
    ls_indiv_ids += file_ameli.keys()
  ls_unique_indiv_ids = list(set(ls_indiv_ids))
  
  ls_columns = ['name', 'zip_code', 'city', 'sector', 'card']
  ls_indexes = []
  ls_ls_df_indiv_info = []
  for indiv_id, indiv_info in ls_files_ameli[0].items():
    ls_indexes.append(indiv_id)
    indiv_name = indiv_info['name']
    indiv_zip, indiv_city = None, None
    # for i in range(5):
      # if len(indiv_info['address']) > i and re.match('([0-9]{5,5}) (.*)', indiv_info['address'][i]):
        # indiv_zip = re.match('([0-9]{5,5}) (.*)', indiv_info['address'][i]).group(1)
        # indiv_city = re.match('([0-9]{5,5}) (.*)', indiv_info['address'][i]).group(2)
        # break
    # if not indiv_zip:
      # print indiv_id, indiv_info['address']
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
  
  pd_df_ameli = pd.DataFrame(ls_ls_df_indiv_info, index = ls_indexes, columns = ls_columns)
  
  # Number by dpt
  pd_df_ameli['dpt'] = pd_df_ameli['zip_code'].apply(lambda x: x[:2])
  pd_se_nb_by_dpt = pd_df_ameli.groupby('dpt').size()
  print pd_se_nb_by_dpt.to_string()
  # Nb seems pretty low in Mayenne (53) => would be good to compare with official data
  
  # Number by sector
  print np.unique(pd_df_ameli['sector'])
  pd_se_nb_by_sector = pd_df_ameli.groupby('sector').size()
  print pd_se_nb_by_sector
  
  # Number by dpt and sector
  pd_se_nb_by_dpt_and_sector = pd_df_ameli.groupby(['sector', 'dpt']).size()
  # print pd_se_nb_by_dpt_and_sector.to_string()
  # Print it with sectors as columns (couldn't do simpler...)
  ls_str_sectors = ('nonconv', 'secteur2', 'secteur1')
  ls_se_sectors_by_dpt = []
  for str_sector in ls_str_sectors:
    pd_df_sector = pd_df_ameli[pd_df_ameli['sector'] == str_sector]
    ls_se_sectors_by_dpt.append(pd_df_sector.groupby('dpt').size())
  pd_df_sectors_by_dpt = pd.concat(dict(zip(ls_str_sectors, ls_se_sectors_by_dpt)), axis= 1)
  pd_df_sectors_by_dpt = pd_df_sectors_by_dpt.fillna(0)
  pd_df_sectors_by_dpt['total'] = pd_df_sectors_by_dpt.sum(axis = 1)
  # pd_df_sectors_by_dpt['total'] = pd_df_sectors_by_dpt['nonconv'] +\
                                  # pd_df_sectors_by_dpt['secteur2'] +\
                                  # pd_df_sectors_by_dpt['secteur1']
  print pd_df_sectors_by_dpt.to_string()
  # plt.scatter(pd_df_sectors_by_dpt['total'], pd_df_sectors_by_dpt['secteur2'])
  # plt.show()
  
  # np.unique(pd_df_ameli['zip_code'][pd_df_ameli['dpt']=='75'])
  # # PBM: Paris 16 only zip 75116... not 75016
  # # TODO: collect Paris 16 and check for missing data in general (nbs vs. official stats or current website)
  
  # APPENDIX
  
  # Check Mayenne with all_out file... does not help
  
  # # print ls_files_ameli[-1][ls_files_ameli[-1].keys()[0]]
  # ls_mayenne = []
  # ls_no_zip = []
  # for indiv_id, indiv_info in ls_files_ameli[-1].items():
    # if re.search('([0-9]{5,5}) (.*)', indiv_info['address']):
      # zip_code = re.search('([0-9]{5,5}) (.*)', indiv_info['address']).group(1)
      # if zip_code[:2] == '53':
        # ls_mayenne.append((indiv_id, indiv_info))
    # else:
      # ls_no_zip.append(indiv_id)