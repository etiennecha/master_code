#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path_sub
from add_to_path_sub import *
from functions_generic_qlmc import *
from functions_geocoding import *
from functions_string import *
import os, sys
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import pprint

path_dir_qlmc = os.path.join(path_data, 'data_qlmc')
path_dir_built_json = os.path.join(path_dir_qlmc, 'data_built' , 'data_json_qlmc')

ls_ls_tuple_stores = dec_json(os.path.join(path_dir_built_json, 'ls_ls_tuple_stores'))

path_dir_insee = os.path.join(path_data, 'data_insee')
path_dir_insee_match = os.path.join(path_dir_insee, 'match_insee_codes')
path_dir_insee_extracts = os.path.join(path_dir_insee, 'data_extracts')

path_dir_built_hdf5 = os.path.join(path_dir_qlmc, 'data_built', 'data_hdf5')

fra_stores = pd.HDFStore(os.path.join(path_dir_built_hdf5, 'fra_stores.h5'))
# qlmc_data = pd.HDFStore(os.path.join(path_dir_built_hdf5, 'qlmc_data.h5'))

# Load df_fra_stores
df_fra_stores = fra_stores['df_fra_stores_current']
# Load insee files
df_insee_areas = pd.read_csv(os.path.join(path_dir_insee_extracts, 'df_insee_areas.csv'))
df_au_agg = pd.read_csv(os.path.join(path_dir_insee_extracts, 'df_au_agg_final.csv'))
df_uu_agg = pd.read_csv(os.path.join(path_dir_insee_extracts, 'df_uu_agg_final.csv'))

# Add insee area codes to df_fra_stores
df_fra_stores = pd.merge(df_insee_areas,
                         df_fra_stores,
                         left_on = 'CODGEO',
                         right_on = 'insee_code',
                         how = 'right')

# NB STORES BY AU
df_au_agg.index = df_au_agg['AU2010']
ls_disp_au = ['AU2010', 'LIBAU2010', 'P10_POP', 'SUPERF', 'POPDENSITY10', 'QUAR2UC10',
              'nb_stores', 'pop_by_store']

se_au_vc = df_fra_stores['AU2010'].value_counts()
df_au_agg['nb_stores'] = se_au_vc
df_au_agg['pop_by_store'] = df_au_agg['P10_POP'] / df_au_agg['nb_stores'] 

print df_au_agg[ls_disp_au][0:10].to_string()

# Nb stores vs. population (# stores by head decreasing in population density?)
# exclude paris (+ todo: check with exclusion of au internationales)
plt.scatter(df_au_agg['P10_POP'][df_au_agg['AU2010']!='001'],
            df_au_agg['nb_stores'][df_au_agg['AU2010']!='001'])
plt.show()

# Store density vs. pop density (# stores by head decreasing in population density?)
plt.scatter(df_au_agg['POPDENSITY10'][df_au_agg['AU2010']!='001'],
            df_au_agg['pop_by_store'][df_au_agg['AU2010']!='001'])
plt.show()


# NB STORES BY UU
df_uu_agg.index = df_uu_agg['UU2010']
ls_disp_uu = ['UU2010', 'LIBUU2010', 'P10_POP', 'SUPERF', 'POPDENSITY10', 'QUAR2UC10',
              'nb_stores', 'pop_by_store']

se_au_vc = df_fra_stores['UU2010'].value_counts()
df_uu_agg['nb_stores'] = se_au_vc
df_uu_agg['pop_by_store'] = df_uu_agg['P10_POP'] / df_uu_agg['nb_stores']

df_uu_agg.sort('P10_POP', ascending=False, inplace=True)
print df_uu_agg[ls_disp_uu][df_uu_agg['nb_stores'] >= 1][0:10].to_string()

## Nb stores vs. population (# stores by head decreasing in population density?)
## exclude paris (+ todo: check with exclusion of au internationales)
#plt.scatter(df_uu_agg['P10_POP'][df_uu_agg['AU2010']!='001'],
#            df_uu_agg['nb_stores'][df_uu_agg['AU2010']!='001'])
#plt.show()
#
## Store density vs. pop density (# stores by head decreasing in population density?)
#plt.scatter(df_uu_agg['POPDENSITY10'][df_uu_agg['AU2010']!='001'],
#            df_uu_agg['pop_by_store'][df_uu_agg['AU2010']!='001'])
#plt.show()
