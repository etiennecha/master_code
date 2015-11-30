#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
import statsmodels.api as sm
import statsmodels.formula.api as smf
from pandas.stats.plm import PanelOLS

path_dir_built_paper = os.path.join(path_data,
                                    u'data_gasoline',
                                    u'data_built',
                                    u'data_paper_total_access')

path_dir_built_csv = os.path.join(path_dir_built_paper,
                                  u'data_csv')

path_dir_built_graphs = os.path.join(path_dir_built_paper,
                                     'data_graphs')

path_dir_insee = os.path.join(path_data, 'data_insee')
path_dir_insee_match = os.path.join(path_dir_insee, 'match_insee_codes')
path_dir_insee_extracts = os.path.join(path_dir_insee, 'data_extracts')

path_dir_lsa = os.path.join(path_data,
                            'data_supermarkets',
                            'data_lsa',
                            'data_built',
                            'data_csv')

pd.set_option('float_format', '{:,.3f}'.format)
#format_float_int = lambda x: '{:10,.0f}'.format(x)
#format_float_float = lambda x: '{:10,.2f}'.format(x)

df_info = pd.read_csv(os.path.join(path_dir_built_csv,
                                   'df_station_info_final_w_lsa_ids.csv'),
                      encoding = 'utf-8',
                      dtype = {'id_station' : str,
                               'adr_zip' : str,
                               'adr_dpt' : str,
                               'ci_1' : str,
                               'ci_ardt_1' :str,
                               'ci_2' : str,
                               'ci_ardt_2' : str,
                               'dpt' : str,
                               'id_lsa' : str},
                      parse_dates = ['start', 'end', 'day_0', 'day_1', 'day_2'])
df_info.set_index('id_station', inplace = True)

df_info = df_info[(df_info['highway'] != 1) &\
                  (~df_info['dpt'].isin(['2A', '2B']))]

df_prices_ht = pd.read_csv(os.path.join(path_dir_built_csv,
                                        'df_prices_ht_final.csv'),
                        parse_dates = ['date'])
df_prices_ht.set_index('date', inplace = True)

df_prices_ttc = pd.read_csv(os.path.join(path_dir_built_csv,
                                         'df_prices_ttc_final.csv'),
                        parse_dates = ['date'])
df_prices_ttc.set_index('date', inplace = True)

df_station_stats = pd.read_csv(os.path.join(path_dir_built_csv,
                                   'df_station_stats.csv'),
                               encoding = 'utf-8',
                               dtype = {'id_station' : str})
df_station_stats.set_index('id_station', inplace = True)

# LOAD COMPETITION

df_comp = pd.read_csv(os.path.join(path_dir_built_csv,
                                  'df_comp.csv'),
                      dtype = {'id_station' : str,
                               'id_ta_0' : str,
                               'id_ta_1' : str,
                               'id_ta_2' : str},
                      encoding = 'utf-8')
df_comp.set_index('id_station', inplace = True)

df_info = pd.merge(df_info,
                   df_comp,
                   how = 'left',
                   left_index = True,
                   right_index = True)
df_info.reset_index(inplace = True, drop = False)

# LOAD LSA

df_lsa = pd.read_csv(os.path.join(path_dir_lsa,
                                  'df_lsa.csv'),
                     dtype = {'Ident': str,
                              'Code INSEE' : str,
                              'Code INSEE ardt' : str,
                              'Siret' : str},
                     parse_dates = [u'DATE ouv',
                                    u'DATE ferm',
                                    u'DATE réouv',
                                    u'DATE chg enseigne',
                                    u'DATE chgt surf'],
                     encoding = 'UTF-8')

df_info = pd.merge(df_info,
                   df_lsa,
                   how = 'left',
                   left_on = 'id_lsa',
                   right_on = 'Ident')

df_info.set_index('id_station', inplace = True)

# ADD ONE PRICE IN df_info

df_prices = df_prices_ttc
df_info_lsa = df_info[~pd.isnull(df_info['id_lsa'])].copy()
df_info_lsa['price'] = df_prices.ix['2012-09-04']

# ##########
# STATS DES
# ##########


# Nb pumps (to do: add stats on SUP not covered)
print df_info_lsa.pivot_table(index = 'brand_0', # Enseigne
                              values = 'Pompes',
                              aggfunc = [np.mean, np.median, np.std])

# Scatter: LECLERC: price vs. nb pompes by Etb affiliation
# SHOULD DO BOX PLOT
se_affi_vc = df_info_lsa[df_info_lsa['brand_0'] == 'INTERMARCHE']['Etb affiliation'].value_counts()
ls_colors = ['r', 'b', 'g', 'k']

