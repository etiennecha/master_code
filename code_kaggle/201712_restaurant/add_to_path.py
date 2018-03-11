#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys

path_current_dir = os.path.abspath(os.path.dirname(sys.argv[0]))

# add_to_path should exist as long as not at global_dir level
path_global_dir = path_current_dir
while os.path.exists(os.path.join(path_global_dir, 'add_to_path.py')):
  path_global_dir = os.path.dirname(path_global_dir)

# 1/ Set functions directory on path

path_dir = os.path.join(path_global_dir, 'functions')
sys.path.append(path_dir)
ls_subdir_names = [f for f in os.listdir(path_dir)\
                     if not os.path.isfile(os.path.join(path_dir, f))]
for subdir_name in ls_subdir_names:
  sys.path.append(os.path.join(path_dir, subdir_name))

# 2/ Set path_data to find demo data or original data

# path_data defaults to data provided on github
path_data = os.path.join(path_global_dir, 'data')
# another location can be provided though
ls_possible_path_data = [r'W:\Bureau\Etienne_work\Data',
                         r'C:\Users\etna\Desktop\Etienne_work\Data',
                         r'C:\Users\CHAMAYOE\Desktop\Perso\recherche\Data']
for my_path in ls_possible_path_data:
  if os.path.exists(my_path):
    path_data = my_path
    break
