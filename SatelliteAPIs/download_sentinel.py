#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

sentineldownload.py

Script to select Sentinel imagery from Copernicus, download and reproject, etc
This relies on the Sentinelsat api in Python but calls GDAL commandline utilities for the
image manipulations

Dependencies:
    Python3, sentinelsat library, gdal utilities version 2.4 or higher

    Need to have an account with Copernicus too.
   
    On one of my computers I need to run a specific install of gdal (hence the
    prefix variable - which points to that directory) OR if you use conda, then load the
    correct environment before running this file with conda activate
    
    Also set the following ENV Variable to avoid warning:
      export CPL_ZIP_ENCODING=UTF-8
      See https://github.com/conda-forge/gdal-feedstock/issues/83

NOTE - This is a first draft - makes assumptions, no error handling, caveat emptor!

Created on Fri Jun 12 06:21:49 2020

@author: dmueller
"""

import os
import sys
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon, Point
import subprocess
import shlex
import shutil
from sentinelsat import SentinelAPI, read_geojson, geojson_to_wkt
import zipfile
from osgeo import gdal

user = 'a.plourde' ## TODO change this to be an argument
password = 'C3ur0Pac' ## TODO change this to be an argument

# set working directory
#### ADMIRALTY INLET
wrkdir = "C:/users/owner/repos/melt_onset/"  #has the coastline layer too...   Need a trailing /

#see notes above about this
gdalprefix = "C:/ProgramData/Miniconda3/pkgs/libgdal-3.0.4-h821c9b7_6/Library/bin/"  # dir (end with /) with gdal utilities

os.chdir(wrkdir)

# define the region of interest (ulx uly lrx lry) in a python list
## in lat/lon WGS84 EPSG:4326

# Note that this box was made carefully to fit into Sentinel2 Tile 16XEG so
# that it would not return hits from multiple tiles (which would mean stiching
# them together)

#NB: The tileid parameter only works for products from April 2017 onward due to
# missing metadata in SciHub’s DHuS catalogue. Before that, but only from
#December 2016 onward (i.e. for single-tile products), you can use a filename
#pattern instead:
#kw['filename'] = '*_T{}_*'.format(tile)  # products after 2016-12-01

#### ADMIRALTY INLET
spat = [-85, 73.6, -84.23, 73]

# define the region of interest min_x  min_y max_x max_y  for the study site
#### ADMIRALTY INLET
## in projected coordinates - CIS projection
bb = "370000 3660000 550000 3800000"  #same as GIBS MODIS
bb = "430000 3680000 530000 3800000"  # more restricted


# define the dates of imagery to fetch
startdate = pd.to_datetime("August 2, 2020")
days = 5
dates = startdate + pd.to_timedelta(np.arange(days), "D")

# define a new projection
prj_psn = "+proj=stere +lat_0=90 +lat_ts=70 +lon_0=-45 +k=1 +x_0=0 +y_0=0 +ellps=WGS84 +datum=WGS84 +units=m +no_defs"
prj_lcc = "+proj=lcc +lat_1=49 +lat_2=77 +lat_0=40 +lon_0=-100 +x_0=0 +y_0=0 +ellps=WGS84 +datum=WGS84 +units=m +no_defs"
prj_lcc = "+proj=lcc +lat_1=49 +lat_2=77 +lat_0=40 +lon_0=-100 +x_0=0 +y_0=0 +ellps=clrk66 +units=m +no_defs"
prj_ll = "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs "

prj_aea = "+proj=aea +lat_1=83 +lat_2=82 +lat_0=82 +lon_0=-75 +x_0=0 +y_0=0 +ellps=WGS84 +datum=WGS84 +units=m +no_defs "

#### ADMIRALTY INLET IS
prj = prj_lcc

# define a new crop zone

#convert spat to well known text (assumes bb is in ulx uly, lrx lry)
spat_lon =[spat[0], spat[2],spat[2], spat[0]]
spat_lat =[spat[1], spat[1],spat[3], spat[3]]
geom = Polygon(zip(spat_lon, spat_lat)) #create the polygon from calculated coordinates
footprint = geom.to_wkt()

# connect to copernicus
api = SentinelAPI(user, password, 'https://scihub.copernicus.eu/dhus')


# query
products = api.query(footprint,
                     date = (dates[0].strftime('%Y%m%d'), dates[-1].strftime('%Y%m%d')),
                     platformname = 'Sentinel-2',
                     processinglevel = 'Level-2A')


#Convert the results to a geopandas dataframe
gpdf = api.to_geodataframe(products)

# filter on the tiles you want
#gpdf = gpdf[gpdf.title.str.contains('|'.join(tiles))]


print("The query returned {} hits".format(len(gpdf)))
ok = input("Each image will take 5-10 minutes to produce... Press 'y' to continue or any other key to cancel: ")
if ok.upper() != "Y":
    print("Operation cancelled by user")
    sys.exit()

"""
# export the query results to a geopackage (can be opened in QGIS)
#gpdf.to_file('products_tile4.gpkg', layer='prod', driver="GPKG")


