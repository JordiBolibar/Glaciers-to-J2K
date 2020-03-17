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
#from numba import jit
#from osgeo import gdal, ogr
import matplotlib.pyplot as plt
import matplotlib.backends.backend_pdf
import numpy as np
import copy
from pathlib import Path
#from glacier_evolution import array2raster, getRasterInfo

import subprocess, os,  sys, glob
try:
    from osgeo import gdal
    from osgeo import osr
except:
    import gdal
#    import osr

command = ["gdalbuildvrt","-te"]

######   FILE PATHS    #######
workspace = str(Path(os.getcwd())) + '\\'
#root = str(workspace.parent) + '\\'
hru_path = workspace + 'HRUs\\'
original_glacier_thickness_path = workspace + 'glacier_thickness\\original_glacier_thickness\\'
aligned_glacier_thickness_path = workspace + 'glacier_thickness\\aligned_glacier_thickness\\'

list_path_glacier_thickness = np.asarray(os.listdir(original_glacier_thickness_path))

###############################################################################
###                           FUNCTIONS                                     ###
###############################################################################


###############################################################################
###                           MAIN                                          ###
###############################################################################

#import pdb; pdb.set_trace()

#### Open HRU raster data ###
raster_HRU = gdal.Open(hru_path + 'hru_cat.tif', gdal.GA_ReadOnly) 
HRUs = raster_HRU.ReadAsArray()
raster_HRU_landuse = gdal.Open(hru_path + 'hru_landuse.tif', gdal.GA_ReadOnly) 
landuse_HRU = raster_HRU_landuse.ReadAsArray()

# We remove all ice from the land use file in order to apply our custom glacier data
# Instead we apply rock
HRU_ice_idx = np.where(landuse_HRU == 7)
HRUs_ID_ice = np.unique(HRUs[HRU_ice_idx])

HRU_glacier = {'ID':0, 'ice_fraction':[], 'years':[]}
HRU_glacier_evolution = []
for HRU_ID in HRUs_ID_ice:
    current_HRU = copy.deepcopy(HRU_glacier)
    current_HRU['ID'] = HRU_ID
    HRU_glacier_evolution.append(current_HRU)
HRU_glacier_evolution = np.asarray(HRU_glacier_evolution)

#import pdb; pdb.set_trace()
# Land use #7 = ice

# Iterate all years of glacier evolution data
for path_glacier_thickness in list_path_glacier_thickness:
   
    full_path_glacier_thickness = original_glacier_thickness_path + path_glacier_thickness
    print("\nGlacier ice thickness file: " + str(full_path_glacier_thickness))
    
    glacier_ID = path_glacier_thickness[-14:-9]
    year = path_glacier_thickness[-8:-4]
    
#    import pdb; pdb.set_trace()

    #### Open raster data ###
    adfGeoTransform = raster_HRU_landuse.GetGeoTransform(can_return_null = True)
    
    # We align the glacier ice thickness with the interpolated land use raster
    if adfGeoTransform is not None:
        dfGeoXUL = adfGeoTransform[0] 
        dfGeoYUL = adfGeoTransform[3] 
        dfGeoXLR = adfGeoTransform[0] + adfGeoTransform[1] * raster_HRU_landuse.RasterXSize + adfGeoTransform[2] * raster_HRU_landuse.RasterYSize
        dfGeoYLR = adfGeoTransform[3] + adfGeoTransform[4] * raster_HRU_landuse.RasterXSize + adfGeoTransform[5] * raster_HRU_landuse.RasterYSize
        xres = str(abs(adfGeoTransform[1]))
        yres = str(abs(adfGeoTransform[5]))
        vrt_glacier_thick_path = aligned_glacier_thickness_path + "glacier_" + year + "_VRT.vrt"
#        print("\nvrt_glacier_thick_path: " + str(vrt_glacier_thick_path))
        subprocess.call(command +[ str(dfGeoXUL), str(dfGeoYLR), str(dfGeoXLR), str(dfGeoYUL), "-tr", xres, yres, vrt_glacier_thick_path, full_path_glacier_thickness])
#        os.system(command +[ str(dfGeoXUL), str(dfGeoYLR), str(dfGeoXLR), str(dfGeoYUL), "-tr", xres, yres, vrt_glacier_thick_path, full_path_glacier_thickness])

        
    # We open the aligned VRT glacier ice thickness raster
    raster_current_glacier = gdal.Open(vrt_glacier_thick_path, gdal.GA_ReadOnly) 
    current_glacier_thickness = raster_current_glacier.ReadAsArray()
    
    ice_mask = np.where(current_glacier_thickness > 0)
    
    # We compute the glaciarized fraction for each HRU with ice
    for HRU_ID, HRU_evolution in zip(HRUs_ID_ice, HRU_glacier_evolution):
#        print("\nHRU ID: " + str(int(HRU_ID)))
        glacier_HRU_idx = np.where(HRUs == HRU_ID)
        current_thickness_HRU = current_glacier_thickness[glacier_HRU_idx]
        glacierized_perc_HRU = current_thickness_HRU[current_thickness_HRU > 0].size/HRUs[glacier_HRU_idx].size
        
        # We store the processed information into the data structure
        HRU_evolution['ice_fraction'].append(glacierized_perc_HRU)
        HRU_evolution['years'].append(year)
    

print("\nProcessed glacierized HRUs evolution: " + str(HRU_glacier_evolution))
    
    
    
    
    
    
    
    