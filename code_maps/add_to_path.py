#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys

path = os.path.abspath(os.path.dirname(sys.argv[0]))
path_global_dir = os.path.dirname(path)

# Set path_data to find demo data or original data

# path_data defaults to data provided on github
path_data = os.path.join(path_global_dir, 'data')
# another location can be provided though
ls_possible_path_data = [r'W:\Bureau\Etienne_work\Data',
                         r'C:\Users\etna\Desktop\Etienne_work\Data']
for my_path in ls_possible_path_data:
  if os.path.exists(my_path):
    path_data = my_path
    break
