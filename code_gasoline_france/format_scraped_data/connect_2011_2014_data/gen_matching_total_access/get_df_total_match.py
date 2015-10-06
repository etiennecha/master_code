#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *

path_dir_built_scraped = os.path.join(path_data,
                                      u'data_gasoline',
                                      u'data_built',
                                      u'data_scraped_2011_2014')

path_dir_built_scraped_csv = os.path.join(path_dir_built_scraped,
                                          u'data_csv')

path_dir_source_ta_csv = os.path.join(path_data,
                                      u'data_gasoline',
                                      u'data_source',
                                      u'data_total_sa',
                                      u'data_csv')

path_dir_built_ta = os.path.join(path_data,
                                 u'data_gasoline',
                                 u'data_built',
                                 u'data_total_access')

path_dir_built_ta_json = os.path.join(path_dir_built_ta, 
                                      'data_json')

path_dir_built_ta_csv = os.path.join(path_dir_built_ta, 
                                     'data_csv')

# #########################
# LOAD INFO STATIONS
# #########################

df_info = pd.read_csv(os.path.join(path_dir_built_scraped_csv,
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
                      parse_dates = [u'day_%s' %i for i in range(4)]) # fix
df_info.set_index('id_station', inplace = True)

# Exclude highway
df_info = df_info[df_info['highway'] != 1]

# Total Access in brands... but could no more be (check by concatenating)
df_info['TA'] = 0
df_info.loc[(df_info['brand_0'] == 'TOTAL_ACCESS') |\
            (df_info['brand_1'] == 'TOTAL_ACCESS') |\
            (df_info['brand_2'] == 'TOTAL_ACCESS') |\
            (df_info['brand_3'] == 'TOTAL_ACCESS'),
            'TA'] = 1
print u'\nNb Total Acces:', df_info['TA'].sum()

# Chge to Total Access recorded (improve?)
df_info['TA_chge'] = 0
for i in range(3):
  df_info.loc[(df_info['brand_%s' %i] != 'TOTAL_ACCESS') &\
              (df_info['brand_%s' %(i+1)] == 'TOTAL_ACCESS'),
              'TA_chge'] = 1
print u'\nNb chge to Total Access:', df_info['TA_chge'].sum()

print u'\nOverview some Total Access:'
ls_disp_ta = ['name', 'adr_street', 'adr_city', 'ci_ardt_1',
              'brand_0', 'brand_1', 'brand_2', 'brand_3']
print df_info[ls_disp_ta][df_info['TA'] == 1][0:10].to_string()

# ################################
# DATE CONVERSION TOTAL ACCESS
# ################################

df_total_ouv = pd.read_csv(os.path.join(path_dir_source_ta_csv,
                                    'df_total_ouv.csv'),
                          dtype = {'CP' : str,
                                   'ci_1': str,
                                   'ci_ardt_1' : str},
                          parse_dates = [u'Date'])

df_total_fer = pd.read_csv(os.path.join(path_dir_source_ta_csv,
                                    'df_total_fer.csv'),
                          dtype = {'CP' : str,
                                   'ci_1' : str,
                                   'ci_ardt_1' : str},
                          parse_dates = [u'Date ouverture', u'Date fermeture'])

df_total_fer = df_total_fer[(df_total_fer['Type station'].str.contains('total access')) |
                            (df_total_fer['Type fermeture'].str.contains('total access'))]

ls_di_fer = ['Type station', 'Type fermeture', 'Date fermeture', 'Date ouverture',
             'Station', 'Adresse', 'CP', 'Ville']

print u'\nOverview total data'
print df_total_fer[ls_di_fer][0:20].to_string()

df_info_ta = df_info[df_info['TA'] == 1].copy()

## Matching: several TA in insee area
#for ci in df_info_ta['ci_ardt_1'].unique():
#  if len(df_info_ta[df_info_ta['ci_ardt_1'] == ci]) > 1:
#    print '-'*50
#    print ci
#    print '\n', df_info_ta[['name', 'adr_street', 'adr_city', 'brand_0', 'brand_1']]\
#             [df_info_ta['ci_ardt_1'] == ci].T.to_string()
#    print '\n', df_total_fer[['Type station', 'Station', 'Adresse', 'Ville']]\
#                  [df_total_fer['ci_ardt_1'] == ci].T.to_string()

### SAGY, SANNOIS: ELF + TOTAL converted
#df_prices[['95110005', '95110001']].plot()
#df_prices[['95450003', '95450004']].plot()

## Matching: unique TA in insee area but several matches in Total file

#c = 0
#for ci in df_info_ta['ci_ardt_1'].unique():
#  if len(df_info_ta[df_info_ta['ci_ardt_1'] == ci]) == 1:
#    if len(df_total_fer[df_total_fer['ci_ardt_1'] == ci]) != 1:
#      print '-'*50
#      print ci
#      print '\n', df_info_ta[['name', 'adr_street', 'adr_city', 'brand_0', 'brand_1']]\
#               [df_info_ta['ci_ardt_1'] == ci].T.to_string()
#      print '\n', df_total_fer[['Type station', 'Station', 'Adresse', 'Ville']]\
#                    [df_total_fer['ci_ardt_1'] == ci].T.to_string()
#      c += 1


# Matching: unique TA in insee area and in Total file
ls_info_disp = ['name', 'adr_street', 'adr_city', 'brand_0', 'brand_1']

dict_ta_dates = {}
c = 0
ls_ta_unique_matches = []
for ci in df_info_ta['ci_ardt_1'].unique():
  if len(df_info_ta[df_info_ta['ci_ardt_1'] == ci]) == 1:
    # accept duplicates but assumes Station uniquely identifies
    if len(df_total_fer['Station']\
             [df_total_fer['ci_ardt_1'] == ci].drop_duplicates(['Station',
                                                                'Adresse',
                                                                'Ville'])) == 1:
      #print '-'*50
      #print ci
      #print '\n', df_info_ta[['name', 'adr_street', 'adr_city', 'brand_0', 'brand_1']]\
      #         [df_info_ta['ci_ardt_1'] == ci].T.to_string()
      #print '\n', df_total_fer[['Type station', 'Station', 'Adresse', 'Ville']]\
      #              [df_total_fer['ci_ardt_1'] == ci].T.to_string()
      c += 1
      id_gouv = df_info_ta[df_info_ta['ci_ardt_1'] == ci].index[0]
      for date in df_total_fer[df_total_fer['ci_ardt_1'] == ci]['Date ouverture'].values:
        if not pd.isnull(date):
          dict_ta_dates.setdefault(id_gouv, []).append(date)
          ls_ta_unique_matches.append([ci, 
                                       df_total_fer[df_total_fer['ci_ardt_1'] == ci]['Station'].iloc[0],
                                       id_gouv])
      # mistakes sometime...
      for date in df_total_fer[df_total_fer['ci_ardt_1'] == ci]['Date fermeture'].values:
        if not pd.isnull(date):
          dict_ta_dates.setdefault(id_gouv, []).append(date)

# Based on matching when several TA in insee area

ls_fer = [('95535', 'RELAIS SAGY 1', '95450004'),
          ('95424', 'RELAIS DU CROISILLON', '95370004'),
          ('95424', 'RELAIS MONTIGNY LES CORMEILLE S', '95370002'),
          ('95582', 'RELAIS SANNOIS GABRIEL PERI', '95110005'),
          ('95582', 'RELAIS BUTTE SANNOIS', '95110001'),
          ('95018', 'RELAIS DES IMPRESSIO NNISTES', '95100028'),
          ('95018', 'RELAIS ARGENTEUI L CHATEAUBR IANT', '95100016'),
          ('95018', 'RELAIS ARGENTEUI L', '95100027'),
          ('92026', 'RELAIS DE COURBEVOI E', '92400001'),
          ('92023', 'RELAIS CLAMART TREBIGNAU D  2', '92140006'), # 1 av..
          ('91692', 'RELAIS ORSAY LES ULIS', '91940004'), # also in ouv
          ('91552', 'RELAIS GRANDE FOLIE', '91180006'),
          ('91552', "RELAIS SAINT GERMAIN L'ARPAJON", '91290001'),
          ('91521', 'RELAIS DE RIS', '91130002'), # also in ouv
          ('91174', 'GRAND GARAGE FERAY', '91100004'),
          ('91174', 'RELAIS CORBEIL ESSONNES', '91100001'),
          ('90010', 'RELAIS DES GLACIS', '90000004'),
          ('90010', 'RELAIS BELFORT LECLERC', '90000010'),
          ('87085', 'RELAIS DU GOLF', '87000011'), # not TA in my data
          ('87085', 'RELAIS LIMOGES LECLERC STAR', '87100003'),
          ('87085', 'RELAIS LIMOGES GROSSEREI X', '87280004'),
          ('83137', 'RELAIS TOULON LA RADE', '83000001'),
          ('83137', 'RELAIS TOULON LA RODE OUEST', '83000008'),
          ('78466', 'RELAIS ORGEVAL', '78630007'), # also in ouv, other too recent
          ('77152', 'RELAIS DAMMARIE LES LYS', '77190002'),
          ('77152', 'RELAIS DAMMARIE LECLERC', '77190001'),
          ('76351', 'RELAIS ROUELLES', '76610001'), # not TA in my data
          ('76351', 'RELAIS AMIRAL MOUCHEZ', '76600017'),
          ('76351', 'RELAIS DU PERREY', '76600013'),
          ('73065', 'RELAIS REVERIAZ', '73000004'),
          ('73065', 'RELAIS LE BOURGET CHAMBERY', '73000003'),
          ('71270', 'RELAIS MACON ED HERRIOT', '71000002'),
          ('69290', 'RELAIS ST PRIEST MI PLAINE', '69800003'),
          ('69290', 'RELAIS ST PRIEST LES BRIGOUDES', '69800011'),
          ('69290', 'RELAIS ST HUBERT', '69800004'),
          ('69290', 'RELAIS ST PRIEST SAYTHE', '69800002'),
          ('69388', 'RELAIS LYON BERLIET', '69008005'),
          ('69388', 'RELAIS LYON MERMOZ', '69008006'),
          ('69387', 'RELAIS TONY GARNIER', '69007001'),
          ('69387', 'relais de Gerland', '69007004'),
          ('68224', 'RELAIS DE DORNACH', '68200007'),
          ('68224', 'RELAIS DES COTEAUX', '68200006'),
          ('63113', 'RELAIS CLERMONT- FERRAND LAVOISIER', '63000020'),
          ('63113', 'RELAIS CHAMPRAD ET', '63000006'),
          ('63113', 'RELAIS DU BREZET', '63100006'),
          ('59560', 'SA GARAGE WACRENIER', '59474001'),
          ('54304', 'RELAIS BEAUREGA RD', '54520003'),
          ('54304', 'RELAIS DE LAXOU', '54520005'),
          ('54547', 'RELAIS DE BRABOIS', '54500002'),
          ('53130', 'RELAIS LAVAL TRAPPISTIN ES', '53000001'),
          ('53130', 'RELAIS LA CLOSERIE', '53000002'),
          ('51454', 'RELAIS DU ROUILLAT', '51100014'),
          ('51454', 'RELAIS DES CHATILLON S', '51100032'),
          ('50129', 'RELAIS CHERBOUR G LES BASSINS', '50100005'),
          ('50129', 'RELAIS CHERBOUR G LEMONNIER', '50100004'),
          ('49007', 'RELAIS BAUMETTES B', '49000008'),
          ('45234', 'RELAIS DU CEDRE', '45000001'),
          ('45903', 'RELAIS ORLEANS LA SOURCE', '45100002'),
          ('44035', 'RELAIS JONELIERE', '44240006'),
          ('44035', 'RELAIS LA CHAPELLE SUR ERDRE', '44240008'),
          ('42218', 'RELAIS ST ETIENNE MASSENET', '42000002'),
          ('42218', 'RELAIS 5 CHEMINS ST ETIENNE', '42100014'), # not TA in my data
          ('42218', 'RELAIS SAINT ETIENNE TARENTAIZ E', '42000013'),
          ('39462', 'RELAIS DU POIRIER 2', '39700005'),
          ('39462', 'RELAIS DU POIRIER', '39700001'),
          ('38565', 'RELAIS DE LA ROIZE', '38340003'),
          ('35288', 'RELAIS ST MALO OUEST PETIT COTE', '35132001'),
          ('35288', 'RELAIS ST MALO EST - GD COTE', '35400005'),
          ('35238', 'RELAIS BARRE THOMAS', '35000009'), # not TA in my data
          ('35238', 'RELAIS RENNES ALMA', '35000002'), # not TA in my data, active?
          ('35238', 'RELAIS RENNES ALMA COCO CODO X DODO COM DODO', '35000002'), # DUP!
          ('35238', 'RELAIS MALIFEU', '35000001'),
          ('35238', 'RELAIS RENNES HIPPODROM E', '35000003'),
          ('35238', 'RELAIS RENNES ROUTE DE NANTES', '35200006'),
          ('34032', 'RELAIS LES ARENES', '34500001'), # not TA in my data
          ('34172', 'RELAIS MONTPELLI ER CLUB', '34070009'),
          ('34172', 'RELAIS MONTPELLI ER VANIERES', '34000002'),
          ('33281', 'RELAIS MERIGNAC', '33700003'),
          ('33535', 'SARL PATACHON', '33370002'),
          ('33535', 'RELAIS TRESSES STAR', '33370004'),
          ('33063', 'RELAIS DE TOURATTE', '33000003'),
          ('33063', 'RELAIS GRAND PARC', '33300002'), # not TA in my data
          ('31069', 'RELAIS BLAGNAC ROCADE', '31700002'),
          ('31069', 'RELAIS BLAGNAC LOMAGNE', '31700003'),
          ('31555', 'RELAIS DE LA PIMPE', '31200011'),
          ('31555', 'RELAIS ROSERAIE', '31000002'),
          ('31555', 'RELAIS LE MIRAIL', '31100007'),
          ('29019', 'RELAIS BREST EUROPE', '29200003'),
          ('29019', 'RELAIS DE KERANROY', '29200011'),
          ('29232', 'RELAIS QUIMPER CENTRE', '29000003'),
          ('29232', 'RELAIS QUIMPER ROCADE SUD', '29000010'),
          ('28405', 'RELAIS DU BOIS DE  VERT', '28500003'),
          ('28085', 'RELAIS CHARTRES MERMOZ', '28000008'),
          ('28085', 'Relais Beaumonts', '28000004'),
          ('26362', 'RELAIS EPERVIERE', '26000003'),
          ('26362', 'relais valence dame blanche', '26000006'), # not TA in my data
          ('19031', 'RELAIS DE VIALMUR', '19000007'),
          ('19031', 'RELAIS BRIVE SEMARD', '19100002'),
          ('18033', 'RELAIS BOURGES AVENIR', '18000013'),
          ('18033', 'RELAIS  BOURGES CAMPING', '18000008'),
          ('17306', 'RELAIS DE ROYAN', '17200002'),
          ('17291', 'RELAIS DE PUILBOREA U', '17138004'),
          ('17291', 'RELAIS DE BEAULIEU', '17138005'),
          ('14118', 'RELAIS ROUEN COTE DE NACRE', '14000001'),
          ('13039', 'RELAIS FOS SUR MER', '13270001'),
          ('13039', 'RELAIS DU VENTILLON', '13270002'),
          ('13039', 'RELAIS MARRONED E', '13270009'),
          ('13001', 'RELAIS AIX EN PR.GAMBET TA', '13100001'),
          ('13001', 'RELAIS DE GALICE', '13100003'),
          ('13001', 'RELAIS DES THERMES', '13100002'),
          ('13001', 'RELAIS DES MILLES', '13100004'),
          ('13001', 'RELAIS PLATRIERE S', '13090014'),
          ('10387', 'RELAIS TROYES POMPIDOU', '10000001')]

ls_ouv = [('95018', 'RELAIS ARGENTEUIL BALMONT', '11/05/2012', '95100002'),
          ('92026', 'RELAIS COURBEVOIE VERDUN', '11/06/2012', '92400007'),
          ('92023', 'RELAIS CLAMART TREBIGNAUD', '24/05/2012', '92140001'),
          ('91692', 'RELAIS ORSAY LES ULIS 2', '22/06/2012', '91940004'),
          ('91692', 'RELAIS ORSAY LES ULIS 1 COURTABOEUF', '08/06/2012', '91940001'),
          ('91521', 'RELAIS DE RIS', '12/11/2012', '91130002'),
          ('91521', 'RELAIS RIS-ORANGIS LIBERATION', '16/04/2012', '91130005'),
          ('90010', 'RELAIS DES GRANDS PRES', '07/05/2012', '90000008'),
          ('86062', 'SARL ROCADE DU FUTUR', '21/01/2013', '86360004'),
          ('86062', 'SARL M ET F CHEBBABI', '01/01/2013', '86360003'),
          ('73065', 'RELAIS CHAMBERY', '13/11/2012', '73000011'),
          ('71270', 'RELAIS CONDEMINES', '24/03/2012', '71000007'),
          ('54547', 'RELAIS  VANDOEUVRE', '30/06/2012', '54500003'),
          ('51454', 'RELAIS CHAMPENOISE', '06/04/2012', '51100005'),
          ('51454', 'RELAIS REIMS BREBANT', '10/03/2012', '51100035'),
          ('38565', 'RELAIS DES BALMES', '12/06/2012', '38340007'),
          ('34032', "RELAIS L'HORT MONSEIGNEUR", '21/12/2012', '34500016'),
          ('34032', 'RELAIS TOTAL DEVEZE', '09/04/2012', '34500020'),
          ('33281', 'RELAIS AQUITAINE', '10/12/2012', '33700008'),
          ('33063', 'RELAIS RAVEZIES', '21/12/2012', '33300004'),
          ('29019', 'ATELIERS CAUGANT SA', '18/10/2012', '29200004'),
          ('26362', 'RELAIS PETIT ROUSSET', '13/06/2012', '26000004'),
          ('10387', 'RELAIS TROYES MAISONNEUVE', '17/03/2012', '10000014')]

# Based on matching when one TA in insee area with several matches in Total file

ls_fer_2 = [('01053', 'RELAIS BOURG', '1000010'),
            ('01503', 'relais bourg', '1000010'), # same but maj
            ('13125', 'RELAIS MISTRAL', '13015014'),
            ('02691', 'POREZ AUTO LOCA STATION', '2100011'),
            ('30189', 'RELAIS NIMES AGEL', '30900012'),
            ('31433', 'RELAIS DU PORTET EST', '31120004'),
            ('37050', 'RELAIS LES RENARDIER ES', '37170001'),
            ('44109', 'RELAIS NANTES LE TERTRE', '44100002'),
            ('59009', "RELAIS VILLENEUVE D'ASCQ", '59650003'),
            ('61001', 'RELAIS ST BLAISE', '61000007'), #same but space
            ('61001', 'RELAIS ST  BLAISE', '61000007'),
            ('06088', 'RELAIS STE MARGUERIT E GRENOBLE', '6200018'),
            ('67482', 'RELAIS DU RHIN', '67000022'),
            ('72181', 'RELAIS LE MANS BOLLEE', '72000004'),
            ('79081', 'RELAIS NIORT CHAURAY', '79180001'),
            ('79801', 'RELAIS NIORT', '79180001'), # same address
            ('84007', 'RELAIS MONTFAVET LA DURANCE', '84140004'),
            ('91377', 'RELAIS MASSY LECLERC', '91300015'),
            ('92050', 'RELAIS NANTERRE', '92000001'),
            ('94028', 'RELAIS DE POMPADOU R', '94000003')]

# Following may essentially be obtained by matching with df_ouv...
ls_ouv_2 = [('10362', 'RELAIS SAINTE SAVINE', '04/06/2012', '10300004'),
            ('13071', 'RELAIS MIRABEAU', '30/11/2012', '13170009'),
            ('16015', 'RELAIS ANGOULEME SILLAC STAR', '16/04/2012', '16000001'),
            ('21278', 'RELAIS ALLOBROGES', '10/03/2012', '21121006'),
            ('21617', 'RELAIS LOGIS BOURGOGNE', '06/07/2012', '21240001'),
            ('02722', 'RELAIS  STE EUGENIE', '15/12/2011', '2200002'),
            ('26004', 'RELAIS LA BAYANNE', '12/06/2012', '26300002'),
            ('26085', 'RELAIS DE LA GIRANE', '20/07/2012', '26780003'),
            ('30007', 'RELAIS BRUEGES', '08/03/2013', '30100006'),
            ('31044', 'RELAIS BALMA AV DE TOULOUSE', '24/04/2012', '31130006'),
            ('33192', 'RELAIS DE GRADIGNAN DE GAULLE', '27/04/2012', '33170006'),
            ('33529', 'RELAIS LA TESTE', '22/04/2013', '33260009'), # two dates
            ('33322', 'M. HADJADJ', '01/12/2012', '33290001'),
            ('33056', 'RELAIS DE LA RENNEY', '02/04/2012', '33290005'),
            ('33162', 'RELAIS EYSINES STAR', '12/04/2012', '33320006'),
            ('34301', 'RELAIS DU TRIOLET', '24/04/2012', '34200004'),
            ('34192', 'RELAIS 4 CANAUX', '18/04/2012', '34250001'),
            ('37261', 'RELAIS TOURS', '17/12/2012', '37100004'),
            ('40192', 'RELAIS MARSAN CLEMENCEAU', '18/05/2012', '40000009'),
            ('43157', 'RELAIS DU PUY', '04/05/2012', '43000007'),
            ('45312', 'RELAIS SOLTERRE LA COMMODITE', '13/08/2012', '45200002'),
            ('45194', 'RELAIS DE MARDIE', '03/04/2012', '45430002'),
            ('51545', 'RELAIS DES CRAYERES', '23/03/2012', '51320002'),
            ('54498', 'RELAIS SEICHAMPS', '03/03/2012', '54280002'),
            ('57463', 'RELAIS PORT MAZEROLLES', '19/03/2012', '57000004'),
            ('59350', 'RELAIS LILLE DOREZ', '30/03/2012', '59000001'),
            ('59288', 'RELAIS HAULCHIN CX STE MARIE', '09/05/2012', '59121001'),
            ('59299', 'RELAIS TROIS BAUDETS', '20/07/2012', '59510002'),
            ('59488', 'RELAIS DE LAXOU', '29/05/2012', '59554004'),
            ('60139', 'RELAIS NEFLIER', '30/11/2012', '60230003'),
            ('60500', 'RELAIS DES IRIS', '07/11/2011', '60330003'), # ambig on address, same date
            ('62643', "RELAIS D'OUTREAU", '17/03/2012', '62230002'),
            ('62355', 'RELAIS FRESNES LES MONTAUBAN', '04/06/2012', '62490001'),
            ('63178', 'RELAIS DU STADE', '23/04/2012', '63500003'),
            ('64445', 'RELAIS DE LA COUETTE', '26/05/2012', '64000004'),
            ('64399', 'RELAIS BIZANOS STAR', '24/05/2012', '64320001'),
            ('67520', 'RELAIS  DE WASSELONNE', '09/06/2012', '67310001'),
            ('67462', 'RELAIS SELESTAT GIESSEN', '24/04/2012', '67600002'),
            ('68297', 'RELAIS DES 3 FRONTIERES', '06/03/2012', '68300001'),
            ('69291', "RELAIS DE L'OZON", '11/01/2012', '69360003'),
            ('69264', 'RELAIS DE LA CALADE', '07/12/2012', '69400012'),
            ('71591', 'EURL PHILIPPE GOUPIL', '01/12/2012', '71260005'),
            ('75113', 'RELAIS VINCENT AURIOL', '14/02/2012', '75013015'),
            ('76533', 'RELAIS DE ROGERVILLE', '03/03/2012', '76700002'),
            ('76575', 'RELAIS CANADIENS', '05/04/2013', '76800006'),
            ('77131', 'RELAIS COULOMMIERS', '23/05/2012', '77120002'),
            ('77053', "RELAIS DE L'YERRES",  '28/12/2011', '77170001'),
            ('77053', "RELAIS ELF DE L'YERRES", '22/12/2011', '77170001'), # almost DUP
            ('77363', 'RELAIS DU PIN', '30/04/2012', '77181001'),
            ('77392', 'RELAIS DE CHANTEMERLE', '27/03/2012', '77230002'),
            ('77407', 'RELAIS MAISON ROUGE', '16/04/2012', '77310005'),
            ('77285', 'RELAIS LA MEE SUR SEINE COURTILLE', '10/04/2012', '77350001'),
            ('78440', 'RELAIS BOUGIMONTS', '04/05/2012', '78130010'),
            ('78524', 'RELAIS DE ROCQUENCOURT', '03/10/2011', '78150001'),
            ('78217', 'RELAIS DE LA MAULDRE', '05/12/2011', '78680003'),
            ('78208', 'RELAIS ELANCOURT', '23/03/2012', '78990001'),
            ('83061', 'RELAIS FREJUS PROVENCE', '23/11/2012', '83600017'),
            ('86194', 'RELAIS TOTAL DE LA BUGELLERIE', '19/10/2012', '86000005'),
            ('88429', 'RELAIS PTE HTES VOSGES', '19/10/2012', '88200004'),
            ('88321', 'RELAIS DES CAPUCINES', '30/04/2012', '88300002'),
            ('89013', 'RELAI ELF APOIGNY', '09/01/2012', '89380002'),
            ('91201', 'RELAIS DRAVEIL DE GAULLE', '25/05/2012', '91210005'),
            ('91216', 'RELAIS EPINAY SUR ORGE', '25/05/2012', '91360001'),
            ('91047', 'RELAIS MOULIN DU GUE', '25/05/2012', '91590008'),
            ('92036', 'RELAIS BONNEQUINS', '03/10/2011', '92230002'),
            ('93050', 'RELAIS NEUILLY SUR MARNE', '25/04/2012', '93330002'),
            ('93078', 'RELAIS DES CARREAUX', '26/10/2012', '93420006'),
            ('93055', 'RELAIS PANTIN LECLERC', '17/12/2012', '93500006'),
            ('94054', 'RELAIS RUNGIS LINDGERGH', '23/11/2012', '94588001'),
            ('95280', 'RELAIS GOUSSAINVILLE A.SARRAUT', '21/04/2012', '95190001'),
            ('95680', 'RELAIS VILLIERS LE BEL LES ERABLES', '13/04/2012', '95400002')]

# Generally: no TA yet in my data... hence enlarge period to include
ls_lo_match = [('94060', 'LA QUEUE EN BRIE-EURO', '94510001'), # not TA in my data
               ('30189', 'RELAIS KM DELTA', '30900009'), # not TA in my data
               ('60159', 'RELAIS COMPIEGNE', '60200010'),
               ('59034', 'NEW STATION', '59710004'), # still BP in my data
               ('83123', 'RELAIS SANARY S/MER BEAUCOUR S', '83110001'),
               ('37261', 'RELAIS SANITAS', '37000001'),
               ('41295', 'RELAIS VINEUIL DENIS PAPIN 1', '41350004'), # unambiguous?
               ('39300', 'RELAIS DU LEVANT', '39000006'),
               ('14220', 'MENNETRIE R SCES AUTO SA/GGE RENAULT', '14800001'),
               ('56148', 'RELAIS DE NOSTANG', '56690003'), # TA, not matched cuz highway?
               ('59278', "RELAIS D'HALLENN ES", '59320002'),
               ('72181', "RELAIS DU BOL D'OR", '72100007'),
               ('17415', "RELAIS LA PALUE", '17100003'),
               ('14514', 'RELAIS AMIRAL HAMELIN', '14130002')]

# #########################
# EXPLOIT MATCHING
# #########################

# Inspect results

# One to one: wrong matching Pierrefite sur seine

for ci, name_ta, id_gouv in ls_fer + ls_fer_2:
  ar_dates = df_total_fer['Date fermeture'][(df_total_fer['ci_ardt_1'] == ci) &\
                                            (df_total_fer['Station'] == name_ta)]
  for date in ar_dates:
    if not pd.isnull(date):
      dict_ta_dates.setdefault(id_gouv, []).append(date)

for ci, name_ta_ouv, str_date, id_gouv in ls_ouv + ls_ouv_2:
  date = pd.to_datetime(str_date, format = '%d/%m/%Y')
  if not pd.isnull(date):
    dict_ta_dates.setdefault(id_gouv, []).append(date)

print u'\nNb TAs from gouv not matched:'
df_info_ta['id_gouv'] = df_info_ta.index
print len(df_info_ta[~(df_info_ta['id_gouv'].isin(dict_ta_dates.keys()))])

def disp_date(some_date):
  try:
    return pd.to_datetime(some_date).strftime('%Y%m%d')
  except:
    return u''

ls_disp_info_ta = ['ci_ardt_1', 'name', 'adr_street', 'adr_city',
                   'day_0', 'brand_0', 'day_1', 'brand_1',
                   'day_2', 'brand_2', 'day_3', 'brand_3']

dict_formatters = dict([('start', disp_date), ('end', disp_date)] +\
                         [('day_%s' %i, disp_date) for i in range(4)])

print u'\nOverview TAs (from gouv) not matched:'
print df_info_ta[ls_disp_info_ta[:-4]]\
                [~(df_info_ta['id_gouv'].isin(dict_ta_dates.keys()))][0:30]\
                  .to_string(formatters = dict_formatters)

print u'\nInspect TAs (from Total) in Marseille in df_total_fer:'
print df_total_fer[['Type station', 'Station', 'Adresse', 'Ville', 'ci_1']]\
        [df_total_fer['Ville'].str.contains('Marseille', case = False)].to_string()

ls_pbm = [('13215', 'RELAIS MISTRAL', '13015014')] # why not matched?

## inspect (check in df_total_ouv?)
# df_total_fer[df_total_fer['ci_ardt_1'] == '10387']

## Check those not matched in df_total_fer and remaining in df_info
#df_lo = df_total_fer.copy()
#for row in ls_fer + ls_fer_2 + ls_ta_unique_matches:
#  df_lo = df_lo[~((df_lo['ci_ardt_1'] == row[0]) &\
#                  (df_lo['Station'] == row[1]))]
#

# Sort dates and check nb of dates per station
dict_nb_dates = {}
for id_station, ls_dates in dict_ta_dates.items():
  ls_dates.sort()
  dict_nb_dates.setdefault(len(ls_dates), []).append(id_station)

print u'\nNb of dates obtained by TA station:'
for k, v in dict_nb_dates.items():
  print k, len(v)

dict_ta_dates_str = {k: [pd.to_datetime(str(x)).strftime('%d/%m/%Y')\
                           for x in v] for k, v in dict_ta_dates.items()}

enc_json(dict_ta_dates_str,
         os.path.join(path_dir_built_ta_json,
                      'dict_ta_dates_str.json'))

### #####################################
### POLICY PRICE CHANGE
### #####################################
##
##df_info['pp_chge'] = df_margin_chge['value']
##df_info['pp_chge_date'] = df_margin_chge['date']
### check chge in policy not TA
##df_info = pd.merge(df_info, df_ta,
##                   left_index = True, right_index = True, how = 'left')
##ls_disp = ['name', 'adr_city', 'adr_dpt', 'brand_0', 'brand_1', 'brand_2',
##           'pp_chge_date', 'id_cl_ta_0', 'dist_cl_ta_0']
##print '\nMargin chge not Total Access:'
##print df_info[ls_disp][(df_info['pp_chge'].abs() >= 0.04) &\
##                       (df_info['TA'] != 1)].to_string()
### Not TA => Gvt announces?
##ax = df_prices[['93420001', '93420006']].plot()
##ax.axvline(x = pd.to_datetime('2012-10-15'), color = 'k', ls = 'dashed')
##ax.axvline(x = pd.to_datetime('2012-10-26'), color = 'k', ls = 'dashed')
##df_prices.mean(1).plot(ax = ax)
##plt.show()
#
## UPDATE DF TA WITH TOTAL AND MARGIN CHGE DATE IF PRESENT
#
#df_info_ta['pp_chge'] = df_margin_chge['value']
#df_info_ta['pp_chge_date'] = df_margin_chge['date']
#
#df_info_ta['ta_chge_date'] = np.datetime64()
#for id_station, ls_dates in dict_ta_dates.items():
#  if id_station in df_info_ta.index:
#    df_info_ta.loc[id_station, 'ta_chge_date'] = max(ls_dates)
#  else:
#    print id_station, 'not in df_info_ta'

## ###############
## OUTPUT
## ################
#
#df_info_ta.to_csv(os.path.join(path_dir_built_csv,
#                               'df_info_ta.csv'),
#                               encoding = 'utf-8')



## ################
## GRAPH INSPECTION
## ################
#
## date on gvt website (always if change)
## date of price policy change (can separate small or beginning/end vs. significant)
## date of chge in my data (unsure if correct but check!)
#
#id_station = df_info_ta.index[0]
#pp_chge_date = df_info_ta['pp_chge_date'].iloc[0]
#ta_chge_date = df_info_ta['ta_chge_date'].iloc[0]
#
#for row_ind, row in df_info_ta.iterrows():
#  id_station = row_ind
#  pp_chge_date = row['pp_chge_date']
#  ta_chge_date = row['ta_chge_date']
#  plt.rcParams['figure.figsize'] = 16, 6
#  ax = df_prices[id_station].plot()
#  se_mean_prices.plot(ax=ax)
#  handles, labels = ax.get_legend_handles_labels()
#  ax.legend(handles, [id_station, u'mean price'], loc = 1)
#  ax.axvline(x = pp_chge_date, color = 'b', ls = 'dashed')
#  ax.axvline(x = ta_chge_date, color = 'r', ls = 'dashed')
#  #plt.ylim(plt.ylim()[0]-0.5, plt.ylim()[1])
#  #print ax.get_position()
#  #ax.set_position((0.125, 0.2, 0.8, 0.7))
#  
#  footnote_text = '\n'.join([row['name'], row['adr_street'], row['adr_city'], row['ci_ardt_1']])
#  plt.figtext(0.1, -0.1, footnote_text) 
#  # plt.text(.02, .02, footnote_text)
#  # plt.tight_layout()
#  # plt.show()
#  if pd.isnull(ta_chge_date):
#    plt.savefig(os.path.join(path_dir_built_graphs,
#                             'total_access_price_series',
#                             'notadate_%s' %id_station), dpi = 200, bbox_inches='tight')
#  else:
#    plt.savefig(os.path.join(path_dir_built_graphs,
#                             'total_access_price_series',
#                             '%s' %id_station), dpi = 200, bbox_inches='tight')
#  plt.close()
