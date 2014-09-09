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
grid_unit = 0.025        # grid unit

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

## First line (strats of column player) to be added by hand so far
#print u'\nNormal form of the game (Caution with nb of digits allowed)'
#ls_ls_temp = [[ls_x[i] for ls_x in ls_ls_tup_profits] for i in range(len(ls_ls_tup_profits))]
#for price, ls_temp in zip(ar_grid_prices, ls_ls_temp):
#  print u"{:>.2f} &".format(price),\
#        u" & ".join([' '.join(map(lambda y: u"{:>.3f}".format(y), x)) for x in ls_temp]),\
#        u"\\\\"

## PRINT TWO FIRM PAYOFFS
#ar_ar_profits = np.array(ls_ls_tup_profits)
#print u'\nPayoffs'
#print ar_ar_profits
#ar_profits = np.reshape(ar_ar_profits, -1)
## print len(ar_profits)
#print ' '.join(["{:>.2f}".format(profit) for profit in ar_profits])

## NUMBER OF STRAT FOR EACH FIRM
#print u'\nNb of possible strats (Size of grid):', len(ar_grid_prices)


dict_mse = {'100' : [{4:8/17.0,
                      5:7/17.0,
                      6:2/17.0}],
            '050' : [{7:1214/3261.0,
                      8:490/3261.0,
                      9:509/2174.0,
                      10:145/2174.0,
                      11:192/1087.0}],
            '025' : [{12:19998/62881.0,
                      14:15553/62881.0,
                      16:11695/62881.0,
                      18:8670/62881.0,
                      20:995/8983.0},
                     {12:23175/79723.0,
                      13:5563/239169.0,
                      14:18482/79723.0,
                      16:48788/239169.0,
                      18:9792/79723.0,
                      20:1451/11389.0},
                     {12:762975/2644187.0,
                      13:202667/7932561.0,
                      14:1214501/5288374.0,
                      15:1115/2266446.0,
                      16:543124/2644187.0,
                      18:321648/2644187.0,
                      20:48619/377741.0}]}

res = [dict_mse['025'][2].get(i, 0) for i in range(1, len(ar_grid_prices) + 1)]
df_eq_strat = pd.DataFrame(zip(ar_grid_prices, res), columns = ['price', 'proba'])
print df_eq_strat

# print ar_ar_a
# print np.around(ar_b,2)
# COMPUTE EACH STRAT EXPECTED PAYOFF VS. EQUILIBRIUM MIXED STRATEGY
print u'\nPayoffs vs. Equilibrium Mixed Strategy'
df_eq_strat['profit'] = np.nan
for price in ar_grid_prices:
  expected_profit = (price - c_1)*(df_eq_strat['proba']\
                                     [df_eq_strat['price']>price].sum() * s +\
                                   df_eq_strat['proba']\
                                     [df_eq_strat['price'] == price].sum() * s/2.0 +\
                                   # sum used to get 0 if empty...
                                    l_1)
  df_eq_strat['profit'][df_eq_strat['price'] == price] = expected_profit
  print u"{:>.3f}".format(price), expected_profit
