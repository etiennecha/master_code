#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import json
import copy
import string
import urllib
import urllib2

def dec_json(chemin):
 with open(chemin, 'r') as fichier:
  return json.loads(fichier.read())

def enc_stock_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

def supprime_accent(ligne):
 accents = { 'a': ['à', 'ã', 'á', 'â', '\xc2', '\xa2'], 
             'c': ['ç','\xe7'],
             'e': ['é', 'è', 'ê', 'ë', 'É', '\xca', '\xc8', '\xe8', '\xe9', '\xc9','\xa9','\xc3\xa9','\xab'], 
             'i': ['î', 'ï', '\xcf', '\xce','\xae'], 
             'o': ['ô', 'ö','\xd4'], 
             'u': ['ù', 'ü', 'û'], 
             ' ': ['&#039;', '\xb0','\xa0', '\xc3', '\xa8'] }
 for (char, accented_chars) in accents.iteritems():
  for accented_char in accented_chars:
   ligne = ligne.replace(accented_char, char)
 return ligne
 
api_key = 'AIzaSyDzJhqpk1dUdKpxOIuv-xSZcMCDMgQmtYc'

# New Fusion Table API:
# https://developers.google.com/fusiontables/docs/sample_code
# https://developers.google.com/fusiontables/docs/v1/getting_started#migrate
# Check: http://stackoverflow.com/questions/15326640/how-do-i-insert-a-row-in-my-google-fusion-table-using-python

# Get table column description
table_id = '1pnwG5pXOCb6bYD5pNT6vpc04kXGs8nirHyJ--Ss'
url = u'https://www.googleapis.com/fusiontables/v1/tables/%s/columns?key=%s' %(table_id, api_key)
table_response = urllib2.urlopen(url)
table_read = table_response.read()
lol = json.loads(table_read)
# Get table content
query = 'SELECT * FROM %s' %table_id
url = u'https://www.googleapis.com/fusiontables/v1/query'
params = {'sql' : query,
          'key' : api_key}
data = urllib.urlencode(params)
request = urllib2.Request(url, data=data)
table_response = urllib2.urlopen(request)
table_read = table_response.read()

# OAuth: https://developers.google.com/accounts/docs/OAuth2WebServer#offline

params = {"name": "Insects",
          "columns": [{"name": "Species", "type": "STRING"},
                      {"name": "Elevation", "type": "NUMBER"},
                      {"name": "Year", "type": "DATETIME"}],
          "description": "Insect Tracking Information.",
          "isExportable": true}

# CREATE TABLE

# table = {'stations_services':{'id': 'STRING',
                              # 'name': 'STRING',
                              # 'gps': 'LOCATION', 
                              # 'address': 'STRING',
                              # 'brand': 'STRING'}}

# print tableid

# # FILL TABLE

# # Get data (name: 'db':list of ...), get rid of Corsica/highway
# # TODO: get list of dict with right keys (corresponding to created db)
# # TODO: then split it in number tolerated (50...)

  # # Build list_master_send : list of dict with righ keys and encoding (TODO)
# for temp_k, temp_v in temp_db.iteritems():
  # row = {} #db[j]
  # row['id'] = None
  # rpw['name'] = None
  # lat = None
  # lng = None
  # row['gps'] = '%s %s' %(lat,lng)
  # row['address'] = None
  # row['brand'] = None
  # for k, v in row.iteritems():
    # if type(v) in (str, unicode):
      # str_v_no_accent = supprime_accent(row[elt].encode('latin-1'))
      # # str_v_no_accent.encode('ascii','ignore')
      # row[k] = '%s' %str_v_no_accent
    # k_2 = k.encode('ASCII','ignore')
    # temp_data= row[k]
    # del row[k]
    # row[k_2] = data

# # Format and send queries

# # A/ compute number of nb X. instructions + remainder
# n_batch = 50
# n_loops = len(db) / n_batch
# n_remainder = len(db) - n_loops * n_batch

# # B/ send full blocks
# c = 0
# for i in range(n_loops):
  # list_rows_to_send = list_master_send[c:c+n_batch]
  # list_instructions_to_send = [SQL().insert(tableid, row) for row in list_rows_to_send]
  # block_to_send = ';'.join(rows) + ';'
  # echo_res = ft_client.query(block_to_send)
  # print echo_res
  # c += n_batch

# # C/ send remainder
# rows = []
# list_rows_to_send = list_master_send[c,c+n_remainder]
# list_instructions_to_send = [SQL().insert(tableid, row) for row in list_rows_to_send]
# block_to_send = ';'.join(rows) + ';'
# echo_res = ft_client.query(block_to_send)
# print echo_res
# c += n_batch

# results = ft_client.query(SQL().showTables())
# print results
# drop table
# ft_client.query(SQL().dropTable(tableid))
# test_sel1= ft_client.query(SQL().select(tableid,['Nom','Commune',]))
# print test_sel1
# description = ft_client.query(SQL().describeTable(tableid))
# print description
# test_sel1= ft_client.query(SQL().select(tableid,['nom','id_station','localisation'],"ser5=1 and ser9=1 and ser13=1"))
# print test_sel1
# test_sel2= ft_client.query(SQL().select(tableid,['nom','ser13'],"ST_INTERSECTS(location,CIRCLE(LATLNG(48.8778,2.1756),20000))"))
# print test_sel2