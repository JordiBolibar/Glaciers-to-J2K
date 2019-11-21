# -*- coding: utf-8 -*-

"""
@author: Jordi Bolibar
Institut des Géosciences de l'Environnement (Université Grenoble Alpes)
jordi.bolibar@univ-grenoble-alpes.fr

DYNAMIC GLACIERIZED PERCENTAGE PER HRU PIXEL COMPUTATION
J2K HYDROLOGICAL MODEL

"""

## Dependencies: ##
import os
from numba import jit
from osgeo import gdal, ogr
import matplotlib.pyplot as plt
import matplotlib.backends.backend_pdf
import numpy as np
from pathlib import Path
from glacier_evolution import array2raster, getRasterInfo

import subprocess, os,  sys, glob
try:
    from osgeo import gdal
    from osgeo import osr
except:
    import gdal
    import osr

command = ["gdalbuildvrt","-te"]

######   FILE PATHS    #######
workspace = str(Path(os.getcwd())) + '\\'
#root = str(workspace.parent) + '\\'
hru_path = workspace + 'HRUs\\'
glacier_thickness_path = workspace + 'glacier_thickness\\'

list_path_glacier_thickness = np.asarray(os.listdir(glacier_thickness_path))

###############################################################################
###                           FUNCTIONS                                     ###
###############################################################################

def store_land_use_raster(land_use_u, land_use_raster, year):
    path_land_use_year = hru_path + 'land_use_' + str(year) + '\\'
    if not os.path.exists(path_land_use_year):
        os.makedirs(path_land_use_year)
    
    path_land_use_year_file = path_land_use_year + 'land_use_' + str(year) + '.tif'
    
    # We get the raster info
    r_projection, r_pixelwidth, r_pixelheight, r_origin = getRasterInfo(land_use_raster)
    
    array2raster(path_land_use_year_file, r_origin, r_pixelwidth, r_pixelheight, land_use_u)
    
    return path_land_use_year_file

###############################################################################
###                           MAIN                                          ###
###############################################################################

#import pdb; pdb.set_trace()

#### Open HRU raster data ###
raster_landuse = gdal.Open(hru_path + 'landuse_32632_interp.tif', gdal.GA_ReadOnly) 
land_use = raster_landuse.ReadAsArray()

# We remove all ice from the land use file in order to apply our custom glacier data
# Instead we apply rock
land_use_no_ice = np.where(land_use == 7, 6, land_use)
# Land use #7 = ice

for path_glacier_thickness in list_path_glacier_thickness:
   
    print(path_glacier_thickness)
    path_glacier_thickness = glacier_thickness_path + path_glacier_thickness
    
    glacier_ID = path_glacier_thickness[-14:-9]
    year = path_glacier_thickness[-8:-4]
    
#    import pdb; pdb.set_trace()

    #### Open raster data ###
    adfGeoTransform = raster_landuse.GetGeoTransform(can_return_null = True)
    
    # We align the glacier ice thickness with the interpolated land use raster
    if adfGeoTransform is not None:
        dfGeoXUL = adfGeoTransform[0] 
        dfGeoYUL = adfGeoTransform[3] 
        dfGeoXLR = adfGeoTransform[0] + adfGeoTransform[1] * raster_landuse.RasterXSize + adfGeoTransform[2] * raster_landuse.RasterYSize
        dfGeoYLR = adfGeoTransform[3] + adfGeoTransform[4] * raster_landuse.RasterXSize + adfGeoTransform[5] * raster_landuse.RasterYSize
        xres = str(abs(adfGeoTransform[1]))
        yres = str(abs(adfGeoTransform[5]))
        vrt_glacier_thick_path = glacier_thickness_path + "glacier_" + year + "_VRT.vrt"
        subprocess.call(command +[ str(dfGeoXUL), str(dfGeoYLR), str(dfGeoXLR), str(dfGeoYUL), "-tr", xres, yres, vrt_glacier_thick_path, path_glacier_thickness])
    
    # We open the aligned VRT glacier ice thickness raster
    raster_current_glacier = gdal.Open(vrt_glacier_thick_path, gdal.GA_ReadOnly) 
    current_glacier_thickness = raster_current_glacier.ReadAsArray()
    
    ice_mask = np.where(current_glacier_thickness > 0)
    
    # We apply the custom ice mask in the interpolated ice-free land use raster
    land_use_no_ice[ice_mask] = 7
    

# After having iterated all the glaciers, we store the customized land use
store_land_use_raster(land_use_u, land_use_raster, year)
    
#    nodata_current_glacier_thickness = raster_current_glacier_thickness.GetRasterBand(1).GetNoDataValue()
#    masked_DEM_currentGlacier = np.ma.masked_values(current_glacier_array_DEM, nodata_DEM_current_glacier)
    
    # If overlap and HRU pixel has > 50% glacierized surface, set HRU pixel as glacier
    
    
    
    
    
    
    
    
    