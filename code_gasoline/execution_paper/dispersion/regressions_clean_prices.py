#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path_sub
from add_to_path_sub import path_data
from generic_master_price import *
from generic_master_info import *
from generic_competition import *
import time
#from statsmodels.distributions.empirical_distribution import ECDF
#from scipy.stats import ks_2samp

path_dir_built_paper = os.path.join(path_data, 'data_gasoline', 'data_built', 'data_paper')

path_dir_built_json = os.path.join(path_dir_built_paper, 'data_json')
path_diesel_price = os.path.join(path_dir_built_json, 'master_price_diesel.json')
path_info = os.path.join(path_dir_built_json, 'master_info_diesel.json')
path_ls_ls_competitors = os.path.join(path_dir_built_json, 'ls_ls_competitors.json')
path_ls_tuple_competitors = os.path.join(path_dir_built_json, 'ls_tuple_competitors.json')

path_dir_source = os.path.join(path_data, 'data_gasoline', 'data_source')
path_dict_brands = os.path.join(path_dir_source, 'data_other', 'dict_brands.json')

path_dir_insee = os.path.join(path_data, 'data_insee')
path_csv_insee_extract = os.path.join(path_dir_insee, 'data_extracts', 'data_insee_extract.csv')

master_price = dec_json(path_diesel_price)
master_info = dec_json(path_info)
ls_ls_competitors = dec_json(path_ls_ls_competitors)
ls_tuple_competitors = dec_json(path_ls_tuple_competitors)
dict_brands = dec_json(path_dict_brands)

zero_threshold = np.float64(1e-10)
pd.set_option('use_inf_as_null', True)
pd.options.display.float_format = '{:6,.4f}'.format

master_np_prices = np.array(master_price['diesel_price'], np.float64)
df_price = pd.DataFrame(master_np_prices.T, index = master_price['dates'], columns = master_price['ids'])
#df_price = pd.DataFrame(master_price['diesel_price'],
#                        columns = master_price['dates'],
#                        index = master_price['ids']).T

se_mean_price = df_price.mean(1)
df_mean_price = pd.DataFrame(se_mean_price, columns = ['avg_price'])
df_mean_price['const'] = 1
se_mean_price_ned = se_mean_price - se_mean_price.mean()

# ############################
# TEST PRICE vs. COST (PROXY)
# ############################

# TODO: improve visual (percent variations etc)
se_margin = df_price['1500003'] - se_mean_price
#plt.plot(se_margin)
#plt.plot(se_mean_price_ned)
#plt.show()
print sm.OLS(se_margin, df_mean_price, missing = 'drop', hasconst = True).fit().summary()
# TODO: add fixed effect (policy etc)

# ############################
# TEST SPREAD vs. COST (PROXY)
# ############################

# TODO: improve visual e.g. with 1500003 and 1500001

# todo: iterate with various diff_bounds (high value: no cleaning of prices)
km_bound = 5
diff_bound = 0.02


ls_res = []
for (indiv_id, comp_id), distance in ls_tuple_competitors[0:1000]:
  if distance <= km_bound: 
    se_prices_1 = df_price[indiv_id]
    se_prices_2 = df_price[comp_id]
    se_spread = pd.Series(se_prices_2 - se_prices_1, name = 'spread')
    res = sm.OLS(se_spread, df_mean_price, missing = 'drop', hasconst = True).fit()
    ls_res.append([indiv_id, comp_id, np.abs(se_spread.mean()),
                   res.params['avg_price'], res.bse['avg_price'], res.tvalues['avg_price'],
                   res.nobs, res.rsquared])
ls_columns = ['id_1', 'id_2', 'avg_spread' ,'b', 'b_std', 't-val', 'nobs', 'r2']
df_res = pd.DataFrame(ls_res, columns = ls_columns)

print len(df_res[np.abs(df_res['t-val']) < 1.96])/float(len(df_res))
