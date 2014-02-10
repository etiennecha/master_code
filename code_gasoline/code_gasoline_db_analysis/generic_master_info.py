#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import os, sys, codecs
import re
import pandas
from generic_master_price import *
from functions_string import *

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

def build_master_addresses(dict_ls_addresses):
  """Harmonizes and erases duplicates in dict of list of addresses (street, zip and city)"""
  dict_ls_addresses_corr = {}
  # soft correction and elimination of duplicates
  for indiv_id, ls_addresses in dict_ls_addresses.iteritems():
    ls_addresses_corr = [tuple(map(str_corr_low_std, address)) for address in ls_addresses if address]
    ls_addresses_corr = list(set(ls_addresses_corr))
    dict_ls_addresses_corr[indiv_id] = ls_addresses_corr
  # elimination of duplicates after standardization (keep softly corrected addresses though
  master_addresses = {}
  for indiv_id, ls_addresses_corr in dict_ls_addresses_corr.iteritems():
    if len(ls_addresses_corr) > 1:
      # get rid of accents and returns list of [(street, score), (city, score)] then add scores
      dict_addresses_std = {}
      for address_corr in ls_addresses_corr:
        tup_tup_address_std = map(str_corr_low_std_noacc, address_corr)
        # tuple of standardized address for comparison
        tup_address_std = (tup_tup_address_std[0][0], tup_tup_address_std[1][0])
        # tuple of correct address and score (the higher the better here)
        tup_address_cor = (address_corr, tup_tup_address_std[0][1] + tup_tup_address_std[1][1])
        dict_addresses_std.setdefault(tup_address_std, []).append(tup_address_cor)
      master_addresses[indiv_id] = [sorted(v, key=lambda x: x[1], reverse=True)[0][0]\
                                      for k,v in dict_addresses_std.items()]
    else:
      master_addresses[indiv_id] = ls_addresses_corr
  return master_addresses

def get_dict_stat(ls_items):
  cnt = Counter()
  for item in ls_items:
    cnt[item] += 1
  return dict_stats

