#!/usr/bin/python
# -*- coding: utf-8 -*-

import numpy as np
from scipy import optimize
from scipy.integrate import quad
from sympy import *
import matplotlib.pyplot as plt

# How to define function properly: http://docs.sympy.org/dev/guide.html
# init_printing(use_unicode=True) # to have nice display...

s_theta, s_p, s_p_bar, s_eta, s_gamma, s_q, s_q_star =\
  symbols('s_theta s_p s_p_bar s_eta s_gamma s_q s_q_star', positive = True)

class function_demand(Function):
  nargs = 4
  
  @classmethod
  def eval(cls, s_theta, s_p, s_p_bar, s_eta):
    return Piecewise((0.0, s_p > s_p_bar), (s_theta + s_p**(-s_eta), True))

class function_inverse_demand(Function):
  nargs = 3
  
  @classmethod
  def eval(cls, s_theta, s_q, s_eta):
    return Piecewise((0.0, s_q < s_theta), ((s_q - s_theta)**(-1/s_eta), True))

# x_axis = np.linspace(0.1, 3.0, int(round(((1.5-0.1)/0.01)))+1)
# p, p_bar, eta, gamma, theta = 0.2, 1.0, 2.0, 0.5, 1
# ls_demands = [function_demand(theta, x, p_bar, eta) for x in x_axis]
# ls_prices = [function_inverse_demand(theta, x, eta) for x in x_axis]
# print function_demand(theta, 0.2, p_bar, eta)
# print function_inverse_demand(theta, 26, eta).evalf() # force evaluation
  
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

class function_exp_profit(Function):
  # problem when gamma is not 1... why, should not be different from function_expected_profit
  nargs = 4
  
  @classmethod
  def eval(cls, s_p, s_p_bar, s_eta, s_gamma):
    return integrate(function_profit(s_theta, s_p, s_p_bar, s_eta)*\
                     diff(function_cdf_theta(s_theta, s_gamma), s_theta), (s_theta, 0, 1))

# p, p_bar, eta, gamma = 0.2, 1.0, 2.0, 0.5
# print function_exp_profit(p, p_bar, eta, gamma)

first_order_condition = integrate(diff(function_profit(s_theta, s_p, s_p_bar, s_eta), s_p)*\
                                    diff(function_cdf_theta(s_theta, s_gamma), s_theta), (s_theta, 0, 1))

expected_profit = integrate(function_profit(s_theta, s_p, s_p_bar, s_eta)*\
                             diff(function_cdf_theta(s_theta, s_gamma), s_theta), (s_theta, 0, 1))

expected_theta = integrate(s_theta*diff(function_cdf_theta(s_theta, s_gamma), s_theta),(s_theta, 0, 1))

consumer_surplus = integrate(function_inverse_demand(s_theta, s_q, s_eta), (s_q, 0, s_q_star))

def function_first_order_condition(p, p_bar, eta, gamma):
  return first_order_condition.subs([(s_p, p), (s_p_bar, p_bar), (s_eta, eta), (s_gamma, gamma)])
  
def function_expected_profit(p, p_bar, eta, gamma):
  return expected_profit.subs([(s_p, p), (s_p_bar, p_bar), (s_eta, eta), (s_gamma, gamma)])
  
def function_expected_theta(gamma):
  return expected_theta.subs([(s_gamma, gamma)])
  
def function_consumer_surplus(theta, q_star, eta):
  return consumer_surplus.subs([(s_theta, theta), (s_q_star, q_star), (s_eta, eta)])

# GRAPHS: PROFIT (NOT EXPECTED) AND CDF

# eta_range = np.linspace(2.0, 5.0, int(round(((5.0-2.0)/0.25)))+1)
# for eta in eta_range:
  # x_axis = np.linspace(0.1, 2.0, int(round(((2.0-0.1)/0.01)))+1)
  # ls_demand = [function_profit(0.5, p, 2.0, eta) for p in x_axis]
  # plt.plot(x_axis, ls_demand, label = 'eta = %s' %eta)
# legend = plt.legend(loc='upper right')
# plt.show()

# gamma_range = np.linspace(0.1, 2.1, int(round(((2.1-0.1)/0.5)))+1)
# for gamma in gamma_range:
  # x_axis = np.linspace(0.0, 1.0, int(round(((1.0-0.0)/0.01)))+1)
  # ls_cdf_theta = [function_cdf_theta(theta, gamma) for theta in x_axis]
  # plt.plot(x_axis, ls_cdf_theta, label = 'gamma = %s' %gamma)
