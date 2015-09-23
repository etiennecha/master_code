#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import *
#from generic_master_price import *
#from generic_master_info import *
import os, sys
import re
import numpy as np
import pandas as pd
import pprint

path_dir_built_paper = os.path.join(path_data,
                                    u'data_gasoline',
                                    u'data_built',
                                    u'data_paper_total_access') # params here too?

path_dir_built_csv = os.path.join(path_dir_built_paper,
                                  u'data_csv')

path_source_other = os.path.join(path_data,
                                 'data_gasoline',
                                 'data_source',
                                 'data_other')

path_lsa_csv = os.path.join(path_data,
                            'data_supermarkets',
                            'data_lsa',
                            'data_built',
                            'data_csv')

# #############
# LOAD DF INFO
# #############

df_info = pd.read_csv(os.path.join(path_dir_built_csv,
                                   'df_station_info_final.csv'),
                      encoding = 'utf-8',
                      dtype = {'id_station' : str,
                               'name': str,
                               'adr_zip' : str,
                               'adr_dpt' : str,
                               'ci_1' : str,
                               'ci_ardt_1' :str,
                               'ci_2' : str,
                               'ci_ardt_2' : str,
                               'dpt' : str},
                      parse_dates = [u'day_%s' %i for i in range(4)]) # fix
df_info.set_index('id_station', inplace = True)

# ############
# LOAD DF LSA
# ############

# TODO: use lsa file fitted for period considered
df_lsa = pd.read_csv(os.path.join(path_lsa_csv,
                                  'df_lsa_active_fm_hsx.csv'),
                     dtype = {'Ident': str,
                              'Code INSEE' : str,
                              'Code INSEE ardt' : str,
                              'Siret' : str},
                     parse_dates = [u'DATE ouv',
                                    u'DATE ferm',
                                    u'DATE réouv',
                                    u'DATE chg enseigne',
                                    u'DATE chgt surf'],
                     encoding = 'UTF-8')

df_lsa_gas = df_lsa[~pd.isnull(df_lsa['Pompes'])].copy()

# ##########
# MATCHING
# ##########

dict_lsa_stores_alt_brand = {u'INTERMARCHE SUPER': u'INTERMARCHE',
                             u'INTERMARCHE CONTACT': u'INTERMARCHE',
                             u'INTERMARCHE HYPER' : u'INTERMARCHE',
                             u'INTERMARCHE EXPRESS': u'INTERMARCHE',
                             u'RELAIS DES MOUSQUETAIRES' : u'INTERMARCHE',
                             u'SUPER U' : u'SYSTEME U',
                             u'U EXPRESS': u'SYSTEME U',
                             u'HYPER U' : u'SYSTEME U',
                             u'MARCHE U' : u'SYSTEME U',
                             u'CARREFOUR CITY' : u'CARREFOUR MARKET',
                             u'MARKET' : u'CARREFOUR MARKET',
                             u'SHOPI' : u'CARREFOUR MARKET',
                             u'CARREFOUR EXPRESS' : u'CARREFOUR MARKET',
                             u'CARREFOUR CONTACT' : u'CARREFOUR MARKET',
                             u'CHAMPION': u'CARREFOUR MARKET',
                             u'GEANT CASINO' : u'GEANT CASINO',
                             u'HYPER CASINO': u'GEANT CASINO',
                             # u'CASINO' : u'GEANT CASINO',
                             u'GEANT' : u'GEANT CASINO',
                             u'CENTRE E.LECLERC' : u'LECLERC',
                             u'LECLERC EXPRESS' : u'LECLERC'}

# Overwrite enseigne alt to make most general
df_lsa_gas['Enseigne_alt'] = df_lsa_gas['Enseigne_alt'].apply(\
                               lambda x: dict_lsa_stores_alt_brand[x]\
                                           if dict_lsa_stores_alt_brand.get(x)\
                                           else x)

