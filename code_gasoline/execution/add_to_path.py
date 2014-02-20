#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys

path = os.path.abspath(os.path.dirname(sys.argv[0]))
path_global_dir = os.path.dirname(path)
for dir_name in ['functions', 'data']:
  path_dir = os.path.join(path_global_dir, dir_name)
  if os.path.exists(path_dir):
    sys.path.append(path_dir)
    ls_subdir_names = [f for f in os.listdir(path_dir) if not os.path.isfile(os.path.join(path_dir, f))]
    for subdir_name in ls_subdir_names:
      sys.path.append(os.path.join(path_dir, subdir_name))
  else:
    print 'Dir:', dir_name, 'Not found: Not added to path'

#print 'System separator', os.path.sep
#print sys.path

# If path data is empy: sample provided on github only (else add your path to the following list)
path_data = ''
ls_my_paths = [r'W:\Bureau\Etienne_work\Data',
               r'C:\Users\etna\Desktop\Etienne_work\Data']
for my_path in ls_my_paths:
  if os.path.exists(my_path):
    path_data = my_path
    break
