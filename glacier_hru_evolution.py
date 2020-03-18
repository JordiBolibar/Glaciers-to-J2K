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
import pandas as pd
#import matplotlib.pyplot as plt
#import matplotlib.backends.backend_pdf
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
hru_glacier_fractions_path = workspace + 'HRU_glacier_fractions\\'
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

# Land use #7 = ice
HRU_ice_idx = np.where(landuse_HRU == 7)
HRUs_ID_ice = np.unique(HRUs[HRU_ice_idx])

raw_HRU_glacier_evolution = ['year']
for HRU_ID in HRUs_ID_ice:
    raw_HRU_glacier_evolution.append(int(HRU_ID))

# Empty dataframe
HRU_glacier_evolution_df = pd.DataFrame()

# Iterate all years of glacier evolution data
for path_glacier_thickness in list_path_glacier_thickness:
   
    full_path_glacier_thickness = original_glacier_thickness_path + path_glacier_thickness
    print("\nGlacier ice thickness file: " + str(full_path_glacier_thickness))
    
    glacier_ID = path_glacier_thickness[-14:-9]
    year = path_glacier_thickness[-8:-4]
    
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
        subprocess.call(command +[ str(dfGeoXUL), str(dfGeoYLR), str(dfGeoXLR), str(dfGeoYUL), "-tr", xres, yres, vrt_glacier_thick_path, full_path_glacier_thickness])

    # We open the aligned VRT glacier ice thickness raster
    raster_current_glacier = gdal.Open(vrt_glacier_thick_path, gdal.GA_ReadOnly) 
    current_glacier_thickness = raster_current_glacier.ReadAsArray()
    
    ice_mask = np.where(current_glacier_thickness > 0)
    current_year = [year]
    
    # We compute the glaciarized fraction for each HRU with ice
    for HRU_ID in HRUs_ID_ice:
#        print("\nHRU ID: " + str(int(HRU_ID)))
        glacier_HRU_idx = np.where(HRUs == HRU_ID)
        current_thickness_HRU = current_glacier_thickness[glacier_HRU_idx]
        glacierized_perc_HRU = current_thickness_HRU[current_thickness_HRU > 0].size/HRUs[glacier_HRU_idx].size
        
        # We create a new row to be stacked on the raw data
        current_year.append(glacierized_perc_HRU)
    
    # We add the row for the current year to the raw data
    raw_HRU_glacier_evolution = np.vstack((raw_HRU_glacier_evolution, current_year))

# We add the raw data into the dataframe
HRU_evolution_df = pd.DataFrame(index= raw_HRU_glacier_evolution[1:,0], columns=raw_HRU_glacier_evolution[0,1:], data=raw_HRU_glacier_evolution[1:,1:])
print("\nProcessed glacierized HRUs evolution dataframe: " + str(HRU_evolution_df))
#import pdb; pdb.set_trace()
 
# Save output in file to be read by J2K
HRU_evolution_df.to_csv(hru_glacier_fractions_path + "HRU_glacier_fractions_" + str(HRU_evolution_df.index.min()) + "_" + str(HRU_evolution_df.index.max()) + '.dat', sep=' ', index_label = 'year')
   
    
    
    
    