#!/usr/bin/python
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from mpl_toolkits.basemap import Basemap
import math
import urllib2
import StringIO
from PIL import Image

def colorbar_index(ncolors, cmap, labels=None, **kwargs):
  """
  This is a convenience function to stop you making off-by-one errors
  Takes a standard colour ramp, and discretizes it,
  then draws a colour bar with correctly aligned labels
  """
  cmap = cmap_discretize(cmap, ncolors)
  mappable = cm.ScalarMappable(cmap=cmap)
  mappable.set_array([])
  mappable.set_clim(-0.5, ncolors+0.5)
  colorbar = plt.colorbar(mappable, **kwargs)
  colorbar.set_ticks(np.linspace(0, ncolors, ncolors))
  colorbar.set_ticklabels(range(ncolors))
  if labels:
    colorbar.set_ticklabels(labels)
  return colorbar

def cmap_discretize(cmap, N):
  """
  Return a discrete colormap from the continuous colormap cmap.
      
    cmap: colormap instance, eg. cm.jet. 
    N: number of colors.
  
  Example
    x = resize(arange(100), (5,100))
    djet = cmap_discretize(cm.jet, 5)
    imshow(x, cmap=djet)
  
  """
  if type(cmap) == str:
    cmap = get_cmap(cmap) #get_cmap? probably cm.get_cmap()
  colors_i = np.concatenate((np.linspace(0, 1., N), (0., 0., 0., 0.)))
  colors_rgba = cmap(colors_i)
  indices = np.linspace(0, 1., N + 1)
  cdict = {}
  for ki, key in enumerate(('red', 'green', 'blue')):
    cdict[key] = [(indices[i], colors_rgba[i - 1, ki], colors_rgba[i, ki]) for i in xrange(N + 1)]
  return matplotlib.colors.LinearSegmentedColormap(cmap.name + "_%d" % N, cdict, 1024)

def deg2num(lat_deg, lon_deg, zoom):
  """
  Tiles to request (OSM) based on gps coordinates and zoom
  """
  lat_rad = math.radians(lat_deg)
  n = 2.0 ** zoom
  xtile = int((lon_deg + 180.0) / 360.0 * n)
  ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
  return (xtile, ytile)

def num2deg(xtile, ytile, zoom):
  """
  This returns the NW-corner of the square. 
  Use the function with xtile+1 and/or ytile+1 to get the other corners. 
  With xtile+0.5 & ytile+0.5 it will return the center of the tile.
  """
  n = 2.0 ** zoom
  lon_deg = xtile / n * 360.0 - 180.0
  lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
  lat_deg = math.degrees(lat_rad)
  return (lat_deg, lon_deg)

def getImageCluster(lat_deg, lon_deg, delta_lat,  delta_long, zoom):
    #base_url = r"http://otile1.mqcdn.com/tiles/1.0.0/map/"
    base_url= r"http://a.tile.openstreetmap.org/"
    smurl = base_url + r"{0}/{1}/{2}.png"
    xmin, ymax = deg2num(lat_deg, lon_deg, zoom)
    xmax, ymin = deg2num(lat_deg + delta_lat, lon_deg + delta_long, zoom)

    bbox_ul = num2deg(xmin, ymin, zoom)
    bbox_ll = num2deg(xmin, ymax + 1, zoom)
    #print bbox_ul, bbox_ll

    bbox_ur = num2deg(xmax + 1, ymin, zoom)
    bbox_lr = num2deg(xmax + 1, ymax +1, zoom)
    #print bbox_ur, bbox_lr

    Cluster = Image.new('RGB',((xmax-xmin+1)*256-1,(ymax-ymin+1)*256-1) )
    for xtile in range(xmin, xmax+1):
        for ytile in range(ymin,  ymax+1):
            try:
                imgurl=smurl.format(zoom, xtile, ytile)
                print("Opening: " + imgurl)
                imgstr = urllib2.urlopen(imgurl).read()
                tile = Image.open(StringIO.StringIO(imgstr))
                Cluster.paste(tile, box=((xtile-xmin)*255 ,  (ytile-ymin)*255))
            except: 
                print("Couldn't download image")
                tile = None

    return Cluster, [bbox_ll[1], bbox_ll[0], bbox_ur[1], bbox_ur[0]]
