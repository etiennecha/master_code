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

dict_dict_stations = {}
dict_dict_stations['2012'] =  dec_json(os.path.join(path_dir_zagaz,
                                                    'data_json',
                                                    '2012_dict_zagaz_stations.json'))
dict_dict_stations['2013'] = dec_json(os.path.join(path_dir_zagaz,
                                                 'data_json',
                                                 '2013_dict_zagaz_stations.json'))

dict_brands = dec_json(os.path.join(path_dir_source,
                                    'data_other',
                                    'dict_brands.json'))

# ######################################
# UPDATE dict_brands TO COVER ZAGAZ DATA
# ######################################

dict_missing_brands = {}
for year, dict_stations in dict_dict_stations.items():
  for k, v in dict_stations.items():
    str_standardized_brand = str_low_noacc(str_correct_html(v[1])).upper()
    if str_standardized_brand not in dict_brands.keys():
      dict_missing_brands.setdefault(str_standardized_brand, []).append(k)
print u'\nBrands missing in dict_brands:'
print dict_missing_brands.keys()
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
                      'AS24' : [u'INDEPENDANT', u'INDEPENDANT', u'IND'],
                      'SPAR' : [u'CASINO', u'CASINO', u'SUP'],
                      'ANTARGAZ' : [u'INDEPENDANT', u'INDEPENDANT', u'IND'],
                      'DIVERS' : [u'INDEPENDANT', u'INDEPENDANT', u'IND'],
                      'MATCH' : [u'CORA', u'CORA', u'SUP'],
                      'PRIMAGAZ' : [u'INDEPENDANT', u'INDEPENDANT', u'IND']}
dict_brands.update(dict_brands_update)

# #############################
# BUILD df_stations DATAFRAMES
# #############################

dict_df_stations = {}
for year, dict_stations in dict_dict_stations.items():
  ls_rows_stations = []
  for k,v in dict_stations.items():
    if year == '2013':
      v[4] = v[4][0]
    ls_rows_stations.append(v[0:7] + v[7])
  df_stations = pd.DataFrame(ls_rows_stations, columns = ['id_zagaz',
                                                          'brand',
                                                          'name',
                                                          'comment',
                                                          'street',
                                                          'zip',
                                                          'municipality',
                                                          'lat',
                                                          'lng',
                                                          'Q'])
  dict_df_stations[year] = df_stations


# ###############################################
# FIX STATION INFO (BASED ON INSEE MATCHING PBMS)
# ###############################################

# ADDRESS

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

def fix_municipality(municipality):
  municipality = re.sub(ur'^Paris 0([1-9])eme$', ur'Paris \1eme', municipality)
  municipality = re.sub(ur'^Paris 01er$', ur'Paris 1er', municipality)
  municipality = municipality.replace(u'\x9c', u'oe')
  return municipality


for year, df_stations in dict_df_stations.items():
  df_stations['municipality'] =\
    df_stations['municipality'].apply(lambda x: fix_municipality(x))
  for (muni, zip_code_old), zip_code_new in ls_fix_zip:
    df_stations.loc[(df_stations['municipality'] == muni) &\
                    (df_stations['zip'] == zip_code_old),
                    'zip'] = zip_code_new
  for (muni_old, zip_code), muni_new in ls_fix_city:
    df_stations.loc[(df_stations['municipality'] == muni_old) &\
                    (df_stations['zip'] == zip_code),
                    'municipality'] = muni_new
  df_stations['street'] = df_stations['street'].apply(lambda x: x.replace(u'\u017d', u"'"))

# GPS

dict_gps_quality = {u"Ces coordonnées n'ont pas été vérifiées " +\
                        u"et sont sujettes à caution" : "Unverified",
                    u"Ces coordonnées ont été vérifiées " +\
                        u"par un internaute" : "Verified"}

for year, df_stations in dict_df_stations.items():
  df_stations['Q'] = df_stations['Q'].apply(lambda x: dict_gps_quality.get(x, None))

# ##########################################
# LOAD INSEE CORRESPONDENCE AND RUN MATCHING
# ##########################################

path_df_corr = os.path.join(path_dir_match_insee, 'df_corr_gas.csv')
matching_insee = MatchingINSEE(path_df_corr)

df_com = pd.read_csv(os.path.join(path_dir_insee_extracts,
                                  u'df_communes.csv'),
                     encoding = 'utf-8',
                     dtype = str)
ls_active_cis = df_com['CODGEO'].values

