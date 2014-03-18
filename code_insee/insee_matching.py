#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
import os, sys

def str_insee_harmonization(word):
  # Just for comparison's sake: no accent and word-word (maybe insufficient?)
  word = word.lower()
  word = re.sub(ur"(^|\s)st(s?)(\s|$|-)", ur" saint\2 ", word)
  word = re.sub(ur"(^|\s)ste(s?)(\s|$|-)", ur" sainte\2 ", word)
  word = word.replace("'", " ")
  word = word.replace("-", " ")
  word = ' '.join(word.split())
  return word.strip()

# TODO: CREATE MATCHING FUNCTION WITH REASONABLE LEVENSHTEIN COMPARISON
# TODO: Search within cpostal (or dpt) closest levenshtein city
# TODO: Set a limit regarding the tolerated score...
# TODO: Build a class: should be able to import from everywhere so as to match with INSEE data...

if __name__=="__main__":
 path_dir_insee = os.path.join(path_data, 'data_insee')

 file_correspondence = open(path_data + r'\data_insee\corr_cinsee_cpostal','r')
 correspondence = file_correspondence.read().split('\n')[1:-1]
 file_correspondence_update = open(path_data + r'\data_insee\corr_cinsee_cpostal_update','r')
 correspondence_update = file_correspondence_update.read().split('\n')[1:]
 correspondence += correspondence_update
 correspondence = [row.split(';') for row in correspondence]

 dict_cpostal = {}
 for (city, cpostal, dpt, cinsee) in correspondence:
   dict_cpostal.setdefault(cpostal, []).append((city, cpostal, dpt, cinsee))

 dict_dpt = {}
 for (city, cpostal, dpt, cinsee) in correspondence:
   dict_dpt.setdefault(cpostal[:-3], []).append((city, cpostal, dpt, cinsee))

 # Large cities: arrondissements
 # Paris code or Arrondissements codes... need flexibility
 Large_cities = {'13055' : ['%s' %elt for elt in range(13201, 13217)], # Marseille
                 '69123' : ['%s' %elt for elt in range(69381, 69390)], # Lyon
                 '75056' : ['%s' %elt for elt in range(75101, 75121)]} # Paris

 # Evolution in communes... manual updating so far

 file_communes_maj = open(path_data + r'\data_insee\Communes_chgt\majcom2013.txt','r')
 communes_maj = file_communes_maj.read().split('\n')
 communes_maj_titles = communes_maj[0].split('\t')
 communes_maj = [row.split('\t') for row in communes_maj[1:-1]]

 file_communes_historiq = open(path_data + r'\data_insee\Communes_chgt\historiq2013.txt','r')
 communes_historiq = file_communes_historiq.read().split('\n')
 communes_historiq_titles = communes_historiq[0].split('\t')
 communes_historiq = [row.split('\t') for row in communes_historiq[1:-1]]

 list_communes_update_todo = []
 for i, elt in enumerate(communes_historiq):
   if elt[0] and elt[3] and elt[13]:
     list_communes_update_todo.append(('%s%s' %(elt[0], elt[3]), elt[13], elt[20]))
 # Not so clear... unecessay for now: manual update in correspondence

 # TODO: confront with current INSEE files

