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
import gc

def extract_bs_text(soup_bloc, ls_text = True):
  if soup_bloc and ls_text:
    return soup_bloc.findAll(text = True)
  elif not soup_bloc and ls_text:
    return []
  elif soup_bloc and not ls_text:
    return soup_bloc.text
  elif not soup_bloc and not ls_text:
    return None

class ScrapCarrefour:
  def __init__(self):
    """
    Returns list of carrefour drives
    """

    self.cookie_jar = cookielib.LWPCookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookie_jar))
    opener.addheaders = [(u'User-agent',
                          u'Mozilla/5.0 (Windows NT 6.0)'+\
                          u'AppleWebKit/537.22 (KHTML, like Gecko)'+\
                          u'Chrome/25.0.1364.172 Safari/537.22')]
    urllib2.install_opener(opener)
    
    # get list of stores
    self.drive_website_url = u'http://courses.carrefour.fr'
    response = urllib2.urlopen(self.drive_website_url + r'/drive/accueil')
    data = response.read()
    soup = BeautifulSoup(data)
    self.ls_bloc_stores = soup.findAll('li', {'class' : 'shop'})
    
    # Browse ls store markers (json)
    ls_json_stores = re.search(u'shopLatLng = (.*?);', data).group(1)
    self.ls_ls_stores = json.loads(ls_json_stores)
  
  def scrap_stores(self, ls_store_id):
    """
    @param store_id: carrefour drive identifier e.g. u"78 - VOISINS LE BRETONNEUX"
    @type store_id: C{str}
    returns prices for list of carrefour drive identifiers provided
    """
    self.dict_ls_store_prices = {}
    for store_id in ls_store_id:
      for bloc_store in self.ls_bloc_stores:
        if bloc_store.find('h2', {'class' : 'heading'}).span.text == store_id:
          try:
            bloc_store_submit = bloc_store.find('li', {'class' : 'submit'})
            store_url = bloc_store_submit.find('form', {'action' : True})['action']
            store_tformdata = bloc_store_submit.find('input', {'name' : 't:formdata'})['value']
            self.dict_ls_store_prices[store_id] =\
              self.fetch_store_prices(store_url, store_tformdata)
            print u'\nCollected {:d} products for Carrefour {:s}'.format(\
                     len(self.dict_ls_store_prices[store_id]),
                     store_id)
          except Exception, e:
            print u'\nCould not collect prices for store: {:s}'.format(store_id)
            print e
          gc.collect()
          break
    return self.dict_ls_store_prices

  def fetch_store_prices(self, store_url, store_tformdata):
    """
    @param store_url: carrefour drive url
    @type store_url: C{str}
    @param store_tformdata: param for post request used to get on store page
    @type store_url: C{str}
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
      dpt_title = dpt_bloc.find('a', {'class' : 'page'}).text.strip()
      # next line to avoid capturing url of dpt
      dpt_sd_bloc = dpt_bloc.find('div', {'class' : 'nextLevel'})
      ls_sd_blocs = dpt_sd_bloc.findAll('a', {'class' : 'page',
                                             'href' : True})
      ls_sds = [(sd_bloc.text, sd_bloc['href']) for sd_bloc in ls_sd_blocs]
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
          gc.collect()
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
