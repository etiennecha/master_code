#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
from matching_insee import *
from functions_string import *
from BeautifulSoup import BeautifulSoup
import collections
import copy

def str_zagaz_corrections(word):
  word = word.lower()
  word = re.sub(ur'(^|\s|,)r?\.?\s?d\.?\s?([0-9]{0,5})(\s|$|,)',
                ur'\1 route departementale \2 \3',
                word)
  word = re.sub(ur'(^|\s|,)r?\.?\s?n\.?\s?([0-9]{0,5})(\s|$|,)',
                ur'\1 route nationale \2 \3',
                word) 
  return word.strip()

path_dir_match_insee = os.path.join(path_data,
                                    u'data_insee',
                                    u'match_insee_codes')

path_dir_insee_extracts = os.path.join(path_data,
                                       u'data_insee',
                                       u'data_extracts')

path_dir_source = os.path.join(path_data,
                               'data_gasoline',
                               'data_source')

path_dir_zagaz = os.path.join(path_dir_source,
                              'data_zagaz_scraped')

path_dir_built_zagaz = os.path.join(path_data,
                                    u'data_gasoline',
                                    u'data_built',
                                    u'data_zagaz')

# #####################
# LOAD ZAGAZ DATA
# #####################

dict_zagaz_stations_2012 = dec_json(os.path.join(path_dir_zagaz,
                                                 'data_json',
                                                 '2012_dict_zagaz_stations.json'))
dict_zagaz_stations_2013 = dec_json(os.path.join(path_dir_zagaz,
                                                 'data_json',
                                                 '2013_dict_zagaz_stations.json'))
dict_zagaz_stations_2014 = dec_json(os.path.join(path_dir_zagaz,
                                                 'data_json',
                                                 '20140124_dict_zagaz_station_ids.json'))

dict_zagaz_stations = dict_zagaz_stations_2013
dict_zagaz_stations.update(dict_zagaz_stations_2012)

# Content of station description within dict_zagaz_stations:
# [id, brand, name, comment, street, zip_code, city, gps_tup, other?]

# Build dicts: brands, gps quality and zip
dict_zagaz_brands, dict_zagaz_gps_quality, dict_zagaz_zip = {}, {}, {}
for zagaz_id, ls_zagaz_info in dict_zagaz_stations.items():
  dict_zagaz_brands.setdefault(ls_zagaz_info[1], []).append(zagaz_id)
  dict_zagaz_gps_quality.setdefault(ls_zagaz_info[7][2], []).append(zagaz_id)
  dict_zagaz_zip.setdefault(ls_zagaz_info[5], []).append((zagaz_id, ls_zagaz_info[4]))

# Inspect Zagaz brands and look for those missing in dict_brands
dict_brands = dec_json(os.path.join(path_dir_source,
                                    'data_other',
                                    'dict_brands.json'))

dict_missing_brands = {}
for zagaz_brand, ls_zagaz_ids in dict_zagaz_brands.items():
  str_standardized_brand = str_low_noacc(str_correct_html(zagaz_brand)).upper()
  if str_standardized_brand not in dict_brands.keys():
    dict_missing_brands[str_standardized_brand] = ls_zagaz_ids
print 'Zagaz brands not in dict_brands: ', dict_missing_brands.keys()

# u'MATCH' => u'SUPERMARCHE MATCH'
# u'SPAR' = u'SPAR STATION' or u'SUPERMARCHES SPAR' check if real difference
# u'8 A HUIT' => u'8  A HUIT'
# u'ENI' => u'AGIP' check

# 'OIL' / 'TEXACO' / 'IDS' / 'AS24' / 'ANTARGAZ' / 'PRIMAGAZ' / 'DIVERS'
# 'OIL' (18) => Indpt ss enseigne or small
# 'TEXACO' (2) => not really in france
# 'IDS' (2) => Indpt ss enseigne
# 'AS24' (2) => Not in my data... (one became Total Access?)
# 'ANTARGAZ' / 'PRIMAGAZ' => Not in my data
# 'DIVERS' (1394) => Indpt ss enseigne... or else?

dict_brands_update = {'OIL' : [u'INDEPENDANT', u'INDEPENDANT', u'IND'],
                      'TEXACO' : [u'INDEPENDANT', u'INDEPENDANT', u'IND'],
                      'ENI' : [u'AGIP', u'AGIP', u'OIL'],
                      'IDS': [u'INDEPENDANT', u'INDEPENDANT', u'IND'],
                      '8 A HUIT' : [u'HUIT_A_HUIT', u'CARREFOUR', u'SUP'],
                      'AS 24' : [u'INDEPENDANT', u'INDEPENDANT', u'IND'],
                      'SPAR' : [u'CASINO', u'CASINO', u'SUP'],
                      'ANTARGAZ' : [u'INDEPENDANT', u'INDEPENDANT', u'IND'],
                      'DIVERS' : [u'INDEPENDANT', u'INDEPENDANT', u'IND'],
                      'MATCH' : [u'CORA', u'CORA', u'SUP'],
                      'PRIMAGAZ' : [u'INDEPENDANT', u'INDEPENDANT', u'IND']}

