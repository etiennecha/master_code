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

# ################
# LOAD DATA
# ################

# LOAD DF PRICES
df_prices_ttc = pd.read_csv(os.path.join(path_dir_built_csv,
                                         'df_prices_ttc_final.csv'),
                        parse_dates = ['date'])
df_prices_ttc.set_index('date', inplace = True)

# LOAD DF INFO TA
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
                      parse_dates = ['start', 'end', 'day_0', 'day_1', 'day_2'])
df_info.set_index('id_station', inplace = True)

# LOAD DFS INSEE
df_insee_areas = pd.read_csv(os.path.join(path_dir_insee_extracts,
                                          'df_insee_areas.csv'),
                             dtype = {'CODGEO' : str,
                                      'UU2010' : str,
                                      'AU2010' : str,
                                      'BV2010' : str},
                             encoding = 'UTF-8')

df_au_agg = pd.read_csv(os.path.join(path_dir_insee_extracts,
                                     'df_au_agg_final.csv'),
                        dtype = {'AU2010' : str,
                                 'CODGEO_CT' : str},
                        encoding = 'UTF-8')
df_au_agg.set_index('AU2010', inplace = True)

df_uu_agg = pd.read_csv(os.path.join(path_dir_insee_extracts,
                                     'df_uu_agg_final.csv'),
                        dtype = {'UU2010' : str,
                                 'CODGEO_CT' : str},
                        encoding = 'UTF-8')
df_uu_agg.set_index('UU2010', inplace = True)

df_bv_agg = pd.read_csv(os.path.join(path_dir_insee_extracts,
                                     'df_bv_agg_final.csv'),
                        dtype = {'BV' : str,
                                 'CODGEO_CT' : str},
                        encoding = 'UTF-8')
df_bv_agg.set_index('BV', inplace = True)

df_com = pd.read_csv(os.path.join(path_dir_insee_extracts,
                                  'data_insee_extract.csv'),
                     dtype = {'DEP': str,
                              'CODGEO' : str},
                     encoding = 'UTF-8')
df_com = df_com[~(df_com['DEP'].isin(['2A', '2B', '971', '972', '973', '974']))]
df_com.set_index('CODGEO', inplace = True)

## ADD INSEE AREA CODES
## i.e. Store viewpoint: add commune char
## need to save index in df_info_ta if does that

# LOAD DF COMP
df_comp = pd.read_csv(os.path.join(path_dir_built_csv,
                                  'df_comp.csv'),
                      dtype = {'id_station' : str},
                      encoding = 'utf-8')
df_comp.set_index('id_station', inplace = True)

# ##########################
# PREPARE DATA
# ##########################

# MERGE DF INFO AND DF INSEE AREAS
df_info.reset_index(inplace = True)
df_info = pd.merge(df_insee_areas,
                   df_info,
                   left_on = 'CODGEO',
                   right_on = 'ci_ardt_1',
                   how = 'right')
df_info.set_index('id_station', inplace = True)

# MERGE DF INFO AND DF COMP
df_info = pd.merge(df_info,
                   df_comp,
                   how = 'left',
                   left_index = True,
                   right_index = True)

# Exclude Corsica and highay
df_info = df_info[(df_info['highway'] != 1) & (df_info['reg'] != 'Corse')]

ls_ids_elf_TA = list(df_info_ta.index[df_info_ta['brand_0'] == 'ELF'])
ls_ids_total_TA = list(df_info_ta.index[df_info_ta['brand_0'] == 'TOTAL'])
ls_ids_total = list(df_info.index[(df_info['brand_0'] == 'TOTAL')])
ls_ids_total_noTA = [id_station for id_station in ls_ids_total\
                       if id_station not in df_info_ta.index]

dict_desc_groups = {'TOTAL' : ls_ids_total,
                    'TOTAL not TA' : ls_ids_total_noTA,
                    'TOTAL-TA' : ls_ids_total_TA,
                    'ELF-TA' : ls_ids_elf_TA}

# ##########################
# DESC TA LOCATIONS
# ##########################

## RURAL/URBAN etc. (pivot table w/ percent? cross tab?)
## Possibly: need to add astype(float)
#pd.crosstab(df_info['group'],
#            df_info['STATUT_2010']).apply(lambda r: r/r.sum(), axis=1)
ls_se_group_envt = []
for group_name, ls_group_ids in dict_desc_groups.items():
  ls_se_group_envt.append(df_info.ix[ls_group_ids]['STATUT_2010'].value_counts())