ls_matching = [[u'INTERMARCHE', u'XXX', u'INTERMARCHE'], # give up direct matching
               [u'INTERMARCHE_CONTACT', u'INTERMARCHE CONTACT', 'INTERMARCHE'],
               [u'AUCHAN', u'AUCHAN', u'AUCHAN'],
               [u'LECLERC', u'CENTRE E.LECLERC', u'LECLERC'],
               [u'CARREFOUR', u'CARREFOUR', u'CARREFOUR'],
               [u'CARREFOUR_MARKET', u'CARREFOUR MARKET', u'CARREFOUR MARKET'],
               [u'CHAMPION', u'XXX', u'CARREFOUR MARKET'],
               [u'SHOPI', u'SHOPI', u'CARREFOUR MARKET'],
               [u'CORA', u'CORA', u'CORA'],
               [u'GEANT', u'GEANT', u'GEANT CASINO'], # ok if beginning only?
               [u'SYSTEMEU', u'XXX', 'SYSTEME U'],
               [u'SIMPLY', u'XXX', u'SIMPLY MARKET'],
               [u'CASINO', u'CASINO', u'CASINO'],
               [u'CARREFOUR_CONTACT', u'CARREFOUR CONTACT', 'CARREFOUR MARKET'],
               [u'ECOMARCHE', u'XXX', u'INTERMARCHE'],
               [u'NETTO', u'NETTO', u'NETTO'],
               [u'COLRUYT', u'COLRUYT', u'COLRUYT'],
               [u'LEADER_PRICE', u'LEADER PRICE', u'LEADER PRICE'],
               [u'MAXIMARCHE', u'MAXIMARCHE', u'MAXIMARCHE']]

ls_rows_matching = []
for enseigne_store, enseigne_lsa, enseigne_lsa_alt in ls_matching:
  for row_ind, row in df_info[(df_info['brand_0'] == enseigne_store)].iterrows():
    insee_code = row['ci_ardt_1'] # need ardt: 1 a priori
    df_city_stores = df_lsa_gas[(df_lsa_gas['Code INSEE ardt'] == insee_code) &\
                                (df_lsa_gas['Enseigne'] == enseigne_lsa)]
    if len(df_city_stores) == 1:
      ls_rows_matching.append((row_ind,
                               df_city_stores.iloc[0]['Ident'],
                               'direct'))
    elif len(df_city_stores) == 0:
      df_city_stores_alt = df_lsa_gas[(df_lsa_gas['Code INSEE ardt'] == insee_code) &\
                                      (df_lsa_gas['Enseigne_alt'] == enseigne_lsa_alt)]
      if len(df_city_stores_alt) == 1:
        ls_rows_matching.append((row_ind,
                                 df_city_stores_alt.iloc[0]['Ident'],
                                 'indirect'))
      elif len(df_city_stores_alt) == 0:
        ls_rows_matching.append((row_ind,
                                  None,
                                  'aucun'))
      else:
        ls_rows_matching.append((row_ind,
                                  None,
                                  'ambiguous'))
    else:
      ls_rows_matching.append((row_ind,
                                None,
                                'ambiguous'))

df_matching = pd.DataFrame(ls_rows_matching,
                           columns = ['id_station',
                                      'id_lsa',
                                      'Q'])
df_matching.set_index('id_station', inplace = True)

df_info_w_lsa = pd.merge(df_info,
                      df_matching,
                      left_index = True,
                      right_index = True,
                      how = 'left')

#df_info_w_lsa = pd.merge(df_info_w_lsa,
#                         df_lsa,
#                         left_on = 'id_lsa',
#                         right_on = 'Ident',
#                         how = 'left')

ls_disp_ma = ['Q', 'brand_0', 'Enseigne',
                   'adr_zip', 'Code postal'
                   'adr_city', 'Ville',
                   'adr_street', 'ADRESSE1', 'ADRESSE2']

ls_disp_noma = ['Q', 'brand_0', 'ci_ardt_1', 'adr_zip', 'adr_city', 'adr_street', 'name']

print u'\nOverview matching quality:'
print df_info_w_lsa['Q'].value_counts()

print u'\nOverview matching quality by brand_0:'
print df_info_w_lsa.pivot_table(index = 'brand_0',
                                columns = 'Q',
                                aggfunc = 'size',
                                fill_value = 0)

#print df_info_w_lsa[ls_disp_noma]\
#                   [(df_info_w_lsa['brand_0'] == 'CORA') &\
#                   (pd.isnull(df_info_w_lsa['id_lsa']))][0:20].to_string()
## Pbm : brand_0 regroups CORA and MATCH under CORA => separate

# READ MATCHED STORES FROM CSV FILE AND UPDATE FIX
df_read_fix_ms = pd.read_csv(os.path.join(path_source_other,
                                          'fix_gas_lsa_matching.csv'),
                               sep = ';',
                               dtype = {'id_station' : str,
                                        'ci_ardt_1' : str,
                                        'id_lsa' : str,
                                        'adr_zip' : str},
                               encoding = 'latin-1')

# keep only those with some added info (need at least 1 for following to work)
df_read_fix_ms = df_read_fix_ms[(~pd.isnull(df_read_fix_ms['id_lsa']))]
# df_read_fix_ms contains all ad hoc matching
df_read_fix_ms.rename(columns={'id_lsa' : 'id_lsa_adhoc'}, inplace = True)
df_read_fix_ms.set_index('id_station', inplace = True)
df_info_w_lsa = pd.merge(df_read_fix_ms[['id_lsa_adhoc']],
                         df_info_w_lsa,
                         left_index = True,
                         right_index = True,
                         how = 'right')

