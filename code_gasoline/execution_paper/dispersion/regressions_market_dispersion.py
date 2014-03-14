#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path_sub
from add_to_path_sub import path_data
from generic_master_price import *
from generic_master_info import *
from generic_competition import *
import time
from statsmodels.distributions.empirical_distribution import ECDF
from scipy.stats import ks_2samp

path_dir_built_paper = os.path.join(path_data, 'data_gasoline', 'data_built', 'data_paper')

path_dir_built_json = os.path.join(path_dir_built_paper, 'data_json')
path_diesel_price = os.path.join(path_dir_built_json, 'master_price_diesel.json')
path_info = os.path.join(path_dir_built_json, 'master_info_diesel.json')
path_ls_ls_competitors = os.path.join(path_dir_built_json, 'ls_ls_competitors.json')
path_ls_tuple_competitors = os.path.join(path_dir_built_json, 'ls_tuple_competitors.json')

path_dir_source = os.path.join(path_data, 'data_gasoline', 'data_source')
path_dict_brands = os.path.join(path_dir_source, 'data_other', 'dict_brands.json')

master_price = dec_json(path_diesel_price)
master_info = dec_json(path_info)
ls_ls_competitors = dec_json(path_ls_ls_competitors)
ls_tuple_competitors = dec_json(path_ls_tuple_competitors)
dict_brands = dec_json(path_dict_brands)

zero_threshold = np.float64(1e-10)

master_np_prices = np.array(master_price['diesel_price'], np.float64)
df_price = pd.DataFrame(master_np_prices.T, index = master_price['dates'], columns = master_price['ids'])
#df_price = pd.DataFrame(master_price['diesel_price'],
#                        columns = master_price['dates'],
#                        index = master_price['ids']).T





# ###########
# DEPRECATED
# ###########

# # REGRESSIONS WITHOUT PANDAS & SM FORMULAS

# # REGRESSION OF MARKET PRICE DISPERSION ON NB COMPETITORS AND PRICE

# nb_competitors = np.vstack([matrix_master_pd[:,0]]).T
# nb_competitors_and_price = np.vstack([matrix_master_pd[:,0], matrix_master_pd[:,1]]).T
# range_prices = matrix_master_pd[:,2]
# std_prices = matrix_master_pd[:,3]
# coeff_var_prices = matrix_master_pd[:,4]
# gain_search = matrix_master_pd[:,5]
# print '\n REGRESSIONS OF MARKET PRICE DISPERSION ON NB COMPETITORS AND PRICE \n'

# res_mstd_1 = sm.OLS(std_prices, sm.add_constant(nb_competitors), missing = "drop").fit()
# print res_mstd_1.summary(yname='std_prices', xname = ['constant', 'nb_competitors'])

# res_mstd_2 = sm.OLS(std_prices, sm.add_constant(nb_competitors_and_price), missing = "drop").fit()
# print res_mstd_2.summary(yname='std_prices', xname = ['constant', 'nb_competitors', 'price'])

# res_cvar_1 = sm.OLS(coeff_var_prices, sm.add_constant(nb_competitors), missing = "drop").fit()
# print res_cvar_1.summary(yname='coeff_var_prices', xname = ['constant', 'nb_competitors'])

# res_cvar_2 = sm.OLS(coeff_var_prices, sm.add_constant(nb_competitors_and_price), missing = "drop").fit()
# print res_cvar_2.summary(yname='coeff_var_prices', xname = ['constant', 'nb_competitors', 'price'])

# res_rp_1 = sm.OLS(range_prices, sm.add_constant(nb_competitors), missing = "drop").fit()
# print res_rp_1.summary(yname='range_prices', xname = ['constant', 'nb_competitors'])

# res_rp_2 = sm.OLS(range_prices, sm.add_constant(nb_competitors_and_price), missing = "drop").fit()
# print res_rp_2.summary(yname='range_prices', xname = ['constant', 'nb_competitors', 'price'])

# res_gs_1 = sm.OLS(gain_search, sm.add_constant(nb_competitors), missing = "drop").fit()
# print res_gs_1.summary(yname='gain_search', xname = ['constant', 'nb_competitors'])

# res_gs_2 = sm.OLS(gain_search, sm.add_constant(nb_competitors_and_price), missing = "drop").fit()
# print res_gs_2.summary(yname='gain_search', xname = ['constant', 'nb_competitors', 'price'])
