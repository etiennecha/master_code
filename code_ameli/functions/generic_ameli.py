#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import os, sys
import re

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

def get_service_price(indiv_id, bloc_service_price):
  normal_price, occu_np, min_price, max_price = None, None, None, None
  ls_consultation_prices = [normal_price, occu_np, min_price, max_price]
  if len(bloc_service_price) == 1:
    ls_prices = re.findall(u'[0-9]{2,4}(?:,[0-9]{0,2})?\s?\u20ac',
                                  bloc_service_price[0])
    if len(ls_prices) == 1:
      # only one price
      normal_price = float(ls_prices[0].rstrip(u'\u20ac').replace(u',', u'.'))
      occu_np, min_price, max_price = 1.0, normal_price, normal_price
    elif len(ls_prices) == 2:
      # two prices but no usual price
      min_price = float(ls_prices[0].rstrip(u'\u20ac').replace(u',', u'.'))
      max_price = float(ls_prices[1].rstrip(u'\u20ac').replace(u',', u'.'))
      normal_price, occu_np = None, None
    else:
      # weird case: no min and max (more info or less?)
      print 'Pbm (1): not expected min and max:', indiv_id, bloc_service_price
    ls_consultation_prices = [normal_price, occu_np, min_price, max_price]
  elif len(bloc_service_price) == 2:
    # normal price
    ls_normal_prices = re.findall(u'[0-9]{2,4}(?:,[0-9]{0,2})?\s?\u20ac',
                                  bloc_service_price[1]) 
    if len(ls_normal_prices) == 1:
      normal_price = float(ls_normal_prices[0].rstrip(u'\u20ac').replace(u',', u'.'))
      re_occu_np = re.search(u'\(([0-9]) cas sur ([0-9]{1,2})\)',
                             bloc_service_price[1])
      if re_occu_np:
        occu_np = float(re_occu_np.group(1)) / float(re_occu_np.group(2))
      else:
        print 'Pbm (2): no expected proba of normal price', indiv_id, bloc_service_price
    else:
      # weird case: no normal price + proba
      print 'Pbm (2): no expected normal price:', indiv_id, bloc_service_price
    # min and max prices
    ls_minmax_prices = re.findall(u'[0-9]{2,4}(?:,[0-9]{0,2})?\s?\u20ac',
                                  bloc_service_price[0]) 
    if len(ls_minmax_prices) == 2:
      min_price = float(ls_minmax_prices[0].rstrip(u'\u20ac').replace(u',', u'.'))
      max_price = float(ls_minmax_prices[1].rstrip(u'\u20ac').replace(u',', u'.'))
    else:
      print 'Pbm (2): not expected min and max:', indiv_id, bloc_service_price
    ls_consultation_prices = [normal_price, occu_np, min_price, max_price]
  else:
    print 'Pbm too many lines:', indiv_id, bloc_service_price
  return ls_consultation_prices

#def ls_to_clean(ls_to_clean):
#  ls_to_clean = map(lambda x:\
#                      x.replace(u'&gt;', u'').replace(u'&nbsp;',u'').strip(),
#                    ls_to_clean)
#  return [x for x in ls_to_clean if x]
