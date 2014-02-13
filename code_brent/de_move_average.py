#!/usr/bin/python
# -*- coding: utf-8 -*-

import numpy as np

k = 5
n = 8

mat_x = np.zeros(shape=(n,n))
for i in range(k-1):
  mat_x[i,i] = 1
for i in range(k-1, n):
  for j in range(i-(k-1), i+1):
    mat_x[i,j] = 1.0/k

ar_sol = np.array(range(1,9), dtype=np.float64)
print np.linalg.solve(mat_x, ar_sol)

mat_y = np.zeros(shape=(n,n))
for i in range(n-(k-1), n):
  mat_y[i,i] = 1
for i in range(n-(k-1)):
  for j in range(i, i+k):
    mat_y[i,j] = 1.0/k

print np.linalg.solve(mat_y, ar_sol)