## Check: works ok, then do within dataframes
## could merge both df_stations first
#dict_ls_match_res = {}
#for year, df_stations in dict_df_stations.items():
#  ls_match_res = []
#  for row_ind, row in df_stations.iterrows():
#    match_res = matching_insee.match_city(row['municipality'],
#                                          row['zip'][:-3],
#                                          row['zip'])
#    if match_res[1] == 'no_match':
#      print u'\nNo match ({:s}):'.format(year), row_ind, row['zip'], row['municipality']
#    ls_match_res.append((row_ind, match_res))
#  dict_ls_match_res[year] = ls_match_res
#
## Check insee code still in use + disambiguate
##set_active_cis = set(df_com['CODGEO'].values)
##ls_2012_cis = [x[1][0][0][2] for x in dict_ls_match_res['2012']]
##ls_2012_pbms = set(ls_2012_cis).difference(set_active_cis)
#ls_active_cis = df_com['CODGEO'].values
#dict_ls_final_match = {}
#for year, ls_match_res in dict_ls_match_res.items():
#  ls_final_match = [refine_insee_code(ls_active_cis, res[1][0][0][2])\
#                      for res in ls_match_res]
#  dict_ls_final_match[year] = ls_final_match
#  print u'\nNb stations ({:s}):'.format(year), len(ls_final_match)
#  print u'Nb matched ({:s}):'.format(year), len([x for x in ls_final_match if x[0]])

for year, df_stations in dict_df_stations.items():
  df_stations['ci'] =\
    df_stations.apply(lambda x: matching_insee.match_city(x['municipality'],
                                                          x['zip'][:-3],
                                                          x['zip'])[0][0][2],
                      axis = 1)
  df_stations['ci'], df_stations['ci_ardt'] =\
      zip(*df_stations['ci'].apply(lambda x: refine_insee_code(ls_active_cis,
                                                               x)))

## Ok: same 4 which are located in Monaco hence no insee code
#print dict_df_stations['2012'][dict_df_stations['2012']['ci_ardt'].isnull()].to_string()
#print dict_df_stations['2013'][dict_df_stations['2013']['ci_ardt'].isnull()].to_string()

# ##########################################
# MERGE 2012 AND 2013
# ##########################################

df_2012, df_2013 = dict_df_stations['2012'], dict_df_stations['2013']
set_dead_2012 = set(df_2012['id_zagaz'].values).difference(set(df_2013['id_zagaz'].values))
df_2013.rename(columns = {'brand' : 'brand_2013'}, inplace = True)
df_stations = pd.concat([df_2013,
                         df_2012[df_2012['id_zagaz'].isin(list(set_dead_2012))]],
                        axis = 0,
                        ignore_index = True)
df_stations.set_index('id_zagaz', inplace = True)
df_2012.set_index('id_zagaz', inplace = True)
df_stations['brand'] = df_2012['brand']
df_stations.rename(columns = {'brand' : 'brand_2012'}, inplace = True)


for year in ['2012', '2013']:
  df_stations['brand_{:s}'.format(year)] =\
      df_stations['brand_{:s}'.format(year)].apply(lambda x: str_low_noacc(str_correct_html(x)).upper()\
                                                             if not pd.isnull(x) else None)
  df_stations['brand_std_{:s}'.format(year)], df_stations['group_{:s}'.format(year)] =\
      zip(*df_stations['brand_{:s}'.format(year)].apply(\
             lambda x: (dict_brands[x][0],
                        dict_brands[x][1]) if not pd.isnull(x) else (None, None)))

#print u'\nNb not in 2012:', len(df_stations[df_stations['brand_2012'].isnull()])
#print u'Nb not in 2013:', len(df_stations[df_stations['brand_2013'].isnull()])
#print u'Nb Total Access in 2013:', len(df_stations[(df_stations['brand_2013'] ==\
#                                         'TOTAL ACCESS')])
#ls_di_0 = ['brand_2012', 'brand_2013', 'name', 'municipality', 'street', 'zip', 'ci', 'ci_ardt']
#print u'\nChanges:'
#print df_stations[(df_stations['brand_2013'] !=\
#                     df_stations['brand_2012'])][ls_di_0].to_string()
## Not much change between the two... probably too close
## Recollect now to study closing

# ##############
# OUTPUT
# ##############

df_stations.to_csv(os.path.join(path_dir_built_zagaz,
                                'data_csv',
                                'df_zagaz_stations.csv'),
                   index_label = 'id_zagaz',
                   float_format='%.3f',
                   encoding='utf-8')
