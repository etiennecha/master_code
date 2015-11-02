#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
import os
from datetime import date, timedelta
from functions_generic_drive import *

path_source = os.path.join(path_data,
                           u'data_supermarkets',
                           u'data_source',
                           u'data_drive',
                           u'data_leclerc')

path_source_json = os.path.join(path_source,
                               u'data_json')

path_built = os.path.join(path_data,
                          u'data_supermarkets',
                          u'data_built',
                          u'data_drive',
                          u'data_leclerc')

path_built_csv = os.path.join(path_built,
                              u'data_csv')

# ###########################
# CHECK ONE FILE WITH PANDAS
# ###########################

date_str = '20150508'
path_file = os.path.join(path_source_json,
                         '{:s}_dict_leclerc'.format(date_str))
dict_period = dec_json(path_file)

# Check fields for each product (with stats)
dict_fields = {}
for store, ls_dict_stores in dict_period.items():
  for dict_product in ls_dict_stores:
    for product_key in dict_product[u'objElement'].keys():
      dict_fields.setdefault(product_key, []).append(dict_product.get('sIdUnique',
                                                                      None))
for k,v in dict_fields.items():
  print k, len(v)

# Need to consider period with same fields
ls_fields = dict_fields.keys()

# ###################
# BUILD DF MASTER
# ###################

path_temp = path_source_json
start_date, end_date = date(2015,5,7), date(2015,6,28)
ls_dates = get_date_range(start_date, end_date)
ls_df_products = []
for date_str in ls_dates:
  path_file = os.path.join(path_temp,
                           '{:s}_dict_leclerc'.format(date_str))
  if os.path.exists(path_file):
    dict_period = dec_json(path_file)
     
    ## Find all keys appearing in at least one product dictionary
    #ls_all_fields = []
    #for dict_product in period_file:
    #  ls_all_fields += dict_product.keys()
    #ls_fields = list(set(ls_all_fields))
    
    # Build dataframe
    ls_rows_products = []
    for store, ls_dict_stores in dict_period.items():
      for dict_product in ls_dict_stores:
        row = [dict_product[u'objElement'].get(field) for field in ls_fields]
        row = [' '.join(x) if isinstance(x, list) else x for x in row]
        row = [store, dict_product.get('sub_dpt')] + [x if x else None for x in row]
        ls_rows_products.append(row)
    df_products = pd.DataFrame(ls_rows_products,
                               columns = ['store', 'sub_dpt'] + ls_fields)
    df_products['date'] = date_str
    ls_df_products.append(df_products)
df_master = pd.concat(ls_df_products, axis = 0, ignore_index = True)

df_master_bu = df_master.copy()

dict_rename_columns = {u'sPrixPromoParUniteDeMesure' : u'promo_per_unit',
                       u'sPrixParUniteDeMesure'      : u'unit_price',
                       u'sPrixUnitaire'              : u'total_price',
                       u'iQteDisponible'             : u'stock',
                       u'sLibelleMarque'             : u'brand',
                       u'sLibelleLigne1'             : u'title',
                       u'sLibelleLigne2'             : u'label',
                       u'sPrixPromo'                 : u'promo',
                       u'fPromo'                     : u'dum_promo',
                       u'sLibelle_TEL_1'             : u'loyalty',
                       u'sLibelle_BRII_1'            : u'lib_0',
                       u'sLibelle_BRII_2'            : u'lib_1',
                       u'sLibellePictoPromo'         : u'lib_promo',
                       u'sId'                        : u'idProduit',
                       u'iIdRayon'                   : u'idRayon',
                       u'iIdFamille'                 : u'idFamille',
                       u'niIdSousFamille'            : u'idSousFamille'}

df_master.rename(columns = dict_rename_columns, inplace = True)
ls_cols = [v for k,v in dict_rename_columns.items()] + ['store', 'date', 'sub_dpt']
df_master = df_master[ls_cols]

df_master['sub_dpt'] =\
  df_master['sub_dpt'].apply(lambda x: x.replace(u'\n', u'').strip())

dict_clean_text = {u'&#224;' : u'à',
                   u'&#226;' : u'â',
                   u'&#233;' : u'é',
                   u'&#232;' : u'è',
                   u'&#234;' : u'ê',
                   u'&#244;' : u'ô',
                   u'&#238;' : u'î',
                   u'&#239;' : u'ï',
                   u'&#249;' : u'ù',
                   u'&#251;' : u'û',
                   u'&#231;' : u'ç',
                   u'&amp;'  : u'&',
                   u'&#176;' : u'°'}

