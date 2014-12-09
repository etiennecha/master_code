#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
import datetime
from params import *

path_dir_built_paper = os.path.join(path_data,
                                    'data_gasoline',
                                    'data_built',
                                    data_paper_folder)

path_dir_built_csv = os.path.join(path_dir_built_paper, u'data_csv')
path_dir_built_json = os.path.join(path_dir_built_paper, 'data_json')

path_dir_source = os.path.join(path_data, 'data_gasoline', 'data_source')
path_dir_other = os.path.join(path_dir_source, 'data_other')

ls_tup_duplicates = dec_json(os.path.join(path_dir_other,
                                          'ls_id_reconciliations.json'))

ls_tup_duplicates_update = [('13010002', '13010010'),
                            ('13370001', '13370005'),
                            ('16300003', '16300004'), # CM => ITM (LSA)
                            ('20200007', '20200008'),
                            ('22600001', '22600008'), # CM/HChamp => ITM (LSA)
                            ('26270001', '26270005'), # highway
                            ('29760003', '29760004'),
                            ('35560001', '35560004'),
                            ('40300001', '40300007'), # highway
                            ('42370002', '42370004'),
                            ('42440001', '42440008'), # highway
                            ('48200002', '48200006'),
                            ('51100031', '51100035'),
                            ('5600001' , '5600005' ), # check: unsure
                            ('57370005', '57370006'), # drop ? (unsure)
                            ('57370006', '57370007'), # drop ? (unsure)
                            ('59211001', '59211002'),
                            ('59492001', '59492002'), # CM => ITM (LSA)
                            ('62120002', '62120013'),  # CM => ITM (LSA)
                            ('62128003', '62128006'), # SHOPI => CarrCont (LSA)
                            ('62217004', '62217006'), # ELF => TA
                            ('62720001', '62720002'),
                            ('63190006', '63190009'),
                            ('66300005', '66300013'), # highway
                            ('73390001', '73390008'), # highway
                            ('86700002', '86700004'),
                            ('86800001', '86800005'),
                            ('91800001', '91800008'), # fix brand
                            ('94651001', '94651002'),
                            ('95330007', '95330008'),
                            ('10000002', '10000015'),
                            ('10000015', '10000016'),
                            ('10000014', '10000017'),
                            ('10260002', '10260003'),
                            ('10500003', '10500004'),
                            ('10600004', '10600008'),
                            ('12170002', '12170004'),
                            ('13004003', '13004004'),
                            ('13008012', '13008015'),
                            ('13012018', '13012021'),
                            ('13012007', '13012020'),
                            ('13014009', '13014012'),
                            ('13015015', '13015017'),
                            ('13016005', '13016006'),
                            ('13500009', '13500010'),
                            ('13590001', '13590003'),
                            ('13660003', '13660004'),
                            ('14000001', '14000015'), # fix brand (get rid of T before TA)
                            ('14000008', '14000017'),
                            ('14051002', '14051003'),
                            ('14123002', '14123006'),
                            ('14130002', '14130006'), # fix brand (get rid of T before TA)
                            ('14200007', '14200008'),
                            ('15000004', '15000015'),
                            ('15100007', '15100010'),
                            ('15110002', '15110003'),
                            ('15400001', '15400004'),
                            ('16700005', '16700006'),
                            ('17120001', '17120005'),
                            ('17670001', '17670002'),
                            ('19150001', '19150002'), # check it (gms)
                            ('19250004', '19250005'),
                            ('19800003', '19800004'),
                            ('20200003', '20200010'),
                            ('20230005', '20230009'),
                            ('20260004', '20260005'),
                            ('21000021', '21000022'),
                            ('22350002', '22350005'),
                            ('22380001', '22380002'), # check it (gms)
                            ('24100002', '24100013'),
                            ('24330002', '24330005'), # check
                            ('24430002', '24430003'),
                            ('25320002', '25000021'),
                            ('25420003', '25420004'),
                            ('25420004', '25420005'),
                            ('26200005', '26200006'),
                            ('26780001', '26780005'),
                            ('27930003', '27930007'),
                            ('28210001', '28210003'),
                            ('28240004', '28240005'),
                            ('28330001', '28330003'),
                            ('29130001', '29300006'),
                            ('29140006', '29140007'),
                            ('29280004', '29290003'),
                            ('29660001', '29660002'),
                            ('29900001', '29900005'),
                            ('30000017', '30000018'),
                            ('30100008', '30100012'),
                            ('30210005', '84140005'), # check
                            ('30240003', '30240004'),
                            ('30300002', '30300009'),
                            ('31100007', '31100009'),
                            ('31500001', '31500013'),
                            ('31200003', '31200019'),
                            ('31410005', '31410008'), # check it (gms)
                            ('31660003', '31660004'),
                            ('33000009', '33000017'), # example of chain with 3
                            ('33000017', '33000020'),
                            ('33800001', '33800002'),
                            ('33300002', '33000018'),
                            ('33130001', '33130006'), # check
                            ('33170002', '33170007'),
                            ('33290005', '33290006'),
                            ('33290006', '33290008'),
                            ('33320006', '33320007'),
                            ('33370004', '33370011'),
                            ('33370011', '33370012'),
                            ('33370010', '33370013'),
                            ('33660002', '33660003'),
                            ('33700017', '33700019'),
                            ('34140005', '34140006'),
                            ('34500019', '34500023'),
                            ('34400014', '34400016'),
                            ('34510001', '34510002'), # check
                            ('34740001', '34740003'),
                            ('35000002', '35000016'),
                            ('35320001', '35320002'),
                            ('35440001', '35440002'),
                            ('35720003', '35720004'),
                            ('35770004', '35770005'),
                            ('36230001', '36230002'),
                            ('37000008', '37000012'),
                            ('37270003', '37270006'),
                            ('37420001', '37420003'),
                            ('38000012', '38000014'),
                            ('38100006', '38100010'),
                            ('38100010', '38100011'),
                            ('38150004', '69340003'), # check (highway)
                            ('38200001', '38200017'),
                            ('38270001', '38270005'),
                            ('38290002', '38290004'),
                            ('38340009', '38340010'),
                            ('38360003', '38360005'),
                            ('38480001', '38480005'), # check (highway)
                            ('38490002', '38490006'),
                            ('38570001', '38570004'), # check (gms)
                            ('38710002', '38600002'),
                            ('38800001', '38800002'),
                            ('39130005', '39130006'), # adr de la mairie...?
                            ('39130006', '39130007'),
                            ('39140002', '39140004'), # highway
                            ('39700004', '39700010'), # check (highway)
                            ('40270002', '40270003'),
                            ('40530004', '40530005'), # check (highway, might be a mistake in brand)
                            ('41000016', '41000017'), # fix brand (get rid of T before TA)
                            ('41000017', '41000018'),
                            ('41150001', '41150003'),
                            ('41240001', '41240003'),
                            ('41360002', '41360004'), # check (gms)
                            ('42100013', '42100015'),
                            ('42100015', '42100016'),
                            ('42220002', '42220003'),
                            ('44300002', '44300014'),
                            ('44120003', '44210004'),
                            ('44240006', '44240009'),
                            ('45100002', '45100007'),
                            ('45360002', '45360005'), # check (gms)
                            ('47500004', '47500006'),
                            ('47550004', '47550006'),
                            ('49070002', '49070007'),
                            ('49110001', '49110003'),
                            ('49140002', '49140003'),
                            ('49450002', '49450006'),
                            ('50100004', '50100006'), # fix brand (getrid of T before TA)
                            ('50150003', '50150004'),
                            ('50310001', '50310002'),
                            ('51100005', '51100041'),
                            ('51100030', '51100038'),
                            ('51100038', '51100039'),
                            ('51100037', '51100040'),
                            ('51300011', '51300012'),
                            ('52160004', '52160006'), # check highway
                            ('53160001', '53160002'),
                            ('53320001', '53320002'),
                            ('54000004', '54000010'),
                            ('54360001', '54300010'),
                            ('54380002', '54380004'),
                            ('54500002', '54500006'),
                            ('54670001', '54670002'),
                            ('55000002', '55000007'),
                            ('55270001', '55270002'),
                            ('56230001', '56230005'),
                            ('56400004', '56400009'),
                            ('57070009', '57000020'),
                            ('57150003', '57150006'),
                            ('57400002', '57400009'),
                            ('57430002', '57430003'),
                            ('59000003', '59000014'),
                            ('59260005', '59000013'), # check (TA...)
                            ('59000013', '59260006'),
                            ('59100009', '59100010'),
                            ('59278002', '59278003'),
                            ('59300012', '59300014'),
                            ('59710004', '59710006'), # BP converted to TA
                            ('60000009', '60000011'),
                            ('60112001', '60112002'),
                            ('60370001', '60370002'),
                            ('60680001', '60680002'),
                            ('60750001', '60750002'),
                            ('61300005', '61300006'),
                            ('62000002', '62000011'),
                            ('62000003', '62000010'),
                            ('62118003', '62118004'),
                            ('62123002', '62123003'),
                            ('62300004', '62300010'),
                            ('62470003', '62470004'),
                            ('62560001', '62560003'),
                            ('62700006', '62700007'),
                            ('62800002', '62800003'),
                            ('62860003', '62860005'),
                            ('63430003', '63430005'),
                            ('63960003', '63960004'),
                            ('33720003', '33720007'),
                            ('57150004', '57150005'),
                            ('67130001', '67130004'),
                            ('67290001', '67290002'), # check (gms)
                            ('67700004', '67700008'),
                            ('67700007', '67700009'),
                            ('68200006', '68200016'), # get rid of T before TA
                            ('68200013', '68200017'),
                            ('68370001', '68370002'),
                            ('69002004', '69002005'),
                            ('69100019', '69100020'),
                            ('69250004', '69250007'),
                            ('69250007', '69250008'),
                            ('69410004', '69410006'),
                            ('69480004', '69480006'),
                            ('69670001', '69670002'),
                            ('69960004', '69960005'),
                            ('70300002', '70300009'),
                            ('70300007', '70300008'),
                            ('71000017', '71000019'),
                            ('71100014', '71100025'),
                            ('71200002', '71200008'),
                            ('71210005', '71210008'),
                            ('71300005', '71300010'),
                            ('71300007', '71300011'),
                            ('72000017', '72000018'),
                            ('73110001', '73110003'),
                            ('73220001', '73220002'),
                            ('74130005', '74130010'),
                            ('74300006', '74300008'),
                            ('74500006', '74500007'),
                            ('74600007', '74600011'),
                            ('74600009', '74600010'),
                            ('74910001', '74910004'),
                            ('75012004', '75012018'),
                            ('75013006', '75013021'),
                            ('75016002', '75016015'),
                            ('75016005', '75016016'), # check
                            ('76000001', '76000010'),
                            ('76000010', '76000011'),
                            ('76120003', '76120007'),
                            ('76300002', '76300007'), # check
                            ('76600018', '76600020'),
                            ('76800006', '76800008'),
                            ('77100006', '77100017'),
                            ('77100014', '77100019'),
                            ('77230003', '77230005'),
                            ('77310005', '77310007'),
                            ('77310007', '77310008'),
                            ('77410006', '77410008'),
                            ('78000002', '78000018'),
                            ('78000014', '78000016'),
                            ('78110004', '78110005'),
                            ('78150008', '78150011'),
                            ('78180007', '78180009'),
                            ('78190007', '78190009'),
                            ('78711001', '78711002'),
                            ('78300001', '78300009'),
                            ('78300007', '78300008'),
                            ('78340001', '78340004'),
                            ('78700004', '78700007'),
                            ('78700007', '78700009'),
                            ('78700005', '78700006'),
                            ('78700006', '78700008'),
                            ('79200002', '79200006'),
                            ('79260003', '79260004'),
                            ('79390002', '79390003'),
                            ('80200001', '80200010'), # check highway
                            ('80330002', '80330003'),
                            ('81250001', '81250003'),
                            ('81700001', '81700005'), # check on zagaz shopi av de revel vs. c contact lieu dit saint martin
                            ('82140002', '82140003'),
                            ('83170008', '83170010'),
                            ('83250006', '83250008'),
                            ('83260002', '83260005'),
                            ('83400007', '83400012'),
                            ('83420002', '83420004'),
                            ('83700005', '83700007'),
                            ('83720003', '83720004'),
                            ('84120002', '84120005'),
                            ('84130003', '84130008'),
                            ('85160003', '85160006'), # intermarche route de challans vs rue de la riviere in Saint Jean de Monts
                            ('85710001', '85710002'), # check LA GARNACHE
                            ('86000008', '86000023'),
                            ('86000009', '86000019'),
                            ('86000019', '86000020'),
                            ('86000016', '86000021'),
                            ('86000017', '86000022'),
                            ('86800002', '86550002'),
                            ('86580001', '86580002'),
                            ('87000005', '87000024'),
                            ('87000008', '87000025'),
                            ('87100003', '87000026'),
                            ('87140001', '87140002'),
                            ('88150002', '88150004'),
                            ('89144001', '89144002'),
                            ('89200004', '89200008'), # check AVALLON
                            ('89420002', '89420005'),
                            ('91100012', '91100013'),
                            ('91190004', '91190010'),
                            ('91150001', '91150010'),
                            ('91150002', '91150011'),
                            ('91220002', '91220003'),
                            ('91300011', '91300016'), # check BPs in Massy 117 route de palaiseau vs. Bois de la Voie de Briis
                            ('91380002', '91380009'),
                            ('91400001', '91400007'),
                            ('91430001', '91430002'),
                            ('91460003', '91460009'),
                            ('91460009', '91460011'),
                            ('91460006', '91460010'),
                            ('91540001', '91540005'), # check rn 191 vs rte de chevannes BPs in MENNECY
                            ('91550001', '91550003'), # check avia in PARAY-VIEILLE-POSTE
                            ('91570002', '91570003'),
                            ('92000004', '92000015'),
                            ('92110005', '92110009'),
                            ('92110006', '92110007'),
                            ('92140001', '92140012'), # check TA
                            ('92140006', '92140013'), # check TA
                            ('92150003', '92150005'),
                            ('92380004', '92380005'),
                            ('92400011', '92400014'),
                            ('92600005', '92600008'),
                            ('92700004', '92700016'),
                            ('92700016', '92700017'),
                            ('93100009', '93100012'),
                            ('93130001', '93130008'),
                            ('93200006', '93200007'),
                            ('93240003', '93240006'),
                            ('93260004', '93260006'),
                            ('93600012', '93600015'),
                            ('93600013', '93600014'),
                            ('93800004', '93800005'),
                            ('94100004', '94100009'),
                            ('94340004', '94340005'),
                            ('94430001', '94430006'),
                            ('95800005', '95800006'),
                            ('95230001', '95230007'), # weird back to T after TA !?
                            ('95300001', '95300003'),
                            ('95310001', '95310009'),
                            ('95320002', '95320003'),
                            ('95320003', '95320005'),
                            ('95370002', '95370006'),
                            ('95450003', '95450005'),
                            ('95740003', '95740004'),
                            ('1000005', '1000011'),
                            ('1160004', '6160007'),
                            ('2130002', '2130005'),
                            ('2130003', '2130006'),
                            ('2370002', '2370003'),
                            ('3100004', '3100011'),
                            ('5000011', '5000014'),
                            ('5000003', '5000016'),
                            ('6000024', '6000025'),
                            ('6200017', '6200022'),
                            ('6200004', '6200021'),
                            ('6200020', '6200024'),
                            ('6300004', '6300015'),
                            ('6130003', '6310001'),
                            ('6210006', '6210008'),
                            ('6500002', '6500002'),
                            ('6510002', '6510003'),
                            ('6560004', '6560004'),
                            ('6500002', '6500007'),
                            ('6560004', '6560005'),
                            ('6800003', '6800016'),
                            ('6800007', '6800015'),
                            ('7250003', '7250004'), # check
                            ('7400001', '7400003'),
                            ('8000003', '8000009'),
                            ('8360002', '8360003'),
                            ('9240001', '9240002')] # check ci_ardt_1 09042 LA BASTIDE DE SEROU

