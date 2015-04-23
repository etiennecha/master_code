#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
import re
import json

def str_low_noacc(word, basic_std = True):
  # Just for comparison's sake: no accent and word-word (maybe insufficient?)
  word = word.lower()
  accents  = {u'a': [u'â', u'à', u'ã', u'á'],
              u'c': [u'ç'],
              u'i': [u'î', u'ï'],
              u'o': [u'ô', u'ö'],
              u'u': [u'û', u'ù', u'ü'], 
              u'e': [u'é', u'è', u'ê', u'ë'],
              u'y': [u'ÿ']}
  for (char, accented_chars) in accents.iteritems():
    for accented_char in accented_chars:
      word = word.replace(accented_char, char)
  if basic_std:
    word = re.sub(ur'\b-\b', ur' ', word)
    word = word.replace(u"'", u" ").replace(u'"', u' ')
    word = u' '.join(word.split())
  return word.strip()

def standardize_intermarche(word):
  word = re.sub(u'^s\.?a\.?s?\.?\s', u' ', word)
  word = re.sub(u'\sdistribution$', u' ', word)
  word = u' '.join(word.split())
  return word.strip()

def str_low_standardize(word):
  # reminder: \b does not work with accents (end of word)
  # todo: "s.a.s", "s.a.r.l" etc? make it robust to upper/lower letters?
  word = word.lower()
  word = re.sub(ur'(^|\s|,)r\.?\s?d\.?\s?([0-9]{0,5})(\s|$|,)', ur'\1 route departementale \2 \3', word)
  word = re.sub(ur'(^|\s|,)r\.?\s?n\.?\s?([0-9]{0,5})(\s|$|,)', ur'\1 route nationale \2 \3', word) 
  #n may be number hence r not optional...
  word = re.sub(ur"(^|\s|,)c\.?\s?d\.?\s?([0-9]{0,5})(\s|$|,)", ur'\1 chemin departemental \2 \3', word)
  word = re.sub(ur'(^|\s|,)rte(\s|$\.)', ur'\1 route ', word)
  word = re.sub(ur'(^|\s|,)b(l|v)?d(\s|$|\.)', ur'\1 boulevard ', word)
  word = re.sub(ur'(^|\s|,)av(\s|$|\.)', ur'\1 avenue ', word)
  word = re.sub(ur'(^|\s|,)c(\s|\\|/|\.)?c\.?(\s|$)', ur'\1 centre commercial ', word)
  word = re.sub(ur'(^|\s|,)z(\s|\\|/|\.)?i\.?(\s|$)', ur'\1 zone industrielle ', word)
  word = re.sub(ur'(^|\s|,)z(\s|\\|/|\.)?a\.?c?\.?(\s|$)', ur"\1 zone d'activite ", word) 
  word = re.sub(ur"(^|\s|,)st(e?)-", ur"\1 saint\2-", word)
  word = re.sub(ur"(^|\s|,)st(e?)(\s|$)", ur"\1 saint\2 ", word) 
  word = ' '.join(word.split())
  return word.strip()

def str_insee_harmonization(word):
  # Just for comparison's sake: no accent and word-word (maybe insufficient?)
  word = word.lower()
  word = re.sub(ur"(^|\s)st(s?)(\s|$|-)", ur" saint\2 ", word)
  word = re.sub(ur"(^|\s)ste(s?)(\s|$|-)", ur" sainte\2 ", word)
  word = word.replace("'", " ")
  word = word.replace("-", " ")
  word = ' '.join(word.split())
  return word.strip()
