#!/usr/bin/python
# -*- coding: utf-8 -*-
import json
import os, sys, codecs
import re
import copy
import xlrd
import itertools
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import statsmodels.api as sm
from decimal import *
from collections import Counter
import pprint

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_stock_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

if __name__=="__main__":
  # path_data: data folder at different locations at CREST vs. HOME
  # could do the same for path_code if necessary (import etc).
  if os.path.exists(r'W:\Bureau\Etienne_work\Data'):
    path_data = r'W:\Bureau\Etienne_work\Data'
  else:
    path_data = r'C:\Users\etna\Desktop\Etienne_work\Data'
  # structure of the data folder should be the same
  folder_built_master_json = r'\data_gasoline\data_built\data_json_gasoline\master_diesel'
  folder_source_brand = r'\data_gasoline\data_source\data_stations\data_brands'
  folder_built_csv = r'\data_gasoline\data_built\data_csv_gasoline'
  folder_dpts_regions = r'\data_insee\Regions_departements'
  
  master_price = dec_json(path_data + folder_built_master_json + r'\master_price')
  master_info = dec_json(path_data + folder_built_master_json + r'\master_info_for_output')
  # cross_distances_dict = dec_json(path_data + folder_built_master_json + r'\dict_ids_gps_cross_distances')
  list_list_competitors = dec_json(path_data + folder_built_master_json + r'\list_list_competitors')
  list_tuple_competitors = dec_json(path_data + folder_built_master_json + r'\list_tuple_competitors')
  dict_dpts_regions = dec_json(path_data + folder_dpts_regions + r'\dict_dpts_regions')
  
  # #####################
  # IMPORT INSEE DATA
  # #####################
  
  folder_communal = r'\data_insee\Communal'
  
  # UNITES URBAINES 2010
  
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
  #uu2010/libuu2010/uuinternational/nb_communes/popmun2007/tailleuu/typeuu
  
  # Sheet: communes (appartenance des communes aux uu)
  sheet_communes_uu = workbook_uu.sheet_by_name(u'Communes')
  list_title_communes_uu = zip(sheet_communes_uu.row_values(0), sheet_communes_uu.row_values(1))
  list_content_communes_uu = [sheet_communes_uu.row_values(i) for i in range(2, sheet_communes_uu.nrows)]
  list_codes_geo_uu = [elt[0] for elt in list_content_communes_uu]
  dict_communes_uu = dict(zip(list_codes_geo_uu, list_content_communes_uu))
  # content: codegeo/commune/region/dpt/uu2010/libuu2010/type2010/statut2010/popmun2007
  # uu2010: 01000, 02000 etc: rural / 01302 etc: code de l'UU 
  # libuu2010: Comm rurale du dpt 01 etc. / Nom de l'UU
  # type2010: Rural/Urbain
  # statut2010: R(Rural)/C(Urbain Centre)/B(Urbain Banlieue)/I(Urbain Isole)
  
  # TODO: exclude all those which are not in an UU => 01000... 95000
  # i.e. code_uu not in ['0%s' %i if len('%s' %i) == 4 else '%s' %i for i in range(1000, 95000,1000)]
  # could keep others if in same code insee?
  
  # AIRES URBAINES 2010
  
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
  # content: codegeo de l'UU/libgeo de l'UU
  
  sheet_communes_au = workbook_au.sheet_by_name(u'Composition communale')
  list_title_communes_au = zip(sheet_communes_au.row_values(0), sheet_communes_au.row_values(1))
  list_content_communes_au = [sheet_communes_au.row_values(i) for i in range(2, sheet_communes_au.nrows)]
  list_codes_geo_au = [elt[0] for elt in list_content_communes_au]
  dict_communes_au = dict(zip(list_codes_geo_au, list_content_communes_au))
  # content: codegeo/commune/au2010/libau2010/tau2010/cataeu2010
  # au2010/libau2010:
  # 000 Communes isolées hors influence des pôles
  # 997 Communes multipolarisées des grandes aires urbaines
  # 998 Autres communes multipolarisées
  # cataeu2010:
  # 111 : Commune appartenant à un grand pôle (10 000 emplois ou plus)
  # 112 : Commune appartenant à la couronne d'un grand pôle
  # 120 : Commune multipolarisée des grandes aires urbaines
  # 211 : Commune appartenant à un moyen pôle (5 000 à moins de 10 000 emplois)
  # 212 : Commune appartenant à la couronne d'un moyen pôle
  # 221 : Commune appartenant à un petit pôle (de 1 500 à moins de 5 000 emplois)
  # 222 : Commune appartenant à la couronne d'un petit pôle
  # 300 : Autre commune multipolarisée
  # 400 : Commune isolée hors influence des pôles
  
  # #####################
  # MARKET DEFINITIONS
  # #####################
  
  dict_markets_insee = {}
  dict_markets_zip = {}
  dict_markets_au = {}
  dict_markets_uu = {}
  # some stations don't have code_geo (short spells which are not in master_info)
  for id, info in master_price['dict_info'].iteritems():
    if 'code_geo' in info:
      dict_markets_insee.setdefault(info['code_geo'], []).append(id)
      dict_markets_zip.setdefault(id[:-3], []).append(id)
      dict_markets_uu.setdefault(dict_communes_uu[info['code_geo']][4], []).append(id)
      dict_markets_au.setdefault(dict_communes_au[info['code_geo']][2], []).append(id)
  
  # TODO: refine and use all categories? (exclude rural stations or ? etc.)
  # TODO: stats by dpt => rural stations / suburbs etc. ?
  # TODO: Investigate market definitions by Zip/Insee/Au/UU/Dist(?)
  
  # CASE OF ARGENTEUIL:
  # TODO: see if switch to code insee or keep both code insee and list of code postal... (e.g. Limoges..)
  # for id_sta, address in dict_zip_master['95100']:
	  # ind = master_price['ids'].index(id_sta)
	  # print id_sta, ind, list_start_end[ind], master_addresses_final[id_sta]
	  # print master_price['dict_info'][id_sta]
  
  # #####################
  # LOAD STAT APPS FILE
  # #####################
  
  folder_stats_apps = r'\data_gasoline\data_stats_apps'
  pd_df_stats_apps = pd.read_csv(path_data + folder_stats_apps + r'\Bretagne.csv', dtype = string)
  pd_df_stats_apps['id_index'] = pd_df_stats_apps['id']
  pd_df_stats_apps = pd_df_stats_apps.set_index('id_index')
  ls_ids_stats_apps = list(np.unique(pd_df_stats_apps['id']))
  ls_pbm_ids = [id_station for id_station in ls_ids_stats_apps if '%s' %id_station not in master_info]
  
  # 10 missing... check if were reconciled => No !
  # file_ls_duplicates = r'\data_gasoline\data_source\data_stations\data_reconciliations\list_id_reconciliations'
  # ls_duplicate_corrections = dec_json(path_data + file_ls_duplicates)
  
  # ls_corrected = [id_station for ls_id in ls_duplicate_corrections for id_station in ls_id]
  # ls_remaining_pbms = [id_station for id_station in ls_pbm_ids if id_station not in ls_corrected]
  
  # Check old info file...
  files_source_data = [r'\20111121_gouv_stations',
                       r'\20120000_gouv_stations',
                       r'\20120314_gouv_stations',
                       r'\20120902_gouv_stations',
                       r'\20130220_gouv_stations',
                       r'\20130707_gouv_stations']
  ls_dict_info_old = []
  ls_remaining_pbms = copy.deepcopy(ls_pbm_ids)
  for file_name in files_source_data:
    folder_source_gouv_stations_std = r'\data_gasoline\data_source\data_stations\data_gouv_stations\std'
    path_old_file = path_data + folder_source_gouv_stations_std + file_name
    ls_dict_info_old.append(dec_json(path_old_file))
    ls_remaining_pbms = [id_station for id_station in ls_remaining_pbms if '%s' %id_station not in ls_dict_info_old[-1]]
  pd_df_ex = pd_df_stats_apps[['id', 'gas', 'brand_1', 'brand_2', 'date']]\
                                [pd_df_stats_apps['id'] == ls_remaining_pbms[0]]
  # print pd_df_ex.to_string()
  # Only one truly missing: never got it in data (no pbm). Others are in old files (first is enough)
  
  # Check ronan's old file
  folder_rls = r'\data_gasoline\data_source\data_stations\data_rls\raw'
  pd_df_rls = pd.read_csv(path_data + folder_rls + r'\data_rls.csv', dtype = str)
  pd_df_rls['idpdv_index'] = pd_df_rls['idpdv']
  pd_df_rls = pd_df_rls.set_index('idpdv_index')
  
  # ############################
  # BULD STAT APPS STATION INFO
  # ############################
  
  # Gps coordinates
  ls_str_ids_stats_apps = ['%s' %id_station for id_station in ls_ids_stats_apps]
  dict_new_info_stats_apps = {}
  for id_station in ls_str_ids_stats_apps:
    if id_station in master_info:
      if master_info[id_station]['gps'][-1]:
        dict_new_info_stats_apps[id_station] = {'gps': master_info[id_station]['gps'][-1]}
      elif int(id_station) in pd_df_rls.index and pd_df_rls.ix[int(id_station)]['latDeg']:
        gps = [pd_df_rls.ix[int(id_station)]['latDeg'], pd_df_rls.ix[int(id_station)]['longDeg']]
        dict_new_info_stats_apps[id_station] = {'gps' : gps}
        print id_station, 'no good gps in master info, rls:', gps
      else:
        print id_station, 'no good gps in master info nor in rls'
    elif int(id_station) in pd_df_rls.index and pd_df_rls.ix[int(id_station)]['latDeg']:
      gps = [pd_df_rls.ix[int(id_station)]['latDeg'], pd_df_rls.ix[int(id_station)]['longDeg']]
      dict_new_info_stats_apps[id_station] = {'gps' : gps}
      print id_station, 'not in master info, rls:', gps
    else:
      print id_station, 'not in master info nor in rls'
  # Two exceptions: use new ids
  # print ls_dict_info_old[0]['29000008'] # Current : '29000010'
  #print ls_dict_info_old[0]['35560001'] # Current : '35560004'
  dict_new_info_stats_apps['29000008'] = {'gps' : master_info['29000010']['gps'][-1]}
  dict_new_info_stats_apps['35560001'] = {'gps' : master_info['35560004']['gps'][-1]}
  
  # Insee code
  for id_station in ls_str_ids_stats_apps:
    if id_station in master_price['dict_info'] and 'code_geo' in master_price['dict_info'][id_station].keys():
      dict_new_info_stats_apps[id_station]['code_geo'] = master_price['dict_info'][id_station]['code_geo']
    elif int(id_station) in pd_df_rls.index and pd_df_rls.ix[int(id_station)]['CodeCom']:
      dict_new_info_stats_apps[id_station]['code_geo'] = pd_df_rls.ix[int(id_station)]['CodeCom']
    else:
      print id_station, 'no insee code'
  dict_new_info_stats_apps['29000008']['code_geo'] = master_price['dict_info']['29000010']['code_geo']
  
  # TODO: check that dict full and looks correct  + match with insee data
  for id_station, info_station in dict_new_info_stats_apps.iteritems():
    if info_station['code_geo'] not in dict_communes_au:
      print id_station, 'code geo not ok'
    if not info_station['gps']:
      print id_station, 'gps coord missing'
    dict_new_info_stats_apps[id_station]['lat'] = info_station['gps'][0]
    dict_new_info_stats_apps[id_station]['lon'] = info_station['gps'][1]
    del(dict_new_info_stats_apps[id_station]['gps'])
  
  pd_df_stats_apps_final = pd.DataFrame(dict_new_info_stats_apps)
  pd_df_stats_apps_final = pd_df_stats_apps_final.T
  
  # Reconciliation of dataset
  
  list_services =  [u'Automate CB',
                    u'Laverie',
                    u'Toilettes publiques',
                    u'Boutique alimentaire',
                    u'Boutique non alimentaire',
                    u'Restauration a emporter',
                    u'Restauration sur place',
                    u'Relais colis',
                    u'Vente de gaz domestique',
                    u'Vente de fioul domestique',
                    u'Vente de petrole lampant',
                    u'Carburant qualite superieure',
                    u'GPL',
                    u'Station de gonflage',
                    u'Station de lavage',
                    u'Lavage multi-programmes',
                    u'Lavage haute-pression',
                    u'Baie de service auto',
                    u'Piste poids lourds',
                    u'Location de vehicules']
  list_services_ser = ['ser_%s' %i for i in range(1,21)]
  dict_replace = dict(zip(list_services_ser, list_services))
  pd_df_stats_apps = pd_df_stats_apps.rename(columns=dict_replace)
  
  pd_df_stats_apps.index = [str(ind) for ind in pd_df_stats_apps.index]
  pd_df_stats_apps = pd_df_stats_apps.join(pd_df_stats_apps_final)
    
  pd_df_stats_apps.to_csv(path_data + folder_stats_apps + r'\Bretagne_updated.csv')