fig = plt.figure()
ax = fig.add_subplot(111)
for color, name, nb in zip(ls_colors[0:4],
                           se_affi_vc[0:4].index,
                           se_affi_vc[0:4]):
  df_info_lsa[df_info_lsa['Etb affiliation'] == name]\
    .plot(kind = 'scatter',
          x = 'Pompes',
          y = 'price',
          c = color,
          label = name,
          ax = ax,
          s = 50)
plt.show()

# ##################################
# REGRESSIONS: REGIONS WITHIN CHAIN
# ##################################

reg = smf.ols('price ~ C(Etb_affiliation) + Pompes',
              data = df_info_lsa[(df_info_lsa['brand_0'] == 'INTERMARCHE') &\
                                 (df_info_lsa['Enseigne'].str.contains('INTERMARCHE'))],
              missing = 'drop').fit()
print reg.summary()

# ####################
# REGRESSIONS: CHAINS
# ####################

reg = smf.ols('price ~ C(brand_0) + Pompes + nb_comp',
              data = df_info_lsa,
              missing = 'drop').fit()
print reg.summary()

### ##########################################
### LONG PANEL: COMP OF TOTAL => TOTAL ACCESS
### ##########################################
#
#
#dum_dist_max_control = True # False for old setting: only require far enough
#dist_comp, dist_max_control = 5, 10 # dist_comp 10 for old setting else 5, (10)
#
## Keep only non Total stations
#df_comp = df_info[(df_info['group'] != 'TOTAL') &\
#                  (df_info['group_last'] != 'TOTAL')].copy()
#
## Keep only if prices not too rigid
#ls_ids_comp = list(df_comp.index)
#ls_ids_good = list(df_station_stats[(df_station_stats['nb_chge'] >= 5) &\
#                                    (df_station_stats['pct_chge'] >= 0.03)].index)
#ls_ids_keep = list(set(ls_ids_comp).intersection(set(ls_ids_good)))
#df_comp = df_comp.ix[ls_ids_keep]
#
## TOTAL-TA COMPETITORS
#
## Keep only competitors of TA with chge
#ls_ta_chge_ids = list(df_info_ta.index[(df_info_ta['pp_chge'] >= 0.04) &\
#                                       (~pd.isnull(df_info_ta['date_beg']))])
#
## Keep only if Total => Total Access among competitors
#df_tta_comp =\
#  df_comp[df_comp.apply(\
#    lambda x: any(((y in ls_ta_chge_ids) and (z <= dist_comp))\
#                    for (y, z) in zip(x[['id_ta_{:d}'.format(i) for i in range(10)]].values,
#                                      x[['dist_ta_{:d}'.format(i) for i in range(10)]].values)),
#    axis = 1)]
#
#      
### Two way fe regression (todo: exploit sparsity)
##df_dpt = df_dpt[~df_dpt['price'].isnull()]
##reg = smf.ols('price ~ C(id_station) + C(time) + ' + ' + '.join(ls_tr_vars),
##              data = df_dpt,
##              missing = 'drop').fit()
##ls_tup_coeffs = zip(reg.params.index.values.tolist(),
##                    reg.params.values.tolist(),
##                    reg.bse.values.tolist(),
##                    # reg.HC0_se,
##                    reg.tvalues.values.tolist(),
##                    reg.pvalues.values.tolist())
##df_tc = pd.DataFrame(ls_tup_coeffs, columns = ['name', 'coeff', 'se', 'tval', 'pval'])
##print df_tc[df_tc['name'].str.startswith('tr_')].to_string()
#
### Two way fe regression
##df_dpt.set_index(['time', 'id_station'], inplace = True, verify_integrity = True)
##reg_pooled  = PanelOLS(y=df_dpt['price'],
##                       x=df_dpt[ls_tr_vars],
##                       time_effects=True,
##                       entity_effects=True)
###print reg_pooled
##ls_tup_coeffs = zip(reg_pooled.beta.index.values.tolist(),
##                    reg_pooled.beta.tolist(),
##                    reg_pooled.std_err.tolist(),
##                    reg_pooled.t_stat.tolist(),
##                    reg_pooled.p_value.tolist())
##df_res_temp = pd.DataFrame(ls_tup_coeffs, columns = ['name', 'coeff', 'se', 'tval', 'pval'])
#
## ls_pctiles = [0.1, 0.25, 0.5, 0.75, 0.9]
