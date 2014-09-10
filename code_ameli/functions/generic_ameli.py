#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import os, sys

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

#def ls_to_clean(ls_to_clean):
#  ls_to_clean = map(lambda x:\
#                      x.replace(u'&gt;', u'').replace(u'&nbsp;',u'').strip(),
#                    ls_to_clean)
#  return [x for x in ls_to_clean if x]
