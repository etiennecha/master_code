#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
import urllib2, urllib, httplib
import json, pprint

client_id = '970870116608.apps.googleusercontent.com'
redirect_uri = 'https://www.example.com/oauth2callback'

path_current = os.path.abspath(os.path.dirname(sys.argv[0]))
dict_api_info = json.loads(open(os.path.join(path_current, 'client_secret_%s.json' %client_id), 'r').read())
client_secret = dict_api_info['web']['client_secret']
# api_key = 'AIzaSyDzJhqpk1dUdKpxOIuv-xSZcMCDMgQmtYc'

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

# Get list of tables (example of query request)
request = urllib2.Request(
  url='https://www.googleapis.com/fusiontables/v1/tables?%s' % \
    (urllib.urlencode({'access_token': access_token})))
request_open = urllib2.urlopen(request)
str_tables_info = request_open.read()
request_open.close()
dict_tables_info = json.loads(str_tables_info)

# Try adding row to this one:

def runRequest(method, url, data=None, headers=None):
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

def insertTemplate(table_id, access_token):
  print "INSERT ROWS"
  data = "'Test', 10\n'Lol', 20""" 
  response = runRequest(
    "POST",
    "/upload/fusiontables/v1/tables/%s/import" % table_id,
    data,
    headers={'Authorization': 'Bearer %s' %access_token,
             'Content-Type':'application/octet-stream'})
  json_response = json.loads(response)
  return json_response

table_id = u'1tSUrkjvpE2r85XvpfwW46LPdbzxoj4mu8G1YeIz_'
lol = insertTemplate(table_id, access_token)

# import
pprint.pprint(dict_tables_info['items'][4])
table_id = u'1tSUrkjvpE2r85XvpfwW46LPdbzxoj4mu8G1YeIz_'
headers =  {u'access_token': access_token,
            u'Content-Type': u'application/octet-stream'} #application/json
url = u'https://www.googleapis.com/fusiontables/v1/tables/%s/import'

# insert row with normal post (?)
#url = u'https://www.googleapis.com/fusiontables/v1/query'
#headers =  {u'access_token': access_token,
#            u'Content-Type': u'application/x-www-form-urlencoded'} #application/json
#data = {u'sql' : u"INSERT INTO %s(Text, Number) VALUES ('75014100', 8);" %table_id}
#request = urllib2.Request(url, data = urllib.urlencode(data), headers = headers)
#request_open = urllib2.urlopen(request)
#str_result = request_open.read()
#dict_result = json.loads(str_result)
# check : https://groups.google.com/forum/#!msg/google-api-php-client/9d2lQAppTvg/o5QGhsXiAQIJ

#data = {u'access_token': access_token,
#        u'Content-Type': u'application/json',
#        u'sql' : u"INSERT INTO %s (id_station, coordinates) VALUES ('75014100', '49.0 1.3');" %table_id}
#params = urllib.urlencode(data)
#url = u'https://www.googleapis.com/fusiontables/v1/query?%s' %params
#request = urllib2.Request(url)
#request_open = urllib2.urlopen(request)
#str_result = request_open.read()
#dict_result = json.loads(str_result)

#POST https://www.googleapis.com/fusiontables/v1/query?access_token={my access token} HTTP/1.1
#Content-Type: application/json
#sql=INSERT INTO 1JOgUG5QWE5hybrDAd2GX3yfjVCGoM6u7WkSVDok ('_id', '_count', 'start_time', 'end_time',  'counts', 'start_plaece', 'end_place', 'distance',  'average_speed', 'send_flag', 'time_span', 'train_type',  'calories', 'weight', 'status', 'map_url', 'rally_id' ) VALUES ('-1', '0', '2013/01/19 09:00:00.000', '2013/01/19 12:34:56.000', '9876', 'Tokorozawa3', 'iidabashi2', '45678',  '67', '0', '986532', '1', '389', '77.70', '0', 'http://www.google.com/',  '3');
#


# table_id = dict_tables_info['items'][0]['tableId']

# # Get rows of tables (example of query request)
# request = urllib2.Request(
  # url='https://www.googleapis.com/fusiontables/v1/query?%s' % \
    # (urllib.urlencode({'access_token': access_token,
                       # 'sql': 'SELECT * FROM %s' %table_id})))
# request_open = urllib2.urlopen(request)
# str_table_content = request_open.read()
# dict_table_content = json.loads(str_table_content)
# print dict_table_content['columns']
# print dict_table_content['rows'][0]

# # Create table
# data = '''{"name": "Insects","columns": [{"name": "Species","type": "STRING"},{"name":"Elevation","type": "NUMBER"},{"name": "Year","type": "DATETIME"}],"description": "Insect Tracking Information.","isExportable": True}'''

#data="""
#{
# "name": "Insects",
# "columns": [
#  {
#   "name": "Species",
#   "type": "STRING"
#  },
#  {
#   "name": "Elevation",
#   "type": "NUMBER"
#  },
#  {
#   "name": "Year",
#   "type": "DATETIME"
#  }
# ],
# "description": "Insect Tracking Information.",
# "isExportable": true
#}
#"""
#
#params = {u'Authorization': access_token,
#          u'Content-Type': u'application/json'}
#url = u'https://www.googleapis.com/fusiontables/v1/tables?%s' %urllib.urlencode(params)
#request = urllib2.Request(url, data=data)
#request_open = urllib2.urlopen(request)
#str_result = request_open.read()
#dict_result = json.loads(str_result)

# def runRequest(method, url, data=None, headers=None):
  # request = httplib.HTTPSConnection("www.googleapis.com")
  # if data and headers: 
    # request.request(method, url, data, headers)
  # else: 
    # request.request(method, url)
  # response = request.getresponse()
  # print response.status, response.reason
  # response = response.read()
  # return response

# headers={}
# headers['Authorization'] = access_token
# headers['Content-Type'] = 'application/json'
# print headers
# response = runRequest("POST","/fusiontables/v1/tables/",data,headers)
# json_response = json.loads(response)


# How to create table (Google)
# https://developers.google.com/fusiontables/docs/v1/reference/table/insert#try-it

# Question (SO)
# http://stackoverflow.com/questions/15919201/trying-to-create-table-in-fusion-tables-returns-invalid-credentials?answertab=oldest#tab-top

# Other resources
# # https://developers.google.com/fusiontables/docs/sample_code
# # Check https://developers.google.com/fusiontables/docs/samples/python?hl=fr
