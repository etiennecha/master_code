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

drive_url = r'%s' %list_drive_url[0]

# shop request
req2 = urllib2.Request(
  'http://www.auchandrive.fr/magasin/magasin.jsp?idMag=985',
  headers={
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.19 (KHTML, like Gecko) Ubuntu/12.04 Chromium/18.0.1025.168 Chrome/18.0.1025.168 Safari/535.19',
    'Referer': auchan_drive_website_url,
    'Cache-Control': 'max-age=0',
		'Host': 'www.auchandrive.fr',
    'Accept': 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
  }
)

response_2 = urllib2.urlopen(req2)
data_2 = response_2.read()
soup_2 = BeautifulSoup(data_2)

departments = soup_2.findAll('li', {'class' : 'HeaderNavOnglet  slider'})
department_url = departments[0].find('a', {'class' : 'HeaderNavOngletLink'})['href']

# department request
req3 = urllib2.Request(
  'http://www.auchandrive.fr/magasin/rayon.jsp?channelId=170',
  headers={
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.19 (KHTML, like Gecko) Ubuntu/12.04 Chromium/18.0.1025.168 Chrome/18.0.1025.168 Safari/535.19',
    'Referer': auchan_drive_website_url + department_url,
    'Cache-Control': 'max-age=0',
		'Host': 'www.auchandrive.fr',
    'Accept': 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
  }
)

response_3 = urllib2.urlopen(req3)
data_3 = response_3.read()
soup_3 = BeautifulSoup(data_3)

response_3 = urllib2.urlopen(req3)
data_3 = response_3.read()
soup_3 = BeautifulSoup(data_3) 

# infra-department request
req4 = urllib2.Request(
  'http://www.auchandrive.fr/magasin/rayon.jsp?channelId=170&ssChannelId=222&tous=tous',
  headers={
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.19 (KHTML, like Gecko) Ubuntu/12.04 Chromium/18.0.1025.168 Chrome/18.0.1025.168 Safari/535.19',
    'Referer': auchan_drive_website_url + department_url,
    'Cache-Control': 'max-age=0',
		'Host': 'www.auchandrive.fr',
    'Accept': 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
  }
)

response_4 = urllib2.urlopen(req4)
data_4 = response_4.read()
soup_4 = BeautifulSoup(data_4)

response_4 = urllib2.urlopen(req4)
data_4 = response_4.read()
soup_4 = BeautifulSoup(data_4) 

print data_4