# Fix zagaz data based on observed matching pbms
ls_fix_zip  = [[[u"Château-d'Olonne", u'85100'], u'85180'],
               [[u'Noiseau', u'94370'], u'94880'],
               [[u'Dompierre-sur-Chalaronne', u'01140'], u'01400'],
               [[u'Tramayes', u'71630'], u'71520'],
               [[u"La Chapelle-d'Aligné", u'72410'], u'72300'],
               [[u"Précigné", u'72410'], u'72300'],
               [[u'Saint-Mars-la-Brière', u'72680'], u'72470'],
               [[u'Saint-Cosme-en-Vairais', u'72580'], u'72110'],
               [[u'Coulanges-lès-Nevers', u'58640'], u'58660'],
               [[u'Marzy', u'58000'], u'58180'],
               [[u'Sault-Brénaz', u'01790'], u'01150'],
               [[u'Diou', u'03490'], u'03290'],
               [[u'Châtillon-sur-Colmont', u'53510'], u'53100'],
               [[u'Liginiac', u'19440'], u'19160'],
               [[u'Prunelli-di-Fiumorbo', u'20240'], u'20243'],
               [[u'Saint-Martin-de-Bonfossé', u'50860'], u'50750'],
               [[u'Saint-Hilaire', u'38720'], u'38660']]

ls_fix_city = [[[u'Périgueux', u'24750'], u'Boulazac'],
               [[u'Château-Chinon(Ville)', u'58120'], u'Château-Chinon Ville']]

for indiv_id, ls_info in dict_zagaz_stations.items():
  ls_info[6] = re.sub(ur'^Paris 0([1-9])eme$', ur'Paris \1eme', ls_info[6])
  ls_info[6] = re.sub(ur'^Paris 01er$', ur'Paris 1er', ls_info[6])
  ls_info[6] = ls_info[6].replace(u'\x9c', u'oe')
  for (zagaz_city, zagaz_zip_code_bad), zagaz_zip_code_good in ls_fix_zip:
    if ls_info[6] == zagaz_city and ls_info[5] == zagaz_zip_code_bad:
      ls_info[5] = zagaz_zip_code_good
  for (zagaz_city_bad, zagaz_zip_code), zagaz_city_good in ls_fix_city:
    if ls_info[6] == zagaz_city_bad and ls_info[5] == zagaz_zip_code:
      ls_info[6] = zagaz_city_good
  dict_zagaz_stations[indiv_id] = ls_info

# ##########################################
# LOAD INSEE CORRESPONDENCE AND RUN MATCHING
# ##########################################

# Load correspondence
df_corr = pd.read_csv(os.path.join(path_dir_match_insee, 'df_corr_gas.csv'),
                      dtype = str)
ls_corr = [list(x) for x in df_corr.to_records(index = False)]
ls_corr = format_correspondence(ls_corr)

# Caution match_res can contain several results
ls_index, ls_res, ls_ind_pbm = [], [], []
for indiv_id, ls_info in dict_zagaz_stations.items():
  ls_index.append(indiv_id)
  zip_code = ls_info[5].rjust(5, '0')
  city = ls_info[6]
  match_res = match_insee_code(ls_corr, city, zip_code[:-3], zip_code)
  if match_res[1] != 'no_match':
    res = match_res[0][0][2]
  else:
    res = None
    ls_ind_pbm.append(indiv_id)
  ls_res.append(res)

# CHECK INSEE CODES STILL IN USE + DISAMB BIG CITY ARDTS

df_com = pd.read_csv(os.path.join(path_dir_insee_extracts,
                                  u'df_communes.csv'),
                     encoding = 'utf-8',
                     dtype = str)

ls_rows_ci = []
for res in ls_res:
  ls_rows_ci.append(list(refine_insee_code(df_com['CODGEO'].values, res)))

df_ci_zagaz = pd.DataFrame(ls_rows_ci,
                           columns = ['ci_1',
                                      'ci_ardt_1'],
                           index = ls_index)

# ##############
# BUILD DF ZAGAZ
# ##############

# No brand harmonization for now
ls_index, ls_rows = [], []
for indiv_id, ls_info in dict_zagaz_stations.items():
  ls_index.append(ls_info[0])
  ls_rows.append(ls_info[1:7] +\
                 list(ls_info[7]) +\
                 ls_info[8:9])

ls_columns = ['brand', 'name', 'comment', 'street', 'zip', 'city',
              'lat', 'lng', 'quality', 'highway'] 
df_zagaz = pd.DataFrame(ls_rows,
                        index = ls_index,
                        columns = ls_columns)

dict_quality = {u"Ces coordonnées n'ont pas été vérifiées " +\
                    u"et sont sujettes à caution" : "Unverified",
                u"Ces coordonnées ont été vérifiées " +\
                    u"par un internaute" : "Verified"}
df_zagaz['quality'] = df_zagaz['quality'].apply(lambda x: dict_quality.get(x, None))

df_zagaz = pd.merge(df_zagaz, df_ci_zagaz,
                    left_index = True, right_index = True)

pd.set_option("display.max_colwidth", 20)
print df_zagaz[0:20].to_string()

len(df_zagaz[pd.isnull(df_zagaz['ci_1'])])

# OUTPUT

df_zagaz.to_csv(os.path.join(path_dir_built_zagaz,
                             'df_zagaz_stations.csv'),
                index_label = 'id_zagaz',
                float_format='%.3f',
                encoding='utf-8')
