# utilisation de google fusion tables api pour envoyer des requêtes spatiales
# query ST_INTERSECTS à utiliser ac les coordonnées GPS récupérées avec geocoding.py
# reste à voir pour query distance...
import sys, getpass, json, copy, string, unicodedata
sys.path.append('C:\\Python27\\fusiontables\\src\\')
from authorization.clientlogin import ClientLogin
from sql.sqlbuilder import SQL
import ftclient
import time
from fileimport.fileimporter import CSVImporter

username='echamayou'
password = getpass.getpass("Enter your password: ")

token = ClientLogin().authorize(username, password)
ft_client = ftclient.ClientLoginFTClient(token)

def dec_json(chemin):
 with open(chemin, 'r') as fichier:
  return json.loads(fichier.read())

def enc_stock_json(database, chemin):
 with open(chemin, 'w') as fichier:
  fichier.write(json.dumps(database))  

# ouverture du fichier et suppression Corse et autoroutieres
# utilisation seulement pour creer nveau fichier
# db_raw = dec_json('C:\\Users\\Etienne\\Desktop\\Programmation\\Python\\Scrapping_project_staser\\geocodingtest\\jsondb_geocoding.txt')

def db_restriction(database):
 db=[]
 for elem in database:
  try:
   if string.find(elem['geolocalisation']['results'][0]['formatted_address'], 'France') != -1 \
   and elem['autoroute'] == 0 and (len(elem['id_station']) != 8 or elem['id_station'][:2] != '20'):
    db.append(elem)
  except:
   pass
 return db

# (my geocoded data) tableid = 2336613
# (gps coord from ronan) 
tableid = 3295306
master_rls = dec_json('C:\\Users\\Etienne\\Desktop\\Programmation\\Python\\Scrapping_project_staser\\adr_and_servs\\data_rls\\data_rls.txt')
# enc_stock_json(master_rls,'C:\\Users\\Etienne\\Desktop\\Programmation\\Python\\Scrapping_project_staser\\adr_and_servs\\data_rls\\data_rls.txt')

dico_distance = {1:1000,
                 2:2000,
                 3:3000,
                 4:4000,
                 5:5000}

# retourne liste des id_station des stations ds un certain rayon
def query_competitors_radius(location,lat,lng,radius):
 result = ft_client.query(SQL().select(tableid,['id_station'],"ST_INTERSECTS(%s,CIRCLE(LATLNG(%s,%s),%s))" %(location, lat, lng, radius)))
 parsed_result = result.split('\n')[1:-1]
 return parsed_result

# fonction qui utilise query_competitors_radius pour remplir le fichier database
# PR FICHIER RLS
def add_competitors(database):
  for dist_st, dist_int in dico_distance.items():
    for station in database.keys():
      try:
        database[station]['competition_%s' %dist_st ]
      except:
        if database[station]['latDeg'] != '':
          lat = database[station]['latDeg']
          lng = database[station]['longDeg']
          try: 
            database[station]['competition_%s' %dist_st ] = query_competitors_radius('coordinates',lat,lng,dist_int)
          except:
            time.sleep(5)
            database[station]['competition_%s' %dist_st ] = query_competitors_radius('coordinates',lat,lng,dist_int)
          database[station]['competition_%s_nb' %dist_st ]=len(database[station]['competition_%s' %dist_st ])
          print station, dist_st

# old function
def add_competitors3km(database, start, end):
 for i in range(start,end):
  lat = database[i]['geolocalisation']['results'][0]['geometry']['location']['lat']
  lng = database[i]['geolocalisation']['results'][0]['geometry']['location']['lng']
  database[i]['competitors3'] = query_competitors_radius('coordinates',lat,lng,3000)
  database[i]['competitors3_nb']=len(database[i]['competitors1'])