# priority given to hand info
df_info_w_lsa.loc[~pd.isnull(df_info_w_lsa['id_lsa_adhoc']), 'Q'] = 'manuel'

df_info_w_lsa.loc[~pd.isnull(df_info_w_lsa['id_lsa_adhoc']),
                  'id_lsa'] = df_info_w_lsa['id_lsa_adhoc']

# df_info_w_lsa.loc[pd.isnullf_info_w_lsa['Q']), 'Q'] = 'no' # check

df_info_w_lsa.drop(['id_lsa_adhoc'], axis = 1, inplace = True)
df_info_w_lsa.sort(columns=['ci_ardt_1', 'brand_0'], inplace = True)

# CHECK FOR DUPLICATES IN MATCHING
df_matched = df_info_w_lsa[~pd.isnull(df_info_w_lsa['id_lsa'])]
df_dup = df_matched[(df_matched.duplicated(subset = ['id_lsa'],
                                           take_last = True)) |\
                    (df_matched.duplicated(subset = ['id_lsa'],
                                           take_last = False))]
print '\nNb id_lsa associated with two different stores: {:d}'.format(len(df_dup))
print '\nInspect duplicates:'
ls_dup_disp = ['name', 'adr_street', 'adr_city', 'adr_zip', 'ci_ardt_1', 'id_lsa']
print df_dup[ls_dup_disp].to_string()

# OUTPUT NO MATCH (INCLUDING MANUAL INPUT) FOR FURTHER INVESTIGATIONS
# Impose Q non null: there must have been a matching attempt
df_unmatched = df_info_w_lsa[(~pd.isnull(df_info_w_lsa['Q'])) &\
                             ((pd.isnull(df_info_w_lsa['id_lsa'])) |\
                              (df_info_w_lsa['Q'] == 'manuel'))].copy()
# Cannot accomodate null INSEE_Code with following method
# Anyway.. if insee code could not be found...?
df_unmatched = df_unmatched[~df_unmatched['ci_ardt_1'].isnull()]
df_unmatched['Nb_Same_Brand'] =\
  df_unmatched.groupby('brand_0')['brand_0'].transform('size')
df_unmatched.sort(['Nb_Same_Brand', 'brand_0', 'ci_ardt_1', 'name'],
                  ascending = False,
                  inplace = True)

df_unmatched.reset_index(drop = False, inplace = True)
#df_unmatched.drop(labels = 'Nb_Same_IC', axis = 1, inplace = True)
ls_unmatched_disp = ['id_station', 'Q', 'ci_ardt_1', 'adr_zip',
                     'adr_city', 'adr_street', 'name',
                     'brand_0', 'id_lsa']

print u'\nNb unmatched period/store (before): {:d}'.format(len(df_unmatched))
print u'\nNb manually matched: {:d}'.format(\
        len(df_unmatched[~df_unmatched['id_lsa'].isnull()]))
print '\nInspect unmatched:'
print df_unmatched[ls_unmatched_disp][0:30].to_string(index = False)

# OUTPUT (try to make it an Excel standard csv?)

for col_str in ['name', 'adr_street']:
  df_unmatched[col_str] =\
    df_unmatched[col_str].apply(lambda x: x.replace(u'"', u"'").replace(u';', u' ')\
                                            if x and not isinstance(x, float) else x)

## dunno why float...
#for col_str in ['name', 'id_lsa']:
#  df_unmatched.loc[pd.isnull(df_unmatched[col_str]),
#                   col_str] = None

df_unmatched[ls_unmatched_disp].to_csv(os.path.join(path_source_other,
                                                    'fix_gas_lsa_matching.csv'),
                                       index = False,
                                       encoding = 'latin-1',
                                       sep = ';',
                                       quoting = 3) 
# quoting has no impact (?) cannot have trailing 0s

## ##############
## OUTPUT TO CSV
## ##############

df_info_w_lsa_output = df_info_w_lsa.copy()

df_info_w_lsa_output.loc[((df_info_w_lsa_output.duplicated(subset = ['id_lsa'],
                                                          take_last = True)) |\
                          (df_info_w_lsa_output.duplicated(subset = ['id_lsa'],
                                                          take_last = False))),
                         ['Q', 'id_lsa']] = ['dup', np.nan]

df_info_w_lsa_output.to_csv(os.path.join(path_dir_built_csv,
                                         'df_station_info_final_w_lsa_ids.csv'),
                            index_label = 'id_station',
                            encoding = 'UTF-8')
