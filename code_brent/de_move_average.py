#!/usr/bin/python
# -*- coding: utf-8 -*-

import numpy as np

def get_series_from_moving_avg_beg(k, ar_sol):
  """
  Finds original series from a k moving average series (not centered) BUT: 
  k first elements of ar_sol are assumed to be data from original series
  """
  n = len(ar_sol) 
  mat_x = np.zeros(shape=(n,n))
  for i in range(k-1):
    mat_x[i,i] = 1
  for i in range(k-1, n):
    for j in range(i-(k-1), i+1):
      mat_x[i,j] = 1.0/k
  return np.linalg.solve(mat_x, ar_sol)

def get_series_from_moving_avg_end(k, ar_sol):
  """
  WRONG => A PRIORI NOT POSSIBLE FROM END
  Find original series from a k moving average series (not centered) BUT: 
  k last elements of ar_sol are assumed to be data from original series
  """
  n = len(ar_sol) 
  mat_y = np.zeros(shape=(n,n))
  for i in range(n-(k-1), n):
    mat_y[i,i] = 1
  for i in range(n-(k-1)):
    for j in range(i, i+k):
      mat_y[i,j] = 1.0/k
  return np.linalg.solve(mat_y, ar_sol)

if __name__ == '__main__': 
  k = 5
  ar_sol = np.array(range(1,9), dtype=np.float64)
  print get_series_from_moving_avg_beg(5, ar_sol)
  print get_series_from_moving_avg_end(5, ar_sol)
  
  n = len(ar_sol) 
  mat_y = np.zeros(shape=(n,n))
  for i in range(n-(k-1), n):
    mat_y[i,i] = 1
  for i in range(n-(k-1)):
    for j in range(i, i+k):
      mat_y[i,j] = 1.0/k
