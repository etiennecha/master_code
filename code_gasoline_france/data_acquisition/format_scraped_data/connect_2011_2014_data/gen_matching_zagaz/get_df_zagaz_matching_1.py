#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
from generic_competition import *
from functions_string import *
from BeautifulSoup import BeautifulSoup
import copy
import collections

def str_zagaz_corrections(word):
  word = word.lower()
  word = re.sub(ur'(^|\s|,)r?\.?\s?d\.?\s?([0-9]{0,5})(\s|$|,)',
                ur'\1 route departementale \2 \3',
                word)
  word = re.sub(ur'(^|\s|,)r?\.?\s?n\.?\s?([0-9]{0,5})(\s|$|,)',
                ur'\1 route nationale \2 \3',
                word) 
  return word.strip()

path_dir_scraped = os.path.join(path_data,
                                u'data_gasoline',
                                u'data_built',
                                u'data_scraped_2011_2014')

path_dir_scraped_csv = os.path.join(path_dir_scraped,
                                    'data_csv')

path_dir_scraped_json = os.path.join(path_dir_scraped,
                                     'data_json')

path_dir_zagaz = os.path.join(path_data,
                              u'data_gasoline',
                              u'data_built',
                              u'data_zagaz')

path_dir_zagaz_csv = os.path.join(path_dir_zagaz, 'data_csv')

path_dir_match_insee = os.path.join(path_data,
                                    u'data_insee',
                                    u'match_insee_codes')

path_dir_insee_extracts = os.path.join(path_data,
                                       u'data_insee',
                                       u'data_extracts')

# ################
# LOAD DF ZAGAZ
# ################

df_zagaz = pd.read_csv(os.path.join(path_dir_zagaz_csv,
                                    'df_zagaz_stations.csv'),
                       encoding='utf-8',
                       dtype = {'id_zagaz' : str,
                                'zip' : str,
                                'ci_1' : str,
                                'ci_ardt_1' : str})
df_zagaz.set_index('id_zagaz', inplace = True)

dict_brands = dec_json(os.path.join(path_data,
                                    'data_gasoline',
                                    'data_source',
                                    'data_other',
                                    'dict_brands.json'))

# update with zagaz
dict_brands_update = {'OIL' : [u'INDEPENDANT', u'INDEPENDANT', u'IND'],
                      'TEXACO' : [u'INDEPENDANT', u'INDEPENDANT', u'IND'],
                      'ENI' : [u'AGIP', u'AGIP', u'OIL'],
                      'IDS': [u'INDEPENDANT', u'INDEPENDANT', u'IND'],
                      '8 A HUIT' : [u'HUIT_A_HUIT', u'CARREFOUR', u'SUP'],
                      'AS 24' : [u'INDEPENDANT', u'INDEPENDANT', u'IND'],
                      'AS24' : [u'INDEPENDANT', u'INDEPENDANT', u'IND'],
                      'SPAR' : [u'CASINO', u'CASINO', u'SUP'],
                      'ANTARGAZ' : [u'INDEPENDANT', u'INDEPENDANT', u'IND'],
                      'DIVERS' : [u'INDEPENDANT', u'INDEPENDANT', u'IND'],
                      'MATCH' : [u'CORA', u'CORA', u'SUP'],
                      'PRIMAGAZ' : [u'INDEPENDANT', u'INDEPENDANT', u'IND']}
dict_brands.update(dict_brands_update)

# NORMALIZATION FOR MATCHING
dict_brands_std = {v[0]: v[1:] for k,v in dict_brands.items()}
dict_brands_norm = {u'SHOPI': [u'CARREFOUR', u'GMS'],
                    u'CARREFOUR_CONTACT': [u'CARREFOUR', u'GMS'],
                    u'ECOMARCHE' : [u'MOUSQUETAIRES', u'GMS'],
                    u'INTERMARCHE_CONTACT' : [u'MOUSQUETAIRES', u'GMS'],
                    u'INTERMARCHE' : [u'MOUSQUETAIRES', u'GMS'],
                    u'ESSO_EXPRESS' : [u'ESSO', u'OIL']}
