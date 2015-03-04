#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
from generic_competition import *
import time
from statsmodels.distributions.empirical_distribution import ECDF
from scipy.stats import ks_2samp

pd.set_option('float_format', '{:,.3f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.3f}'.format(x)

# ###################
# LOAD DATA
# ###################

path_dir_built_paper = os.path.join(path_data,
                                    'data_gasoline',
                                    'data_built',
                                    'data_paper_dispersion')

path_dir_built_csv = os.path.join(path_dir_built_paper, u'data_csv')

path_dir_built_json = os.path.join(path_dir_built_paper, 'data_json')

path_dir_source = os.path.join(path_data, 'data_gasoline', 'data_source')

# LOAD DF PRICES
df_prices_ttc = pd.read_csv(os.path.join(path_dir_built_csv,
                                         'df_prices_ttc_final.csv'),
                        parse_dates = ['date'])
df_prices_ttc.set_index('date', inplace = True)

df_prices_cl = pd.read_csv(os.path.join(path_dir_built_csv,
                                        'df_cleaned_prices.csv'),
                          parse_dates = ['date'])
df_prices_cl.set_index('date', inplace = True)

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
                               'dpt' : str})
df_info.set_index('id_station', inplace = True)

# LOAD DF STATION STATS
print '\nLoad df_station_stats'
df_station_stats = pd.read_csv(os.path.join(path_dir_built_csv,
                                            'df_station_stats.csv'),
                               encoding = 'utf-8',
                               dtype = {'id_station' : str})
df_station_stats.set_index('id_station', inplace = True)

# LOAD DF DISPERSION
print '\nLoad df_ppd'
ls_dtype_temp = ['id', 'ci_ardt_1']
dict_dtype = dict([('%s_b' %x, str) for x in ls_dtype_temp] +\
                  [('%s_a' %x, str) for x in ls_dtype_temp])
df_ppd = pd.read_csv(os.path.join(path_dir_built_csv,
                     'df_pair_raw_price_dispersion.csv'),
              encoding = 'utf-8',
              dtype = dict_dtype)

# LOAD DF PAIR STATS
print '\nLoad df_pair_stats'
df_ps = pd.read_csv(os.path.join(path_dir_built_csv,
                                 'df_pair_stats.csv'),
                                 dtype = {'id_a' : str,
                                          'id_b' : str},
                    encoding = 'utf-8')

# MERGE
# drop duplicate columns
df_ps.drop(['distance', 'nb_spread'], axis = 1, inplace = True)
df_pairs = pd.merge(df_ppd,
                    df_ps,
                    how = 'left',
                    on = ['id_a', 'id_b'])

# ##################
# FILTER DATA
# ##################

# DROP PAIRS WITH INSUFFICIENT PRICE DATA (temp?)

print "Dropped pairs (insuff spread obs):",\
        len(df_pairs[(pd.isnull(df_pairs['avg_spread'])) |\
                   (df_pairs['nb_spread'] < 100)])

df_pairs = df_pairs[(~pd.isnull(df_pairs['avg_spread'])) &\
                (df_pairs['nb_spread'] >= 100)]

ls_exclude_ids = df_station_stats.index[(df_station_stats['nb_chge'] < 10) |\
                                        (df_station_stats['pct_chge'] < 0.03)]

print "Dropped pairs (insuff price data):",\
        len(df_pairs[(df_pairs['id_a'].isin(ls_exclude_ids)) |\
                   (df_pairs['id_b'].isin(ls_exclude_ids))])

df_pairs = df_pairs[(~df_pairs['id_a'].isin(ls_exclude_ids)) &\
                (~df_pairs['id_b'].isin(ls_exclude_ids))]

# ###############################################
# PRICE LEVEL IF NON DIFFERENTIATED COMPETITOR
# ###############################################

len(df_pairs[df_pairs['pct_same'] > 0.5])
len(df_pairs[df_pairs['pct_same'] > 0.3])

set_ids_1 = set(df_pairs['id_a'][df_pairs['pct_same'] > 0.3].values)
set_ids_2 = set(df_pairs['id_b'][df_pairs['pct_same'] > 0.3].values)
set_ids = set_ids_1.union(set_ids_2)

df_info['price'] = df_prices_ttc.iloc[0]

import statsmodels.api as sm
import statsmodels.formula.api as smf

df_info['sp_dum'] = 0
df_info.loc[list(set_ids), 'sp_dum'] = 1

print smf.ols(formula = 'price ~ C(brand_last) + sp_dum',
              data = df_info).fit().summary()
