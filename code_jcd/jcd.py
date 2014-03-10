import os, sys
import json
import numpy as np
import urllib2
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.collections import PatchCollection
import matplotlib.font_manager as fm
#import shapefile
from mpl_toolkits.basemap import Basemap
from shapely.geometry import Point, Polygon, MultiPoint, MultiPolygon, shape
from shapely.prepared import prep
from descartes import PolygonPatch
#from pysal.esda.mapclassify import Natural_Breaks as nb
from matplotlib import colors

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

key_jcd = '82c9828532a0826fae7d88c65da42bb000409d60'
# GET https://api.jcdecaux.com/vls/v1/stations?contract={contract_name}&apiKey={api_key}
# https://twitter.com/jcdecauxdev
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

for station_velib in ls_velib_paris:
  station_velib['lat'] = station_velib['position']['lat']
  station_velib['lng'] = station_velib['position']['lng']
  del(station_velib['position'])

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

w = x2 - x1
h = y2 - y1
extra = 0.025

# Lambert conformal for France (as suggested by IGN... check WGS84 though?)
m_route = Basemap(resolution='i',
                  projection='lcc',
                  ellps = 'WGS84',
                  lat_1 = 44.,
                  lat_2 = 49.,
                  lat_0 = 46.5,
                  lon_0 = 3,
                  llcrnrlat=y1 - extra * h,
                  urcrnrlat=y2 + extra * h,
                  llcrnrlon=x1 - extra * w,
                  urcrnrlon=x2 + extra * w)

path_data_ubuntu = os.path.join('~', 'Documents', 'Etienne', 'sf_Data')
path_data_windows = os.path.join('C:\\', 'Users', 'etna', 'Desktop', 'Etienne_work', 'Data')
path_data_work = os.path.join('W:\\', 'Bureau', 'Etienne_work', 'Data')
if os.path.exists(path_data_windows):
  path_data = path_data_windows
elif os.path.exists(path_data_ubuntu):
  path_data = path_data_ubuntu
else:
  path_data = path_data_work 

path_dir_route_500 = os.path.join(path_data, 'data_maps' ,'ROUTE500_WGS84', 'TRONCON_ROUTE')
path_dir_dpt = os.path.join(path_data, 'data_maps', 'GEOFLA_DPT_WGS84', 'DEPARTEMENT')
path_dir_com = os.path.join(path_data, 'data_maps', 'GEOFLA_COM_WGS84', 'COMMUNE')

m_route.readshapefile(path_dir_route_500, 'routes_fr', color = 'none', zorder=2)
m_route.readshapefile(path_dir_dpt, 'departements_fr', color = 'none', zorder=2)
m_route.readshapefile(path_dir_com, 'communes_fr', color = 'none', zorder=2)

## TODO: replace with lambda
#def get_point(x):
#  return Point(m_route(x[0], x[1]))
#df_velib['point'] = df_velib[['lng', 'lat']].apply(get_point, axis = 1)
df_velib['point'] = df_velib[['lng', 'lat']].apply(lambda x: Point(m_route(x[0], x[1])),
                                                   axis = 1)

# DF DPT
df_dpt = pd.DataFrame({'poly' : [Polygon(xy) for xy in m_route.departements_fr],
                       'dpt_name' : [d['NOM_DEPT'] for d in m_route.departements_fr_info],
                       'dpt_code' : [d['CODE_DEPT'] for d in m_route.departements_fr_info],
                       'region_name' : [d['NOM_REGION'] for d in m_route.departements_fr_info],
                       'region_code' : [d['CODE_REG'] for d in m_route.departements_fr_info]})
#print df_dpt[['dpt_code', 'dpt_name','region_code', 'region_name']].to_string()

# Some regions must be broken in mult polygons: appear mult times (138 items, all France Metr)
region_multipolygon = MultiPolygon(list(\
                        df_dpt[df_dpt['region_name'] == "ILE-DE-FRANCE"]['poly'].values))
region_multipolygon_prep = prep(region_multipolygon)
region_bounds = region_multipolygon.bounds

# DF COM

ls_com = []
for com_poly, com_info in zip(m_route.communes_fr, m_route.communes_fr_info):
  com_info['poly'] = Polygon(com_poly)
  ls_com.append(com_info)
df_com = pd.DataFrame(ls_com)


# MAP: TEST PARIS ARDTS

df_com['patches'] = df_com['poly'].map(lambda x: PolygonPatch(x,
                                                              facecolor='#FFFFFF', # '#555555'
                                                              edgecolor='#555555', # '#787878'
                                                              lw=.25, alpha=.3, zorder=1))
plt.clf()
fig = plt.figure()
ax = fig.add_subplot(111, axisbg = 'w', frame_on = False)
dev = m_route.scatter([station.x for station in df_velib[df_velib['available_bikes'] != 0]['point']],
                      [station.y for station in df_velib[df_velib['available_bikes'] != 0]['point']],
                      8, marker = 'D', lw=0.25, facecolor = '#000000', edgecolor = 'w', alpha = 0.9,
                      antialiased = True, zorder = 3)
dev = m_route.scatter([station.x for station in df_velib[df_velib['available_bikes'] == 0]['point']],
                      [station.y for station in df_velib[df_velib['available_bikes'] == 0]['point']],
                      8, marker = 'D', lw=0.25, facecolor = '#FF0000', edgecolor = 'w', alpha = 0.9,
                      antialiased = True, zorder = 3)
