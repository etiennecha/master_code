#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *

path_dir_built = os.path.join(path_data,
                              u'data_gasoline',
                              u'data_built',
                              u'data_scraped_2011_2014')
path_dir_built_csv = os.path.join(path_dir_built, u'data_csv')
path_dir_built_json = os.path.join(path_dir_built, u'data_json')
path_dir_built_graphs = os.path.join(path_dir_built, u'data_graphs')

path_dir_built_zagaz = os.path.join(path_data,
                                    u'data_gasoline',
                                    u'data_built',
                                    u'data_zagaz')
path_dir_built_zagaz_csv = os.path.join(path_dir_built_zagaz, 'data_csv')

path_dir_insee = os.path.join(path_data, 'data_insee')
path_dir_insee_extracts = os.path.join(path_dir_insee, 'data_extracts')

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# ##############
# LOAD DATA
# ##############

# INFO

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

# MATCHING ZAGAZ

df_matching_0 = pd.read_csv(os.path.join(path_dir_built_zagaz_csv,
                                         'df_zagaz_stations_match_0.csv'),
                            dtype = {'zag_id' : str,
                                     'gov_id' : str,
                                     'ci' : str},
                            encoding = 'utf-8')

df_matching_1 = pd.read_csv(os.path.join(path_dir_built_zagaz_csv,
                                         'df_zagaz_stations_match_1.csv'),
                            dtype = {'zag_id' : str,
                                     'gov_id' : str,
                                     'ci' : str},
                            encoding = 'utf-8')

# ZAGAZ INFO

df_zagaz_info = pd.read_csv(os.path.join(path_dir_built_zagaz_csv,
                                         'df_zagaz_stations.csv'),
                            encoding='utf-8',
                            dtype = {'id_zagaz' : str,
                                     'zip' : str,
                                     'ci_1' : str,
                                     'ci_ardt_1' : str})
df_zagaz_info.set_index('id_zagaz', inplace = True)

# todo: drop dup in zagaz
df_zagaz_info = df_zagaz_info[df_zagaz_info.index != '19674']

# #################
# DF HIGHWAY GOV
# #################

# A1, A4, A6, A7, A8, A9, A10, A26, A31, A43 done
str_hw = '63'

df_hw_gov = df_info[df_info['highway'] == 1].copy()

lsdhwgov = ['name', 'adr_street', 'adr_city', 'ci_1', 'brand_0', 'brand_1']

print()
print(u'Overview of gov highway stations')
print(df_hw_gov[lsdhwgov][0:20].to_string())

print()
print(u'Overview of gov A{:s} stations'.format(str_hw))
print(df_hw_gov[df_hw_gov['adr_street'].str.contains('A\s?{:s}(?:\s|$|-)'.format(str_hw))]\
               [lsdhwgov].to_string())

#print(df_hw_gov[df_hw_gov['ci_1'] == '89438'][lsdhwgov].to_string())
#print(df_hw_gov[df_hw_gov['dpt'] == '89'][lsdhwgov].to_string())

# #################
# DF HIGHWAY ZAGAZ
# #################

df_hw_zag = df_zagaz_info[~df_zagaz_info['highway'].isnull()].copy()

# Temp fix
df_hw_zag.loc['7318', 'highway'] =\
  df_hw_zag.loc['7318', 'highway'].replace('Paris / Strasbourg', 'Strasbourg / Paris')

# Match zagaz w/ gov id (can result in duplicates: inspect and fix)
df_hw_zag = pd.merge(df_hw_zag,
                     df_matching_1[['zag_id', 'gov_id',
                                    'gov_street', 'gov_city',
                                    'gov_br_0', 'gov_br_1']],
                     left_index = True,
                     right_on = 'zag_id',
                     how = 'left')

# add gov name and street (rename name to adr_name to avoid conflict)
df_hw_zag = pd.merge(df_hw_zag,
                     df_info[['name']],
                     left_on = 'gov_id',
                     right_index = True,
                     how = 'left')
df_hw_zag.rename(columns = {'name_x' : 'name',
                            'name_y' : 'gov_name'}, inplace = True)

# Extract highway info
def format_highway(highway):
  res = re.search('Autoroute (.*?) - (.*?) \(km (.*?)\)', highway)
  return res.group(1), res.group(2), int(res.group(3))

