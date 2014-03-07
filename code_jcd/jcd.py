import os, sys
import json
import urllib2
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.collections import PatchCollection
import matplotlib.font_manager as fm
import shapefile
from mpl_toolkits.basemap import Basemap
from shapely.geometry import Point, Polygon, MultiPoint, MultiPolygon, shape
from shapely.prepared import prep
from descartes import PolygonPatch
from pysal.esda.mapclassify import Natural_Breaks as nb
from matplotlib import colors

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

key_jcd = '82c9828532a0826fae7d88c65da42bb000409d60'
#GET https://api.jcdecaux.com/vls/v1/stations?contract={contract_name}&apiKey={api_key}

path = os.path.abspath(os.path.dirname(sys.argv[0]))
paris_json = dec_json(os.path.join(path, 'Paris.json'))
print type(paris_json), len(paris_json)
print paris_json[0]

url_contracts = 'https://api.jcdecaux.com/vls/v1/contracts?apiKey=%s' %key_jcd
response_contracts = urllib2.urlopen(url_contracts)
ls_contracts = json.loads(response_contracts.read())

contract = 'Paris'
url_test = 'https://api.jcdecaux.com/vls/v1/stations?contract=%s&apiKey=%s' %(contract, key_jcd)
response = urllib2.urlopen(url_test)
ls_velib_paris = json.loads(response.read())

df_velib = pd.DataFrame(ls_velib_paris)

print '\nCurrent velib global stats'
print '---------------------------'

print 'Nb stations', len(df_velib)
print 'Nb open stations', len(df_velib[df_velib['status'] == 'OPEN'])
print 'Nb stations w/ CB', len(df_velib[df_velib['banking'] == True])
print 'Nb bonus stations', len(df_velib[df_velib['bonus'] == True])

print 'Total station bike capacity', df_velib['bike_stands'].sum()
print 'Current station bike capacity', df_velib['available_bike_stands'].sum()
print 'Nb available bikes', df_velib['available_bikes'].sum()
print 'Broken bikes?', (df_velib['bike_stands'].sum() -
                        df_velib['available_bike_stands'].sum())-\
                       (df_velib['available_bikes'].sum())

print 'Stations with 0 bike', len(df_velib[df_velib['available_bikes'] == 0])

# PARIS MAP : 48.8148 48.9047 2.2294 2.4688

x1 = 2.2294
x2 = 2.4688
y1 = 48.8148
y2 = 48.9047

# Lambert conformal for France (as suggested by IGN... check WGS84 though?)
m_route = Basemap(resolution='i',
                  projection='lcc',
                  ellps = 'WGS84',
                  lat_1 = 44.,
                  lat_2 = 49.,
                  lat_0 = 46.5,
                  lon_0 = 3,
                  llcrnrlat=y1,
                  urcrnrlat=y2,
                  llcrnrlon=x1,
                  urcrnrlon=x2)

m_route.readshapefile(path_data + path_route_500 + '\TRONCON_ROUTE', 'routes_fr', color = 'none', zorder=2)

for shape_dict, shape in zip(m_route.routes_fr_info, m_route.routes_fr):
  if not region_multipolygon.disjoint(MultiPoint(shape)):
    xx, yy = zip(*shape)
    if shape_dict['CLASS_ADM'] == 'Autoroute':
      temp = m_route.plot(xx, yy, linewidth = 0.6, color = 'b')
    elif shape_dict['CLASS_ADM'] == 'Nationale':
      temp = m_route.plot(xx, yy, linewidth = 0.5, color = 'r')
    elif shape_dict['CLASS_ADM'] == 'D\xe9partementale':
      temp = m_route.plot(xx, yy, linewidth = 0.2, color = 'c')
    else:
      temp = m_route.plot(xx, yy, linewidth = 0.1, color = 'k')


plt.xlim((x1, x2))
plt.ylim((y1, y2))
plt.show()