# legend = plt.legend(loc='lower right')
# plt.show()

# EXPRESSIONS

# print diff((s_p-0.1)*(s_theta + s_p**(-s_eta)), s_p)
# print diff(s_theta ** s_gamma, s_theta)
# function_profit(s_theta, s_p, s_p_bar, s_eta)
# function_cdf_theta(s_theta, s_gamma)
# function_exp_profit(0.5, 2, 10, 1.0)

# OPTIMIZATION

# p, p_bar, eta, gamma = 0.2, 1.0, 2.0, 0.5
# I = function_expected_profit(p, p_bar, eta, gamma)

# for gamma in [0.5, 0.7, 1.0, 1.2, 1.5]:
  # # Solve optimization problem
  # print 'Optimal price for gamma:', gamma
  # p_star = optimize.newton(function_first_order_condition, 0.1, args=(p_bar, eta, gamma))
  # print 'Optimal price', p_star, 'yields profit:', function_expected_profit(p_star, p_bar, eta, gamma)
  # # Draw profit as a function of p
  # x_axis = np.linspace(0.1, 1.5, int(round(((1.5-0.1)/0.01)))+1)
  # ls_profits = [function_expected_profit(x, p_bar, eta, gamma) for x in x_axis]
  # plt.plot(x_axis, ls_profits, label = 'gamma = %s' %gamma)
# legend = plt.legend(loc='upper right')
# plt.show()
# # Sensitivity of p_star = BR(gamma) is very low... how to increase it?

# gamma, theta = 1, 1
# for eta in [2.0, 2.5, 3.0]:
  # # Solve optimization problem
  # p_star = optimize.newton(function_first_order_condition, 0.1, args=(p_bar, eta, gamma))
  # e_profit = function_expected_profit(p_star, p_bar, eta, gamma)
  # e_theta = function_expected_theta(gamma)
  # e_q_star = function_demand(e_theta, p_star, p_bar, eta)
  # e_consumer_surplus = function_consumer_surplus(e_theta, e_q_star, eta)
  # print '\nFor eta:', eta
  # print 'Optimal Price', p_star, 'and Quantity:', e_q_star
  # print 'Profit one firm:', e_profit, 'and Consumer surplus', e_consumer_surplus
  # # Draw profit as a function of p
  # x_axis = np.linspace(0.1, 1.5, int(round(((1.5-0.1)/0.01)))+1)
  # ls_profits = [function_expected_profit(x, p_bar, eta, gamma) for x in x_axis]
  # plt.plot(x_axis, ls_profits, label = 'eta = %s' %eta)
# legend = plt.legend(loc='upper right')
# plt.show()



# ############
# DEPRECATED
# ############

# OPTIMIZATION: EXAMPLE/READING

# x_0 = [1]
# optimize.fmin(lambda x: x*(x+1), x_0)

# function_expected_profit(s_p, 10.0, 1.0, 1.0)

# solvers.solvers.nsolve(function_expected_profit, (s_p, 10.0, 1.0, 1.0), 1), 1)

# # TODO: read https://groups.google.com/forum/#!msg/sympy/Uz06ihU3wys/TTVHLIoQaKMJ
# # TODO: read about Scipy integration: http://www.johndcook.com/blog/2012/03/20/scipy-integration/
# # TODO: read http://stackoverflow.com/questions/19144554/python-integrating-a-piecewise-function

# OLD: OPTIMIZATION

# for gamma in [0.5, 0.7, 1.0]:
  # print fmin(minus_expected_profit, x0=1 ,args = (eta, gamma))
  # x_axis = np.linspace(0.1, 2.0, int(round(((2.0-0.1)/0.01)))+1)
  # ls_profits = [quad(fo_expected_profit, 0, 1, args = (p, eta, gamma))[0] for p in x_axis]
  # plt.plot(x_axis, ls_profits, label = 'gamma = %s' %gamma)
# legend = plt.legend(loc='upper right')
# plt.show()
  
# def minus_expected_profit(p, eta, gamma):
  # return -quad(integrand_expected_profit, 0, 1, args = (p_bar, p, eta, gamma))[0]

# p_bar, p, eta, gamma = 1.0, 0.2, 2.0, 0.5
# I = quad(integrand_expected_profit, 0, 1, args = (p_bar, p, eta, gamma))
# print I
# print -minus_expected_profit(1.0, 0.2, 2.0, 0.5)

# OLD: FUNCTIONS

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