dict_brands_std.update(dict_brands_norm)

df_zagaz['brand_std_last'] = df_zagaz['brand_std_2013']
df_zagaz.loc[df_zagaz['brand_std_last'].isnull(),
             'brand_std_last'] = df_zagaz['brand_std_2012']

df_zagaz['brand_std_last'] = df_zagaz['brand_std_last'].apply(\
                               lambda x: dict_brands_std.get(x, [None, None])[0])

# ################
# LOAD DF GOUV
# ################

# duplicates within master_info... (hence might match dropped ids)
master_info = dec_json(os.path.join(path_dir_scraped_json,
                                    'master_info_fixed.json'))


dict_addresses = {indiv_id: [indiv_info['address'][i] for i in (8, 7, 6, 5, 3, 4, 0)\
                               if indiv_info['address'][i]]\
                    for indiv_id, indiv_info in master_info.items()}
master_addresses = build_master_addresses(dict_addresses)

df_info = pd.read_csv(os.path.join(path_dir_scraped_csv,
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

for field_brand in ['brand_0', 'brand_1',  'brand_2']:
  df_info[field_brand] = df_info[field_brand].apply(\
                              lambda x: dict_brands_std.get(x, [None, None])[0])

# #############
# LOAD MATCH 0
# #############

df_zagaz_match_0 = pd.read_csv(os.path.join(path_dir_zagaz_csv,
                                            'df_zagaz_matching_0.csv'),
                               dtype = {'zag_id' : str,
                                        'gov_id' : str,
                                        'ci' : 'str'},
                               encoding = 'UTF-8')
ls_unmatched_gov_ids = [gov_id for gov_id in df_info.index\
                           if gov_id not in df_zagaz_match_0['gov_id'].values]
ls_unmatched_zag_ids = [zag_id for zag_id in df_zagaz.index\
                           if zag_id not in df_zagaz_match_0['zag_id'].values]

df_info_um = df_info.ix[ls_unmatched_gov_ids].copy()
df_zagaz_um = df_zagaz.ix[ls_unmatched_zag_ids].copy()

ls_cols = 0
dict_no_match = {'zag_ci_n' : [], # one in ci, no one of same brand
                 'zag_ci_m_nbr' : [], # seberal in ci, no one of same brand
                 'zag_ci_m_mbr' : []} # several in ci, several of same brand
dict_matching_quality = {'zag_ci_u_ebr' : [],
                         'zag_ci_u_dbr' : [], # diff brand, match but not good?
                         'zag_ci_m_ebr' : []} # several in ci but only one of same brand
for gov_id, gov_station in df_info_um.iterrows():
  gov_station_ci = gov_station['ci_1']
  brand_station_0 = gov_station['brand_0']
  brand_station_1 = gov_station['brand_1']
  df_zagaz_ci = df_zagaz_um[df_zagaz_um['ci'] == gov_station_ci]
  if len(df_zagaz_ci) == 0:
    dict_no_match['zag_ci_n'].append(gov_id)
  elif len(df_zagaz_ci) == 1:
    if len(df_zagaz_ci[(df_zagaz_ci['brand_std_last'] == brand_station_0) |
                       (df_zagaz_ci['brand_std_last'] == brand_station_1)]) == 1:
      dict_matching_quality['zag_ci_u_ebr'].append((gov_id,
                                                    df_zagaz_ci.index[0]))
    else:
      dict_matching_quality['zag_ci_u_dbr'].append((gov_id,
                                                    df_zagaz_ci.index[0]))
  else:
    # risk of loss due to less precision...
    df_zagaz_ci_br = df_zagaz_ci[(df_zagaz_ci['brand_std_last'] == brand_station_0) |
                                 (df_zagaz_ci['brand_std_last'] == brand_station_1)]
    if len(df_zagaz_ci_br) == 0:
      dict_no_match['zag_ci_m_nbr'].append(gov_id)
    elif len(df_zagaz_ci_br) == 1:
      dict_matching_quality['zag_ci_m_ebr'].append((gov_id,
                                                    df_zagaz_ci_br.index[0]))
    else:
      dict_no_match['zag_ci_m_mbr'].append(gov_id)

for k, v in dict_matching_quality.items():
	print k, len(v)

for k, v in dict_no_match.items():
	print k, len(v)

# Not many no match left... but probably quite a few duplicates
# Clean results first, then finish

# ################
# BUILD DF RESULTS
# ################

# Build df results (slight pbm... not gov address from master_address but df_info)
# todo: overwrite if manual matching conflicting
ls_rows_matches = []
for quality, ls_matches in dict_matching_quality.items():
  for gov_id, zag_id in ls_matches:
    ls_rows_matches.append([quality,
                            gov_id,
                            zag_id] +\
                           list(df_info.ix[gov_id][['adr_street',
                                                    'adr_city',
                                                    'brand_0',
                                                    'brand_1',
                                                    'lat',
                                                    'lng',
                                                    'ci_1']]) +\
                           list(df_zagaz.ix[zag_id][['street',
                                                     'municipality',
                                                     'brand_std_last',
                                                     'lat',
                                                     'lng']]))

ls_columns = ['quality', 'gov_id', 'zag_id',
              'gov_street', 'gov_city',
              'gov_br_0', 'gov_br_1', 'gov_lat', 'gov_lng', 'ci',
              'zag_street', 'zag_city',
              'zag_br', 'zag_lat', 'zag_lng']
df_matches = pd.DataFrame(ls_rows_matches,
                          columns = ls_columns)

df_matches['dist'] = df_matches.apply(\
                           lambda x: compute_distance(\
                                            (x['gov_lat'], x['gov_lng']),
                                            (x['zag_lat'], x['zag_lng'])), axis = 1)

ls_ma_di_0 = ['gov_id', 'zag_id',
              'gov_street', 'zag_street',
              'gov_br_0', 'gov_br_1', 'zag_br', 'dist']

ls_ma_di_1 = ['gov_id', 'zag_id', 'gov_city', 'zag_city',
              'gov_street', 'zag_street',
              'gov_br_0', 'gov_br_1', 'zag_br', 'dist']

# may not want to keep one result but diff brand?
print '\nOne match in ci, different brands:'
print df_matches[ls_ma_di_0][df_matches['quality'] == 'zag_ci_u_dbr'].to_string()
# todo: drop this from final matching and keep only handpicked selection

print '\nOne match in ci, same brands:'
print df_matches[ls_ma_di_0][df_matches['quality'] == 'zag_ci_u_ebr'][0:30].to_string()

print '\nMult match in ci, only one w/ same brand:'
print df_matches[ls_ma_di_0][df_matches['quality'] == 'zag_ci_m_ebr'][0:30].to_string()

# ###################
# MERGE W/ PREVIOUS
# ###################

df_output = pd.concat([df_zagaz_match_0,
                       df_matches[df_matches['quality'] != 'zag_ci_u_dbr']])

# ###################
# MANUAL MATCHING
# ###################

ls_hand_matching = [('10210001', '15803'),
                    ('10270004',   '679'), # Total => Carrefour
                    ('11390001', '15657'),
                    ('11590001',   '757'), 
                    ('1250001' ,    '35'),
                    ('1250002' ,    '63'),
                    ('12780002',   '908'),
                    ('13130006',   '976'),
                    ('1360002' , '19981'),
                    ('14760001',  '1263'),
                    ('15290001',  '1426'),
                    ('15500006', '13814'),
                    ('16230002',  '1544'),
                    ('16270001',  '1560'),
                    ('16400002', '13592'), # check
                    ('17110001',  '1705'),
                    ('17120002',  '1610'),
                    ('17139002', '13984'),
                    ('17160002', '18328'),
                    ('17360001',  '1693'),
                    ('17420001',  '1720'),
                    ('19800001',  '1908'),
                    ('20156001',  '2086'),
                    ('21240001',  '2222'),
                    ('21800006',  '2197'),
                    ('22290003', '15762'),
                    ('22400002',  '2254'),
                    ('24160001',  '2592'),
                    ('24170002',  '2607'),
                    ('25420005', '14978'),
                    ('26170001', '18955'),
                    ('27350003',  '3012'),
                    ('27930007',  '2948'),
                    ('2880001' ,   '156'),
                    ('29160001',  '3213'),
                    ('84140005',  '3461'), # check
                    ('30340002',  '3540'),
                    ('30960001',  '3474'),
                    ('31240005',  '3630'),
                    ('31420002', '18693'), # duplicates? 
                    ('32340001', '17370'), # check
                    ('32460001', '17387'), # check
                    ('32730003',  '3851'),
                    ('33260010', '20220'), # check
                    ('33290008',  '3890'),
                    ('33480004', '13991'),
                    ('33490001',  '4100'), # check
                    ('34160001',  '4184'),
                    ('34320003', '14487'), # check
                    ('34620001',  '4299'), # check
                    ('34670001',  '4155'), # check
                    ('35111001', '18218'), # check
                    ('35800001', '16640'),
                    ('35850004', '18725'), # end of 0:100
                    ('36110001',  '4621'),
                    ('36290001', '17537'),
                    ('37370001',  '4766'),
                    ('38450001',  '5004'), # check
                    ('38570004', '15002'),
                    ('38850001',  '4840'), # check
                    ('38850002',  '4835'),
                    ('39170001',  '5100'),
                    ('39230004', '16818'), # check
                    ('39570007',  '5087'),
                    ('40140001', '15853'),
                    ('40280004',  '5173'),
                    ('40420003',  '5140'), # check
                    ('4120002',  '19752'), # check
                    ('44115001',  '5573'),
                    ('44260003', '14170'), # check
                    ('47300002', '15769'),
                    ('49360001',  '6332'),
                    ('50690001',  '6489'), # check
                    ('51800004', '15968'), # check
                    ('52400003', '16055'),
                    ('56350003',  '7038'), # check
                    ('57660001', '15228'),
                    ('59110002',  '7649'),
                    ('59223002',  '7729'),
                    ('59260001',  '7668'),
                    ('59279002', '15177'), 
                    ('59370003', '13108'),
                    ('59510002',  '7638'),
                    ('59850002',  '7707'),
                    ('60270002', '15825'),
                    ('60230003', '13639'), # check just with ids
                    ('60330003', '15321'),
                    ('60350001',  '7864'),
                    ('62250006',  '8225'),
                    ('62770001',  '8058'), # check, end of 100:200
                    ('83000007', '11280'),
                    ('83000003', '11279'),
                    ('83000002', '11276'), # pby chge in brand (small volumes..)
                    ('20137005',  '2064'),
                    ('14520003',  '1382'), # weird... check 14220001, 14520004
                    ('13123001', '14972'),
                    ('13200013', '20032'),
                    ('93200005', '12395'),
                    ('93210002', '13276'),
                    ('84200007', '20081'), # close since then
                    ('84200008', '20358'),
                    ('89100005', '13273'),
                    ('20620002',  '2010'),
                    ('20620004', '19174'),
                    ('56170003',  '7219'),
                    ('56170002',  '7217'),
                    ('20200011',  '2000'),
                    ('20200001',  '2091'),
                    ('18100002',  '1858'),
                    ('18100003',  '1859'),
                    ('49300012',  '6283'),
                    ('47300004', '15783'),
                    ('47000001', '15781'),
                    ('25210002', '14610'),
                    ('25210003',  '2693'),
                    ('49000006', '17486'),
                    ('49000008',  '6236'),
                    ('53061001',  '6819'),
                    ('53940001',  '6860'),
                    ('12400004', '14739'),
                    ('13210001',  '1203'),
                    ('13210003',  '1205'),
                    ('14700001', '15007'),
                    ('14700006',  '1307'),
                    ('20290009', '15387'),
                    ('20290008', '15385'),
                    ('20290002', '15386'),
                    ('20290006',  '2051'),
                    ('57000003',  '7348'),
                    ('35200005',  '4493'),
                    ('35205001', '14841'),
                    ('28000004', '13941'),
                    ('28000005',  '3054'),
                    ('28000002',  '3055'),
                    ('14700007',  '1305'),
                    ('51100039',  '6647'),
                    ('59114001',  '7767'),
                    ('59114003',  '7766'),
                    ('12260001',   '927'),
                    ('12260002', '19868'),
                    ('69007005',  '9215'),
                    ('20000002',  '1990'), # todo: check AJACCIO
                    ('76000001', '16873'),
                    ('76000011', '13771'),
                    ('81000004', '10902'),
                    ('81000006', '10896'),
                    ('1200001',     '14'),
                    ('1200003',     '39'),
                    ('71000019',  '9465'),
                    ('71000005', '18163'),
                    ('66000004',  '8736'),
                    ('66000005', '17190'),
                    ('92000015', '12265'),
                    ('85120004', '11471'),
                    ('17530001',  '1593'),
                    ('17530003',  '1594'),
                    ('40100005',  '5137'),
                    ('40180003',  '5247'),
                    ('13170010', '13846'),
                    ('13170008', '19274'), # following: errors found by obs
                    ('20090001',  '1989'), # not 100% sure between this and next
                    ('20090011',  '1981'),
                    ('20200002',  '2007'), # wrong address on gouv? ided by name
                    ('22100005',  '1997'),
                    ('95490004', '12693'),
                    ('76600013', '10315'),
                    ('76600002', '10306'),
                    ('66000009',  '8737'),
                    ('39700001', '20884'),
                    ('39700005',  '5091'),
                    ('73000003',  '9767'),
                    ('73000011',  '9794'),
                    ('95450003', '17460'),
                    ('95450005', '17459'),
                    ('66000016', '20721'), # not yet in zagaz data
                    ('12400005', '20967')] # not yet in zagaz data

# comes from zagaz highway matching
ls_highway_matching = [('80200010', '10791'), # A1
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
                       ('69360002', '9272' ), # A 7
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
                       ('52160006', '6738' ), # A 31
                       ('52160007', '15641'),
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
                       ('6250003',  '12788'), # A8
                       ('87280002', '13272'), # A20
                       ('62860004', '8065' ), # A26
                       ('2690001' , '234'  ),
                       ('62860005', '8221' ),
                       ('10150003', '16712'),
                       ('64210002', '8476' ), # A 63
                       ('64210001', '8477' ),
                       ('40530001', '5150' ),
                       ('40530002', '5151' ),
                       ('33610004', '15886'), # check..
                       ('33610006', '17001'),
                       ('40410004', '5229' ),
                       ('63190002', '8385' ), # A 89
                       ('63190010', '8373' ), # check if same '63190003' 
                       ('42440008', '5409' ),
                       ('42440006', '5408' ), # not 100% sure which is which
                       ('3100006' , '17434'), # A 71
                       ('3170001' , '17604'),
                       ('21250009', '2162' ), # A36
                       ('21250005', '16213'),
                       ('39700011', '5092' ),
                       ('31290003', '16015'), # A61
                       ('31290002', '3564' ),
                       ('11290002', '725'  ),
                       ('11290001', '726'  ),
                       ('85210007', '11586'), # A83
                       ('64170009', '8502' ), # A 64
                       ('64170008', '15429'),
                       ('31410003', '15494'),
                       ('31410002', '3587' ),
                       ('78630002', '13433'), # A13
                       ('78630003', '13435'),
                       ('78710003', '13434'),
                       ('78710002', '12952'),
                       ('61230001', '16080'), # A28
                       ('80140002', '10835'),
                       ('80140001', '10836'),
                       ('89190005', '12116'), # A5 (not 100%)
                       ('89190004', '12118'),
                       ('10270002', '669'  ),
                       ('10270001', '670'  ),
                       ('77130009', '13427'),
                       ('77130010', '10482'),
                       ('13320001', '979'  ), # A51
                       ('4130003',  '402'  ),
                       ('4130002',  '403'  ),
                       ('4200006',  '348'  ),
                       ('94000002', '13714'), # A86
                       ('94003001', '12462'),
                       ('94150001', '12513'), # todo: fix dum highway
                       ('94150002', '12514'),
                       ('62250004', '8201' ), # A16
                       ('12150001', '916'  ), # A75
                       ('49160003', '13087'), # A85
                       ('49160004', '13086'),
                       ('37190003', '20120'),
                       ('59242001', '14750'), # A23
                       ('59242002', '14749'),
                       ('59494008', '14752'),
                       ('59494003', '7714' ),
                       ('68390001', '8933' ), # A35
                       ('67600003', '13689'),
                       ('21130005', '2191' ), # A39
                       ('21130006', '2192' ),
                       ('73100007', '9815' ), # A41
                       ('62147001', '8159' ), # A2
                       ('62147003', '8148' ),
                       ('33520003', '3921' ), # Rocade A630
                       ('33520002', '3922' ),
                       ('33700008', '14512'), # todo: fix dum highway?
                       ('33700007', '4049' ),
                       ('33170003', '13672'),
                       ('33170004', '3967' ),
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
                       ('69360005', '9110' ),
                       ('69360004', '9109' ),
                       ('94150003', '12509'), # remainder
                       ('74570005', '9924' ),
                       ('74570002', '9922' ),
                       ('69700004', '9263' ),
                       ('69700008', '15128'),
                       ('38690002', '17384'),
                       ('26730004', '2794' ),
                       ('13011004', '13351'),
                       ('13320005', '983'  ), # not listed as hw (gov)
                       ('13180001', '13596'),
                       ('77550001', '10572'),
                       ('77550002', '10573'), # not listed as hw (gov)
                       ('81600004', '14300'),
                       ('41600003', '5263' ),
                       ('42600008', '5414' ),
                       ('42600005', '5413' ),
                       ('77410008', '14085'),
                       ('31300003', '14054'), # not listed as hw (gov)
                       ('31300004', '14826')] # not listed as hw (gov)

ls_missing_zagaz = ['62100010', # added since then: '20742
                    '56850002',
                    '6250007'] # twin stations, this one stopped

# todo: drop '56000007' (temp dup of '56000005')
# todo (NEW): drop '29910001'

dict_matching_manual = {}
dict_matching_manual['manual'] = ls_hand_matching
dict_matching_manual['manual_hw'] = ls_highway_matching

ls_rows_manual = []
for quality, ls_matches in dict_matching_manual.items():
  for gov_id, zag_id in ls_matches:
    try:
      ls_rows_manual.append([quality,
                              gov_id,
                              zag_id] +\
                             list(df_info.ix[gov_id][['adr_street',
                                                      'adr_city',
                                                      'brand_0',
                                                      'brand_1',
                                                      'lat',
                                                      'lng',
                                                      'ci_1']]) +\
                             list(df_zagaz.ix[zag_id][['street',
                                                       'municipality',
                                                       'brand_std_last',
                                                       'lat',
                                                       'lng']]))
    except:
      print gov_id, zag_id, ': gov_id no more in data? (dup?)'

df_manual = pd.DataFrame(ls_rows_manual,
                         columns = ls_columns)

df_manual['dist'] = df_manual.apply(\
                           lambda x: compute_distance(\
                                            (x['gov_lat'], x['gov_lng']),
                                            (x['zag_lat'], x['zag_lng'])), axis = 1)

# drop match previously found if existed (both gov and zag)
ls_drop_id_gov = df_manual['gov_id'].values.tolist()
df_output = df_output[~(df_output['gov_id'].isin(ls_drop_id_gov))]
ls_drop_id_zag = df_manual['zag_id'].values.tolist()
df_output = df_output[~(df_output['zag_id'].isin(ls_drop_id_zag))]
df_output = pd.concat([df_output, df_manual],
                     axis = 0)

# drop gov id not in zagaz (manual input)
df_output = df_output[~(df_output['gov_id'].isin(ls_missing_zagaz))]

# #######
# OUTPUT
# #######

print u'\nOverview output:'
print df_output[ls_ma_di_1][0:30].to_string()

# Inspect duplicates (can be only in zagaz)
se_zag_id_vc = df_output['zag_id'].value_counts()
se_zag_id_dup = se_zag_id_vc[se_zag_id_vc > 1]

# TODO: check why '83000002', '83000003' are highway?

df_duplicates = df_output.copy()
df_duplicates.set_index('zag_id', inplace = True)
# caution: diff from .ix[] which does not get all
df_duplicates = df_duplicates.loc[se_zag_id_dup.index]
df_duplicates.reset_index(inplace = True)
# might have want to be more careful before
pd.set_option('display.max_colwidth', 30)
print u'\nOverview duplicates (if any):'
if len(df_duplicates) != 0:
  print df_duplicates[ls_ma_di_1 + ['ci']][0:30].to_string()

df_output.to_csv(os.path.join(path_dir_zagaz_csv,
                              'df_zagaz_matching_1.csv'),
                 index = False,
                 encoding = 'utf-8')

# Excel output: need to get rid of potential \r and \n
for col in ['gov_street']:
  df_output[col] = df_output[col].str.replace(u'\r\n', u' ')\
                                 .str.replace(u'\r', u'')\
                                 .str.replace(u'\n', u' ')
ls_di_oexcel = ['gov_id', 'zag_id', 'gov_br_0', 'gov_br_1', 'zag_br',
                'gov_street', 'zag_street', 'gov_city', 'zag_city',
                'ci', 'quality', 'dist']
df_output[ls_di_oexcel].to_csv(os.path.join(path_dir_zagaz_csv,
                                            'csv_excel',
                                            'df_zagaz_matching_1_excel.csv'),
                               index = False,
                               encoding = 'latin-1',
                               sep = ';',
                               escapechar = '\\',
                               quoting = 1) 

## ###########
## DEPRECATED?
## ###########
# Strategy 1: within similar ZIP, compare standardized address 
#             + check on name station (print) if score is ambiguous
# Strategy 2: compare standardized string: address, ZIP, City

# Standardization: suppress '-' (?), replace ' st ' by 'saint'
# master: 26200005, 40390001 (C/C => Centre Commercial ?), 35230001, 13800007 (Av. => Avenue)
# master: 67540002 (\\ => ), 59860002 (386/388 => 386/388 (?))
# master: lack of space (not necessarily big pbm) 78120010
# check weird : 18000014, 82500001, 58240002

# loop on all zagaz stations within zip code area
# loop on all master sub-adresses vs. zagaz sub-addresses: keep best match
# produces a list with best match for each zagaz station within zip code are
# can be more than 2 components... some seem to have standard format DXXX=NXX

## Distance : gouv error: 13115001 ("big" mistake still on website)
## Correct zagaz error
#dict_zagaz_stations['14439'][7] = (dict_zagaz_stations['14439'][7][0],
#                                   str(-float(dict_zagaz_stations['14439'][7][1])),
#                                   dict_zagaz_stations['14439'][7][2]) # was fixed on zagaz already
#dict_zagaz_stations['19442'][7] = (u'46.527805',
#                                   u'5.60754',
#                                   dict_zagaz_stations['19442'][7][2]) # fixed it on zagaz
#
## Stations out of France: short term fix for GFT/GMap output
#ls_temp_matching = {'4140001'  : '20101',
#                    '33830004' : '17259',
#                    '13115001' : '20072', # included in top mistakes found upon matching
#                    '20189002' : '1980',  # from here on: Corsica
#                    '20167010' : '13213',
#                    '20118004' : '13220',
#                    '20213004' : '13600',
#                    '20213003' : '17310'}
