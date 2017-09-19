#!/usr/bin/env python
# -*- coding: utf-8 -*- 

from __future__ import print_function
import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.iolib.summary2 import summary_col

path_built = os.path.join(path_data, 'data_supermarkets', 'data_built')
path_built_csv = os.path.join(path_built, 'data_qlmc_2014_2015', 'data_csv')
path_built_csv_stats = os.path.join(path_built, 'data_qlmc_2014_2015', 'data_csv_stats')
path_built_lsa_csv = os.path.join(path_built, 'data_lsa', 'data_csv')
path_built_lsa_comp_csv = os.path.join(path_built_lsa_csv, '201407_competition')

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# ###########
# LOAD DATA
# ###########

df_compa = pd.read_csv(os.path.join(path_built_csv_stats,
                                    'df_pair_dispersion_static.csv'),
                       encoding = 'utf-8',
                       dtype = {'id_lsa_A' : str,
                                'id_lsa_B' : str})

df_lsa = pd.read_csv(os.path.join(path_built_lsa_csv, 'df_lsa_active_hsx.csv'),
                     dtype = {u'id_lsa' : str,
                              u'c_insee' : str,
                              u'c_insee_ardt' : str,
                              u'c_postal' : str,
                              u'c_siren' : str,
                              u'c_nic' : str,
                              u'c_siret' : str},
                     parse_dates = [u'date_ouv', u'date_fer', u'date_reouv',
                                    u'date_chg_enseigne', u'date_chg_surface'],
                     encoding = 'utf-8')

ls_ev = ['hhi', 'demand_cont_10', 'CO_med_rev']
str_ev = " + ".join(ls_ev)

# ###############
# REGRESSIONS
# ###############

## Keep only pairs which are not too differentiated (done in loop)
#df_compa = df_compa[(df_compa['compa_pct'].abs() <= 3)]

dict_res = {}
for d_dist, dist_var, dist_max in [['d_dist_5', 'dist', 10],
                                   ['d_gg_dur_12', 'gg_dur', 20]]:
  # filter: not too differentiated, not too far
  df_compa = (df_compa[(df_compa['compa_pct'].abs() <= 3) &
                            (df_compa[dist_var] <= dist_max)])
  
  print()
  print(u'-'*30)
  print(u'Variable for close distance:', d_dist)
  
  # NO CONTROL
  ols_res = smf.ols('pct_rr ~ {:s}'.format(d_dist), data = df_compa).fit()
  #print()
  #print(ols_res.summary())
  
  ls_res = []
  ls_quantiles = [0.25, 0.5, 0.75] # use 0.7501 if issue
  for quantile in ls_quantiles:
    #print()
    #print(quantile)
    #print(smf.quantreg('pct_rr~d_dist_5', data = df_repro_compa).fit(quantile).summary())
    ls_res.append(smf.quantreg('pct_rr ~ {:s}'.format(d_dist),
                               data = df_compa[~df_compa[d_dist].isnull()]).fit(quantile))
  
  print(summary_col([ols_res] + ls_res,
                    stars = True,
                    float_format = '%0.2f',
                    model_names = (['OLS'] + [u'Q{:2.0f}'.format(quantile*100)
                                                for quantile in ls_quantiles]),
                    info_dict = {'N':lambda x: "{0:d}".format(int(x.nobs)),
                                 'R2':lambda x: "{:.2f}".format(x.rsquared)}))
  
  # WITH CONTROLS
  ols_res_ctrl = smf.ols('pct_rr ~ {:s} + {:s}'.format(d_dist, str_ev),
                           data = df_compa).fit()
  #print()
  #print(ols_res_ctrl.summary())
  
  ls_res_ctrl = ([smf.quantreg('pct_rr ~ {:s} + {:s}'.format(d_dist, str_ev),
                               data = df_compa[~df_compa[d_dist].isnull()]).fit(quantile)
                   for quantile in ls_quantiles])
  
  print(summary_col([ols_res_ctrl] + ls_res_ctrl,
                    stars = True,
                    float_format = '%0.2f',
                    model_names = (['OLS'] + [u'Q{:2.0f}'.format(quantile*100) 
                                                for quantile in ls_quantiles]),
                    info_dict = {'N':lambda x: "{0:d}".format(int(x.nobs)),
                                 'R2':lambda x: "{:.2f}".format(x.rsquared)}))

  dict_res[d_dist] = [ols_res, ls_res, ols_res_ctrl, ls_res_ctrl]

# see if relation between rank reversals and distance
# control by tup chain (concat)
# create distance dummy?
# create closest competitor dummy? (how? take chain into account?)
