#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
import httplib, urllib2
import urllib
import cookielib
from cookielib import Cookie
from bs4 import BeautifulSoup
import re
import json
import time

def extract_bs_text(soup_bloc, ls_text = True):
  if soup_bloc and ls_text:
    return [unicode(x) for x in soup_bloc.findAll(text = True)]
  elif not soup_bloc and ls_text:
    return []
  elif soup_bloc and not ls_text:
    return unicode(soup_bloc.text)
  elif not soup_bloc and not ls_text:
    return None

def makeCookie(name, value):
  return Cookie(
    version=0,
    name=name,
    value=value,
    port=None,
    port_specified=False,
    domain="",
    domain_specified=False,
    domain_initial_dot=False,
    path="/",
    path_specified=True,
    secure=False,
    expires=None,
    discard=False,
    comment=None,
    comment_url=None,
    rest=None
   )

class ScrapCarrefour:
  def __init__(self):
    """
    Creates list of drive gps markers and dict of store urls (and a post param)
    """

    self.cookie_jar = cookielib.LWPCookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookie_jar))
    opener.addheaders = [(u'User-agent',
                          u'Mozilla/5.0 (Windows NT 6.0)'+\
                          u'AppleWebKit/537.22 (KHTML, like Gecko)'+\
                          u'Chrome/25.0.1364.172 Safari/537.22')]
    urllib2.install_opener(opener)
    
    # open welcome page and get carrefour drive stores
    self.drive_website_url = u'http://courses.carrefour.fr'
    response = urllib2.urlopen(self.drive_website_url + r'/drive/accueil')
    data = response.read()
    soup = BeautifulSoup(data)
    ls_bloc_stores = soup.findAll('li', {'class' : 'shop'})
    # get store markers
    ls_json_stores = re.search(u'shopLatLng = (.*?);', data).group(1)
    self.ls_store_markers = json.loads(ls_json_stores)
    # get store urls (in dict only if found)
    self.dict_store_urls = {}
    for bloc_store in ls_bloc_stores:
      store_id = unicode(bloc_store.find('h2', {'class' : 'heading'}).span.text)
      bloc_store_submit = bloc_store.find('li', {'class' : 'submit'})
      try:
        store_url = unicode(bloc_store_submit.find('form', {'action' : True})['action'])
        store_tformdata = unicode(bloc_store_submit.find('input', {'name' : 't:formdata'})['value'])
        self.dict_store_urls[store_id] = [store_url, store_tformdata]
      except:
        pass

  def scrap_stores(self, ls_store_id):
    """
    @param list of store_id: carrefour drive identifier e.g. [u"78 - VOISINS LE BRETONNEUX"]
    @type store_id: C{str}
    returns prices for list of carrefour drive identifiers provided
    """
    self.dict_ls_store_prices = {}
    for store_id in ls_store_id:
      if store_id in self.dict_store_urls:
        try:
          store_url, store_tformdata = self.dict_store_urls[store_id]
          self.dict_ls_store_prices[store_id] =\
            self.fetch_store_prices(store_url, store_tformdata)
          print u'\nCollected {:d} products for Carrefour {:s}'.format(\
                   len(self.dict_ls_store_prices[store_id]),
                   store_id)
        except Exception, e:
          print u'\nCould not collect prices for store: {:s}'.format(store_id)
          print e
      else:
        print u'\nNo URL for store {:s} found in welcome page'.format(store_id)
    return self.dict_ls_store_prices

  def fetch_store_prices(self, store_url, store_tformdata):
    """
    @param store_url: carrefour drive url
    @type store_url: C{str}
    @param store_tformdata: param for post request used to get on store page
    @type store_tformdata: C{str}
    returns store prices
    """
    store_headers = {u'Host' : 'courses.carrefour.fr',
                     u'Origin' : 'http://courses.carrefour.fr',
                     u'Referer' : 'http://courses.carrefour.fr/drive/accueil',
                     u'X-Requested-With' : u'XMLHttpRequest',
                     u'X-Prototype-Version' : u'1.6.0.3',
                     u'Content-type' : u'application/x-www-form-urlencoded; charset=UTF-8'}
    store_post = {'t:formdata' : store_tformdata}
    store_req = urllib2.Request(self.drive_website_url + store_url,
                                data = urllib.urlencode(store_post),
                                headers = store_headers)
    store_response = urllib2.urlopen(store_req)
    ## Alternative way to go to store page (add cookies manually)
    #cookie_jar.set_cookie(makeCookie("serviceDrive", "3"))
    #cookie_jar.set_cookie(makeCookie("storeDrive", "215"))
    #cookie_jar.set_cookie(makeCookie("browserSupportCheck", "checked"))
    # pprint.pprint(cookie_jar.__dict__)
    
    # GET DPTS AND SUBDPTS (PAGES TO VISIT)
    store_response_2 = urllib2.urlopen(self.drive_website_url + '/drive/accueil')
    store_data = store_response_2.read()
    store_soup = BeautifulSoup(store_data)
    ## Alternative to get dpt and sub dpt links
    #ls_dsd_href = store_soup.findAll('a', {'class' : 'page',
    #                                       'href' : re.compile('/drive/tous-les-rayons/*')})
    
    bloc_dpts = store_soup.find('div', {'class' : 'lowerLevel'})
    ls_dpt_blocs = bloc_dpts.findAll('li', {'class' : True,
                                            'onmouseout' : True,
                                            'onmouseover' : True})
    dict_dsds = {}
    for dpt_bloc in ls_dpt_blocs:
      dpt_title = unicode(dpt_bloc.find('a', {'class' : 'page'}).text).strip()
      # next line to avoid capturing url of dpt
      dpt_sd_bloc = dpt_bloc.find('div', {'class' : 'nextLevel'})
      ls_sd_blocs = dpt_sd_bloc.findAll('a', {'class' : 'page',
                                             'href' : True})
      ls_sds = [(unicode(sd_bloc.text), unicode(sd_bloc['href'])) for sd_bloc in ls_sd_blocs]
      dict_dsds[dpt_title] = ls_sds
    
    # VISIT AND PARSE SUBDPT PAGES
    ls_products = []
    for dpt, ls_sds in dict_dsds.items():
      for sub_dpt, sub_dpt_href in ls_sds:
        # exclude pages displaying specific selections of products
        if re.match('/drive/tous-les-rayons/', sub_dpt_href):
          try:
            response_3 = urllib2.urlopen(self.drive_website_url + sub_dpt_href)
            data_3 = response_3.read()
            soup_3 = BeautifulSoup(data_3)
            
            ls_sd_dict_products = self.parse_product_page(soup_3)
            # scrap other pages if any
            ac_param = sub_dpt_href.split('/')[-1]
            for cookie in self.cookie_jar:
              if cookie.name == 'JSESSIONID':
                jsessionid = cookie.value
            ls_page_nbs = extract_bs_text(soup_3.find('ul', {'class' : 'pageNumbers'}))
            if ls_page_nbs and len(ls_page_nbs) > 1:
              for page_nb in ls_page_nbs[1:]:
                headers_page = {u'Host' : 'courses.carrefour.fr',
                                u'Origin' : 'http://courses.carrefour.fr',
                                u'Referer' : self.drive_website_url + sub_dpt_href +\
                                             u';jsessionid=' + jsessionid,
                                u'X-Requested-With' : u'XMLHttpRequest',
                                u'X-Prototype-Version' : u'1.6.0.3',
                                u'Content-type' : u'application/x-www-form-urlencoded; charset=UTF-8'}
                data_page = {'t:ac' : ac_param}
                req_page = urllib2.Request(u'http://courses.carrefour.fr/drive'+\
                                           u'/rayon.categoryproductlistcontainer'+\
                                           u'.paging.selectpage/{:s}?t:ac={:s}'.format(page_nb,
                                                                                       ac_param),
                                           data = urllib.urlencode(data_page),
                                           headers = headers_page)
                response_page = urllib2.urlopen(req_page)
                data_page = response_page.read()
                
                json_content = json.loads(data_page)
                data_prods = json_content['zones']['componentZone']
                soup_prods = BeautifulSoup(data_prods)
                ls_sd_dict_products += self.parse_product_page(soup_prods)
            for dict_product in ls_sd_dict_products:
              dict_product['department'] = dpt
              dict_product['sub_department'] = sub_dpt
            ls_products += ls_sd_dict_products
          except Exception, e:
            print [dpt, sub_dpt, sub_dpt_href]
            print e
    return ls_products
  
  def parse_product_page(self, product_soup):
    ls_dict_products = []
    ls_bloc_products = product_soup.findAll('li', {'class' : 'product'})
    for bloc_product in ls_bloc_products:
      ls_product_title = extract_bs_text(bloc_product.find('h3'))
      # bloc img_alt
      bloc_product_main = bloc_product.find('div', {'class' : 'productMain clearfix'})
      bloc_img = bloc_product_main.find('div', {'class' : 'img'})
      img_name = None
      if bloc_img and bloc_img.find('img', {'alt' : True}):
        img_name = bloc_img.find('img', {'alt' : True})['alt']
      # bloc price
      bloc_price = bloc_product.find('div', {'class' : 'specs priceSpecs'})
      ls_price = extract_bs_text(bloc_price) # conservative: captures all
      ls_promo = extract_bs_text(bloc_price.find('div', {'class' : 'priceBlock promoBlock'}))
      ls_promo_heading = extract_bs_text(bloc_price.find('h4', {'class' : 'heading'}))
      ls_reduction = extract_bs_text(bloc_price.find('div', {'class' : 'spec reduction'}))
      ls_format = extract_bs_text(bloc_price.find('span', {'class' : 'unit'}))
      ls_total_price = extract_bs_text(bloc_price.find('div', {'class' : 'spec price'}))
      ls_unit_price = extract_bs_text(bloc_price.find('div', {'class' : 'unitPrice'}))
      dict_product = {'ls_product_title' : ls_product_title,
                      'ls_price' : ls_price,
                      'ls_promo' : ls_promo,
                      'ls_promo_heading' : ls_promo_heading,
                      'ls_reduction': ls_reduction,
                      'ls_format' : ls_format,
                      'ls_total_price' : ls_total_price,
                      'ls_unit_price' : ls_unit_price,
                      'img_name' : img_name}
      ls_dict_products.append(dict_product)
    return ls_dict_products



