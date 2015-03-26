#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import *
import os, sys
import httplib
import urllib, urllib2
from bs4 import BeautifulSoup
import re
import json
import pandas as pd
from functions_generic_qlmc import *
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import textwrap

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

path_qlmc_scraped = os.path.join(path_data,
                                  'data_qlmc',
                                  'data_source',
                                  'data_scraped')

path_csv = os.path.join(path_data,
                        'data_qlmc',
                        'data_built',
                        'data_csv')

df_stores = pd.read_csv(os.path.join(path_csv,
                                     'qlmc_scraped',
                                     'df_stores.csv'),
                        encoding = 'utf-8')

df_comp = pd.read_csv(os.path.join(path_csv,
                                   'qlmc_scraped',
                                   'df_competitors.csv'),
                      encoding = 'utf-8')

df_france = pd.read_csv(os.path.join(path_csv,
                                     'qlmc_scraped',
                                     'df_france.csv'),
                        encoding = 'utf-8')

## Most common products
se_prod_vc = df_france['product'].value_counts()
#print u'\nShow most common products'
#print se_prod_vc[0:30].to_string()

## Most common chains
se_chain_vc = df_france['chain'].value_counts()
#print u'\nShow most common chains'
#print se_chain_vc[0:30].to_string()

## todo: check for each trigram if name starts with cor. dict entry
#dict_chains = {'ITM' : 'INTERMARCHE SUPER',
#               'USM' : 'SUPER U',
#               'CAR' : 'CARREFOUR',
#               'CRM' : 'CARREFOUR MARKET', # or MARKET
#               'AUC' : 'AUCHAN',
#               'GEA' : 'GEANT CASINO',
#               'COR' : 'CORA',
#               'SCA' : 'CASINO',
#               'HSM' : 'HYPER U',
#               'SIM' : 'SIMPLY MARKET',
#               'MAT' : 'SUPERMARCHE MATCH',
#               'HCA' : 'HYPER CASINO',
#               'UEX' : 'U EXPRESS',
#               'ATA' : 'ATAC',
#               'CAS' : 'CASINO',
#               'UHM' : 'HYPER U',
#               'MIG' : 'MIGROS',
#               'G20' : 'G 20',
#               'REC' : 'RECORD',
#               'HAU' : "LES HALLES D'AUCHAN"}

df_france.set_index('product', inplace = True)
df_france['freq_prod'] = se_prod_vc
df_france.reset_index(inplace = True)

df_u_prod = df_france.drop_duplicates('product')
df_u_prod = df_u_prod[['family', 'subfamily', 'product', 'freq_prod']]

df_u_prod.sort('freq_prod', ascending = False, inplace = True)
df_u_prod.set_index(['family', 'subfamily', 'product'], inplace = True)
df_u_prod.sort_index(inplace = True)