ls_tup_duplicates += ls_tup_duplicates_update

# Doubts: try to use zagaz
# 13127001, 13127003, 13127009
# insee_code 13014: likely two ESSO_EXPRESS replaced
# 13370004, 13370006
# 14700003, 14700007
# 33220002, 33220006 relocation of leclerc?
# 13790002, 13790003 highway
# 40410001 => 40410003 or 40410004 ? (highway)
# Check Clermont Ferrand: 63000021 missing TA
# 63190003, 63190010 highway unsure
# 46110003, 46110004
# get rid of 76170004?
# check MOISSAC intermarches (2) and hypermarche
# check SAINTE HERMINE: get rid of some? one station only? (highway all)
# look 94170003, 94170004

# #########################
# LOAD INFO STATIONS
# #########################

df_info = pd.read_csv(os.path.join(path_dir_built_csv,
                                   'df_station_info.csv'),
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

ls_di0 = ['name', 'adr_street', 'adr_city', 'ci_ardt_1']
ls_di1 = ls_di0 + ['start', 'end', 'brand_0', 'brand_1', 'brand_2']

ls_disp_noinfo = ['name', 'adr_street', 'adr_city', 'ci_ardt_1',
                  'start', 'end', 'brand_0', 'brand_1', 'brand_2']
print df_info[pd.isnull(df_info['name'])][ls_disp_noinfo].to_string()

# #########################
# LOAD PRICES
# #########################

df_prices_ht = pd.read_csv(os.path.join(path_dir_built_csv, 'df_prices_ht.csv'),
                        parse_dates = ['date'])
df_prices_ht.set_index('date', inplace = True)

df_prices_ttc = pd.read_csv(os.path.join(path_dir_built_csv, 'df_prices_ttc.csv'),
                        parse_dates = ['date'])
df_prices_ttc.set_index('date', inplace = True)

# ##############################
# DROP THOSE WITH NO PRICE INFO
# ##############################

df_info_bu = df_info.copy()
df_prices_ttc_bu = df_prices_ttc.copy()
df_prices_ht_bu = df_prices_ht.copy()

for id_station in df_info.index[pd.isnull(df_info['start'])]:
	if id_station in df_prices_ttc.columns:
		df_prices_ttc.drop(id_station, 1, inplace = True)
		df_prices_ht.drop(id_station, 1, inplace = True)
df_info = df_info[~pd.isnull(df_info['start'])]

# adhoc fixes
df_info.loc['51100035', 'brand_0'] = 'TOTAL_ACCESS'
df_info.loc['51100035', 'brand_1'] = np.nan
df_info.loc['51100035', 'day_1'] = np.nan
df_info.loc['60230003', 'brand_0'] = 'TOTAL_ACCESS'
df_info.loc['60230003', 'brand_1'] = np.nan
df_info.loc['60230003', 'day_1'] = np.nan

## DETECT DUPLICATES
#first_date, last_date = df_info['start'].min(), df_info['end'].max()
#
#ls_check = []
#for ci_1 in df_info['ci_1'].unique():
#  # could check cross distances within and alert if 0 here
#  df_temp = df_info[(df_info['ci_1'] == ci_1) &
#                    ((df_info['start'] != first_date) | (df_info['end'] != last_date))].copy()
#  if len(df_temp) > 1:
#    df_ee = df_temp[(df_temp['start'] == first_date) & (df_temp['end'] != last_date)]
#    df_ls = df_temp[(df_temp['start'] != first_date) & (df_temp['end'] == last_date)]
#    df_sh = df_temp[(df_temp['start'] != first_date) & (df_temp['end'] != last_date)]
#    if (len(df_temp) != len(df_ee)) and (len(df_temp) != len(df_ls)):
#        ls_check.append(ci_1)
#        print '\n', '-'*30
#        print df_temp[ls_di1].to_string()
#
#print '\nDuplicates about to be fixed:'
#for x, y in ls_tup_duplicates:
#  if x in df_info.index and y in df_info.index:
#    print x,y

# DELETE DUPLICATES (W/O LOSING INFO: EX BRAND / EX ADDRESS ?)
for x, y in ls_tup_duplicates:
  if x in df_info.index and y in df_info.index:
    # just to make sure:
    if df_info.ix[y]['start'] > df_info.ix[x]['start']:
      
      # fix prices
      date_switch = df_info.ix[y]['start']
      df_prices_ttc.loc[:date_switch-datetime.timedelta(days=1), y] =\
         df_prices_ttc.loc[:date_switch-datetime.timedelta(days=1), x]
      df_prices_ht.loc[:date_switch-datetime.timedelta(days=1), y] =\
         df_prices_ht.loc[:date_switch-datetime.timedelta(days=1), x]
      
      # drop prices
      df_prices_ttc.drop(x, axis = 1, inplace = True)
      df_prices_ht.drop(x, axis = 1, inplace = True)
      
      # TODO: fix start date + other fields not to lose info

      # fix brand (assuming weird stuffs may be possible)
      ls_tup_x = [(df_info.ix[x]['brand_%s' %i],
                   df_info.ix[x]['day_%s' %i]) for i in range(3)\
                      if not pd.isnull(df_info.ix[x]['brand_%s' %i])]
      ls_tup_y = [(df_info.ix[y]['brand_%s' %i],
                   df_info.ix[y]['day_%s' %i]) for i in range(3)\
                      if not pd.isnull(df_info.ix[y]['brand_%s' %i])]
      ls_tup_xy = ls_tup_x + ls_tup_y
      # sort on date to be sure
      ls_tup_xy = sorted(ls_tup_xy, key=lambda tup: tup[1])
      # avoid duplicate brand
      ls_tup_xy_final = [ls_tup_xy[0]]
      for tup_brand in ls_tup_xy[1:]:
        if tup_brand[0] != ls_tup_xy_final[-1][0]:
          ls_tup_xy_final.append(tup_brand)
      # add to df (will break if more than 3)
      for i, tup_brand in enumerate(ls_tup_xy_final):
        df_info.loc[y, 'brand_%s' %i] = tup_brand[0]
        df_info.loc[y, 'day_%s' %i] = tup_brand[1]
      
      # drop info
      df_info.drop(x, axis = 0, inplace = True)

# DETECT REMAINING DUPLICATES
first_date, last_date = df_info['start'].min(), df_info['end'].max()

ls_check = []
for ci_1 in df_info['ci_1'].unique():
  # could check cross distances within and alert if 0 here
  df_temp = df_info[(df_info['ci_1'] == ci_1) &
                    ((df_info['start'] != first_date) | (df_info['end'] != last_date))].copy()
  if len(df_temp) > 1:
    df_ee = df_temp[(df_temp['start'] == first_date) & (df_temp['end'] != last_date)]
    df_ls = df_temp[(df_temp['start'] != first_date) & (df_temp['end'] == last_date)]
    df_sh = df_temp[(df_temp['start'] != first_date) & (df_temp['end'] != last_date)]
    if (len(df_temp) != len(df_ee)) and (len(df_temp) != len(df_ls)):
        ls_check.append(ci_1)
        print '\n', '-'*30
        print df_temp[ls_di1].to_string()

# OUTPUT

df_info.to_csv(os.path.join(path_dir_built_csv,
                                    'df_station_info_final.csv'),
                       index_label = 'id_station',
                       float_format= '%.3f',
                       encoding = 'utf-8')

df_prices_ttc.to_csv(os.path.join(path_dir_built_csv, 'df_prices_ttc_final.csv'),
                     index_label = 'date',
                     float_format= '%.3f',
                     encoding = 'utf-8')

df_prices_ht.to_csv(os.path.join(path_dir_built_csv, 'df_prices_ht_final.csv'),
                    index_label = 'date',
                    float_format= '%.3f',
                    encoding = 'utf-8')