def clean_text(x):
  for k,v in dict_clean_text.items():
    x = x.replace(k, v)
  return x

for field in ['title', 'brand', 'label', 'lib_0']:
  df_master[field] =\
    df_master[field].apply(lambda x: clean_text(x) if x else x)

df_dpts = df_master.drop_duplicates(u'idRayon')

#print u'\nOne sub_dpt for each idRayon:'
#print df_dpts[[u'idRayon', 'sub_dpt']].to_string()

dict_rayons = {284322 : u'Viandes Poissons',
               284323 : u'Fruits Légumes',
               284321 : u'Pains Pâtisseries',
               284320 : u'Frais',
               284246 : u'Surgelés',
               284319 : u'Epicerie salée',
               284309 : u'Epicerie sucrée',
               284310 : u'Boissons',
               284311 : u'Bébé',
               284314 : u'Bio',
               284315 : u'Hygiène Beauté',
               284316 : u'Entretien Nettoyage',
               284317 : u'Animalerie',
               284318 : u'Bazar Textile'}

df_master['dpt'] =\
  df_master['idRayon'].apply(lambda x: dict_rayons.get(x) if x else None)

df_master['unit_price'], df_master['unit'] =\
  zip(*df_master['unit_price'].apply(lambda x:\
                                       [x.strip() for x in x.split(u'\u20ac')]\
                                          if x else [None, None]))

df_master['unit'] =\
  df_master['unit'].apply(lambda x: x.replace('/', '').strip() if x else x)

df_master['unit_price'] =\
  df_master['unit_price'].apply(lambda x: x.replace(u'\u20ac', u'')\
                                            .strip() if x else None).astype(float)

df_master['total_price'] =\
  df_master['total_price'].apply(lambda x: x.replace(u'\u20ac', u'')\
                                            .strip() if x else x).astype(float)

df_master['promo'] =\
  df_master['promo'].apply(lambda x: x.replace(u'\u20ac', u'')\
                                      .strip() if x else x).astype(float)

#df_sub = df_master[(df_master['date'] == '20150509') &\
#                   (df_master['store'] == 'Clermont Ferrand')]
#
#print u'\nNb products in one store (collected and unique):'
#print len(df_sub)
#print len(df_sub['idProduit'].unique())
## print len(df_sub[df_sub['dpt'].isnull()])
#df_master = df_master[~pd.isnull(df_master['title'])]
#
### lib_1 and lib_promo : no interesting info
##print df_master['lib_1'].value_counts()
##print df_master['lib_promo'].value_counts()
#df_master.drop(['lib_1', 'lib_promo'], axis = 1, inplace = True)
#
#print u'\nOverview promo:'
#print df_master[df_master['promo'] != u'0.00 \u20ac'][0:10].to_string()
## promo is the actual price (after reduction  in lib_0)
## total_price not relevant to products in promotion

# ############
# OUTPUT
# ############

df_master.rename(columns = {u'dpt': u'section',
                            u'sub_dpt': u'family'},
                 inplace = True)

ls_dup_id_cols = ['store', 'date', 'section', 'family', 'idProduit']

df_master_nodup =\
  df_master[~((df_master.duplicated(ls_dup_id_cols)) |\
              (df_master.duplicated(ls_dup_id_cols,
                                    take_last = True)))]

ls_price_cols = ['store', 'date',
                 'idProduit', 'title', 'brand', 'label',
                 'total_price', 'unit_price', 'unit',
                 'promo', 'promo_per_unit', 'dum_promo',
                 'lib_0', 'loyalty', 'stock']

df_prices = df_master_nodup[ls_price_cols].drop_duplicates(ls_price_cols[:3])

ls_product_cols = ['section', 'family',
                   'idProduit', 'title', 'brand', 'label',
                   'idRayon', 'idFamille', 'idSousFamille']

df_products = df_master_nodup[ls_product_cols].drop_duplicates()

dict_leclerc_2015 = {'df_master_leclerc_2015' : df_master,
                     'df_prices_leclerc_2015' : df_prices,
                     'df_products_leclerc_2015': df_products}

for file_title, df_file in dict_leclerc_2015.items():
  df_file.to_csv(os.path.join(path_price_built_csv,
                              '{:s}.csv'.format(file_title)),
                   encoding = 'utf-8',
                   float_format='%.2f',
                   index = False)
