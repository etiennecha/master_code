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

def enc_json(data, path_file):
  with open(path_file, 'w') as f:
    json.dump(data, f)

def dec_json(path_file):
  with open(path_file, 'r') as f:
    return json.loads(f.read())

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

dict_reg_leclerc = dec_json(os.path.join(path_qlmc_scraped,
                                         'dict_reg_leclerc_stores.json'))

dict_leclerc_comp = dec_json(os.path.join(path_qlmc_scraped,
                                          'dict_leclerc_comp.json'))

# todo: load df_comp (contains pairs actually collected)
# todo: compare with dict_leclerc_comp (pairs on website)
