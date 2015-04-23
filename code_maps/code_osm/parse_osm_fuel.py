import os, sys
import xml.etree.ElementTree as ET

path = os.path.abspath(os.path.dirname(sys.argv[0]))
# tree = ET.parse(os.path.join(path, 'haute-normandie-latest.osm'))
tree = ET.parse(os.path.join(path, 'france_fuel.osm'))
root = tree.getroot()

## Check first 50 elements
#for i in range(50):
#  print '\n', root[i].tag, root[i].attrib
#  for elt in root[i]:
#    print elt.tag, elt.attrib # elt.tag always tag?

# need to check way too apparently (can be way + node for same station?)
ls_fuel = []
for i, row in enumerate(root):
  # if row.tag == 'relation':
  if row.tag == 'node' or row.tag == 'way' or row.tag=='relation':
    for row_elt in row:
      if row_elt.attrib == {'k': 'amenity', 'v': 'fuel'}:
        ls_fuel.append(i)
        break

# extract info in list of dict (add distinction way/node?)
ls_dict_stations = []
for i in ls_fuel:
  dict_station = root[i].attrib
  if root[i].tag == 'node':
    for row_elt in root[i]:
      dict_station[row_elt.attrib['k']] = row_elt.attrib['v']
  else:
    for row_elt in root[i]:
      if 'k' in row_elt.attrib:
        dict_station[row_elt.attrib['k']] = row_elt.attrib['v']
  ls_dict_stations.append(dict_station)

# todo:
# do with france or dl each region and loop (extract osm?)

# todo: 
# with geofla: check in which commune and get insee code
# with gps: look for nearest stations (with zagaz? gouv?)
