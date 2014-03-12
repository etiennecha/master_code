#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
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


if __name__=="__main__":

  path_dir_insee = os.path.join(path_data, 'data_insee')
  
  # #####################################
  # 0/ CODE INSEE VS. ZIP CODE (AND CITY)
  # #####################################

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
  
  
  # ################################# 
  # 1/ DATA AT CITY LEVEL ("COMMUNE")
  # #################################

  path_dir_communes = os.path.join(path_dir_insee, 'communes')
  
  # ####################################################
  # 1A/ MOBILITY BETWEEN HOME AND WORK (not used so far)
  
  path_xls_mob = os.path.join(path_dir_communes,
                              'Mobilite_Dom_Travail',
                              'base-flux-mobilite-domicile-lieu-travail-2010.xls')
  wb_mob = xlrd.open_workbook(path_xls_mob)
  # sh = wb.sheet_by_index(0)
  # sh_nb_rows = sh.nrows
  # first_column = sh.col_values(0)
  # cell_A1 = sh.cell(0,0).value
  # cell_C4 = sh.cell(rowx=3, colx=2).value
  print 'Sheets in file', wb_mob.sheet_names()
 
  # Communes info: people working in communes vs. outside
  sh_com_work = wb_mob.sheet_by_name(u'TOTAL')
  ls_columns = sh_com_work.row_values(5) # 4 has details but long fields
  ls_rows = [sh_com_work.row_values(i) for i in range(6, sh_com_work.nrows)]
  df_com_work = pd.DataFrame(ls_rows, columns = ls_columns, dtype = str)
  
  # Mobility info: people commuting to work
  sh_mob = wb_mob.sheet_by_name(u'FLUX>=100')
  ls_columns = sh_mob.row_values(5)
  ls_rows = [sh_mob.row_values(i) for i in range(6, sh_mob.nrows)]
  df_mob = pd.DataFrame(ls_rows, columns = ls_columns, dtype = str)
 
  # ########################
  # 1B/ UNITES URBAINES 2010

  path_xls_uu = os.path.join(path_dir_communes, 'UnitesUrbaines', 'UU2010.xls')
  wb_uu = xlrd.open_workbook(path_xls_uu)
  print 'Sheets in file', wb_uu.sheet_names()
  
  # Sheet: unites urbaines (info par uu)
  sh_uu_info = wb_uu.sheet_by_name(u'Liste des unit\xe9s urbaines 2010')
  ls_columns = sh_uu_info.row_values(1)
  ls_rows = [sh_uu_info.row_values(i) for i in range(2, sh_uu_info.nrows)]
  df_uu_info = pd.DataFrame(ls_rows, columns = ls_columns, dtype = str)

  # Sheet: communes (appartenance des communes aux uu)
  sh_uu_com = wb_uu.sheet_by_name(u'Communes')
  ls_columns = sh_uu_com.row_values(1)
  ls_rows = [sh_uu_com.row_values(i) for i in range(2, sh_uu_com.nrows)]
  # note: statut: r(rural)/c(urbain centre)/b(urbain banlieue)/i(urbain isole)
  df_uu_com = pd.DataFrame(ls_rows, columns = ls_columns, dtype = str)
  
  # Check, clean and merge 
  df_uu_info.rename(columns={'NB_COM' : 'NB_COM_UU',
                             'POP_MUN_2007' : 'POP_MUN_07_UU',
                             'TAILLE' : 'TAILLE_UU',
                             'TYPE' : 'TYPE_UU'}, inplace=True) 
  df_uu_com.rename(columns={'TYPE_2010' : 'TYPE_2010_COM',
                            'STATUT_2010' : 'STATUT_2010_COM',
                            'POP_MUN_2007': 'POP_MUN_2007_COM'}, inplace=True)  
  del(df_uu_com['LIBUU2010'], df_uu_com['REG'], df_uu_com['DEP']) 
  df_uu = pd.merge(df_uu_info, df_uu_com, on = 'UU2010')
  
  # #######################
  # 1C/ AIRES URBAINES 2010
  
  path_xls_au = os.path.join(path_dir_communes, 'AiresUrbaines', 'AU2010.xls')
  wb_au = xlrd.open_workbook(path_xls_au)
  print 'Sheets in file', wb_au.sheet_names()
  
  # Sheet: aires urbaines (info par au)
  sh_au_info = wb_au.sheet_by_name(u'Zonage en aires urbaines 2010')
  ls_columns = sh_au_info.row_values(1)
  ls_rows = [sh_au_info.row_values(i) for i in range(2, sh_au_info.nrows)]
  df_au_info = pd.DataFrame(ls_rows, columns = ls_columns, dtype = str)
  
  # Sheet: communes (appartenance des communes aux au)
  sh_au_com = wb_au.sheet_by_name(u'Composition communale')
  ls_columns = sh_au_com.row_values(1)
  ls_rows = [sh_au_com.row_values(i) for i in range(2, sh_au_com.nrows)]
  df_au_com = pd.DataFrame(ls_rows, columns = ls_columns, dtype = str)
 
  # No need to merge: all info in df_au_com 
  df_au = df_au_com

  # #######################
  # 1D/ LOGEMENT 2010

  path_xls_logement = os.path.join(path_dir_communes, 'Logement', 'base-cc-logement-2010.xls')
  
  wb_logement = xlrd.open_workbook(os.path.join(path_dir_communes, 'Logement', 'base-cc-logement-2010.xls'))
  print 'Sheets in file', wb_logement.sheet_names()
  
  sh_logement_com = wb_logement.sheet_by_name(u'COM')
  ls_columns = sh_logement_com.row_values(5)
  ls_rows = [sh_logement_com.row_values(i) for i in range(6, sh_logement_com.nrows)]
  df_logement_com = pd.DataFrame(ls_rows, columns = ls_columns, dtype = str)
  
  sh_logement_arm = wb_logement.sheet_by_name(u'ARM')
  ls_columns = sh_logement_arm.row_values(5)
  ls_rows = [sh_logement_arm.row_values(i) for i in range(6, sh_logement_arm.nrows)]
  df_logement_arm = pd.DataFrame(ls_rows, columns = ls_columns, dtype = str)
 
  # P10_RP = P10_MEN and P_10_PMEN = P10_NPER_NP (resp. nb menages, nb habitants)
  ls_select_columns = [u'CODGEO', u'LIBGEO',
                       u'P10_LOG', u'P10_MEN', u'P10_PMEN',
                       u'P10_RP_VOIT1P', 'P10_RP_VOIT1', 'P10_RP_VOIT2P']
  
  df_logement = pd.concat([df_logement_com, df_logement_arm], ignore_index = True)
  df_logement = df_logement[ls_select_columns] 

  # #################################### 
  # 1E/ Merge INSEE communes dataframes
 
  print df_uu.info()
  print df_au.info()
  print df_logement.info()
  del(df_au['LIBGEO'], df_logement['LIBGEO'])
  df_insee = pd.merge(df_uu, df_au, on = 'CODGEO')
  df_insee = pd.merge(df_insee, df_logement, on = 'CODGEO') 

  print df_insee.info()
  
  #folder_built_csv = r'\data_gasoline\data_built\data_v_gasoline'
  #path_dir_gas_source = os.path.join(path_data, 'data_gasoline', 'data_source', 'data_other')
  #df_insee.to_csv(os.path.join(path_dir_gas_source, 'data_insee_extract'),
  #                float_format='%.3f', encoding='utf-8', index=False)
  
  # e.g. groupy to build aggregate stats
  # check : http://bconnelly.net/2013/10/22/summarizing-data-in-python-with-pandas/
  ls_columns_interest = ['P10_LOG', 'P10_MEN', 'P10_PMEN', 'P10_RP_VOIT1P', 'P10_RP_VOIT1', 'P10_RP_VOIT2P']
  for column in ls_columns_interest:
    df_insee[column] = df_insee[column].apply(lambda x: float(x) if x else np.nan)
  df_uu_agg = df_insee.groupby('UU2010')[ls_columns_interest].sum()
  # TODO: add suffixes to have proper variable names
  df_insee = pd.merge(df_insee, df_uu_agg, left_on = "UU2010", right_index = True)
  
  ## If only one: series
  #se_uu_men = df_insee.groupby('UU2010')['P10_MEN'].sum()
  #df_uu_men = pd.Series(se_uu_men, name = 'P10_MEN_UU').reset_index()
  #df_insee = pd.merge(df_insee, df_uu_men, on = "UU2010")

  # ####################################### 
  # 2/ DATA AT INDIVIDUAL LEVEL (BIG FILES)
  # #######################################

  #path_txt_mob_ind = os.path.join(path_dir_insee, 'Mobilite_par_individu', 'FD_MOBPRO_2009.txt')
  #file_opened = open(path_txt_mob_ind, 'r')
  #data = file_opened.read()
  #data_part = data[0:10000000].split('\n') # memory error if take the whole file
  #variable_names = data_part[0].split(';')
  #first_observation = data_part[1].split(';')
  #tuple_example = zip(variable_names, first_observation)
