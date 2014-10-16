fantoir_file = open(r'C:\Users\etna\Desktop\Etienne_work\Data\data_insee\FANTOIR.txt', 'r')
fantoir = fantoir_file.read()
ls_fantoir = fantoir.split('\n')

# Check elt[4] == ' ': all departements (titles... useless?)
ls_content_direction = [[   1,   2, u"Code département"],
                        [   3,   3, u"Code direction"],
                        [   4,  10, u"Filler 1"],
                        [  11,  11, u"Clé Rivoli"],
                        [  12,  41, u"Libellé Direction"],
                        [  42, 150, u"Filler"]]

ls_content_commune   = [[   1,   2, u"Code département"],
                        [   3,   3, u"Code direction"],
                        [   4,   6, u"Code commune"],
                        [   7,  10, u"Id voie ds commune"],
                        [  11,  11, u"Clé Rivoli"],
                        [  12,  41, u"Libellé commune"],
                        [  42,  42, u"Filler 1"],
                        [  43,  43, u"Type de commune"],
                        [  44,  45, u"Filler 2"],
                        [  46,  46, u"Caractère PUR"],
                        [  47,  49, u"Filler 3"],
                        [  50,  50, u"Caractère de population"],
                        [  51,  52, u"Filler 4"],
                        [  53,  59, u"Population réelle"],
                        [  60,  66, u"Population à part"],
                        [  67,  73, u"Population fictive"],
                        [  74,  74, u"Caractère d'annulation"],
                        [  75,  81, u"Date d'annulation"],
                        [  82,  88, u"Date de création de l'article"],
                        [  89, 150, u"Filler 5"]]

ls_content_voie      = [[   1,   2, u"Code département"],
                        [   3,   3, u"Code direction"],
                        [   4,   6, u"Code commune"],
                        [   7,  10, u"Id voie ds commune"],
                        [  11,  11, u"Clé Rivoli"],
                        [  12,  15, u"Code nature de voie"],
                        [  16,  41, u"Libellé de voie"],
                        [  42,  42, u"Filler 1"],
                        [  43,  43, u"Type de commune"],
                        [  44,  45, u"Filler 2"],
                        [  46,  46, u"Caractère PUR"],
                        [  47,  48, u"Filler 3"],
                        [  49,  49, u"Caractère de voie"],
                        [  50,  50, u"Caractère de population"],
                        [  51,  59, u"Filler 4"],
                        [  60,  66, u"Population à part"],
                        [  67,  73, u"Population fictive"],
                        [  74,  74, u"Caractère d'annulation"],
                        [  75,  81, u"Date d'annulation"],
                        [  82,  88, u"Date de création de l'article"],
                        [  89, 103, u"Filler 5"],
                        [ 104, 108, u"Code identifiant MAJIC de voie"],
                        [ 109, 109, u"Type de voie"],
                        [ 110, 110, u"Caractère du lieu dit"],
                        [ 111, 112, u"Filler 6"],
                        [ 113, 120, u"Dernier mot alpha libelle voie"],
                        [ 121, 150, u"Filler 7"]]

ls_communes = [row for row in ls_fantoir if row and len(row) > 41 and len(row) < 89]
ls_voies = [row for row in ls_fantoir if row and len(row) > 88]

def split_row(row, ls_content):
  return [row[beg-1:end] for beg, end, title in ls_content]

import pprint
ls_voie_titles = [elt[-1] for elt in ls_content_voie]
pprint.pprint(zip(ls_voie_titles, split_row(ls_voies[0], ls_content_voie)))

import datetime
test = datetime.datetime.strptime('2001', '%Y') + datetime.timedelta(days=1)
test_2 = test.strftime('%Y/%m/%d')