if __name__=="__main__":
  if os.path.exists(r'W:\Bureau\Etienne_work\Data'):
    path_data = r'W:\Bureau\Etienne_work\Data'
  else:
    path_data = r'C:\Users\etna\Desktop\Etienne_work\Data'
  
  folder_built_master_json = r'\data_gasoline\data_built\data_json_gasoline'
  folder_source_brands = r'\data_gasoline\data_source\data_stations\data_brands'
  folder_built_csv = r'\data_gasoline\data_built\data_csv_gasoline'
  
  dict_brands = dec_json(path_data + folder_source_brands + r'\dict_brands')
  
  master_price = dec_json(path_data + folder_built_master_json + r'\master_diesel\master_price_diesel')
  master_info = dec_json(path_data + folder_built_master_json + r'\master_diesel\master_info_diesel_raw')
  ls_series = ['diesel_price', 'diesel_date']
  #master_price = dec_json(path_data + folder_built_master_json + r'\master_gas\master_price_gas')
  #master_info = dec_json(path_data + folder_built_master_json + r'\master_gas\master_info_gas_raw')
  #ls_series = ['sp95_price', 'sp95_date', 'e10_price', 'e10_date']
  
  # Build master_addresses (addresses corrected for html pbms and somewhat stdized)
  dict_addresses = {indiv_id: [indiv_info['address'][i] for i in (5, 3, 4, 0) if indiv_info['address'][i]]\
                      for (indiv_id, indiv_info) in master_info.items()}
  master_addresses = build_master_addresses(dict_addresses)
  master_addresses['15400003'] = [(u'zone industrielle du sedour', u'15400 riom-\xc8s-montagnes')]
  master_addresses['76170004'] = [(u'autoroute a 29', u'76210 bolleville')] # TODO: check/clean

  # Check zip from station address vs. zip from indiv_id (break if zip code not found in address)
  dict_describe_addresses = {}
  for indiv_id, ls_addresses in master_addresses.items():
    zip_indiv_id = indiv_id[:-3].rjust(5, '0')
    ls_zip_address = [re.match('([0-9]{5})\s.*', address[1]).group(1).rjust(5, '0')\
                        for address in ls_addresses if re.match('([0-9]{5})\s.*', address[1])] 
    if not ls_addresses:
      dict_describe_addresses.setdefault('No_address', []).append(indiv_id)
    else:
      if len(ls_addresses) > 1:
        dict_describe_addresses.setdefault('Multi_address', []).append(indiv_id)
      if len(ls_addresses) != len(ls_zip_address):
        dict_describe_addresses.setdefault('No_zip_address', []).append(indiv_id)
      if any(zip_address != zip_indiv_id for zip_address in ls_zip_address):
        dict_describe_addresses.setdefault('Several_zip', []).append(indiv_id)
  print 'Issues with addresses / zip codes:'
  for k, v in dict_describe_addresses.items():
    print k, len(v)
  
  # ####################
  # MATCHING VS. INSEE:
  # ####################
  
  # 1: Search within same zip if city name matches
  
  # Load zip code - insee code correspondence file
  file_correspondence = open(path_data + r'\data_insee\corr_cinsee_cpostal','r')
  correspondence = file_correspondence.read().split('\n')[1:-1]
  # Update changes in city codes (correspondence is a bit old)
  file_correspondence_update = open(path_data + r'\data_insee\corr_cinsee_cpostal_update','r')
  correspondence_update = file_correspondence_update.read().split('\n')[1:]
  correspondence += correspondence_update
  # Patch ad hoc for gas station cedexes
  file_correspondence_gas_path = open(path_data + r'\data_insee\corr_cinsee_cpostal_gas_patch','r')
  correspondence_gas_patch = file_correspondence_gas_path.read().split('\n')
  correspondence += correspondence_gas_patch
  correspondence = [row.split(';') for row in correspondence]
  
  # Corrections: standardize insee codes to 5 chars (zip assumed to be ok)
  correspondence = [(commune, zip_code, department, insee_code.rjust(5, '0'))\
                      for(commune, zip_code, department, insee_code) in correspondence]
  # Generate dict (key: zip code) with correspondence file
  dict_corr_zip_insee = {}
  for (city, zip_code, department, insee_code) in correspondence:
    dict_corr_zip_insee.setdefault(zip_code, []).append((city, zip_code, department, insee_code))
  # Generate dict (key: dpt code) with correspondence file
  dict_corr_dpt_insee = {}
  for (city, zip_code, department, insee_code)  in correspondence:
    dict_corr_dpt_insee.setdefault(zip_code[:-3], []).append((city, zip_code, department, insee_code))
  
  # Check best matching based on zip: first if same city name then if contained
  ls_matching = []
  for indiv_id, ls_addresses in master_addresses.iteritems():
    if ls_addresses:
      for address in ls_addresses:
        zip_and_city = re.match('([0-9]{5,5}) (.*)', address[1])
        zip_code = zip_and_city.group(1)
        city = zip_and_city.group(2)
        found_indicator = False
        for city_insee, zip_insee, dpt_insee, code_insee  in dict_corr_zip_insee[zip_code]:
          if str_insee_harmonization(str_low_noacc(city)) == str_insee_harmonization(city_insee):
            ls_matching.append((indiv_id, zip_code, code_insee))
            found_indicator = True
            break
        if not found_indicator:
          for city_insee, zip_insee, dpt_insee, code_insee  in dict_corr_zip_insee[zip_code]:
            if str_insee_harmonization(str_low_noacc(city)) in str_insee_harmonization(city_insee):
              ls_matching.append((indiv_id, zip_code, code_insee))
              print 'Matched', city, city_insee, zip_insee, '(', indiv_id, ')'
              found_indicator = True
              break
        if found_indicator:
          break
      if not found_indicator:
        print indiv_id, zip_insee, city, dict_corr_zip_insee[zip_code]
        print 'Could not match', str_insee_harmonization(str_low_noacc(city))
  
  # Check insee codes are still in use
  pd_df_insee = pd.read_csv(path_data + folder_built_csv + r'\master_insee_output.csv',
                            encoding = 'utf-8')
  ls_france_insee_codes = list(pd_df_insee[u'Département - Commune CODGEO'].astype(str))
  
  dict_large_cities = dict(list(itertools.product(map(str,range(13201, 13217)), ['13055']))+\
                           list(itertools.product(map(str,range(69381, 69390)), ['69123']))+\
                           list(itertools.product(map(str,range(75101, 75121)), ['75056'])))
  
  ls_unmatched_code_geo = []
  ls_indiv_id_not_in_master_price = []
  for (indiv_id, indiv_zip, indiv_insee_code) in ls_matching:
    if indiv_id in master_price['dict_info']:
      if indiv_insee_code in ls_france_insee_codes:
        final_insee_code, final_ardt_insee_code = indiv_insee_code, indiv_insee_code
      elif indiv_insee_code[:2] == '20':
        indiv_insee_code_a = indiv_insee_code[:1] + 'A' + indiv_insee_code[2:]
        indiv_insee_code_b = indiv_insee_code[:1] + 'B' + indiv_insee_code[2:]
        if indiv_insee_code_a in ls_france_insee_codes:
          final_insee_code, final_ardt_insee_code = indiv_insee_code_a, indiv_insee_code_a
        elif indiv_insee_code_b in ls_france_insee_codes:
          final_insee_code, final_ardt_insee_code = indiv_insee_code_b, indiv_insee_code_b
        else:
          final_insee_code, final_ardt_insee_code = None, None
          ls_unmatched_code_geo.append(indiv_insee_code)
      elif indiv_insee_code in dict_large_cities:
        final_insee_code, final_ardt_insee_code = dict_large_cities[indiv_insee_code], indiv_insee_code
      else:
        final_insee_code, final_ardt_insee_code = None, None
        ls_unmatched_code_geo.append(indiv_insee_code)
      master_price['dict_info'][indiv_id]['code_geo'] = final_insee_code
      master_price['dict_info'][indiv_id]['code_geo_ardts'] = final_ardt_insee_code
    else:
      ls_indiv_id_not_in_master_price.append(indiv_id)
  print len(ls_unmatched_code_geo), 'code_geo not present in recent insee files'
  print len(ls_indiv_id_not_in_master_price), 'indiv_id matched (insee) not in master_price'
  
  # # ####################
  # # DUPLICATE CORRECTION
  # # ####################
  
  # Generalize on series (diesel => sp95, e10, be cautious with date series too)
  
  # Corrections of duplicates based on json list of indiv_id tuples
  # Need to correct a/ master_file and b/ master_info
  file_ls_duplicates = r'\data_gasoline\data_source\data_stations\data_reconciliations\list_id_reconciliations'
  ls_duplicate_corrections = dec_json(path_data + file_ls_duplicates)
  ls_duplicate_corrected = []
  for indiv_id_1, indiv_id_2 in ls_duplicate_corrections:
    # master_price reconciliation
    if (indiv_id_1 in master_price['ids']) and\
       (indiv_id_2 in master_price['ids']):
      ind_1 = master_price['ids'].index(indiv_id_1)
      ind_2 = master_price['ids'].index(indiv_id_2)
      # find switching point (first valid
      switch = len(master_price['dates']) - 1 # initiating
      for series in ls_series:
        switch_temp = 0
        while (switch_temp < len(master_price['dates'])) and\
              ((master_price[series][ind_2][switch_temp] != master_price[series][ind_2][switch_temp]) or\
              (not master_price[series][ind_2][switch_temp])):
          switch_temp += 1
        switch = min(switch, switch_temp)
      # stick series (price, dates...)
      for series in ls_series:
        master_price[series][ind_2][:switch] = master_price[series][ind_1][:switch]
      # brand reconciliation:
      list_brand_and_period =  master_price['dict_info'][indiv_id_1]['brand'] +\
                               master_price['dict_info'][indiv_id_2]['brand']
      master_price['dict_info'][indiv_id_2]['brand'] = []
      ls_brand_temp = []
      for brand, period in list_brand_and_period:
        if brand not in ls_brand_temp:
          ls_brand_temp.append(brand)
          master_price['dict_info'][indiv_id_2]['brand'].append([brand, period])
      # name and city are left as such (most recent info) => delete indiv_id_1
      del master_price['ids'][ind_1], master_price['dict_info'][indiv_id_1]
      for series in ls_series:
        del master_price[series][ind_1]
    # master_info reconciliation
    if indiv_id_1 in master_info and indiv_id_2 in master_info:
      for field, content in master_info[indiv_id_2].iteritems():
        i = 0
        while not content[i] and i < len(content) - 1:
          i += 1
        master_info[indiv_id_2][field] = master_info[indiv_id_1][field][:i] + content[i:]
      del master_info[indiv_id_1] #, master_addresses[indiv_id_1] master_addresses rebuilt anyway
      # keep track for checking (only master_info)
      ls_duplicate_corrected.append((indiv_id_1, indiv_id_2))
  
  # Delete info-less stations (TODO: function)
  list_garbage = ['39700002', '39700004', '78150008', '85210005', '85210006',\
                  '51400005', '51400006', '94170003', '34400014']
  for indiv_id in list_garbage:
    if indiv_id in master_price['ids'] and indiv_id in master_info:
      ind = master_price['ids'].index(indiv_id)
      del master_price['ids'][ind], master_price['dict_info'][indiv_id], master_info[indiv_id]
      for series in ls_series:
        del master_price[series][ind]
  
  # Overwrite 'rank' in master_price['dict_info'] with up to date info
  for i, indiv_id in enumerate(master_price['ids']):
    master_price['dict_info'][indiv_id]['rank'] = i
  
  # # ###################
  # # DUPLICATES CHECK
  # # ###################
  
  # Build dict_zip (used for duplicate detection)
  dict_zip_master = {}
  for indiv_id, ls_addresses in master_addresses.items():
    for address in ls_addresses:
      zip_and_city = re.match('([0-9]{5,5}) (.*)', address[1])
      zip_code = zip_and_city.group(1)
      if zip_code in dict_zip_master:
        list_zip_indiv_ids = [station[0] for station in dict_zip_master[zip_code]]
        if indiv_id not in list_zip_indiv_ids:
          dict_zip_master[zip_code].append((indiv_id, address))
      else:
        dict_zip_master[zip_code] = [(indiv_id, address)]
  
  # Build dict_corr_dpt_insee (to be used for duplicate detection)
  dict_insee_master = {}
  for indiv_id, ls_addresses in master_addresses.iteritems():
    for address in ls_addresses:
      zip_and_city = re.match('([0-9]{5,5}) (.*)', address[1])
      zip_code = zip_and_city.group(1)
      dpt = zip_and_city.group(1)[:2]
      city = zip_and_city.group(2)
      if dpt in dict_insee_master:
        list_dpt_indiv_ids = [station[0] for station in dict_insee_master[dpt]]
        if indiv_id not in list_dpt_indiv_ids:
          dict_insee_master[dpt].append((indiv_id, zip_code, city, address))
      else:
        dict_insee_master[dpt] = [(indiv_id, zip_code, city, address)]
  
  # Check stations' activity record
  # TODO: May not want to run with sp95/e10 => need to adapt
  series = ls_series[0]
  ls_ls_price_durations = get_price_durations_nan(master_price[series])
  # ls_ls_price_variations = get_price_variations_nan(ls_ls_price_durations)
  ls_start_end, ls_none, ls_ls_dilettante =  get_overview_reporting_nan(master_price[series],
                                                                        ls_ls_price_durations,
                                                                        master_price['dates'],
                                                                        master_price['missing_dates'])
  
  # ls_none with data end 2012: [326, 550, 1406, 3293, 3423, 4918, 4919, 5075, 5859, 5876, 7307, 8260, 8647]
  # TODO: clarify treatment of None, None (a priori... already old => potential duplicate)
  ls_late_start = []
  ls_early_end = []
  ls_short_spell = []
  ls_full_spell = []
  start_ind_full, end_ind_full = 0, len(master_price['dates'])-1
  for i, (start, end) in enumerate(ls_start_end):
    if start != start_ind_full and end == end_ind_full:
      ls_late_start.append(i)
    elif start == start_ind_full and end != end_ind_full:
      ls_early_end.append(i)
    elif start != start_ind_full and end != end_ind_full:
      ls_short_spell.append(i)
    else:
      ls_full_spell.append(i)
  # Detection of potential duplicates (too complex to be automatic...)
  for zip_code, ls_stations in dict_zip_master.iteritems():
    ls_zip_indiv_ids = [station[0] for station in ls_stations]
    ls_zip_inds = [master_price['ids'].index(indiv_id) for indiv_id in ls_zip_indiv_ids\
                      if indiv_id in master_price['ids']]
    if (any(ind in ls_early_end for ind in ls_zip_inds) and\
         (any(ind in ls_short_spell for ind in ls_zip_inds) or\
          any(ind in ls_late_start for ind in ls_zip_inds))\
       ) or\
       (any(ind in ls_short_spell for ind in ls_zip_inds) and\
         (any(ind in ls_late_start for ind in ls_zip_inds) or\
         len([ind for ind in ls_zip_inds if ind in ls_short_spell]) > 1)
       ):
      print '\n', zip_code
      for ind in ls_zip_inds:
        if ind not in ls_full_spell:
          print master_price['ids'][ind], ls_start_end[ind],\
                master_addresses[master_price['ids'][ind]],\
                master_price['dict_info'][master_price['ids'][ind]]['brand']
      # # display also full spell stations ?
      # for ind in ls_zip_inds:
        # if ind in ls_full_spell:
          # print master_price['ids'][ind], ls_start_end[ind],\
                # master_addresses[master_price['ids'][ind]],\
                # master_price['dict_info'][master_price['ids'][ind]]['brand']
  
  # TODO: add (35560001, 35560004), (42440001, 42440008), (47180001, 47180002)
  
  # ##########################
  # BRAND INFO (master_price)
  # ##########################
  
  # Harmonizes brands (softly though so far)
  for indiv_id, indiv_info in master_price['dict_info'].items():
    if indiv_info['brand']:
      master_price['dict_info'][indiv_id]['brand'] = [[get_str_no_accent_up(brand), day_ind]\
                                                         for brand, day_ind in indiv_info['brand']]
  
  # Resets brand starting date consistent with price series
  ls_to_be_chged = []
  for i, (start, end) in enumerate(ls_start_end):
    if start != master_price['dict_info'][master_price['ids'][i]]['brand'][0][1]:
      ls_to_be_chged.append(i)
      if start:
        master_price['dict_info'][master_price['ids'][i]]['brand'][0][1] = start
 
  #for indiv_ind in ls_to_be_chged:
  #  print indiv_ind, ls_start_end[indiv_ind],\
  #        master_price['dict_info'][master_price['ids'][indiv_ind]]['brand']
  #
  ## Brand change visual check
  #for indiv_id, indiv_info in master_price['dict_info'].items():
  #  if len(indiv_info['brand']) > 1:
  #    print indiv_id, indiv_info['brand']
 
  series = 'diesel_price'
  master_np_prices = np.array(master_price['diesel_price'], dtype = np.float32)
  matrix_np_prices_ma = np.ma.masked_array(master_np_prices, np.isnan(master_np_prices))
  ar_period_mean_prices = np.mean(matrix_np_prices_ma, axis = 0)
  # Resets Total Access brand change based on change in price
  window_limit = 20
  ls_mean_diffs = []
  matrix_np_prices_ma_cl = matrix_np_prices_ma - ar_period_mean_prices
  for i in range(window_limit, len(master_price['dates']) - window_limit):
    ls_mean_diffs.append(np.nansum(matrix_np_prices_ma_cl[:,:i], axis = 1)/\
                           np.sum(~np.isnan(matrix_np_prices_ma_cl[:,:i]), axis =1)-
                         np.nansum(matrix_np_prices_ma_cl[:,i:], axis = 1)/\
                           np.sum(~np.isnan(matrix_np_prices_ma_cl[:,i:]), axis =1))
    ## CAUTION: stats.nanmean first compute with 0 instead of nan then adjusts : imprecision...
    #scipy.stats.nanmean(matrix_np_prices_ma_cl[:,:i], axis= 1) -\
    #                     scipy.stats.nanmean(matrix_np_prices_ma_cl[:,i:], axis= 1))
  np_ar_mean_diffs = np.ma.array(ls_mean_diffs, fill_value=0).filled()
  # Filling with np.nan generates pbm with argmax
  np_ar_mean_diffs = np_ar_mean_diffs.T
  np_ar_diffs_maxs = np.nanmax(np.abs(np_ar_mean_diffs), axis = 1)
  np_ar_diffs_argmaxs = np.nanargmax(np.abs(np_ar_mean_diffs), axis = 1)
  ls_candidates = np.where(np_ar_diffs_maxs > 0.04)[0].astype(int).tolist()
  # Check if corresponds to a change in brand (TODO: exclude highly rigid prices)
  ls_total_access_chges = []
  ls_total_access_no_chges = []
  for indiv_ind, indiv_id in enumerate(master_price['ids']):
    ls_brands = [dict_brands[get_str_no_accent_up(brand)][0] for brand, period\
                   in master_price['dict_info'][indiv_id]['brand']]
    ls_brands = [x[0] for x in itertools.groupby(ls_brands)]
    if len(ls_brands) > 1 and 'TOTAL_ACCESS' in ls_brands:
      if indiv_ind in ls_candidates:
        ls_total_access_chges.append(indiv_ind)
      else:
        ls_total_access_no_chges.append(indiv_ind)
  
  ## Check original brand change info
  #for indiv_ind in ls_total_access_chges:  
  #  print indiv_ind, np_ar_diffs_argmaxs[indiv_ind], np_ar_diffs_maxs[indiv_ind],\
  #        master_price['dict_info'][master_price['ids'][indiv_ind]]['brand']
  
  for indiv_ind in ls_total_access_chges:
    ls_brands = zip(*master_price['dict_info'][master_price['ids'][indiv_ind]]['brand'])[0]
    ta_ind = ls_brands.index('TOTAL ACCESS') # 'TOTAL_ACCESS' depend if harmonized...
    master_price['dict_info'][master_price['ids'][indiv_ind]]['brand'][ta_ind][1] =\
      int(np_ar_diffs_argmaxs[indiv_ind]) + window_limit
  
   #TODO: add corrections to be done manually...
   #Check 437 (3 changes...)

  # #################################
  # HIGHWAY GAS STATION (master_info)
  # #################################
  
  dict_addresses = {indiv_id: [indiv_info['address'][i] for i in (5, 3, 4, 0) if indiv_info['address'][i]]\
                      for (indiv_id, indiv_info) in master_info.items()}
  master_addresses = build_master_addresses(dict_addresses)
  
  set_highway_ids = set()
  for indiv_id, ls_addresses in master_addresses.items():
    for address in ls_addresses:
      if 'autoroute' in address[0] or\
         re.search('(^|\s|-)a\s?[0-9]{1,3}($|\s|-|,)', address[0]) or\
         master_info[indiv_id]['highway'][3] == 1:
        set_highway_ids.add(indiv_id)
  ls_mistakes_highway = ['93130007', '75017016', '56190007', '68127001', '7580002']
  ls_highway_indiv_ids = [indiv_id for indiv_id in list(set_highway_ids) if indiv_id not in ls_mistakes_highway]
  # for indiv_id in list(set_highway_ids):
    # if indiv_id in master_price['dict_info'].keys():
      # print indiv_id, master_price['dict_info'][indiv_id]['name'], master_addresses[indiv_id]
  # # excluded: 93130007 (address incl. 'chasse a 3'), 75017016 ('6 a 8'),  56190007 (dummy 1), 
  # # excluded: 68127001 ('pres sortie...'), 7580002 (dummy 1, RN)
  
  # enc_json(master_price, path_data + folder_built_master_json + r'\master_diesel\master_price_diesel')
  # enc_json(master_info, path_data + folder_built_master_json + r'\master_diesel\master_info_diesel')