# api.download_all(products)  - #holy crap these are ~1GB files - watch out!!

#See GDAL:
    #https://gdal.org/drivers/raster/sentinel2.html


# go through each image in the list of images
for i in range(len(gpdf)):

    print("Working on "+gpdf.title[i]+".......")
    #download the file
    api.download(gpdf.uuid[i])

    # wait for download?---------???

    #  unzip
    with zipfile.ZipFile(gpdf.title[i]+'.zip', 'r') as zip_ref:
        zip_ref.extractall()
    os.chdir(gpdf.title[i]+'.SAFE')
   
    s2 = gdal.Open( "MTD_MSIL2A.xml" )
    s2sub = s2.GetSubDatasets()
    s2_10m = s2sub[0][0]
   
    s2 = gdal.Open(s2_10m)
    bands = s2.RasterCount  # should be 4.
   
    sd3_upper = 0
    mm_upper = 0
    mm_lower = 1
    sd3_lower = 1
   
    for band in range(1, 4):
        data = s2.GetRasterBand(band).ReadAsArray()
        #calculate mean without value 0 (no data) and 2^16 (saturated)
        bmean = np.mean(data[(data != 0) & (data != 2^16)])
        bstd = np.std(data[(data != 0) & (data != 2^16)])
        bmin = np.min(data[(data != 0) & (data != 2^16)])
        bmax = np.max(data[(data != 0) & (data != 2^16)])
        sd3_upper = max(sd3_upper,bmean+bstd*3)
        sd3_lower = min(sd3_lower, bmean-bstd*3)
        mm_upper = max(mm_upper,bmax)
        mm_lower = min(mm_lower,bmin)
        print("Band {}: Mean = {:.2f}, Std =  {:.2f}, Min = {}, Max = {}".format(band, bmean, bstd, bmin, bmax))
       
    stretchLow = max(1,sd3_lower)  # custom stretch values
    stretchHigh = min(mm_upper,sd3_upper)
   
    dimgname = gpdf.beginposition[i].strftime('%Y%m%d_%H%M%S')+"_s2_432_tc_a_"+gpdf.title[i].split('_')[-2]
   
    cmd_a = gdalprefix+"gdal_translate -ot byte -b 1 -b 2 -b 3 -scale_1 "+ \
        str(stretchLow)+" "+str(stretchHigh)+" 1 255 -scale_2 "+ \
        str(stretchLow)+" "+str(stretchHigh)+" 1 255 -scale_3 "+ \
        str(stretchLow)+" "+str(stretchHigh)+" 1 255 "+s2_10m+" "+os.path.join(wrkdir,dimgname+"_utm.tif")
   
    command = shlex.split(cmd_a)
    p = subprocess.Popen(command, stdout = subprocess.PIPE)
    p_status = p.wait()

    os.chdir(wrkdir)
   
    cmd_b = gdalprefix+"gdalwarp -r cubicspline -co COMPRESS=LZW -te "+bb+" -t_srs '"+prj+"' "+dimgname+"_utm.tif "+dimgname+"_aea.tif"
    command = shlex.split(cmd_b)
    p = subprocess.Popen(command, stdout = subprocess.PIPE)
    p_status = p.wait()

# THIS CODE WILL 'BURN' A COASTLINE IN - COMMENTED OUT FOR NOW

# =============================================================================
#     cmd_c = gdalprefix+"gdal_rasterize  -b 1 -b 2 -b 3 -burn 255 -burn 0 -burn 0 -l coast_line coast_line.shp "+dimgname+"_aea.tif"
#     command = shlex.split(cmd_c)
#     p = subprocess.Popen(command, stdout = subprocess.PIPE)
#     p_status = p.wait()
#    
# =============================================================================
    #clean up
    s2=None
   
    os.remove(dimgname+"_utm.tif")
    #os.remove(gpdf.title[i]+'.zip')
    shutil.rmtree(gpdf.title[i]+'.SAFE')
"""