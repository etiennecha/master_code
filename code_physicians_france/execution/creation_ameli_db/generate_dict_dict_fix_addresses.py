#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_ameli import *
from geocoding import *
import numpy as np
import pandas as pd
import pprint

path_dir_built_json = os.path.join(path_data, u'data_ameli', 'data_built', 'json')

ls_file_extensions = [u'ophtalmologiste_75',
                      u'generaliste_75']

#ls_ophtalmogiste_75_tofix =\
#  ['B7c1ljMzODW3', # [u'1 RUE DU COL MOLL', u'75017 PARIS']
#  'B7c1ljE1Mjaw', # [u'6 PLACE DE LA REPUBLIQUE DOMI', u'75017 PARIS']
#  'B7c1lzIyNjqz', # [u'6 PLACE DE LA REPUBLIQUE DOMI', u'75017 PARIS']]
#  'B7c1lDQwNTe2', # [u'23 RUE GEORGES SAND', u'75016 PARIS']
#  'B7c1ljI3OTKz', # [u'110 RUE DU FAUBOURG POISSONNI', u'75010 PARIS']
#  'B7c1lTIzOTKx', # [u'27 RUE DE L AML MOUCHEZ', u'75013 PARIS']
#  'B7c1kDozMju2', # [u'10 RUE DU COL.ROZANOFF', u'75012 PARIS']
#  'B7c1mzE5ODK2'] # [u'23 RUE GEORGES SAND', u'75016 PARIS']
#ls_ophtalmologiste_75_ok =\
#  ['B7c1mjMzNzOy', # [u'23 RUE GEORGES BIZET', u'75016 PARIS']
#   'B7c1mzY1Mjqz'] # [u'2 PLACE GAMBETTA', u'75020 PARIS']

dict_fix_opthalmologiste_75 =\
  {'B7c1ljMzODW3' : [u'1 RUE DU COLONEL MOLL', u'75017 PARIS'], # APPRO
   'B7c1ljE1Mjaw' : [u'6 PLACE DE LA REPUBLIQUE DOMINICAINE', u'75017 PARIS'],
   'B7c1lzIyNjqz' : [u'6 PLACE DE LA REPUBLIQUE DOMINICAINE', u'75017 PARIS'],
   'B7c1lDQwNTe2' : [u'23 RUE GEORGE SAND', u'75016 PARIS'],
   'B7c1ljI3OTKz' : [u'110 RUE DU FAUBOURG POISSONNIERE', u'75010 PARIS'],
   'B7c1lTIzOTKx' : [u"27 RUE DE L'AMIRAL MOUCHEZ", u'75013 PARIS'],
   'B7c1kDozMju2' : [u'10 RUE DU COLONEL ROZANOFF', u'75012 PARIS'],
   'B7c1mzE5ODK2' : [u'23 RUE GEORGE SAND', u'75016 PARIS'],
   'B7c1lTI0NjS0' : [u'46 RUE NICOLO', u'75016 PARIS'], #GEOM
   'B7c1ljEzNTO7' : [u'44 RUE MICHEL ANGE', u'75016 PARIS']}

dict_fix_generaliste_75 =\
  {'B7c1kjI0NjK2' : [u'15 RUE JEAN-BAPTISTE BERLIER', u'75013 PARIS'], # APPRO
   'B7c1kTs3NzO2' : [u"33 RUE DE L'AMIRAL MOUCHEZ", u'75013 PARIS'],
   'B7c1kTI5NDK2' : [u'2 SQUARE DE LA TOUR-MAUBOURG', u'75007 PARIS'],
   'B7c1kTYyNjuy' : [u'75 RUE SAINT-MAUR', u'75011 PARIS'],
   'B7c1lzI1MjW3' : [u"13 RUE DE L'AMIRAL ROUSSIN", u'75015 PARIS'],
   'B7c1kTU4Mje0' : [u'20 RUE DU COLONEL MOLL', u'75017 PARIS'],
   'B7c1mzE3NjW3' : [u'15 RUE JEAN-BAPTISTE BERLIER', u'75013 PARIS'],
   'B7c1kTcyMzKz' : [u'14 AVENUE DU COLONEL BONNET', u'75016 PARIS'],
   'B7c1ljQyNDqy' : [u'25 RUE PHILIPPE DE GIRARD', u'75010 PARIS'],
   'B7c1kTYyNTKy' : [u'7 RUE DU COLONEL OUDOT', u'75012 PARIS'],
   'B7c1kTQwNjuw' : [u'36 BOULEVARD DE LA TOUR-MAUBOURG', u'75007 PARIS'],
   'B7c1kTU3OTe3' : [u"94 RUE DE L'AMIRAL MOUCHEZ", u'75014 PARIS'],
   'B7c1kTs4NzS1' : [u'61 RUE DE LA GRANGE AUX BELLES', u'75010 PARIS'],
   'B7c1ljQ2NDe1' : [u'7B RUE DU COLONEL OUDOT', u'75012 PARIS'],
   'B7c1kTU4OTuz' : [u'38 ALLEE DES FRERES VOISIN', u'75015 PARIS'],
   'B7c1lzI3NTux' : [u'2 CITE DE TREVISE', u'75009 PARIS'], #GEOM
   'B7c1mzE4ODez' : [u"33 RUE DE L'AMIRAL MOUCHEZ", u'75013 PARIS'],
   'B7c1mzc2Nze2' : [u'28 RUE DE PONTHIEU', u'75008 PARIS'],
   #'B7c1mzYwODO0' : [u'1 RUE COLETTE MAGNY', u'75019 PARIS'], # NO FIX??
   #'B7c1mzswMzu7' : [u'1 RUE COLETTE MAGNY', u'75019 PARIS'], # NO FIX?
   'B7c1ljMwNTe2' : [u'39 RUE FRANCOIS 1ER', u'75008 PARIS'],
   #'B7c1mzYyOTG1' : [u'1 RUE COLETTE MAGNY', u'75019 PARIS'] # NO FIX?
   'B7c1lzQ5Mzq1' : [u'7 RUE TROUSSEAU', u'75011 PARIS'], # ZERO_RES NO FIX?
   'B7c1kTc5MjO7' : [u"1 AVENUE SAINT-HONORE D'EYLAU", u'75016 PARIS']}

dict_dict_fix_addresses = {'ophtalmologiste_75': dict_fix_opthalmologiste_75,
                           'generaliste_75' : dict_fix_generaliste_75}

enc_json(dict_dict_fix_addresses, os.path.join(path_dir_built_json, 'dict_dict_fix_addresses.json'))
