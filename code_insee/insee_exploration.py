#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
import xlrd
import re
import pandas as pd

def str_insee_harmonization(word):
  # Just for comparison's sake: no accent and word-word (maybe insufficient?)
  word = word.lower()
  word = re.sub(ur"(^|\s)st(s?)(\s|$|-)", ur" saint\2 ", word)
  word = re.sub(ur"(^|\s)ste(s?)(\s|$|-)", ur" sainte\2 ", word)
  word = word.replace("'", " ")
  word = word.replace("-", " ")
  word = ' '.join(word.split())
  return word.strip()

# path_data: data folder at different locations at CREST vs. HOME
# could do the same for path_code if necessary (import etc).
if os.path.exists(r'W:\Bureau\Etienne_work\Data'):
  path_data = r'W:\Bureau\Etienne_work\Data'
  # sys.path.append(r'\W:\Bureau\Etienne_work\Code\code_gasoline\code_gasoline_db_analysis')
else:
  path_data = r'C:\Users\etna\Desktop\Etienne_work\Data'

folder_built_csv = r'\data_gasoline\data_built\data_csv_gasoline'

if __name__=="__main__":

  # 0/ CODE INSEE VS. ZIP CODE (AND CITY)

  # file_correspondence = open(path_data + r'\data_insee\corr_cinsee_cpostal','r')
  # correspondence = file_correspondence.read().split('\n')[1:-1]
  # file_correspondence_update = open(path_data + r'\data_insee\corr_cinsee_cpostal_update','r')
  # correspondence_update = file_correspondence_update.read().split('\n')[1:]
  # correspondence += correspondence_update
  # correspondence = [row.split(';') for row in correspondence]

  # dict_cpostal = {}
  # for (city, cpostal, dpt, cinsee) in correspondence:
    # dict_cpostal.setdefault(cpostal, []).append((city, cpostal, dpt, cinsee))

  # dict_dpt = {}
  # for (city, cpostal, dpt, cinsee) in correspondence:
    # dict_dpt.setdefault(cpostal[:-3], []).append((city, cpostal, dpt, cinsee))
  
  # # TODO: CREATE MATCHING FUNCTION WITH REASONABLE LEVENSHTEIN COMPARISON
  # # TODO: Search within cpostal (or dpt) closest levenshtein city
  # # TODO: Set a limit regarding the tolerated score...
  # # TODO: Build a class: should be able to import from everywhere so as to match with INSEE data...
  
  # # Large cities: arrondissements
  # # Paris code or Arrondissements codes... need flexibility
  # Large_cities = {'13055' : ['%s' %elt for elt in range(13201, 13217)], # Marseille
                  # '69123' : ['%s' %elt for elt in range(69381, 69390)], #Lyon
                  # '75056' : ['%s' %elt for elt in range(75101, 75121)]} # Paris

  
  # # Evolution in communes... manual updating so far

  # file_communes_maj = open(path_data + r'\data_insee\Communes_chgt\majcom2013.txt','r')
  # communes_maj = file_communes_maj.read().split('\n')
  # communes_maj_titles = communes_maj[0].split('\t')
  # communes_maj = [row.split('\t') for row in communes_maj[1:-1]]
  
  # file_communes_historiq = open(path_data + r'\data_insee\Communes_chgt\historiq2013.txt','r')
  # communes_historiq = file_communes_historiq.read().split('\n')
  # communes_historiq_titles = communes_historiq[0].split('\t')
  # communes_historiq = [row.split('\t') for row in communes_historiq[1:-1]]
  
  # list_communes_update_todo = []
  # for i, elt in enumerate(communes_historiq):
	  # if elt[0] and elt[3] and elt[13]:
		  # list_communes_update_todo.append(('%s%s' %(elt[0], elt[3]), elt[13], elt[20]))
  # # Not so clear... unecessay for now: manual update in correspondence
  
  
  
  # 1/ DATA AT CITY LEVEL ("COMMUNE")
  
  folder_communal = r'\data_insee\Communal'
  
  # 1A/ MOBILITY BETWEEN HOME AND WORK
  
  file_name = r'\Mobilite_Dom_Travail\base-flux-mobilite-domicile-lieu-travail-2010.xls'
  workbook = xlrd.open_workbook(path_data + folder_communal + file_name)
  # sh = wb.sheet_by_index(0)
  # sh_nb_rows = sh.nrows
  # first_column = sh.col_values(0)
  # cell_A1 = sh.cell(0,0).value
  # cell_C4 = sh.cell(rowx=3,colx=2).value
  print 'Opened', file_name
  print 'Sheets in file', workbook.sheet_names()
  # Communes info: people working in communes vs. outside
  sheet_communes_work_info = workbook.sheet_by_name(u'TOTAL')
  ls_title_communes_work_info = sheet_communes_work_info.row_values(5) # 4 has details but long fields
  ls_communes_work_info = []
  for row_ind in range(6, sheet_communes_work_info.nrows):
    ls_communes_work_info.append(sheet_communes_work_info.row_values(row_ind))
  pd_df_communes_work_info = pd.DataFrame([list(i) for i in zip(*ls_communes_work_info)],\
                                            ls_title_communes_work_info, dtype = str).T
  # Mobility info: people commuting to work
  sheet_mobility_info = workbook.sheet_by_name(u'FLUX>=100')
  ls_title_mobility_info = sheet_mobility_info.row_values(5)
  ls_mobility_info = []
  for row_ind in range(6, sheet_mobility_info.nrows):
    ls_mobility_info.append(sheet_mobility_info.row_values(row_ind))
  pd_df_mobility_info = pd.DataFrame([list(i) for i in zip(*ls_mobility_info)],\
                                            ls_title_mobility_info, dtype = str).T
  
  # 1B/ UNITES URBAINES 2010
  
  file_name_uu = r'\UnitesUrbaines\UU2010.xls'
  workbook_uu = xlrd.open_workbook(path_data + folder_communal + file_name_uu)
  print 'Opened', file_name_uu
  print 'Sheets in file', workbook_uu.sheet_names()
  print workbook_uu.sheet_names()
  # Sheet: unites urbaines (info par uu)
  sheet_liste_des_uu = workbook_uu.sheet_by_name(u'Liste des unit\xe9s urbaines 2010')
  list_title_uu = zip(sheet_liste_des_uu.row_values(0), sheet_liste_des_uu.row_values(1))
  list_content_uu = [sheet_liste_des_uu.row_values(i) for i in range(2, sheet_liste_des_uu.nrows)]
  list_codes_uu = [elt[0] for elt in list_content_uu]
  dict_uu = dict(zip(list_codes_uu, list_content_uu))
  pd_df_uu_info = pd.DataFrame([list(i) for i in zip(*list_content_uu)],\
                                list_title_uu, dtype = str).T
  # Sheet: communes (appartenance des communes aux uu)
  sheet_communes_uu = workbook_uu.sheet_by_name(u'Communes')
  list_title_communes_uu = zip(sheet_communes_uu.row_values(0), sheet_communes_uu.row_values(1))
  list_content_communes_uu = [sheet_communes_uu.row_values(i) for i in range(2, sheet_communes_uu.nrows)]
  list_codes_geo_uu = [elt[0] for elt in list_content_communes_uu]
  dict_communes_uu = dict(zip(list_codes_geo_uu, list_content_communes_uu))
  # Note: statut: R(Rural)/C(Urbain Centre)/B(Urbain Banlieue)/I(Urbain Isole)
  pd_df_uu_communes = pd.DataFrame([list(i) for i in zip(*list_content_communes_uu)],\
                                    list_title_communes_uu, dtype = str).T
  #Rename columns and merge
  for column in pd_df_uu_info.columns:
    pd_df_uu_info[' '.join(column)] = pd_df_uu_info[column]
    del(pd_df_uu_info[column])
  for column in pd_df_uu_communes.columns:
    pd_df_uu_communes[' '.join(column)] = pd_df_uu_communes[column]
    del(pd_df_uu_communes[column])
  pd_df_uu = pd.merge(pd_df_uu_communes, pd_df_uu_info, on = u"Code géographique de l'unité urbaine UU2010")
  
  # 1C/ AIRES URBAINES 2010
  
  file_name_au = r'\AiresUrbaines\AU2010.xls'
  workbook_au = xlrd.open_workbook(path_data + folder_communal + file_name_au)
  print 'Opened', file_name_au
  print 'Sheets in file', workbook_au.sheet_names()
  print workbook_au.sheet_names()
  # Sheet: aires urbaines (info par au)
  sheet_liste_des_au = workbook_au.sheet_by_name(u'Zonage en aires urbaines 2010')
  list_title_au = zip(sheet_liste_des_au.row_values(0), sheet_liste_des_au.row_values(1))
  list_content_au = [sheet_liste_des_au.row_values(i) for i in range(2, sheet_liste_des_au.nrows)]
  list_codes_au = [elt[0] for elt in list_content_au]
  dict_au = dict(zip(list_codes_au, list_content_au))
  pd_df_au_info = pd.DataFrame([list(i) for i in zip(*list_content_au)],\
                                list_title_au, dtype = str).T
  # Sheet: communes (appartenance des communes aux au)
  sheet_communes_au = workbook_au.sheet_by_name(u'Composition communale')
  list_title_communes_au = zip(sheet_communes_au.row_values(0), sheet_communes_au.row_values(1))
  list_content_communes_au = [sheet_communes_au.row_values(i) for i in range(2, sheet_communes_au.nrows)]
  list_codes_geo_au = [elt[0] for elt in list_content_communes_au]
  dict_communes_au = dict(zip(list_codes_geo_au, list_content_communes_au))
  pd_df_au_communes = pd.DataFrame([list(i) for i in zip(*list_content_communes_au)],\
                                    list_title_communes_au, dtype = str).T
  # Rename columns and merge
  for column in pd_df_au_info.columns:
    pd_df_au_info[u' '.join(column)] = pd_df_au_info[column]
    del(pd_df_au_info[column])
  for column in pd_df_au_communes.columns:
    pd_df_au_communes[u' '.join(column)] = pd_df_au_communes[column]
    del(pd_df_au_communes[column])
  pd_df_au_info[u'Code AU2010'] = pd_df_au_info[u'Code CODGEO']
  pd_df_au = pd.merge(pd_df_au_communes, pd_df_au_info, on = u'Code AU2010')
  
  # 1/D Merge INSEE communes dataframes
  
  pd_df_uu[u"Département - Commune CODGEO"] = pd_df_uu[u"Département - commune CODGEO"]
  del(pd_df_uu[u"Département - commune CODGEO"])
  pd_df_insee_communes = pd.merge(pd_df_uu, pd_df_au, on= u"Département - Commune CODGEO")
  
  # Some duplicates to handle... need to classify info (may not be a good idea to have all in one db) 
  for i, column_a in enumerate(pd_df_insee_communes.columns):
    for j, column_b in enumerate(pd_df_insee_communes.columns[i+1:], i+1):
      if all(pd_df_insee_communes[column_a] == pd_df_insee_communes[column_b]):
        print i, j, column_a, column_b
  
  del(pd_df_insee_communes[u"Libellé LIBGEO"])
  del(pd_df_insee_communes[u"Code CODGEO"]) # Actual Code AU (duplicate)
  del(pd_df_insee_communes[u"Libellé de l'unité urbaine LIBUU2010_y"])
  pd_df_insee_communes[u"Libellé de l'unité urbaine LIBUU2010"] =\
    pd_df_insee_communes[u"Libellé de l'unité urbaine LIBUU2010_x"]
  del(pd_df_insee_communes[u"Libellé de l'unité urbaine LIBUU2010_x"])
  
  pd_df_insee_communes[u"Population municipale 2007 POP_MUN_2007_UU"]=\
    pd_df_insee_communes[u"Population municipale 2007 POP_MUN_2007_y"]
  del(pd_df_insee_communes[u"Population municipale 2007 POP_MUN_2007_y"])
  
  pd_df_insee_communes[u"Population municipale 2007 POP_MUN_2007"]=\
    pd_df_insee_communes[u"Population municipale 2007 POP_MUN_2007_x"]
  del(pd_df_insee_communes[u"Population municipale 2007 POP_MUN_2007_x"])
  
  # pd_df_insee_communes.to_csv(path_data + folder_built_csv + r'/master_insee_output.csv',\
                                # float_format='%.3f', encoding='utf-8', index=False)
  
  
  
  # 2/ DATA AT INDIVIDUAL LEVEL (BIG FILES)

  # folder_insee_mob_par_ind = r'\data_insee\Mobilite_par_individu'
  # file_opened = open(path_data + folder_insee_mob_par_ind + r'\FD_MOBPRO_2009.txt', 'r')
  # data = file_opened.read()
  # data_part = data[0:10000000].split('\n') # memory error if take the whole file
  # variable_names = data_part[0].split(';')
  # first_observation = data_part[1].split(';')
  # tuple_example = zip(variable_names, first_observation)