#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
import re
import json

def enc_stock_json(database, chemin):
 with open(chemin, 'w') as fichier:
  json.dump(database, fichier)

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def get_levenshtein(seq_1, seq_2):
  one_ago = None
  this_row = range(1, len(seq_2) + 1) + [0]
  for x in xrange(len(seq_1)):
    two_ago, one_ago, this_row = one_ago, this_row, [0] * len(seq_2) + [x + 1]
    for y in xrange(len(seq_2)):
      del_cost = one_ago[y] + 1
      add_cost = this_row[y - 1] + 1
      sub_cost = one_ago[y - 1] + (seq_1[x] != seq_2[y])
      this_row[y] = min(del_cost, add_cost, sub_cost)
  return this_row[len(seq_2) - 1]
  
def get_levenshtein_tuple(seq_1, seq_2):
  levenshtein_stat = get_levenshtein(seq_1, seq_2)
  min_len = min(len(seq_1), len(seq_2))
  max_len = max(len(seq_1), len(seq_2))
  tuple_result = (levenshtein_stat, min_len, max_len)
  return tuple_result

def str_correct_html(word):
  """
  for k,v in master_info.iteritems():
    if v['address'][3]:
      print k, get_corrected_str(v['address'][3][2])
  """
  accents  = {u'É' : [u'Ã©', u'\xc3\x89', u'\xc3\u2030'], 
              u'È' : [u'Ã¨'],
              u'Ê' : [u'Ãª'],
              u'Ë' : [u'Ã«'],
              u'Ô' : [u'Ã´'],
              u'Û' : [u'Ã»'],
              u'Â' : [u'Ã¢'],
              u'Ç' : [u'\xc3\xa7']} # u'Ã§' does not work       
  # u'Ã‰' and u'Ã' are u'\xc3\x89', u'\xc3\u2030'
  # u'Ãª' is u'\xc3\xaa'
  # u'Ã§' is u'\xc3\xa7'
  for (char, accented_chars) in accents.iteritems():
    for accented_char in accented_chars:
      word = word.replace(accented_char, char)
  word = word.replace('&#039;','\'').replace('#039;','\'')
  word = word.replace('&amp;', '&').replace('&quot;','"')
  word = ' '.join(word.split())
  return word.strip()

def str_low_standardize(word):
  # Reminder: \b does not work with accents (end of word)
  # TODO: "s.a.s", "s.a.r.l" etc? make it robust to upper/lower letters?
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

def str_low_noacc(word):
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
  word = re.sub(ur'\b-\b', ur' ', word)
  word = word.replace("'", " ").replace('"', ' ')
  word = word.replace('[',' ').replace(']',' ').replace('(','').replace(')',' ')
  word = word.replace('.', ' ').replace(',',' ').strip()
  word = ' '.join(word.split())
  return word.strip()

def str_corr_low_std(word):
  return str_low_standardize(str_correct_html(word))

def str_corr_low_std_noacc(word, levenshtein = True):
  original_word = word
  if levenshtein:
    std_word = str_low_noacc(str_low_standardize(str_correct_html(word)))
    levenshtein_stat = get_levenshtein(std_word, \
                                   str_low_standardize(str_correct_html(word)))
    return (std_word, levenshtein_stat)
  else:
    return str_low_noacc(str_low_standardize(str_correct_html(word)))

def str_insee_harmonization(word):
  # Just for comparison's sake: no accent and word-word (maybe insufficient?)
  word = word.lower()
  word = re.sub(ur"(^|\s)st(s?)(\s|$|-)", ur" saint\2 ", word)
  word = re.sub(ur"(^|\s)ste(s?)(\s|$|-)", ur" sainte\2 ", word)
  word = word.replace("'", " ")
  word = word.replace("-", " ")
  word = ' '.join(word.split())
  return word.strip()

if __name__=="__main__":
  if os.path.exists(r'W:\Bureau\Etienne_work\Data'):
    path_data = r'W:\Bureau\Etienne_work\Data'
  else:
    path_data = r'C:\Users\etna\Desktop\Etienne_work\Data'
  
  # TODO: write test of functions with master_info