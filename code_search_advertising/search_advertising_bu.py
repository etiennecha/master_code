#!/usr/bin/python
# -*- coding: utf-8 -*-

import numpy as np
from scipy.optimize import fmin
from scipy.integrate import quad
from sympy import *
import matplotlib.pyplot as plt

# How to define function properly: http://docs.sympy.org/dev/guide.html
# init_printing(use_unicode=True) # to have nice display...

s_theta, s_p, s_p_bar, s_eta, s_gamma = symbols('s_theta s_p s_p_bar s_eta s_gamma', positive = True)

class function_profit(Function):
  nargs = 4
  
  @classmethod
  def eval(cls, s_theta, s_p, s_p_bar, s_eta):
    return Piecewise((0.0, s_p > s_p_bar), ((s_p - 0.1)*(s_theta + s_p**(-s_eta)), True))

class function_cdf_theta(Function):
  nargs = 2
  
  @classmethod
  def eval(cls, s_theta, s_gamma):
    return Piecewise((0.0, s_theta < 0.0), (1.0, s_theta > 1.0), (s_theta**s_gamma, True))

class function_expected_profit(Function):
  nargs = 4
  # Caution: should be derivative of profit
  
  @classmethod
  def eval(cls, s_p, s_p_bar, s_eta, s_gamma):
    return integrate(function_profit(s_theta, s_p, s_p_bar, s_eta)*\
                     diff(function_cdf_theta(s_theta, s_gamma), s_theta), (s_theta, 0.1, 1.0))

# ############################
# Check functions: some graphs
# ############################

# eta_range = np.linspace(2.0, 5.0, int(round(((5.0-2.0)/0.25)))+1)
# for eta in eta_range:
  # x_axis = np.linspace(0.1, 2.0, int(round(((2.0-0.1)/0.01)))+1)
  # ls_demand = [function_profit(0.5, p, 2.0, eta) for p in x_axis]
  # plt.plot(x_axis, ls_demand, label = 'eta = %s' %eta)
# legend = plt.legend(loc='upper right')
# plt.show()

# gamma_range = np.linspace(0.1, 1.0, int(round(((1.0-0.1)/0.25)))+1)
# for gamma in gamma_range:
  # x_axis = np.linspace(0.0, 1.0, int(round(((1.0-0.0)/0.01)))+1)
  # ls_cdf_theta = [function_cdf_theta(theta, gamma) for theta in x_axis]
  # plt.plot(x_axis, ls_cdf_theta, label = 'gamma = %s' %gamma)
# legend = plt.legend(loc='lower right')
# plt.show()

# #########################################
# Check expected profits wrt eta and gamma
# #########################################

# print diff((s_p-0.1)*(s_theta + s_p**(-s_eta)), s_p)
# print diff(s_theta ** s_gamma, s_theta)
# print integrate((-s_eta*s_p**(-s_eta)*(s_p - 0.1)/s_p + s_theta + s_p**(-s_eta))*(s_gamma*s_theta**s_gamma/s_theta), (s_gamma, 0, 1))
# function_profit(s_theta, s_p, s_p_bar, s_eta)
# function_cdf_theta(s_theta, s_gamma)

# function_expected_profit(0.5, 2, 10, 1.0)

# for eta in(2.0, 2.5, 3.0):
  # x_axis = np.linspace(0.1, 2.0, int(round(((2.0-0.1)/0.01)))+1)
  # ls_profits = [function_expected_profit(x, 2.0, eta, 1.0) for x in x_axis]
  # plt.plot(x_axis, ls_profits, label = 'eta = %s' %eta)
# legend = plt.legend(loc='upper right')
# plt.show()

# TODO: see why does not work with gamma not integer
for gamma in [1.0]: #0.5, 0.7
  x_axis = np.linspace(0.1, 2.0, int(round(((2.0-0.1)/0.1)))+1)
  ls_profits = [function_expected_profit(x, 2.0, 2.0, gamma) for x in x_axis]
  plt.plot(x_axis, ls_profits, label = 'gamma = %s' %gamma)
legend = plt.legend(loc='upper right')
plt.show()

# Inspect piecewise result

fo_expected_profit = integrate(diff(function_profit(s_theta, s_p, s_p_bar, s_eta),s_p)*\
                                 diff(function_cdf_theta(s_theta, s_gamma), s_theta), (s_theta, 0, 1))

def integrand_expected_profit(theta, p_bar, p, eta, gamma):
  return fo_expected_profit.subs([(s_theta, theta), (s_p_bar, p_bar), (s_p, p), (s_eta, eta), (s_gamma, gamma)])

def minus_expected_profit(p_bar, p, eta, gamma):
  return -quad(integrand_expected_profit, 0, 1, args = (p_bar, p, eta, gamma))[0]

p_bar, p, eta, gamma = 1.0, 0.2, 2.0, 0.5
I = quad(integrand_expected_profit, 0, 1, args = (p_bar, p, eta, gamma))
print I
print -minus_expected_profit(1.0, 0.2, 2.0, 0.5)

for gamma in [0.5, 0.7, 1.0]:
  print fmin(minus_expected_profit, x0=1 ,args = (eta, gamma))
  x_axis = np.linspace(0.1, 2.0, int(round(((2.0-0.1)/0.01)))+1)
  ls_profits = [quad(integrand_expected_profit, 0, 1, args = (p, eta, gamma))[0] for p in x_axis]
  plt.plot(x_axis, ls_profits, label = 'gamma = %s' %gamma)
legend = plt.legend(loc='upper right')
plt.show()



# ##################################
# Compute optimal price and welfare
# ###################################

# function_expected_profit(x, 10.0, 1/2, 1.0)
# x_0 = [1]
# fmin(lambda x: x*(x+1), x_0)

# function_expected_profit(s_p, 10.0, 1.0, 1.0)

# solvers.solvers.nsolve(function_expected_profit, (s_p, 10.0, 1.0, 1.0), 1), 1)

# # TODO: read https://groups.google.com/forum/#!msg/sympy/Uz06ihU3wys/TTVHLIoQaKMJ
# # TODO: read about Scipy integration: http://www.johndcook.com/blog/2012/03/20/scipy-integration/
# # TODO: read http://stackoverflow.com/questions/19144554/python-integrating-a-piecewise-function

# ############
# DEPRECATED
# ############

# class function_profit(Function):
  # nargs = 4
  
  # @classmethod
  # def eval(cls, s_theta, s_p, s_p_bar, s_eta):
    # return Piecewise((0, s_p > s_p_bar), (s_p*(exp(s_theta - s_eta * s_p)), True))

# class function_cdf_theta(Function):
  # nargs = 2
  
  # @classmethod
  # def eval(cls, s_theta, s_gamma):
    # return Piecewise((0, s_theta < 0), (1, s_theta > 1), (s_theta**s_gamma, True))

# class function_expected_profit(Function):
  # nargs = 4
  
  # @classmethod
  # def eval(cls, s_p, s_p_bar, s_eta, s_gamma):
    # return integrate(function_profit(s_theta, s_p, s_p_bar, s_eta)*\
                     # diff(function_cdf_theta(s_theta, s_gamma), s_theta), (s_theta, 0, 1))