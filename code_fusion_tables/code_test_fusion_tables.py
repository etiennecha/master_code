#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
import urllib2, urllib, httplib
import json, pprint

def runRequest(method, url, data=None, headers=None):
  """
  Function to run http requests (adapted from a Google code sample)
  """
  request = httplib.HTTPSConnection("www.googleapis.com")
  if data and headers:
    request.request(method, url, data, headers)
  else: 
    request.request(method, url)
  response = request.getresponse()
  print response.status, response.reason
  response = response.read()
  print response
  return response

def insertRow(table_id, access_token, data):
  """
  Function to insert rows in a table (csv? adapted from a Google code sample)
  """
  print "INSERT ROWS"
  response = runRequest(
    "POST",
    "/upload/fusiontables/v1/tables/%s/import" % table_id,
    data,
    headers={'Authorization': 'Bearer %s' %access_token,
             'Content-Type':'application/octet-stream'})
  json_response = json.loads(response)
  return json_response

# Authentication with OAuth, inspired by: 
# https://developers.google.com/fusiontables/docs/samples/python?hl=FR

client_id = '970870116608.apps.googleusercontent.com'

path_current = os.path.abspath(os.path.dirname(sys.argv[0]))
dict_api_info = json.loads(open(os.path.join(path_current, 'client_secret_%s.json' %client_id), 'r').read())
client_secret = dict_api_info['web']['client_secret']
redirect_uri = dict_api_info['web']['redirect_uris'][0]

# Originally in Google sample code:
# Copy paste displayed url in navigator
# Requires to log in with Google account if not already done (cookies...)
# Copy paste code and the end of redirect url back to python
# TODO: check google api to automate (log in step)
print 'Visit the URL below in a browser to authorize'
print '%s?client_id=%s&redirect_uri=%s&scope=%s&response_type=code' % \
  ('https://accounts.google.com/o/oauth2/auth',
  client_id,
  redirect_uri,
  'https://www.googleapis.com/auth/fusiontables')

auth_code = raw_input('Enter authorization code (parameter of URL): ')

# Application requests an access token (and refresh token???) from Google
# Check if needed: https://developers.google.com/accounts/docs/OAuth2WebServer?hl=fr#offline
data = urllib.urlencode({
  'code': auth_code,
  'client_id': client_id,
  'client_secret': client_secret,
  'redirect_uri': redirect_uri,
  'grant_type': 'authorization_code'
})
request = urllib2.Request(
  url='https://accounts.google.com/o/oauth2/token',
  data=data)
request_open = urllib2.urlopen(request)

# Google returns access token (refresh token?) and expiration of access token
response = request_open.read()
request_open.close()
tokens = json.loads(response)
access_token = tokens['access_token']
# refresh_token = tokens['refresh_token']

# Get list of tables
request = urllib2.Request(
  url='https://www.googleapis.com/fusiontables/v1/tables?%s' % \
    (urllib.urlencode({'access_token': access_token})))
request_open = urllib2.urlopen(request)
str_tables_info = request_open.read()
request_open.close()
dict_tables_info = json.loads(str_tables_info)
pprint.pprint(dict_tables_info['items'][4])

# Example: table_id and data
table_id = u'1tSUrkjvpE2r85XvpfwW46LPdbzxoj4mu8G1YeIz_'
data = "test3, 51\ntest4, 31"

# Get rows of a table
request = urllib2.Request(u'https://www.googleapis.com/fusiontables/v1/query?%s'\
                            %(urllib.urlencode({'access_token': access_token,
                                                'sql': 'SELECT * FROM %s' %table_id})))
request_open = urllib2.urlopen(request)
str_table_content = request_open.read()
dict_table_content = json.loads(str_table_content)
print dict_table_content['columns']
print dict_table_content['rows'][0]

## Insert rows as csv with functions from Google code sample
#test = insertRow(table_id, access_token, data)
#
## Insert rows as csv with urllib2
#headers =  {u'Authorization': 'Bearer %s' %access_token,
#            u'Content-Type': u'application/octet-stream'} #application/json
#url = u'https://www.googleapis.com/upload/fusiontables/v1/tables/%s/import' %table_id
#request = urllib2.Request(url, headers = headers)
#try:
#  request_open = urllib2.urlopen(request, data = data)
#except urllib2.HTTPError, e:
#  print 'HTTP error'
#  pprint.pprint(e.readlines())
#except urllib2.URLError, e:
#  print 'URL error'
#  error = e

# Insert row as sql query with urllib2
url = u'https://www.googleapis.com/fusiontables/v1/query'
headers =  {u'Authorization': 'Bearer %s' %access_token,
            u'Content-Type': u'application/x-www-form-urlencoded'} #application/json
data = {u'sql' : u"INSERT INTO %s(Text, Number) VALUES ('75014100', 8);" %table_id}
request = urllib2.Request(url, data = urllib.urlencode(data), headers = headers)
try:
  request_open = urllib2.urlopen(request)
  print request_open.read()
except urllib2.HTTPError, e:
  print 'HTTP error'
  pprint.pprint(e.readlines())
except urllib2.URLError, e:
  print 'URL error'
  error = e

# Create table
data="""
{
 "name": "Insects",
 "columns": [
  {
   "name": "Species",
   "type": "STRING"
  },
  {
   "name": "Elevation",
   "type": "NUMBER"
  },
  {
   "name": "Year",
   "type": "DATETIME"
  }
 ],
 "description": "Insect Tracking Information.",
 "isExportable": true
}
"""

#data_1 = {"name": "Insects",
#          "description": "Insect Tracking Information.",
#          "isExportable": True}
#data_2 = {"columns": [{"name": "Species",   "type": "STRING"},
#                    {"name": "Elevation", "type": "NUMBER"},
#                    {"name": "Year",      "type": "DATETIME"}]}
#data = urllib.urlencode(data_1) + '&' + urllib.urlencode(data_2) 

data = {"name": "Insects",
        "columns": [{"name": "Species",   "type": "STRING"},
                    {"name": "Elevation", "type": "NUMBER"},
                    {"name": "Year",      "type": "DATETIME"}],
        "description": "Insect Tracking Information.",
        "isExportable": True}
data = urllib.urlencode(data)

url = u'https://www.googleapis.com/fusiontables/v1/tables'
headers = {u'Authorization': u'Bearer %s' %access_token,
           u'Content-Type' : u'application/json'} 
request = urllib2.Request(url, data = data, headers = headers)
try:
  request_open = urllib2.urlopen(request)
  print request_open.read()
except urllib2.HTTPError, e:
  print 'HTTP error'
  pprint.pprint(e.readlines())
except urllib2.URLError, e:
  print 'URL error'
  error = e

# How to create table (Google)
# https://developers.google.com/fusiontables/docs/v1/reference/table/insert#try-it

# Other resources
# # https://developers.google.com/fusiontables/docs/sample_code
# # Check https://developers.google.com/fusiontables/docs/samples/python?hl=fr