df_groups_envt_ct = pd.concat(ls_se_group_envt, keys = dict_desc_groups.keys(), axis = 1)
df_groups_envt_pct = df_groups_envt_ct.apply(lambda x: x * 100/x.sum().astype('float'))
df_groups_envt_ct['stat'] = 'count'
df_groups_envt_ct.set_index('stat', inplace = True, append = True)
df_groups_envt_pct['stat'] = 'pct'
df_groups_envt_pct.set_index('stat', inplace = True, append = True)
df_groups_envt = pd.concat([df_groups_envt_ct, df_groups_envt_pct])
df_groups_envt = df_groups_envt.sortlevel(0).astype(int)
new_index, indexer = df_groups_envt.index.reindex(['C', 'B', 'I', 'R'], level=0)
df_groups_envt = df_groups_envt.reindex(index=new_index)

print u"\nDescribe stations' municipality type (urban, rural etc.) by brand:"
print df_groups_envt[['TOTAL', 'TOTAL not TA', 'TOTAL-TA', 'ELF-TA']].to_string()

# ###############################
# DESC TA MARKET COMPETITIVENESS
# ###############################

# pivot table: http://pbpython.com/pandas-pivot-table-explained.html (bof here)

ls_desc_vars = ['dist_c', 'dist_s', 'dist_c_sup', 'nb_c_1km', 'nb_c_3km', 'nb_c_5km']
ls_dfs_group_desc = []
for group_name, ls_group_ids in dict_desc_groups.items():
  df_group_desc = df_info.ix[ls_group_ids][ls_desc_vars].describe()
  df_group_desc.index.name = 'stat'
  df_group_desc['group_name'] = group_name
  df_group_desc.set_index('group_name', inplace = True, append = True)
  ls_dfs_group_desc.append(df_group_desc)
df_groups_desc = pd.concat(ls_dfs_group_desc)
df_groups_desc = df_groups_desc.T.stack(0)
#print df_groups_desc.loc[(slice(None), ['mean', 'std', '50%']),:]
#print df_groups_desc.query('stat == "mean" | stat == "50%"')
new_index, indexer = df_groups_desc.index.reindex(['count', 'mean', 'std'], level=1)
df_groups_desc = df_groups_desc.reindex(index=new_index)

print u"\nDescribe stations' market competitiveness by brand:"
print df_groups_desc[['TOTAL', 'TOTAL not TA', 'TOTAL-TA', 'ELF-TA']].T.to_string()

# ##########################
# DESC TA AMENITIES
# ##########################

## Cross tab interesting for categorical variables
# pd.crosstab(df_info['group'], df_info['Automate CB'])

# Describe amenities (should display percentage equiped with?)

ls_amenities = [u'Laverie', u'Baie de service auto', u'Boutique alimentaire',
                u'Automate CB', u'Restauration sur place', u'Relais colis',
                u'Boutique non alimentaire', u'Vente de pétrole lampant',
                u'Vente de fioul domestique', u'Douches', u'Toilettes publiques',
                u'GPL', u'Piste poids lourds', u'Bar', u'Restauration à emporter',
                u'Lavage multi-programmes', u'Station de lavage',
                u'Espace bébé / change', u'Station de gonflage', u'Aire de camping-cars',
                u'Vente de gaz domestique', u'Location de véhicule',
                u'Lavage haute-pression', u'Carburant qualité supérieure']

ls_dfs_group_amen = []
for group_name, ls_group_ids in dict_desc_groups.items():
  df_group_amen = df_info.ix[ls_group_ids][ls_amenities].describe()
  df_group_amen.index.name = 'stat'
  df_group_amen['group_name'] = group_name
  df_group_amen.set_index('group_name', inplace = True, append = True)
  ls_dfs_group_amen.append(df_group_amen)
df_groups_amen = pd.concat(ls_dfs_group_amen)
df_groups_amen = df_groups_amen.T.stack(0)
new_index, indexer = df_groups_amen.index.reindex(['count', 'mean'], level=1)
df_groups_amen = df_groups_amen.reindex(index=new_index)
df_groups_amen_pct = df_groups_amen.loc[(slice(None), ['mean']),:].\
                       reset_index('stat', drop = True)

df_groups_amen_pct = df_groups_amen_pct[(df_groups_amen_pct['TOTAL'] >= 0.05) |
                                        (df_groups_amen_pct['TOTAL-TA'] >= 0.05) |
                                        (df_groups_amen_pct['ELF-TA'] >= 0.05)]

print u'\nDescribe amenities: pctage of equipment by brand:'
print df_groups_amen_pct[['TOTAL', 'TOTAL not TA', 'TOTAL-TA', 'ELF-TA']].to_string()

