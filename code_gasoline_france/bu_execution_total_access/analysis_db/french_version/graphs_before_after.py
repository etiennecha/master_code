#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *

path_dir_built_paper = os.path.join(path_data,
                                    u'data_gasoline',
                                    u'data_built',
                                    u'data_paper_total_access')

path_dir_built_csv = os.path.join(path_dir_built_paper,
                                  u'data_csv')

path_dir_built_json = os.path.join(path_dir_built_paper,
                                  u'data_json')

path_dir_built_graphs = os.path.join(path_dir_built_paper,
                                     'data_graphs')

path_dir_insee = os.path.join(path_data, 'data_insee')
path_dir_insee_match = os.path.join(path_dir_insee, 'match_insee_codes')
path_dir_insee_extracts = os.path.join(path_dir_insee, 'data_extracts')

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# ##############
# LOAD DF PRICES
# ##############

df_prices_ttc = pd.read_csv(os.path.join(path_dir_built_csv,
                                         'df_prices_ttc_final.csv'),
                        parse_dates = ['date'])
df_prices_ttc.set_index('date', inplace = True)

df_station_stats = pd.read_csv(os.path.join(path_dir_built_csv,
                                   'df_station_stats.csv'),
                               encoding = 'utf-8',
                               dtype = {'id_station' : str})
df_station_stats.set_index('id_station', inplace = True)

# ################
# LOAD DF INFO TA
# ################

df_info_ta = pd.read_csv(os.path.join(path_dir_built_csv,
                                      'df_info_ta_fixed.csv'),
                         encoding = 'utf-8',
                         dtype = {'id_station' : str,
                                  'adr_zip' : str,
                                  'adr_dpt' : str,
                                  'ci_1' : str,
                                  'ci_ardt_1' :str,
                                  'ci_2' : str,
                                  'ci_ardt_2' : str,
                                  'dpt' : str},
                         parse_dates = [u'day_%s' %i for i in range(4)] +\
                                       ['pp_chge_date', 'ta_chge_date'])
df_info_ta.set_index('id_station', inplace = True)

# ##############
# LOAD DF INFO
# ##############

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
                      parse_dates = ['start', 'end', 'day_0', 'day_1', 'day_2'])
df_info.set_index('id_station', inplace = True)

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

# ###############
# LOAD DICT COMP
# ###############

dict_ls_comp = dec_json(os.path.join(path_dir_built_json,
                                     'dict_ls_comp.json'))

# #########################
# DEFINE GROUPS OF STATIONS
# #########################

# Control: all not Total Access
ls_ids_nota = [x for x in df_prices_ttc.columns if x not in df_info_ta.index]

# Total (from beginning)
df_total = df_info[(df_info['brand_0'] == 'TOTAL')]
ls_total = list(df_total.index)

# Total Access
df_total_ta = df_info[(df_info['brand_0'] == 'TOTAL') &\
                      (df_info['brand_last'] == 'TOTAL_ACCESS')]
ls_total_ta = list(df_total_ta.index)

df_ta_mc = df_info_ta[(df_info_ta['brand_0'] == 'TOTAL') &\
                      (df_info_ta['brand_last'] == 'TOTAL_ACCESS') &\
                      (df_info_ta['pp_chge'] >= 0.02)]

# Elf

df_elf = df_info[df_info['brand_0'] == 'ELF']
ls_elf = list(df_elf.index)

df_elf_mc = df_info_ta[(df_info_ta['brand_0'] == 'ELF') &\
                       (df_info_ta['brand_last'] == 'TOTAL_ACCESS') &\
                       (df_info_ta['pp_chge'] >= 0.02)]

df_elf_nomc = df_info_ta[(df_info_ta['brand_0'] == 'ELF') &\
                         (df_info_ta['brand_last'] == 'TOTAL_ACCESS') &\
                         (df_info_ta['pp_chge'] < 0.02)]

# ###################################
# GRAPHS: PRICE HISTOGRAMS FOR TOTAL
# ###################################

# First day
bins = np.linspace(1.20, 1.60, 41)
plt.hist(df_prices_ttc[ls_total].iloc[0].values,
         bins, alpha=0.5, label=u'"Total" (pas de conversion à venir)', color = 'g')
plt.hist(df_prices_ttc[ls_total_ta].iloc[0].values,
         bins, alpha=0.5, label=u'"Total" prochainement "Total Access"', color = 'b')