ax.add_collection(PatchCollection(df_com[df_com['NOM_DEPT'] == "PARIS"]['patches'].values,
                                  match_original = True))
plt.show()
print ax.get_xlim(), ax.get_ylim()

## MAP: TEST HEATMAP

## http://stackoverflow.com/questions/6652671/efficient-method-of-calculating-density-of-irregularly-spaced-points
#import scipy.ndimage as ndi
#data = np.random.rand(30000,2)*255       ## create random dataset
#img = np.zeros((256,256))                ## blank image
#for i in xrange(data.shape[0]):          ## draw pixels
#  img[data[i,0], data[i,1]] += 1
#img = ndi.gaussian_filter(img, (10,10))  ## gaussian convolution
#plt.imshow(img)

# Some scale problem (check ll_corner etc but looks not too bad)

#import scipy.ndimage as ndi
#ll_corner = m_route(x1 - extra *w, y1 - extra *1)
#ur_corner = m_route(x2 + extra *w, y2 + extra * h)
#w2 = ur_corner[0] - ll_corner[0]
#h2 = ur_corner[1] - ll_corner[1]
#
#c = 0
#img = np.zeros((h2/100, w2/100))
#for station in df_velib['point'][df_velib['available_bikes'] == 0]:
#  yn = (station.y - ll_corner[1]) / 100
#  xn = (station.x - ll_corner[0]) / 100
#  try:
#    img[yn, xn] += 1
#  except:
#    c=+1
#img = ndi.gaussian_filter(img, (10,10))
#plt.clf()
#fig = plt.figure()
#ax = fig.add_subplot(111, axisbg = 'w', frame_on = False)
#
#plt.imshow(img, origin = 'lower', zorder = 0,  extent = [ll_corner[0], ur_corner[0], ll_corner[1], ur_corner[1]]) 
#ax.add_collection(PatchCollection(df_com[df_com['NOM_DEPT'] == "PARIS"]['patches'].values,
#                                  match_original = True))
#plt.show()

# http://stackoverflow.com/questions/15160123/adding-a-background-image-to-a-plot-with-known-corner-coordinates

# MAP: STATIONS AS POINTS

#df_dpt['patches'] = df_dpt['poly'].map(lambda x: PolygonPatch(x,
#                                                              facecolor='#FFFFFF',
#                                                              edgecolor='#787878',
#                                                              lw=.25, alpha=.9, zorder=4))
#
#plt.clf()
#fig = plt.figure()
#ax = fig.add_subplot(111, axisbg = 'w', frame_on = False)
#
#for shape_dict, shape in zip(m_route.routes_fr_info, m_route.routes_fr):
#  if not region_multipolygon.disjoint(MultiPoint(shape)):
#    xx, yy = zip(*shape)
#    if shape_dict['CLASS_ADM'] == 'Autoroute':
#      temp = m_route.plot(xx, yy, linewidth = 0.6, color = 'b')
#    elif shape_dict['CLASS_ADM'] == 'Nationale':
#      temp = m_route.plot(xx, yy, linewidth = 0.5, color = 'r')
#    elif shape_dict['CLASS_ADM'] == 'D\xe9partementale':
#      temp = m_route.plot(xx, yy, linewidth = 0.2, color = 'c')
#    else:
#      temp = m_route.plot(xx, yy, linewidth = 0.1, color = 'k')
#
#dev = m_route.scatter([station.x for station in df_velib[df_velib['available_bikes'] != 0]['point']],
#                      [station.y for station in df_velib[df_velib['available_bikes'] != 0]['point']],
#                      8, marker = 'D', lw=0.25, facecolor = '#000000', edgecolor = 'w', alpha = 0.9,
#                      antialiased = True, zorder = 3)
#dev = m_route.scatter([station.x for station in df_velib[df_velib['available_bikes'] == 0]['point']],
#                      [station.y for station in df_velib[df_velib['available_bikes'] == 0]['point']],
#                      8, marker = 'D', lw=0.25, facecolor = '#FF0000', edgecolor = 'w', alpha = 0.9,
#                      antialiased = True, zorder = 3)
#
#ax.add_collection(PatchCollection(df_dpt[df_dpt['region_name'] == "ILE-DE-FRANCE"]['patches'].values,
#                                  match_original = True))
#plt.show()

# MAP: HEATMAP WITH HEX: NOT SO GOOD RENDERING

#df_dpt['patches'] = df_dpt['poly'].map(lambda x: PolygonPatch(x,
#                                                              facecolor='#555555',
#                                                              edgecolor='#787878',
#                                                              lw=.25, alpha=.9, zorder=0))
#
#plt.clf()
#fig = plt.figure()
#ax = fig.add_subplot(111, axisbg = 'w', frame_on = False)
#
#ax.add_collection(PatchCollection(df_dpt[df_dpt['region_name'] == "ILE-DE-FRANCE"]['patches'].values,
#                                  match_original = True))
#
#hx = m_route.hexbin(np.array([station.x for station in df_velib[df_velib['available_bikes'] == 0]['point']]),
#                    np.array([station.y for station in df_velib[df_velib['available_bikes'] == 0]['point']]),
#                    gridsize=20,
#                    #bins='log',
#                    mincnt=1,
#                    edgecolor='none',
#                    alpha=1.,
#                    lw=0.2,
#                    cmap=plt.get_cmap('Blues'))
#
#plt.show()
