#!/usr/bin/python
# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd

def get_moving_average(k, a) :
    ret = np.cumsum(a, dtype=float)
    ret[k:] = ret[k:] - ret[:-k]
    return ret[k - 1:] / k

def get_series_from_moving_avg_beg(k, ar_sol):
  """
  Finds original series from a k moving average series (not centered) BUT: 
  k-1 first elements of ar_sol are assumed to be data from original series
  there is a mistake on k but it works as such...
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
  WRONG => A PRIORI NOT POSSIBLE FROM END...
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
  # ar_base = np.array(range(1,20), dtype=np.float64)
  ar_base = np.random.rand(1,20)[0]
  print '\nOriginal array:', ar_base
  ar_ma = get_moving_average(k, ar_base)
  
  # Array retrieved
  ar_sol = get_series_from_moving_avg_beg(k,  np.hstack([ar_base[:k-1], ar_ma]))
  print '\nArray retrieved:', ar_sol
  # print get_series_from_moving_avg_end(5, ar_sol)
  
  #n = len(ar_sol) 
  #mat_y = np.zeros(shape=(n,n))
  #for i in range(n-(k-1), n):
  #  mat_y[i,i] = 1
  #for i in range(n-(k-1)):
  #  for j in range(i, i+k):
  #    mat_y[i,j] = 1.0/k
