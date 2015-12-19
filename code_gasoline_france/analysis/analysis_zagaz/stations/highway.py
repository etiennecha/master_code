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
# DF HIGHWAY ZAGAZ
# #################

df_hw_zag = df_zagaz_info[~df_zagaz_info['highway'].isnull()].copy()

# Temp fixes
ls_fixes = [['7318', u'Autoroute A4 - Strasbourg / Paris (km 358)'],
            ['5229', u'Autoroute A63 - Bordeaux / Hendaye (km 0)']]
for id_zagaz, str_highway in ls_fixes:
  df_hw_zag.loc[id_zagaz, 'highway'] = str_highway

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

# Inspect zagaz highways

# Checked:
# A1, A4, A6, A7, A8, A9, A10, A13, A26, A31, A36, A43, A61, A71, A83, A64, A89

#ls_str_hw = ['61', '83', '64']
ls_str_hw = [x[1:] for x in df_hw_zag['hw_id'].value_counts()[0:40].index.tolist()\
                   if x[0] == 'A']
ls_other_hw = [x for x in df_hw_zag['hw_id'].value_counts()[0:40].index.tolist()\
                  if x[0] != 'A']

df_hw_zag.sort(['hw_id', 'hw_dir', 'hw_km'], ascending = True, inplace = True)
for str_hw in ls_str_hw:
  print()
  print(u'Inspect highway: {:s}'.format(str_hw))
  print(df_hw_zag[df_hw_zag['hw_id'] == 'A{:s}'.format(str_hw)][lsdhw].to_string(index = False))

# #################
# DF HIGHWAY GOV
# #################

df_hw_gov = df_info[df_info['highway'] == 1].copy()

lsdhwgov = ['name', 'adr_street', 'adr_city', 'ci_1', 'brand_0', 'brand_1']

print()
print(u'Overview of gov highway stations')
print(df_hw_gov[lsdhwgov][0:20].to_string())

for str_hw in ls_str_hw:
  print()
  print(u'Overview of gov A{:s} highway stations'.format(str_hw))
  print(df_hw_gov[df_hw_gov['adr_street'].str.contains('A\s?{:s}(?:\s|$|-)'.format(str_hw))]\
                 [lsdhwgov].to_string())

#print(df_hw_gov[df_hw_gov['ci_1'] == '89438'][lsdhwgov].to_string())
#print(df_hw_gov[df_hw_gov['dpt'] == '89'][lsdhwgov].to_string())

# #################
# MANUAL MATCHING
# #################

# len(df_hw_zag[df_hw_zag['gov_id'].isnull()])
# Only 22 left in zag, check from gov side

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
            ('64210002',  '8476'), # A63
            ('64210001',  '8477'),
            ('40530001',  '5150'),
            ('40530002',  '5151'),
            ('33610004', '15886'), # check..
            ('33610006', '17001'),
            ('40410004',  '5229'),
            ('63190002',  '8385'), # A89
            ('63190010',  '8373'), # check if same '63190003' 
            ('42440008',  '5409'),
            ('42440006',  '5408'), # not 100% sure which is which
            ('3100006' , '17434'), # A71
            ('3170001' , '17604'),
            ('21250009',  '2162'), # A36
            ('21250005', '16213'),
            ('39700011',  '5092'),
            ('31290003', '16015'), # A61
            ('31290002',  '3564'),
            ('11290002',   '725'),
            ('11290001',   '726'),
            ('85210007', '11586'), # A83
            ('64170009',  '8502'), # A 64
            ('64170008', '15429'),
            ('31410003', '15494'),
            ('31410002',  '3587'),
            ('78630002', '13433'), # A13
            ('78630003', '13435'),
            ('78710003', '13434'),
            ('78710002', '12952'),
            ('61230001', '16080'), # A28
            ('80140002', '10835'),
            ('80140001', '10836'),
            ('89190005', '12116'), # A5 (not 100%)
            ('89190004', '12118'),
            ('10270002',   '669'),
            ('10270001',   '670'),
            ('77130009', '13427'),
            ('77130010', '10482'),
            ('13320001',   '979'), # A51
            ('4130003',    '402'),
            ('4130002',    '403'),
            ('4200006',    '348'),
            ('94000002', '13714'), # A86
            ('94003001', '12462'),
            ('94150001', '12513'), # todo: fix dum highway
            ('94150002', '12514'),
            ('62250004',  '8201'), # A16
            ('12150001',   '916'), # A75
            ('49160003', '13087'), # A85
            ('49160004', '13086'),
            ('37190003', '20120'),
            ('59242001', '14750'), # A23
            ('59242002', '14749'),
            ('59494008', '14752'),
            ('59494003',  '7714'),
            ('68390001',  '8933'), # A35
            ('67600003', '13689'),
            ('21130005',  '2191'), # A39
            ('21130006',  '2192'),
            ('73100007',  '9815'), # A41
            ('62147001',  '8159'), # A2
            ('62147003',  '8148'),
            ('33520003',  '3921'), # Rocade A630
            ('33520002',  '3922'),
            ('33700008', '14512'), # todo: fix dum highway?
            ('33700007',  '4049'),
            ('33170003', '13672'),
            ('33170004',  '3967'),
            ('33310002', '14728'), # todo: fix dum highway?
            ('91100007', '13196'), # Francil N104
            ('91250009', '13195'), # todo: fix dum highway?
            ('91460011', '13017'),
            ('91460010', '13018'),
            ('75012008', '10085'), # Periph: check + highway?
            ('75012013', '10086'),
            ('75018003', '10173'),
            ('1390004' , '13279'), # Lyon Est A 46
            ('1390006' , '13280'),
            ('69360005',  '9110'),
            ('69360004',  '9109')]

# not found in gouv '983', '15160'
                            
# todo (if not done yet):   
# drop '62128009' (temp dup  of '62128004')
# drop '76170004' (temp dup  of '76210003')
# drop '41000015' (ctd dup  of '41000006')
# drop '45190008' (temp dup  of '45190004')
# drop '85210005', '8521000 6' (almost no info)
# drop '87160005', '8716000 6' (almost no info)
# drop '34400014' (temp dup of '34400016')
# drop '44370007' (temp dup of '44370004')
# drop '38080005' (temp dup of '38080004')
