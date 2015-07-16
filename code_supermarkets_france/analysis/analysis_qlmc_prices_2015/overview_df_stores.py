#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import *
from functions_string import *
from functions_generic_qlmc import *
import os, sys
import re
import json
import pandas as pd
from mpl_toolkits.basemap import Basemap
from matplotlib.collections import PatchCollection
from shapely.geometry import Point, Polygon, MultiPoint, MultiPolygon, shape
from shapely.prepared import prep
from descartes import PolygonPatch

pd.set_option('float_format', '{:,.3f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.3f}'.format(x)

path_qlmc_scraped = os.path.join(path_data,
                                 'data_supermarkets',
                                 'data_qlmc_2015',
                                 'data_source',
                                 'data_scraped_201503')

path_csv = os.path.join(path_data,
                        'data_supermarkets',
                        'data_qlmc_2015',
                        'data_built',
                        'data_csv_201503')

df_stores = pd.read_csv(os.path.join(path_csv,
                                     'df_stores_final.csv'),
                        dtype = {'ic' : str,
                                 'lsa_id' : str,
                                 'Code INSEE ardt' : str},
                        encoding = 'utf-8')

print u'\nNf of hypers and supers:'
print df_stores['Type'].value_counts()

print u'\nNb of stores by retail group:'
print df_stores['Groupe'].value_counts()

print u'\nNb of stores by chain:'
print df_stores['Enseigne'].value_counts()

# todo: check H/S split of sample vs. H/S split by retail group

se_rg_vc = df_stores['Groupe'].value_counts()
ls_rg = list(se_rg_vc.index[se_rg_vc >= 1])
pd.set_option('float_format', '{:,.0f}'.format)

print u'\nSurface distribution by retail group:'
ls_df_desc_surf = []
for rg in ls_rg:
  ls_df_desc_surf.append(df_stores[df_stores['Groupe'] == rg]['Surf Vente'].describe())
df_surf_by_rg = pd.concat(ls_df_desc_surf,
                          keys = ls_rg,
                          axis = 1)
df_surf_by_rg.columns = ['{:7s}'.format(x[0:7]) for x in df_surf_by_rg.columns]
print df_surf_by_rg.to_string()
# todo: force column size to improve table display

print u'\nNb employees by retail group:'
ls_df_desc_nemp = []
for rg in ls_rg:
  ls_df_desc_nemp.append(df_stores[df_stores['Groupe'] == rg]['Nbr emp'].describe())
df_nemp_by_rg = pd.concat(ls_df_desc_nemp,
                          keys = ls_rg,
                          axis = 1)
df_nemp_by_rg.columns = ['{:>7s}'.format(x[0:7]) for x in df_nemp_by_rg.columns]
print df_nemp_by_rg.to_string()
# todo: force column size to improve table display
