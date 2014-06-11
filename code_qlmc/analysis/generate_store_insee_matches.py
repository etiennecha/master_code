#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
import os, sys
import json

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

ls_match = [[[u'SYSTEME U', u'BARALLE MARQUION'], ['BARALLE', '62860', 'PAS DE CALAIS', '62081']],
            [[u'E.LECLERC', u'MARLY'], ['MARLY', '57155', 'MOSELLE', '57447']],
            [[u'CORA', u'MASSY'], ['MASSY', '91300', 'ESSONNE', '91377']],
            [[u'AUCHAN', u'LE PONTET'], ['LE PONTET', '84130', 'VAUCLUSE', '84092']],
            [[u'GEANT', u'FONTAINE'], ['FONTAINE', '38600', 'ISERE', '38169']],
            [[u'GEANT', u'ST MARTIN DES CHAMPS'], ['ST MARTIN DES CHAMPS', '29600', 'FINISTERE', '29254']],
            [[u'CORA', u'STE MARGUERITE'], ['STE MARGUERITE', '88100', 'VOSGES', '88424']],
            [[u'CARREFOUR', u'PUGET SUR ARGENS CEDEX'], ['PUGET SUR ARGENS', '83480', 'VAR', '83099']],
            [[u'E.LECLERC', u'OLIVET'], ['OLIVET', '45160', 'LOIRET', '45232']],
            [[u'SYSTEME U', u'VERNOUILLET'], ['VERNOUILLET', '28500', 'EURE ET LOIR', '28404']],
            [[u'SYSTEME U', u'MONTBRISON'], ['MONTBRISON', '42600', 'LOIRE', '42147']],
            [[u'SYSTEME U', u'LES ARCS'], ['LES ARCS', '83460', 'VAR', '83004']],
            [[u'CARREFOUR', u'MONT SAINT AIGNAN'],['MONT ST AIGNAN', '76130', 'SEINE MARITIME', '76451']],
            [[u'CORA', u'PACE'], ['PACE', '35740', 'ILLE ET VILAINE', '35210']],
            [[u'GEANT', u'CHAMPNIERS'], ['CHAMPNIERS', '16430', 'CHARENTE', '16078']],
            [[u'AUCHAN', u'BIAS'], ['BIAS', '47300', 'LOT ET GARONNE', '47027']],
            [[u'CHAMPION', u'VERNON'], ['VERNON', '27200', 'EURE', '27681']],
            [[u'E.LECLERC', u'VALENCE'], ['VALENCE', '26000', 'DROME', '26362']],
            [[u'CORA', u'VERDUN'], ['VERDUN', '55100', 'MEUSE', '55545']],
            [[u'E.LECLERC', u'BOIS D ARCY'], ['BOIS D ARCY', '78390', 'YVELINES', '78073']],
            [[u'GEANT', u'AMILLY'], ['AMILLY', '45200', 'LOIRET', '45004']],
            [[u'INTERMARCHE', u'AMILLY'], ['AMILLY', '45200', 'LOIRET', '45004']],
            [[u'INTERMARCHE', u'ST CYPRIEN'], ['ST CYPRIEN', '42160', 'LOIRE', '42211']],
            [[u'E.LECLERC', u'VERDUN'], ['VERDUN', '55100', 'MEUSE', '55545']],
            [[u'SYSTEME U', u'LA MONTAGNE'], ['LA MONTAGNE', '44620', 'LOIRE ATLANTIQUE', '44101']],
            [[u'AUCHAN', u'BORDEAUX'], ['BORDEAUX', '33000', 'GIRONDE', '33063']],
            [[u'E.LECLERC', u'MARGON'], ['MARGON', '28400', 'EURE ET LOIR', '28236']],
            [[u'SYSTEME U', u'BASSENS'], ['BASSENS', '33530', 'GIRONDE', '33032']],
            [[u'E.LECLERC', u'ST GREGOIRE'], ['ST GREGOIRE', '35760', 'ILLE ET VILAINE', '35278']],
            [[u'AUCHAN', u'EPAGNY'], ['EPAGNY', '74330', 'HAUTE SAVOIE', '74112']],
            [[u'E.LECLERC', u'PRADINES'], ['PRADINES', '46090', 'LOT', '46224']],
            [[u'CHAMPION', u'ROCHEFORT'], ['ROCHEFORT', '17300', 'CHARENTE MARITIME', '17299']],
            [[u'SYSTEME U', u'CHATEAUBOURG'], ['CHATEAUBOURG', '35220', 'ILLE ET VILAINE', '35068']],
            [[u'CORA', u'ST MAXIMIN'], ['ST MAXIMIN', '60740', 'OISE', '60589']],
            [[u'CHAMPION', u'BRETEUIL'], ['BRETEUIL', '60120', 'OISE', '60104']], # second period
            [[u'INTERMARCHE', u'GIGNAC'], ['GIGNAC', '34150', 'HERAULT', '34114']],
            [[u'SUPER U', u'BOMPAS'], ['BOMPAS', '66430', 'PYRENEES ORIENTALES', '66021']],
            [[u'CENTRE E. LECLERC', u'ST ETIENNE FONTBELLON'], ['ST ETIENNE DE FONTBELLON', '07200', 'ARDECHE', '07231']],
            [[u'SUPER U', u'CRAON'], ['CRAON', '53400', 'MAYENNE', '53084']],
            [[u'SUPER U', u'DANNEMARIE'], ['DANNEMARIE', '68210', 'HAUT RHIN', '68068']],
            [[u'CENTRE E. LECLERC', u'BUXEROLLES'], ['BUXEROLLES', '86180', 'VIENNE', '86041']],
            [[u'AUCHAN', u'VILLARS'], ['VILLARS', '42390', 'LOIRE', '42330']],
            [[u'SUPER U', u'MARSEILLE RUE TADDEI'], ['MARSEILLE', '13000', 'BOUCHES DU RHONE', '13055']],
            [[u'CORA', u'LEMPDES'], ['LEMPDES', '63370', 'PUY DE DOME', '63193']],
            [[u'INTERMARCHE', u'LA CHARIT\xc9 SUR LOIRE'], ['LA CHARITE SUR LOIRE', '58400', 'NIEVRE', '58059']],
            [[u'CHAMPION', u'BOIS GUILLAUME AV EUROPE'], ['BOIS GUILLAUME', '76230', 'SEINE MARITIME', '76108']],
            [[u'CHAMPION', u'MOUTIERS TARENTAISE'], ['MOUTIERS', '73600', 'SAVOIE', '73181']],
            [[u'CENTRE E. LECLERC', u'ACHERES'], ['ACHERES', '78260', 'YVELINES', '78005']],
            [[u'CENTRE E. LECLERC', u'MONTDIDIER'], ['MONTDIDIER', '80500', 'SOMME', '80561']],
            [[u'GEANT CASINO', u'ST GREGOIRE'], ['ST GREGOIRE', '35760', 'ILLE ET VILAINE', '35278']],
            [[u'AUCHAN', u'TOURS NORD'], ['TOURS', '37000', 'INDRE ET LOIRE', '37261']],
            [[u'CARREFOUR', u'CHALON S. SAONE CC CHALON SUD'], ['CHALON SUR SAONE', '71100', 'SAONE ET LOIRE', '71076']],
            [[u'AUCHAN', u'CLAMECY'], ['CLAMECY', '58500', 'NIEVRE', '58079']],
            [[u'CENTRE E. LECLERC', u'PERPIGNAN LANGUEDOC'], ['PERPIGNAN', '66000', 'PYRENEES ORIENTALES', '66136']],
            [[u'AUCHAN', u'FAYET'], ['FAYET', '02100', 'AISNE', '02303']],
            [[u'CENTRE E. LECLERC', u'NORMANVILLE'], ['NORMANVILLE', '27930', 'EURE', '27439']],
            [[u'HYPER U', u'VERNOUILLET'], ['VERNOUILLET', '28500', 'EURE ET LOIR', '28404']], # duplicate SYSTEME U?
            [[u'AUCHAN', u'BLOIS VINEUIL'], ['VINEUIL', '41350', 'LOIR ET CHER', '41295']],
            [[u'CARREFOUR', u'BASSENS'], ['BASSENS', '73000', 'SAVOIE', '73031']],
            [[u'AUCHAN', u'MAUREPAS'], ['MAUREPAS', '78310', 'YVELINES', '78383']],
            [[u'CARREFOUR', u'NICE N202'], ['NICE', '06000', 'ALPES MARITIMES', '06088']],
            [[u'CENTRE E. LECLERC', u'LES ANGLES'], ['LES ANGLES', '30133', 'GARD', '30011']],
            [[u'GEANT CASINO', u'FENOUILLET'], ['FENOUILLET', '31150', 'HAUTE GARONNE', '31182']],
            [[u'GEANT CASINO', u'CASTRES'], ['CASTRES', '81100', 'TARN', '81065']],
            [[u'INTERMARCHE', u'GRANDVILLIERS'], ['GRANDVILLIERS', '60210', 'OISE', '60286']],
            [[u'GEANT CASINO', u'CHAUMONT'], ['CHAUMONT', '52000', 'HAUTE MARNE', '52121']],
            [[u'CENTRE E. LECLERC', u'LURE'], ['LURE', '70200', 'HAUTE SAONE', '70310']],
            [[u'CENTRE E. LECLERC', u'MASSY'], ['MASSY', '91300', 'ESSONNE', '91377']],
            [[u'INTERMARCHE', u'LE PASSAGE'], ['LE PASSAGE', '47520', 'LOT ET GARONNE', '47201']],
            [[u'CENTRE E. LECLERC', u'CHAMBRY'], ['CHAMBRY', '02000', 'AISNE', '02157']],
            [[u'INTERMARCHE', u'EVREUX AV 14 JUILLET'], ['EVREUX', '27000', 'EURE', '27229']],
            [[u'CENTRE E. LECLERC', u'ST PIERRE DOLERON'], ['ST PIERRE D OLERON', '17310', 'CHARENTE MARITIME', '17385']],
            [[u'INTERMARCHE', u'USSEL'], ['USSEL', '19200', 'CORREZE', '19275']],
            [[u'GEANT CASINO', u'FONTAINE'], ['FONTAINE', '38600', 'ISERE', '38169']], # duplicate GEANT or confusion w/ FONTAINE LES DIJON
            [[u'GEANT CASINO', u'ST LOUIS'], ['ST LOUIS', '68300', 'HAUT RHIN', '68297']],
            [[u'CHAMPION', u'FRENEUSE'], ['FRENEUSE', '78840', 'YVELINES', '78255']],
            [[u'GEANT CASINO', u'AVIGNON CC CAP SUD'], ['AVIGNON', '84000', 'VAUCLUSE', '84007']],
            [[u'SUPER U', u'CASTRES'], ['CASTRES', '81100', 'TARN', '81065']],
            [[u'AUCHAN', u'MONT ST MARTIN'], ['MONT ST MARTIN', '54350', 'MEURTHE ET MOSELLE', '54382']], # third period
            [[u'AUCHAN', u'CLERMONT EN AUVERGNE'], ['CLERMONT FERRAND', '63100', 'PUY DE DOME', '63113']],
            [[u'GEANT CASINO', u'CLERMONT FERRAND BREZET'], ['CLERMONT FERRAND', '63100', 'PUY DE DOME', '63113']],
            [[u'SUPER U', u'ROCHE SUR YON'], ['LA ROCHE SUR YON', '85000', 'VENDEE', '85191']],
            [[u'GEANT CASINO', u'VALENCE'], ['VALENCE', '26000', 'DROME', '26362']],
            [[u'AUCHAN', u'BORDEAUX C.C. MERIADECK'], ['BORDEAUX', '33000', 'GIRONDE', '33063']],
            [[u'INTERMARCHE', u'ROUEN RUE CARREL'], ['ROUEN', '76000', 'SEINE MARITIME', '76540']],
            [[u'SUPER U', u'BOURGUET'], []], # mistake Bourget? Maubourguet? => rather drop it
            [[u'GEANT CASINO', u'AMILLY'], ['AMILLY', '45200', 'LOIRET', '45004']], # duplicate GEANT?
            [[u'CENTRE E. LECLERC', u"RAON L'ETAPE"], ['RAON L ETAPE', '88110', 'VOSGES', '88372']],
            [[u'AUCHAN', u'LA TRINITE'], ['LA TRINITE', '06340', 'ALPES MARITIMES', '06149']],
            [[u'GEANT CASINO', u'TORCY'], ['TORCY', '71210', 'SAONE ET LOIRE', '71540']],
            [[u'CHAMPION', u'PARIS 13 NATIONALE'], ['PARIS', '75000', 'PARIS', '75056']],
            [[u'CENTRE LECLERC', u'CLERMONT FERR. FLAUBERT'], ['CLERMONT FERRAND', '63000', 'PUY DE DOME', '63113']],
            [[u'GEANT CASINO', u'CARCASSONNE C.C. CITE2'], ['CARCASSONNE', '11000', 'AUDE', '11069']],
            [[u'SUPER U', u'LE PONT DE BEAUVOISIN'], ['LE PONT DE BEAUVOISIN', '73330', 'SAVOIE', '73204']],
            [[u'INTERMARCHE', u'VITRE'], ['VITRE', '35500', 'ILLE ET VILAINE', '35360']],
            [[u'CHAMPION', u'CLERMONT FERRAND ST ALYRE'], ['CLERMONT FERRAND', '63000', 'PUY DE DOME', '63113']],
            [[u'SUPER U', u'MAGNE'], ['MAGNE', '79460', 'DEUX SEVRES', '79162']],
            [[u'INTERMARCHE', u'ROUEN RUE PARC'], ['ROUEN', '76000', 'SEINE MARITIME', '76540']],
            [[u'CHAMPION', u'LIMOGES MAS LOUBIER'], ['LIMOGES', '87000', 'HAUTE VIENNE', '87085']],
            [[u'SUPER U', u'CAEN BEAULIEU'], ['CAEN', '14000', 'CALVADOS', '14118']],
            [[u'CHAMPION', u'AUBUSSON'], ['AUBUSSON', '23200', 'CREUSE', '23008']],
            [[u'CHAMPION', u'REIMS AV EPERNAY'], ['REIMS', '51100', 'MARNE', '51454']],
            [[u'INTERMARCHE', u'POLIGNY'], ['POLIGNY', '39800', 'JURA', '39434']],
            [[u'CHAMPION', u'CLERMONT FERRAND BARR. DE JAUD'],  ['CLERMONT FERRAND', '63000', 'PUY DE DOME', '63113']],
            [[u'CHAMPION', u'BOIS GUILLAUME REPUBLIQUE'], ['BOIS GUILLAUME', '76230', 'SEINE MARITIME', '76108']],
            [[u'CHAMPION', u'NIORT ANGELY'], ['NIORT', '79000', 'DEUX SEVRES', '79191']],
            [[u'CHAMPION', u'LIMOGES PAGUENAUD'], ['LIMOGES', '87000', 'HAUTE VIENNE', '87085']],
            [[u'CHAMPION', u'ARQUES'], ['ARQUES', '62510', 'PAS DE CALAIS', '62040']],
            [[u'CARREFOUR', u'STE GENEVIEVE DES BOIS'], ['STE GENEVIEVE DES BOIS', '91700', 'ESSONNE', '91549']],
            [[u'AUCHAN', u'DURY'], ['DURY', '80480', 'SOMME', '80261']],
            [[u'CHAMPION', u'COZE'], ['COZES', '17120', 'CHARENTE MARITIME', '17131']], #mispelled
            [[u'CENTRE E. LECLERC', u'NICE RTE TURIN'], ['NICE', '06300', 'ALPES MARITIMES', '06088']],
            [[u'CHAMPION', u'ST FLOUR'], ['ST FLOUR', '15100', 'CANTAL', '15187']],
            [[u'INTERMARCHE', u"NIORT ROUTE D'AIFFRES"], ['NIORT', '79000', 'DEUX SEVRES', '79191']],
            [[u'INTERMARCHE', u'CHELLES'], ['CHELLES', '77500', 'SEINE ET MARNE', '77108']],
            [[u'CENTRE E. LECLERC', u'LILLE FIVES'], ['LILLE', '59800', 'NORD', '59350']],
            [[u'CENTRE E. LECLERC', u'ST LOUP'], ['ST LOUP', '69490', 'RHONE', '69223']],
            [[u'INTERMARCHE', u'MONTEILS'], ['MONTEILS', '82300', 'TARN ET GARONNE', '82126']],
            [[u'GEANT CASINO', u'NIORT CHAURAY'], ['CHAURAY', '79180', 'DEUX SEVRES', '79081']],
            [[u'SUPER U', u'FRANQUEVILLE SAINT PIERRE'], ['FRANQUEVILLE ST PIERRE', '76520', 'SEINE MARITIME', '76475']],
            [[u'AUCHAN', u'CLAMECY'], ['CLAMECY', '58500', 'NIEVRE', '58079']],
            [[u'CENTRE E. LECLERC', u'FLERS'], ['FLERS', '61100', 'ORNE', '61169']],
            [[u'CHAMPION', u'BOIS GUILLAUME BOCQUETS'], ['BOIS GUILLAUME', '76230', 'SEINE MARITIME', '76108']], # duplicate av europe
            [[u'SUPER U', u'GRENADE SUR GARONNE'], ['GRENADE', '31330', 'HAUTE GARONNE', '31232']],
            [[u'CHAMPION', u'NIORT AV. PARIS'], ['NIORT', '79000', 'DEUX SEVRES', '79191']],
            [[u'INTERMARCHE', u'CLERMONT FERRAND FONTGIEVE'], ['CLERMONT FERRAND', '63000', 'PUY DE DOME', '63113']],
            [[u'INTERMARCHE', u'ST AMBROIX'], ['ST AMBROIX', '30500', 'GARD', '30227']],
            [[u'CENTRE E. LECLERC', u'BETTING'], ['FREYMING MERLEBACH', '57800', 'MOSELLE', '57240']],
            [[u'AUCHAN', u'CASTRES'], ['CASTRES', '81100', 'TARN', '81065']]]

path_dir_qlmc = os.path.join(path_data, 'data_qlmc')
path_dir_built_json = os.path.join(path_dir_qlmc, 'data_built' , 'data_json_qlmc')

enc_json(ls_match, os.path.join(path_dir_built_json, 'ls_city_match'))
