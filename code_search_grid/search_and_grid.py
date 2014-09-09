import math
import numpy as np
import pandas as pd

def compute_profit(s, l_1, l_2, c_1, c_2, p_1, p_2):
  if p_1 > p_2:
    profit_1 = (p_1 - c_1)*(l_1)
    profit_2 = (p_2 - c_2)*(l_2 + s)
  elif p_1 == p_2:
    profit_1 = (p_1 - c_1)*(l_1 + s/2.0)
    profit_2 = (p_2 - c_2)*(l_2 + s/2.0)
  else:
    profit_1 = (p_1 - c_1)*(l_1 + s)
    profit_2 = (p_2 - c_2)*(l_2)
  return [profit_1, profit_2]

# PARAMETERS
l_1, l_2 = 1, 1          # uninformed customers
s = 1                    # informed customers
c, c_1, c_2 = 1, 1, 1    # firms' unit cost
v = 1.5                  # customer reserve price
grid_unit = 0.100        # grid unit

# PRICE GRID
steps = (v-c+grid_unit)/grid_unit
if np.abs(math.ceil(steps) - steps) < np.abs(math.floor(steps) - steps):
  ar_grid_prices = np.linspace(c, v, math.ceil(steps))
else:
  ar_grid_prices = np.linspace(c, v, math.floor(steps))
# print ar_grid_prices

# PRINT DF SUMMARY OF GAME
ls_same_price = [[x, x] for x in ar_grid_prices]
ls_undercut = [[x-grid_unit, x] for x in ar_grid_prices]

ls_same_price_profits = [compute_profit(s, l_1, l_2, c_1, c_2, p_1, p_2)\
                           for p_1, p_2 in ls_same_price]
ls_undercut_profits = [compute_profit(s, l_1, l_2, c_1, c_2, p_1, p_2)\
                         for p_1, p_2 in ls_undercut]
ls_rows = [x + y + z + t for (x, y, z, t)\
            in zip(ls_same_price, ls_same_price_profits, ls_undercut, ls_undercut_profits)]
ls_col = ['p_eq', 'p2', 'profit_eq', 'profit_2_sym',
          'p_1_cut', 'p_2', 'profit_1_cut', 'profit_2_cut']
df_profits = pd.DataFrame(ls_rows, columns = ls_col)
print u'\nSummary of game'
print df_profits[['p_eq', 'p_1_cut', 'profit_eq', 'profit_1_cut', 'profit_2_cut']].to_string()

## PRICE GRID WITH A LOWER BOUND

# COMPUTE ONE FIRM PAYOFFS
ls_ls_profits = []
for price in ar_grid_prices:
  ls_profits = []
  for price_comp in ar_grid_prices:
    ls_profits.append(compute_profit(s, l_1, l_2, c_1, c_2, price, price_comp)[0])
  ls_ls_profits.append(ls_profits)

np.set_printoptions(precision=4) # round float when printing
np.set_printoptions(suppress=True) # avoid scientific notation when printing

# PRINT NORMAL FORM OF THE GAME
ls_ls_tup_profits = []
for price_comp in ar_grid_prices:
  ls_tup_profits = []
  for price in ar_grid_prices:
    ls_tup_profits.append(compute_profit(s, l_1, l_2, c_1, c_2, price, price_comp))
  ls_ls_tup_profits.append(ls_tup_profits)

# First line (strats of column player) to be added by hand so far
print u'\nNormal form of the game (Caution with nb of digits allowed)'
ls_ls_temp = [[ls_x[i] for ls_x in ls_ls_tup_profits] for i in range(len(ls_ls_tup_profits))]
for price, ls_temp in zip(ar_grid_prices, ls_ls_temp):
  print u"{:>.2f} &".format(price),\
        u" & ".join([' '.join(map(lambda y: u"{:>.3f}".format(y), x)) for x in ls_temp]),\
        u"\\\\"

# PRINT TWO FIRM PAYOFFS
ar_ar_profits = np.array(ls_ls_tup_profits)
print u'\nPayoffs'
print ar_ar_profits
ar_profits = np.reshape(ar_ar_profits, -1)
# print len(ar_profits)
print ' '.join(["{:>.4f}".format(profit) for profit in ar_profits])

# NUMBER OF STRAT FOR EACH FIRM
print u'\nNb of possible strats (Size of grid):', len(ar_grid_prices)

# SOLVE FOR MSE (TODO: iterate check MSEs with 0 weight)

# Need to restrict manually to right support so far
p_lower = 1.3
steps = (v-p_lower+grid_unit)/grid_unit
if np.abs(math.ceil(steps) - steps) < np.abs(math.floor(steps) - steps):
  ar_prices = np.linspace(p_lower, v, math.ceil(steps))
else:
  ar_prices = np.linspace(p_lower, v, math.floor(steps))
ls_ls_profits = []
for price in ar_prices:
  ls_profits = []
  for price_comp in ar_prices:
    ls_profits.append(compute_profit(s, l_1, l_2, c_1, c_2, price, price_comp)[0])
  ls_ls_profits.append(ls_profits)
# Solve well defined pbm (check?)
ls_ar_a = []
for ls_profits in ls_ls_profits[1:]:
  ar_a = np.array(ls_profits) - np.array(ls_ls_profits[0])
  ls_ar_a.append(ar_a)
ls_ar_a.append(np.ones(len(ar_prices)))
ar_ar_a = np.array(ls_ar_a)
ar_b = np.array([0 for price in ar_prices[:-1]] + [1])
res = np.linalg.solve(ar_ar_a, ar_b)
print u'\nSolution of game (assumes right support provided)'
df_eq_strat = pd.DataFrame(zip(ar_prices, res), columns = ['price', 'proba'])
print df_eq_strat
# print ar_ar_a
# print np.around(ar_b,2)

# COMPUTE EACH STRAT EXPECTED PAYOFF VS. EQUILIBRIUM MIXED STRATEGY
print u'\nPayoffs vs. Equilibrium Mixed Strategy'
for price in ar_grid_prices:
  expected_profit = (price - c_1)*(df_eq_strat['proba']\
                                     [df_eq_strat['price']>price].sum() * s +\
                                   df_eq_strat['proba']\
                                     [df_eq_strat['price'] == price].sum() * s/2.0 +\
                                   # sum used to get 0 if empty...
                                    l_1)
  print price, expected_profit
