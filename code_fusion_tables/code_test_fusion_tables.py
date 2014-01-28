#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import urllib2, urllib, httplib
import simplejson, json, pprint

client_id = '970870116608.apps.googleusercontent.com'
redirect_uri = 'https://www.example.com/oauth2callback'
client_secret = 'sWVyRObf0HffVzpZAnPavIvh'
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

params = {u'Authorization': access_token,
          u'Content-Type': u'application/json'}
url = u'https://www.googleapis.com/fusiontables/v1/tables?%s' %urllib.urlencode(params)
request = urllib2.Request(url, data=data)
request_open = urllib2.urlopen(request)
str_result = request_open.read()
dict_result = json.loads(str_result)

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
# json_response = simplejson.loads(response)


# How to create table (Google)
# https://developers.google.com/fusiontables/docs/v1/reference/table/insert#try-it

# Question (SO)
# http://stackoverflow.com/questions/15919201/trying-to-create-table-in-fusion-tables-returns-invalid-credentials?answertab=oldest#tab-top

# Other resources
# # https://developers.google.com/fusiontables/docs/sample_code
# # Check https://developers.google.com/fusiontables/docs/samples/python?hl=fr