## check how old information is, update?
## more Boutique... consistant with necessity to make more revenue

## ################
## LOGIT
## ################
#
#df_logit = df_info[(df_info['brand_0'] == 'TOTAL') &\
#                   (~pd.isnull(df_info['dist_cl']))].copy()
#df_logit['rebranded'] = 0
#df_logit.loc[df_logit['brand_last'] == 'TOTAL_ACCESS', 'rebranded'] = 1
#
#ls_dist_disp = ['name', 'adr_street', 'adr_city', 'dist_cl' , 'dist_cl_sup']
#print df_logit[df_logit['reg']  == 'Corse'][ls_dist_disp].to_string()
#
#df_logit = df_logit[df_logit['reg'] != 'Corse']
#
#print df_logit[(df_logit['dist_cl'] == 0) |\
#               (df_logit['dist_cl_sup'] == 0)][ls_dist_disp].to_string()
#
##import statsmodels.api as sm
##exo = sm.add_constant(df_logit['dist_cl_sup'])
##logit_mod = sm.Logit(df_logit['Rebranded'], exo)
##logit_res = logit_mod.fit()
##print logit_res.summary()
#
## http://statsmodels.sourceforge.net/stable/examples/notebooks/generated/discrete_choice_example.html
#
#from statsmodels.formula.api import logit, probit
#df_logit['nb_comp_1km'] = df_logit['1km']
#rebranded_mod = logit('rebranded ~ dist_cl_sup',
#                      df_logit).fit()
#print rebranded_mod.summary()
## prediction not working?
#rebranded_mod.pred_table()
## marginal effects
#mfx = rebranded_mod.get_margeff()
#print mfx.summary()
#
## todo: departementales, nationales + Rural / Center / Suburb
## if does not help either => show hard to predict rebranding, good repartition
#df_logit['crowded'] = 0
#df_logit.loc[(df_logit['adr_street'].str.contains('nationale', case = False))|\
#             (df_logit['adr_street'].str.contains('departementale', case = False))|\
#             (df_logit['adr_street'].str.contains('départementale', case = False))|\
#             (df_logit['adr_street'].str.contains('RN', case = True))|\
#             (df_logit['adr_street'].str.contains('RD', case = True)), 'crowded'] = 1
#
#df_logit = pd.merge(df_logit,
#                    df_insee_areas,
#                    how = 'left',
#                    left_on = 'ci_ardt_1',
#                    right_on = 'CODGEO')
#
#print pd.crosstab(df_logit['rebranded'], df_logit['STATUT_2010'], rownames=['rebranded'])
#
#df_logit['CB'] = df_logit['Automate CB']
#df_logit['BA'] = df_logit['Boutique alimentaire']
#df_logit['BNA'] = df_logit['Boutique non alimentaire']
#
#for service in ['CB', 'BA', 'BNA']:
#  df_ser = pd.crosstab(df_logit['rebranded'], df_logit[service], rownames=['rebranded'])
#  df_ser_pct = pd.concat([df_ser[0] / (df_ser[0] + df_ser[1]),
#                          df_ser[1] / (df_ser[0] + df_ser[1])], axis = 1)
#  print u'\n', service
#  print df_ser_pct
#
## check if actually works
## http://nbviewer.ipython.org/github/adparker/GADSLA_1403/blob/master/src/lesson07/Logistic%20Regression%20and%20Statsmodels%20tutorial.ipynb
#rebranded_mod = logit('rebranded ~ C(STATUT_2010) + CB + dist_cl_sup',
#                      df_logit).fit()
#print rebranded_mod.summary()
#mfx = rebranded_mod.get_margeff(at = 'mean')
#print mfx.summary()
#print rebranded_mod.pred_table()
## pbm... no prediction => run with R or STATA
#
##import statsmodels.formula.api as smf
##print smf.ols('rebranded ~ C(STATUT_2010) + CB + dist_cl_sup',
##                      df_logit).fit().summary()
#
#for i in range(1,6):
#  df_logit['nb_comp_%skm' %i] = df_logit['%skm' %i]
#
#ls_output_stata = ['rebranded', 'STATUT_2010', 'CB', 'BA', 'BNA',
#                   'dist_cl', 'dist_cl_sup',
#                   'nb_comp_1km', 'nb_comp_3km', 'nb_comp_5km',
#                   'crowded']
#
#df_logit[ls_output_stata].to_csv(os.path.join(path_dir_built_csv,
#                                              'df_rebranding_logit.csv'),
#                                 index = False)