plt.xticks(np.linspace(1.20, 1.60, 9))
plt.xlim(1.20, 1.60)
plt.legend()
plt.savefig(os.path.join(path_dir_built_graphs,
                         'french_version',
                         'price_dist_total_before.png'),
            bbox_inches='tight')
plt.close()
#plt.show()

# Last day
bins = np.linspace(1.00, 1.50, 51)
plt.hist(df_prices_ttc[ls_total].iloc[-1].values,
         bins, alpha=0.5, label=u'"Total"', color = 'g')
plt.hist(df_prices_ttc[ls_total_ta].iloc[-1].values,
         bins, alpha=0.5, label=u'"Total Access" anciennement "Total"', color = 'b')
plt.xticks(np.linspace(1.00, 1.50, 11))
plt.xlim(1.00, 1.50)
plt.legend()
plt.savefig(os.path.join(path_dir_built_graphs,
                         'french_version',
                         'price_dist_total_after.png'),
            bbox_inches='tight')
plt.close()
#plt.show()

# forced exclusion of price above 1.50... seems not valid anyway
# df_prices_ttc[ls_total].iloc[-1][df_prices_ttc[ls_total].iloc[-1] > 1.5].index
# df_prices_ttc[['37000002', '6000010']].plot()

## ######################################
## GRAPHS: PRICE HISTOGRAMS FOR TREATED
## ######################################

ls_keep_info = list(df_info[df_info['highway'] != 1].index)
ls_keep_stats = list(df_station_stats[(df_station_stats['nb_chge'] >= 5) &\
                                      (df_station_stats['pct_chge'] >= 0.03)].index)
ls_keep_ids = list(set(ls_keep_info).intersection(set(ls_keep_stats)))

ls_ta_ids = list(df_info_ta.index)

dict_ls_ta_comp = {}
for id_station, ls_comp in dict_ls_comp.items():
  ls_ta_comp = [(comp_id, distance) for comp_id, distance in ls_comp\
                                    if comp_id in ls_ta_ids]
  dict_ls_ta_comp[id_station] = ls_ta_comp

ls_control_ids = []
for id_station, ls_ta_comp in dict_ls_ta_comp.items():
  if (id_station in ls_keep_ids) and\
     ((not ls_ta_comp) or\
      (ls_ta_comp[0][1] > 10)):
    ls_control_ids.append(id_station)

ls_ta_chge_ids = list(df_info_ta.index[(df_info_ta['pp_chge'] >= 0.04) &\
                                       (~pd.isnull(df_info_ta['date_beg']))])

df_comp = df_info[(df_info['group'] != 'TOTAL') &\
                  (df_info['group_last'] != 'TOTAL')]

df_treated_comp = df_comp[((~df_comp['id_ta_0'].isnull()) &\
                           (df_comp['id_ta_0'].isin(ls_ta_chge_ids))) |\
                          ((~df_comp['id_ta_1'].isnull()) &\
                           (df_comp['id_ta_1'].isin(ls_ta_chge_ids)))]

ls_treated_comp = list(df_treated_comp.index)
ls_nontreated_comp = [x for x in df_comp.index if x not in ls_treated_comp]

# First day
bins = np.linspace(1.20, 1.60, 41)
plt.hist(df_prices_ttc[ls_nontreated_comp].iloc[0].values,
         bins, alpha=0.5, label=u'Stations qui ne seront pas affectées', color = 'g')
plt.hist(df_prices_ttc[ls_treated_comp].iloc[0].values,
         bins, alpha=0.5, label=u'Stations prochainement affectées', color = 'b')
plt.xticks(np.linspace(1.20, 1.60, 9))
plt.xlim(1.20, 1.60)
plt.legend()
plt.savefig(os.path.join(path_dir_built_graphs,
                         'french_version',
                         'price_dist_treated_before.png'),
            bbox_inches='tight')
plt.close()
#plt.show()

# Last day
bins = np.linspace(1.00, 1.50, 51)
plt.hist(df_prices_ttc[ls_nontreated_comp].iloc[-1].values,
         bins, alpha=0.5, label=u'Stations non affectées', color = 'g')
plt.hist(df_prices_ttc[ls_treated_comp].iloc[-1].values,
         bins, alpha=0.5, label=u'Stations ayant été affectées', color = 'b')
plt.xticks(np.linspace(1.00, 1.50, 11))
plt.xlim(1.00, 1.50)
plt.legend()
plt.savefig(os.path.join(path_dir_built_graphs,
                         'french_version',
                         'price_dist_treated_after.png'),
            bbox_inches='tight')
plt.close()
#plt.show()