class ScrapAuchan:
  def __init__(self):
    """
    Creates list of drive gps markers and dict of store urls (and a post param)
    """

    self.cookie_jar = cookielib.LWPCookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookie_jar))
    opener.addheaders = [('User-agent',
                          'Mozilla/5.0 (Windows NT 6.1; WOW64) '+\
                            'AppleWebKit/537.11 (KHTML, like Gecko) '+\
                            'Chrome/23.0.1271.64 Safari/537.11')]
    urllib2.install_opener(opener)
    
    # open welcome page and get auchan drive stores 
    self.website_url = r'http://www.auchandrive.fr'
    response = urllib2.urlopen(self.website_url)
    data = response.read()
    soup = BeautifulSoup(data)
    # get list of stores
    bloc_stores = soup.find('div', {'class' : 'zoneRight right float'})
    #bloc_li_stores = bloc_stores.find('div', {'id' : 'liste_drives'})
    #ls_bloc_stores = bloc_li_stores.findAll('li')
    # Browse dict store markers (json)
    dict_json_stores = json.loads(unicode(bloc_stores.script.text)\
                                    .lstrip(u'var shopList = ')\
                                    .rstrip(u';'))
    ls_dict_stores = dict_json_stores['markers']
    self.dict_store_urls = {x['Ville'] : x for x in ls_dict_stores}

  def scrap_stores(self, ls_store_id):
    """
    @param list of store_id: auchan drive identifier
    @type store_id: C{str}
    returns prices for list of auchan drive identifiers provided
    """
    self.dict_ls_store_prices = {}
    for store_id in ls_store_id:
      if store_id in self.dict_store_urls:
        try:
          store_url = self.dict_store_urls[store_id][u'UrlEntreeMagasin']
          store_referer = self.dict_store_urls[store_id][u'UrlFicheMagasin']
          self.dict_ls_store_prices[store_id] =\
            self.fetch_store_prices(store_url, store_referer)
          print u'Collected {:d} products for Auchan {:s}'.format(\
                   len(self.dict_ls_store_prices[store_id]),
                   store_id)
        except Exception, e:
          print u'Could not collect prices for store: {:s}'.format(store_id)
          print e
      else:
        print u'No URL for store {:s} found in welcome page'.format(store_id)
    return self.dict_ls_store_prices

  def fetch_store_prices(self, store_url, store_referer):
    """
    @param store_url: carrefour drive url
    @type store_url: C{str}
    @param store_refer: param for headers in request used to get on store page
    @type store_referer: C{str}
    returns store prices
    """
    # GET COOKIE TO ENTER STORE
    # Alternative way: cookie_jar.set_cookie(makeCookie('auchanCook','"935|"'))
    headers_store = {u'Host' : 'www.auchandrive.fr',
                     u'Referer' : store_referer}
    req_store = urllib2.Request(self.website_url + store_url,
                                headers = headers_store)
    response_store = urllib2.urlopen(req_store)
    data_store = response_store.read()
    soup_store = BeautifulSoup(data_store)
    
    ls_dpt_blocs = soup_store.findAll('div', {'class' : 'item-content'})
    dict_dpt_sub_dpts = {}
    for dpt_bloc in ls_dpt_blocs:
      dpt_title = extract_bs_text(dpt_bloc.find('p', {'class' : 'titre'}),
                                  ls_text = False)
      if dpt_title:
        ls_sub_dpt_blocs = dpt_bloc.findAll('a', {'class' : 'linkImage',
                                                  'href' : True})
        ls_sub_dpts = []
        for sub_dpt_bloc in ls_sub_dpt_blocs:
          sub_dpt_href = unicode(sub_dpt_bloc['href'])
          sub_dpt_img = sub_dpt_bloc.find('img', {'alt' : True})
          sub_dpt_title = None
          if sub_dpt_img:
            sub_dpt_title = unicode(sub_dpt_img['alt'])
          ls_sub_dpts.append((sub_dpt_title, sub_dpt_href))
        dict_dpt_sub_dpts[dpt_title] = ls_sub_dpts
    
    # SCRAP SUB DPT PAGES
    ## todo: finish (affichePopinProduit + addProductToShoppingList2 blocks)
    #sub_dpt_title  = u'Cr\xe8merie'
    #sub_dpt_href = u'/drive/Velizy-935/Produits-Frais-R3686962/Cremerie-3686963/'
    
    ls_products = []
    for dpt_title, ls_sub_dpts in dict_dpt_sub_dpts.items():
      for (sub_dpt_title, sub_dpt_href) in ls_sub_dpts:
        time.sleep(1)
        
        response_3 = urllib2.urlopen(self.website_url + sub_dpt_href)
        data_3 = response_3.read()
        soup_3 = BeautifulSoup(data_3)
        
        bloc_main = soup_3.find('div', {'id' : 'central-container'}) # include all prods
        bloc_itemsList = soup_3.find('div', {'class' : 'itemsList t-zone'}) # similar
        bloc_titreCategorie = soup_3.find('div', {'class' : 'titreCategorie'}) # only forms
        
        # Display 100 items per page (appears to work)
        bloc_pagination = bloc_titreCategorie.find('div', {'class' : 'limite-pagination'})
        pagi_href = None
        if bloc_pagination:
          ls_pagi_blocs = bloc_pagination.findAll('li')
          if ls_pagi_blocs and ls_pagi_blocs[-1].find('a', {'href' : True}):
            pagi_href = ls_pagi_blocs[-1].a['href']
            # add in POST: t:zoneid = itemsList
        if pagi_href:
          dict_params = {'t%3Azoneid' : 'itemsList'}
          headers = {'Referer' : self.website_url + sub_dpt_href,
                     'X-Requested-With' : 'XMLHttpRequest',
                     'X-Prototype-Version' : '1.6.0.3',
                     'Content-type' : 'application/x-www-form-urlencoded; charset=UTF-8'}
          params = urllib.urlencode(dict_params)  
          req  = urllib2.Request(self.website_url + pagi_href, params, headers)
          response_4 = urllib2.urlopen(req)
          data_4 = response_4.read()
          # soup_4 = BeautifulSoup(data_4)
          json_content = json.loads(data_4)
          soup_products = BeautifulSoup(json_content['zones']['itemsList'])
          ls_products += self.parse_product_page(soup_products, dpt_title, sub_dpt_title)
    
          # loop over pages
          #print json_content['inits'][0]['linkZone'][0]
          ls_pages_toloop = []
          for dict_elt in json_content['inits'][0]['linkZone']:
            url_temp = dict_elt.get('url', '')
            page_url_match  = re.match(u'/drive/rayon.productlist.pagination.topage/([0-9]*?)\?',
                                       url_temp)
            if page_url_match:
              if page_url_match.group(1) != '1':
                ls_pages_toloop.append(dict_elt)
            else:
              break
          for dict_page in ls_pages_toloop:
            page_href = dict_page['url']
            dict_params = {u'zoneId' : u'forceAjax'}
            params = urllib.urlencode(dict_params)  
            req  = urllib2.Request(self.website_url + page_href, params, headers)
            response_4 = urllib2.urlopen(req)
            data_4 = response_4.read()
            try:
              json_content = json.loads(data_4)
              soup_products = BeautifulSoup(json_content['zones']['itemsList'])
              ls_products += self.parse_product_page(soup_products, dpt_title, sub_dpt_title)
            except:
              print u'Empty page in sub_dpt:', sub_dpt_title, 'in store:', store_url

        else:
          print u'Disp 100 items per page did not work:', sub_dpt_title
          good_part = re.search(u'<!-- FIN PAGINATION -->(.*?)<!-- PAGINATION -->', data_3, re.DOTALL)
          html_candidate = good_part.group(1)
          soup_products = BeautifulSoup(html_candidate)
          ls_products += self.parse_product_page(soup_products, dpt_title, sub_dpt_title)
    return ls_products

  def parse_product_page(self, soup_products, dpt_title, sub_dpt_title):
    ls_dict_products = []
    # Parse products
    ls_prod_blocs = soup_products.findAll('div', {'class' : 'vignette-box'})
    # print len(ls_prod_blocs_1)
    for bloc_prod in ls_prod_blocs:
      # product availability, product promo
      prod_available_dum = 'yes'
      if bloc_prod.find('div', {'class' : 'vignette vignette-indispo'}):
        prod_available_dum = 'no'
      prod_promo_dum = 'no'
      if bloc_prod.find('div', {'class' : 'vignette-content promo'}):
        prod_promo_dum = 'yes'
      # product visuel
      bloc_prod_visuel = bloc_prod.find('div', {'class' : 'visuel-produit'})
      prod_img = None
      if bloc_prod_visuel and bloc_prod_visuel.find('img', {'alt' : True}):
        prod_img = unicode(bloc_prod_visuel.find('img', {'alt' : True})['alt'])
      # product info
      bloc_prod_info = bloc_prod.find('div', {'class' : 'infos-produit'})
      bloc_prod_name = bloc_prod_info.find('p', {'class' : re.compile('libelle-produit.*')})
      prod_name = extract_bs_text(bloc_prod_name, ls_text = False)
      # does not accept several promo
      bloc_prod_promo =\
          bloc_prod_info.find('p', {'class' : re.compile('operation-produit.*')})
      prod_promo = [None, None]
      if bloc_prod_promo:
        prod_promo = [unicode(bloc_prod_promo['class']), # not sure why get list
                      extract_bs_text(bloc_prod_promo, ls_text = False)]
      # product price
      bloc_prod_price = bloc_prod.find('div', {'class' : 'infos-prix'})
      bloc_prod_total_price = bloc_prod_price.find('p', {'class' : 'prix-produit'})
      prod_total_price = extract_bs_text(bloc_prod_total_price)
      bloc_prod_unit_price = bloc_prod_price.find('p', {'class' : 'prix-unitaire'})
      prod_unit_price = extract_bs_text(bloc_prod_unit_price)
      # todo: add pictos
      dict_product = {'dpt' : dpt_title,
                      'sub_dpt' : sub_dpt_title,
                      'dum_available' : prod_available_dum,
                      'dum_promo' : prod_promo_dum,
                      'img' : prod_img,
                      'name' : prod_name,
                      'promo' : prod_promo,
                      'total_price' : prod_total_price,
                      'unit_price' : prod_unit_price}
      ls_dict_products.append(dict_product)
    return ls_dict_products