df_hw_zag['hw_id'], df_hw_zag['hw_dir'], df_hw_zag['hw_km'] =\
    zip(*df_hw_zag['highway'].apply(lambda x: format_highway(x)))

lsdhw = ['hw_id', 'hw_dir', 'hw_km', 'name', 'gov_name', 'gov_street',
         'municipality', 'gov_city', 'ci',
         'zag_id', 'gov_id', 'brand_2013', 'gov_br_0', 'gov_br_1']

print()
print(u'Top 20 highways in terms of station count')
print(df_hw_zag['hw_id'].value_counts()[0:20])

print()
print(u'Inspect duplicates')
df_hw_zag['dup'] = df_hw_zag.groupby('zag_id')['zag_id'].transform(len)
print(df_hw_zag[df_hw_zag['dup'] > 1][lsdhw].to_string(index = False))

# Check highways
df_hw_zag.sort(['hw_id', 'hw_dir', 'hw_km'], ascending = True, inplace = True)
print()
print(u'Inspect highways')
print(df_hw_zag[df_hw_zag['hw_id'] == 'A{:s}'.format(str_hw)][lsdhw].to_string(index = False))

ls_match = [('80200010', '10791'), # A1
            ('80200005', '13343'),
            ('62128008', '8227' ),
            ('62119001', '13296'),
            ('91100003', '13042'), # A6
            ('91100006', '12987'), 
            ('77116001', '14194'),
            ('77760003', '10413'),
            ('89290006', '14197'), # mistake in gvt name (A41...)
            ('21320003', '2152' ),
            ('21320005', '2193' ),
            ('21190005', '2177' ),
            ('21190003', '2178' ),
            ('69380001', '9164' ),
            ('69380002', '9163' ),
            ('91640001', '13188'), # A10
            ('45520002', '5892' ),
            ('86130003', '11643'),
            ('86130007', '11644'),
            ('17350001', '1615' ),
            ('17350002', '13539'),
            ('17800001', '1714' ),
            ('17800002', '1715' ),
            ('33240002', '4082' ),
            ('77600002', '10432'), # A4
            ('77600001', '10433'),
            ('77260007', '10610'),
            ('77260008', '10609'),
            ('2130005' , '164'  ),
            ('2130006' , '165'  ),
            ('51390002', '6694' ),
            ('51400008', '6634' ),
            ('51400007', '6635' ),
            ('51800008', '13680'),
            ('51800006', '13679'),
            ('55160011', '7016' ),
            ('55160012', '7015' ),
            ('67170002', '8790' ),
            ('67170001', '8785' ),
            ('69360002', '9272' ), # A7
            ('69360006', '13902'),
            ('26140005', '2850' ),
            ('26270005', '2857' ),
            ('26780002', '2757' ),
            ('26780004', '2758' ),
            ('84550001', '13712'),
            ('84550002', '13713'),
            ('84700003', '11387'),
            ('13680001', '1049' ),
            ('13680002', '1048' ),
            ('34400016', '13324'), # A9
            ('34290004', '4248' ),
            ('34290003', '4247' ),
            ('11110003', '823'  ),
            ('11110002', '812'  ),
            ('52160005', '15641'), # A31
            ('52160007', '6738' ),
            ('52140005', '6755' ),
            ('52140004', '6754' ),
            ('72400012', '9725' ), # A11
            ('72190001', '9714' ),
            ('72300004', '9677' ),
            ('72300005', '13908'),
            ('69800012', '14208'), # A43
            ('69800013', '14187'),
            ('38480005', '4936' ),
            ('73390008', '9773' ),
            ('73390007', '9772' ),
            ('6250003' , '12788'), # A8
            ('87280002', '13272'), # A20
            ('62860004',  '8065'), # A26
            ('2690001' ,   '234'),
            ('62860005',  '8221'),
            ('10150003', '16712'),
            ('64210002',  '8476'), # A 63
            ('64210001',  '8477'),
            ('40530001',  '5150'),
            ('40530002',  '5151')]

# todo (if not done yet):
# drop '62128009' (temp dup of '62128004')
# drop '76170004' (temp dup of '76210003')
# drop '41000015' (ctd dup of '41000006')
# drop '45190008' (temp dup of '45190004')
# drop '85210005', '85210006' (almost no info)
# drop '87160005', '87160006' (almost no info)
# drop '34400014' (temp dup of '34400016')
# drop '44370007' (temp dup of '44370004')
# drop '38080005' (temp dup of '38080004')
