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

response_5 = urllib2.urlopen('http://www.auchandrive.fr/magasin/chargementListArticles.jsp?sort=viewNumOrdre&order=ascending&pageNum=1&channelId=170&ssChannelId=222&tous=tous&nbDisplay=0')
data_5 = response_5.read()
soup_5 = BeautifulSoup(data_5)

print soup_5

list_products = []
product_blocs = soup_5.findAll("div", { "class" : "vignette" })
na_product_blocs = soup_5.findAll("div", { "class" : "vignette produitNonDispo" })
all_product_blocs = product_blocs + na_product_blocs
for product_bloc in all_product_blocs:
  product_title = product_bloc.find("p", {"class" : "labelProduit"})
  product_unit_price = product_bloc.find("p", {"class" : "prixUnitaire"})
  product_total_price = product_bloc.find("p", {"class" : "prixTotal"})
  list_products.append({'product_title' : product_title.contents,
                        'product_unit_price' : product_unit_price.contents,
                        'product_total_price' : product_total_price.contents})