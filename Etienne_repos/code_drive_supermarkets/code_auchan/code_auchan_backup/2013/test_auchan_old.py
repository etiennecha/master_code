# -*- coding: iso-8859-1 -*-
import cookielib
import urllib, urllib2
from BeautifulSoup import BeautifulSoup
import re
import json
import string

list_drive_url = []

cookie_jar = cookielib.LWPCookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))
urllib2.install_opener(opener)

auchan_drive_website_url = 'http://www.auchandrive.fr'

response = urllib2.urlopen(auchan_drive_website_url)
data = response.read()
soup = BeautifulSoup(data)
lis = soup.findAll('li', {'class' : re.compile('dpt*')})
for li in lis:
  list_drive_url.append(li('a')[0]['href'])

drive_url = list_drive_url[0]
response_2 = urllib2.urlopen(drive_url)
data_2 = response_2.read()
soup_2 = BeautifulSoup(data_2)

departments = soup_2.findAll('li', {'class' : 'HeaderNavOnglet  slider'})
department_url = departments[0].find('a', {'class' : 'HeaderNavOngletLink'})['href']

"""
arguments = {'channelID' :'170'}
research = urllib.urlencode(arguments)
req = urllib2.Request(auchan_drive_website_url + department_url, research)
"""

response_3 = urllib2.urlopen(auchan_drive_website_url + department_url)
data_3 = response_3.read()
soup_3 = BeautifulSoup(data_3)