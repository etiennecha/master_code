#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
import datetime, time
import statsmodels.api as sm
import statsmodels.formula.api as smf

path_dir_built_paper = os.path.join(path_data,
                                    u'data_gasoline',
                                    u'data_built',
                                    u'data_paper_dispersion')

path_dir_built_csv = os.path.join(path_dir_built_paper, u'data_csv')

pd.set_option('float_format', '{:,.3f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.3f}'.format(x)

# ########################
# LOAD DF PRICES AND COSTS
# ########################

# LOAD DF COST
df_cost = pd.read_csv(os.path.join(path_dir_built_csv,
                                   'df_quotations.csv'),
                                 encoding = 'utf-8',
                                 parse_dates = ['date'])
df_cost.set_index('date', inplace = True)

# LOAD DF PRICES TTC
df_prices_ttc = pd.read_csv(os.path.join(path_dir_built_csv,
                                         'df_prices_ttc_final.csv'),
                        parse_dates = ['date'])
df_prices_ttc.set_index('date', inplace = True)

# LOAD DF PRICES HT
df_prices_ht = pd.read_csv(os.path.join(path_dir_built_csv,
                                         'df_prices_ht_final.csv'),
                        parse_dates = ['date'])
df_prices_ht.set_index('date', inplace = True)

# LOAD DF INFO
df_info = pd.read_csv(os.path.join(path_dir_built_csv,
                                   'df_station_info_final.csv'),
                      encoding = 'utf-8',
                      dtype = {'id_station' : str,
                               'adr_zip' : str,
                               'adr_dpt' : str,
                               'ci_1' : str,
                               'ci_ardt_1' :str,
                               'ci_2' : str,
                               'ci_ardt_2' : str,
                               'dpt' : str},
                      parse_dates = ['day_0', 'day_1', 'day_2'])
df_info.set_index('id_station', inplace = True)
df_info = df_info[df_info['highway'] != 1]

# LOAD DF STATION STATS
df_station_stats = pd.read_csv(os.path.join(path_dir_built_csv,
                                   'df_station_stats.csv'),
                               encoding = 'utf-8',
                               dtype = {'id_station' : str})
df_station_stats.set_index('id_station', inplace = True)

# ################
# ANALYSIS: INDIV
# ################

# not sure if need to keep this... compare UFIP for robustness if needed
df_cost_nowe = df_cost[~((df_cost.index.weekday == 5) |\
                         (df_cost.index.weekday == 6))].copy()
df_cost_nowe['ULSD 10 CIF NWE S1 EL'] = df_cost_nowe['ULSD 10 CIF NWE EL'].shift(1)
df_cost_nowe['ULSD 10 CIF NWE S1 R5 EL'] = pd.stats.moments.rolling_apply(
                                             df_cost_nowe['ULSD 10 CIF NWE S1 EL'], 5,
                                             lambda x: x[~pd.isnull(x)].mean(), 2)
df_cost['ULSD 10 CIF NWE S1 R5 EL'] = df_cost_nowe['ULSD 10 CIF NWE S1 R5 EL']

# build df_indiv for regression (could avoid that step)
df_indiv = df_cost[['ULSD 10 FOB MED EL',
                    'ULSD 10 CIF NWE EL',
                    'ULSD 10 CIF NWE S1 R5 EL']].copy()
df_indiv['dum_taxcut_1'] = 0
df_indiv.loc['2012-08-31':'2012-11-30', 'dum_taxcut_1'] = 1
df_indiv['dum_taxcut_2'] = 0
df_indiv.loc['2012-12-01':'2013-01-11', 'dum_taxcut_2'] = 1
# df_indiv.loc['2012-11-30':'2012-12-05',:]

indiv_ind = df_station_stats[df_station_stats['nb_chge'] > 300].index[0]

str_cost = 'ULSD_CIF_NWE_S1_R5_EL'

ls_rows_res = []
for indiv_ind in df_station_stats.index[0:10]:
  try:
    ## can stop on 30th (31: drop)
    df_indiv['price'] = df_prices_ttc.loc[:'2012-08-30', indiv_ind]
    
    #df_indiv['price'] = df_prices_ttc[indiv_ind]
    ## set price to nan during gvt intervention
    #df_indiv.loc['2012-08-31':'2013-01-11', 'price'] = np.nan
    
    df_indiv.rename(columns = {'ULSD 10 FOB MED EL' : 'ULSD_FOB_MED_EL',
                               'ULSD 10 CIF NWE EL' : 'ULSD_CIF_NWE_EL',
                               'ULSD 10 CIF NWE S1 R5 EL' : 'ULSD_CIF_NWE_S1_R5_EL'},
                    inplace = True)
    
    df_indiv_fi = df_indiv[(~df_indiv['price'].isnull()) &\
                           (~df_indiv['ULSD_FOB_MED_EL'].isnull()) &\
                           (~df_indiv['ULSD_CIF_NWE_EL'].isnull())]
    
    # could use newly set prices and check robustness vs cost series shifting
    
    formula_1 = 'price ~ %s' %str_cost
    formula_2 = 'price ~ %s + dum_taxcut_1 + dum_taxcut_2' %str_cost
    reg0 = smf.ols(formula_1,
                   df_indiv,
                   missing = 'drop').fit()
    #print reg0.summary()
    nobs = reg0.nobs
    r2a = reg0.rsquared_adj
    param = reg0.params.ix[str_cost]
    tval = reg0.tvalues.ix[str_cost]
    ls_conf_int = reg0.conf_int().ix[str_cost].tolist()
    ls_rows_res.append([indiv_ind, nobs, r2a, param, tval] + ls_conf_int)
  except:
    pass

df_res = pd.DataFrame(ls_rows_res, columns = ['id_station',
                                              'nobs',
                                              'r2a',
                                              'param',
                                              'tval',
                                              'lb',
                                              'ub'])
df_res.set_index('id_station', inplace = True)

df_res_sg = df_res[df_res['tval'].abs() > 1.96].copy()
df_res_sg['param'].describe()

# simply add nb_chges for now
df_res_sg['nb_chges'] = df_station_stats['nb_chge']
df_res_sg = df_res_sg[df_res_sg['nb_chges'] > 10]

# relation between price level (improve...) and param
df_res_sg['price'] = df_prices_ttc.iloc[100]
print smf.ols('price ~ param',
              data = df_res_sg).fit().summary()

# TODO: exclude change in margin policy

# Check specific cases
df_indiv['price'] = df_prices_ttc['75005001']
df_indiv.loc['2012-08-31':'2013-01-11', 'price'] = np.nan

from pylab import *
rcParams['figure.figsize'] = 16, 6

fig = plt.figure()
ax1 = fig.add_subplot(111)
line_1 = ax1.plot(df_indiv.index, df_indiv['price'].values,
                  ls='--', c='b', label='Retail price')
line_1[0].set_dashes([4,2])
ax2 = ax1.twinx()
line_3 = ax2.plot(df_indiv.index, df_indiv[str_cost].values,
                  ls='-', c='r', label=r'Rotterdam price (Right axis)')

lns = line_1 + line_3
labs = [l.get_label() for l in lns]
ax1.legend(lns, labs, loc=0)
ax1.axvline(x=pd.to_datetime('2012-08-31'), linewidth=1, color='k')
ax1.axvline(x=pd.to_datetime('2012-12-01'), linewidth=1, color='k')
ax1.axvline(x=pd.to_datetime('2013-01-11'), linewidth=1, color='k')
plt.show()

plt.scatter(df_indiv[str_cost].values,
            df_indiv['price'].values)
plt.show()
