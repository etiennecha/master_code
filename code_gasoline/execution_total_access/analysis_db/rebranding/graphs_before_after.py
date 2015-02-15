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

# ############################
# GRAPHS: PRICE HISTOGRAMS
# ############################

# First day
bins = np.linspace(1.20, 1.60, 41)
plt.hist(df_prices_ttc[ls_total].iloc[0].values,
         bins, alpha=0.5, label='"Total"', color = 'g')
plt.hist(df_prices_ttc[ls_total_ta].iloc[0].values,
         bins, alpha=0.5, label='"Total" to be rebranded', color = 'b')
plt.xlim(1.20, 1.60)
plt.legend()
plt.show()

# Last day
bins = np.linspace(1.00, 1.50, 51)
plt.hist(df_prices_ttc[ls_total].iloc[-1].values,
         bins, alpha=0.5, label='"Total" and ex "Total" now "Total Access"', color = 'g')
plt.hist(df_prices_ttc[ls_total_ta].iloc[-1].values,
         bins, alpha=0.5, label='Ex "Total" now "Total Access"', color = 'b')
plt.xlim(1.00, 1.50)
plt.legend()
plt.show()

# forced exclusion of price above 1.50... seems not valid anyway
# df_prices_ttc[ls_total].iloc[-1][df_prices_ttc[ls_total].iloc[-1] > 1.5].index
# df_prices_ttc[['37000002', '6000010']].plot()

# ############################
# GRAPHS: TOTAL ACCESS TRENDS
# ############################

# Think of puting on same graph?

# BEFORE REBRANDING VS. NO TA
for date in ['2013-01-01', '2014-01-01']:
  
  # plot no ta and ta
  ls_ids_disp = df_ta_mc.index[df_ta_mc['pp_chge_date'] >= date]
  lab1 = 'Rebranded after {:s} ({:d})'.format(date, len(ls_ids_disp))
  lab2 = 'Control ({:d})'.format(len(ls_ids_nota))
  ax = df_prices_ttc[ls_ids_disp].mean(1).ix[:date].plot(label = lab1)
  df_prices_ttc[ls_ids_nota].mean(1).ix[:date].plot(ax = ax, label = lab2)
  plt.legend()
  plt.show()
  
  ## plot difference
  #se_diff = df_prices_ttc[ls_ids_nota].mean(1).ix[:date] -\
  #            df_prices_ttc[ls_ids_disp].mean(1).ix[:date]
  #se_diff.plot()
  #plt.show()

# AFTER REBRANDING VS. NO TA
for date in ['2013-01-01', '2014-01-01']:
  
  # plot no ta and ta
  ls_ids_disp = df_ta_mc.index[df_ta_mc['pp_chge_date'] <= date]
  lab1 = 'Rebranded before {:s} ({:d})'.format(date, len(ls_ids_disp))
  lab2 = 'Control ({:d})'.format(len(ls_ids_nota))
  ax = df_prices_ttc[ls_ids_disp].mean(1).ix[date:].plot(label = lab1)
  df_prices_ttc[ls_ids_nota].mean(1).ix[date:].plot(ax = ax, label = lab2)
  plt.legend()
  plt.show()
  
  ## plot difference
  #se_diff = df_prices_ttc[ls_ids_nota].mean(1).ix[date:] -\
  #            df_prices_ttc[ls_ids_disp].mean(1).ix[date:]
  #se_diff.plot()
  #plt.show()

# #########################################
# GRAPHS: TOTAL ACCESS PRICES W/ QUANTILES
# #########################################

date = '2014-01-01'
ls_ids_disp = df_ta_mc.index[df_ta_mc['pp_chge_date'] <= date]
lab_ref = 'Rebranded before {:s} ({:d})'.format(date, len(ls_ids_disp))
ax = df_prices_ttc[ls_ids_disp].mean(1).ix[date:].plot(c = 'b', ls = '-', label = lab_ref)
df_prices_ttc[ls_ids_disp].quantile(0.25, 1).ix[date:].plot(ax = ax , label = 'Q25',
                                                            c = 'b', ls = '--')
df_prices_ttc[ls_ids_disp].quantile(0.75, 1).ix[date:].plot(ax = ax, label = 'Q75',
                                                            c = 'b', ls = '--')
plt.legend()
plt.show()

# ###########################
# GRAPHS: ELF TRENDS
# ###########################


ls_ids_disp = list(df_elf_nomc.index)

## ELF
#lab_ref = 'Elf rebranded ({:d})'.format(len(ls_ids_disp))
#ax = df_prices_ttc[ls_ids_disp].mean(1).plot(c = 'b', ls = '-', label = lab_ref)
#df_prices_ttc[ls_ids_disp].quantile(0.25, 1).plot(ax = ax,
#                                                  c = 'b', ls = '--')
#df_prices_ttc[ls_ids_disp].quantile(0.75, 1).plot(ax = ax,
#                                                  c = 'b', ls = '--')
## CONTROL
#lab_ctrl = 'Control ({:d})'.format(len(ls_ids_disp))
#df_prices_ttc[ls_ids_nota].mean(1).plot(ax = ax, c = 'g', ls = '-', label = lab_ctrl)
#df_prices_ttc[ls_ids_nota].quantile(0.25, 1).plot(ax = ax ,
#                                                  c = 'g', ls = '--')
#df_prices_ttc[ls_ids_nota].quantile(0.75, 1).plot(ax = ax,
#                                                  c = 'g', ls = '--')
#
#plt.legend()
#plt.show()

plt.figure()
# ELF
lab_ref = 'Elf rebranded ({:d})'.format(len(ls_ids_disp))
plt.plot(df_prices_ttc.index,
         df_prices_ttc[ls_ids_disp].mean(1),
         c = 'b', ls = '-', label = lab_ref)
plt.plot(df_prices_ttc.index,
         df_prices_ttc[ls_ids_disp].quantile(0.25, 1),
         c = 'b', ls = '--')
plt.plot(df_prices_ttc.index,
         df_prices_ttc[ls_ids_disp].quantile(0.75, 1),
         c = 'b', ls = '--')
# CONTROL
lab_ctrl = 'Control ({:d})'.format(len(ls_ids_nota))
plt.plot(df_prices_ttc.index,
         df_prices_ttc[ls_ids_nota].mean(1),
         c = 'g', ls = '-', label = lab_ctrl)
plt.plot(df_prices_ttc.index,
         df_prices_ttc[ls_ids_nota].quantile(0.25, 1),
         c = 'g', ls = '--')
plt.plot(df_prices_ttc.index,
         df_prices_ttc[ls_ids_nota].quantile(0.75, 1),
         c = 'g', ls = '--')
plt.legend()
plt.grid()
plt.show()
