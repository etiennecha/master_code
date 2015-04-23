#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import *
import os, sys
import re
import pandas as pd

path_lycees = os.path.join(path_data,
                           'data_lycees')

with open(os.path.join(path_lycees,
                       'data_source',
                       'general_info',
                       'national',
                       'dataset-564055.ttl'), 'r') as f:
  data_info_schools = f.read()

ls_info_schools_rows = data_info_schools.split('\n')

dict_schools = {}

# find location of first null and start right after
i = ls_info_schools_rows.index('') + 1
j = i

# store all lines above whenever '' is found 
# last item is '' so got everything
while i <= len(ls_info_schools_rows) - 1:
  if not ls_info_schools_rows[i]:
    dict_schools[ls_info_schools_rows[j]] = ls_info_schools_rows[j:i]
    j = i + 1
  i += 1

# ls_info_schools_rows ends with two empty items hence
dict_schools.pop('', None)

# Starting tag (todo: list all first tag without code (refuse number?)
ls_schools_info_keys = [k for k in dict_schools.keys()\
                        if re.match('<http://data.eurecom.fr', k)]

dict_starting_tag = {}
ls_other_tag = []
for k,v in dict_schools.items():
  if v and re.match('<http://data.eurecom.fr/([a-z/]*)', v[0]):
    str_tag = re.match('<http://data.eurecom.fr/([a-z/]*)',
                       v[0]).group(1)
    dict_starting_tag.setdefault(str_tag, []).append(k)
  elif v:
    ls_other_tag.append(k)

# Check if other_tag is always node: ok
ls_nodes = [x for x in ls_other_tag if re.match('_:node', x)]

# Extract geometry (i.e. gps)
dict_gps = {}
for k in dict_starting_tag['id/school/geometry/']:
  v = dict_schools[k]
  s_id = re.match('<http://data.eurecom.fr/id/school/geometry/([0-9a-zA-Z]*)', k).group(1)
  s_lng = re.search('geometrie#coordX>(.*?)<', k).group(1)
  s_lat = re.search('geometrie#coordY>(.*?)<', v[1]).group(1)
  dict_gps[s_id] = (re.match(' "(.*?)"', s_lat).group(1),
                    re.match(' "(.*?)"', s_lng).group(1))

# Extract school info
dict_info = {}
for k in dict_starting_tag['id/school/']:
  v = dict_schools[k]
  s_id = re.match('<http://data.eurecom.fr/id/school/([0-9a-zA-Z]*)', k).group(1)
  dict_info[s_id] =  {re.match('\t<(.*?)>(.*)(<|$)', x).group(1) :\
                        re.match('\t<(.*?)>(.*)(<|$)', x).group(2)\
                          for x in v[1:]}

# Tags in dict_info
set_info_tags = set()
for s_id, s_info in dict_info.items():
  set_info_tags.update(set(s_info.keys()))
ls_info_tags = list(set_info_tags)
print u'\nNb info tags:', len(ls_info_tags)

# More items in dict_info than items in dict_gps... check missing
ls_missing = list(set(dict_info.keys()).difference(set(dict_gps.keys())))
# Appears that there are coordinates avail in L93 and not in WGS84

# Extract L93 (all tags not in dict_info and dict_gps)
dict_l93 = {}
for geo_tag in ls_other_tag:
  v = dict_schools[geo_tag]
  geo_id = re.match('(.*?) ', geo_tag).group(1)
  s_x = re.search('geometrie#coordX> "(.*?)"', v[2]).group(1)
  s_y = re.search('geometrie#coordY> "(.*?)"', v[3]).group(1)
  dict_l93[geo_id] = (s_x, s_y)

ls_ref_geo_tags = []
for s_id, s_info in dict_info.items():
  geo = s_info.get('http://data.ign.fr/ontologies/geometrie#geometrie', None)

  if geo:
    k = geo[1:-2]
    ls_ref_geo_tags.append(k)
    dict_info[s_id]['http://data.ign.fr/ontologies/geometrie#geometrie'] = dict_l93[k]

## weird: a lot of elts in ls_other_tag are not linked to a school
#ls_unref_geo_tags = list(set(ls_other_tag).difference(set(ls_ref_geo_tags)))

# BUILD DATAFRAME

ls_txt_tags = ls_info_tags
ls_txt_tags.remove('http://data.eurecom.fr/ontologies/ecole#nature') # preproces??
ls_txt_tags.remove('http://data.ign.fr/ontologies/geometrie#geometrie')
ls_txt_tags.remove('http://data.ign.fr/ontologies/geometrie#geometry') # unsure?

# Loop on dict_info and pick in dict_gps
ls_rows = []
for s_id, s_info in dict_info.items():
  s_info_clean = {k: re.match(' "(.*?)"', v).group(1).decode('utf-8')\
                    for k,v in s_info.items() if k in ls_txt_tags}
  row = [s_info_clean.get(tag, None) for tag in ls_txt_tags]
  row += list(s_info.get('http://data.ign.fr/ontologies/geometrie#geometrie', (None, None)))
  row += list(dict_gps.get(s_id, (None, None)))
  ls_rows.append(row)

ls_cols = [re.search('.*(#|/)(.*?)$', x).group(2) for x in ls_txt_tags]
ls_cols += ['l93_x', 'l93_y', 'lat', 'lng']

df_schools = pd.DataFrame(ls_rows,
                          columns = ls_cols)

df_schools.set_index('code', inplace = True)

for col in ['lat', 'lng']:
  df_schools[col] = df_schools[col].astype(float)

pd.set_option('float_format', '{:,.2f}'.format)

print df_schools[0:100].to_string()

#print df_schools[(df_schools['l93_x'].isnull()) &\
#                 (df_schools['lat'].isnull())][0:20].to_string()

print u'\nNo standard GPS but Lambert 93 may be available:'
print len(df_schools[(~df_schools['l93_x'].isnull()) &\
                     (df_schools['lat'].isnull())])

print df_schools[(~df_schools['l93_x'].isnull()) &\
                 (df_schools['lat'].isnull())][0:20].to_string()

# OUTPUT TO CSV
df_schools.to_csv(os.path.join(path_lycees,
                               'data_built',
                               'csv',
                               'df_lycees_geo_fra.csv'),
                  encoding = 'utf-8',
                  float_format='%.3f',
                  index_label = 'code')
