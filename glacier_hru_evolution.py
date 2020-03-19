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
#import datetime
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

# List of paths to glacier ice thickness raster data
list_path_glacier_thickness = np.asarray(os.listdir(original_glacier_thickness_path))


###############################################################################
###                           FUNCTIONS                                     ###
###############################################################################

def align_rasters(raster_HRU_landuse, full_path_glacier_thickness, aligned_glacier_thickness_path):
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
    
    return current_glacier_thickness

def interpolate_glacier_fractions(hydro_year_range, hru_idx):
    current_HRU_ice_fraction = []
    for day in hydro_year_range:
#                print(day)
        if(day < (pd.Timestamp(int(year), 3, 1))):
            # Same glacierized percentage during accumulation season
            current_HRU_ice_fraction.append(float(raw_HRU_glacier_evolution[-1,hru_idx+1]))
        else:
            # Append the transition between the previous ice fraction and current year's
            current_HRU_ice_fraction = np.concatenate((current_HRU_ice_fraction, np.linspace(current_HRU_ice_fraction[-1], glacierized_perc_HRU, num=(hydro_year_range[-1] - day).days+1)))
            break
        
    return current_HRU_ice_fraction
        
def initialize_dataframe(i_interp_annual_ice_fraction, i_hydro_year_range):
    print("\nInitializing dataframe")
    start_joining = False
    daily_HRU_glacier_evolution_df = pd.DataFrame()
    for hru, HRU_ID  in zip(i_interp_annual_ice_fraction, HRUs_ID_ice):
            current_column = pd.DataFrame(data={str(int(HRU_ID)): hru}, index = i_hydro_year_range)
            if(start_joining):
                daily_HRU_glacier_evolution_df = daily_HRU_glacier_evolution_df.join(current_column)
            else:
                daily_HRU_glacier_evolution_df = current_column
                start_joining = True
    
    return daily_HRU_glacier_evolution_df


###############################################################################
###                           MAIN                                          ###
###############################################################################


#### Open HRU raster data ###
raster_HRU = gdal.Open(hru_path + 'hru_cat.tif', gdal.GA_ReadOnly) 
HRUs = raster_HRU.ReadAsArray()
raster_HRU_landuse = gdal.Open(hru_path + 'hru_landuse.tif', gdal.GA_ReadOnly) 
landuse_HRU = raster_HRU_landuse.ReadAsArray()

# Land use #7 = ice
HRU_ice_idx = np.where(landuse_HRU == 7)
HRUs_ID_ice = np.unique(HRUs[HRU_ice_idx])

raw_HRU_glacier_evolution = ['year']
columns = ['date']
for HRU_ID in HRUs_ID_ice:
    raw_HRU_glacier_evolution.append(int(HRU_ID))
    columns.append(str(int(HRU_ID)))    

isFirst, initDF = True, True


######## Iterate all years of glacier evolution data   ###########

for path_glacier_thickness in list_path_glacier_thickness:
   
    full_path_glacier_thickness = original_glacier_thickness_path + path_glacier_thickness
#    print("\nGlacier ice thickness file: " + str(full_path_glacier_thickness))
    
    glacier_ID = path_glacier_thickness[-14:-9]
    year = path_glacier_thickness[-8:-4]
    
    # Align the current glacier ice thickness raster to the baseline HRU raster
    current_glacier_thickness = align_rasters(raster_HRU_landuse, full_path_glacier_thickness, aligned_glacier_thickness_path)
    
    ice_mask = np.where(current_glacier_thickness > 0)
    current_year = [year]
    
    # We create the dates of the hydrological year with an annual timestep
    year = int(year)
    print("\nYear: " + str(year))
    hydro_year_range = pd.date_range(start=str(year-1) + '-10-01', end=str(year) + '-09-30')
    interp_annual_ice_fraction = []
    
    ########   We compute the glaciarized fraction for each HRU with ice   ###########
    
    hru_idx = 0
    for HRU_ID in HRUs_ID_ice:
        glacier_HRU_idx = np.where(HRUs == HRU_ID)
        current_thickness_HRU = current_glacier_thickness[glacier_HRU_idx]
        glacierized_perc_HRU = current_thickness_HRU[current_thickness_HRU > 0].size/HRUs[glacier_HRU_idx].size
        
        # We create a new row to be stacked on the raw data
        current_year.append(glacierized_perc_HRU)
        
        if(not isFirst):
            # Move from annual to daily resolution
            current_HRU_ice_fraction = interpolate_glacier_fractions(hydro_year_range, hru_idx)
            
            # We add the current HRU's interpolated data to all the data from this year
            current_HRU_ice_fraction = np.asarray(current_HRU_ice_fraction)
            interp_annual_ice_fraction.append(current_HRU_ice_fraction)
            
        hru_idx=hru_idx+1
        
    # We add the raw annual data to the matrix
    raw_HRU_glacier_evolution = np.vstack((raw_HRU_glacier_evolution, current_year))
    
    # We add the daily dataframe with the current year to the full daily dataframe
    if(not isFirst):
        interp_annual_ice_fraction = np.asarray(interp_annual_ice_fraction)
        if(initDF):
            daily_HRU_glacier_evolution_df = initialize_dataframe(interp_annual_ice_fraction, hydro_year_range)
            initDF = False
        else:
            new_year_dataframe = initialize_dataframe(interp_annual_ice_fraction, hydro_year_range)
            daily_HRU_glacier_evolution_df = daily_HRU_glacier_evolution_df.append(new_year_dataframe)
    
    isFirst = False

# We add the raw data into the original annual dataframe
HRU_evolution_df = pd.DataFrame(index= raw_HRU_glacier_evolution[1:,0], columns=raw_HRU_glacier_evolution[0,1:], data=raw_HRU_glacier_evolution[1:,1:])

print("\nProcessed glacierized HRUs daily evolution dataframe: " + str(daily_HRU_glacier_evolution_df))

# Save output in file to be read by J2K
daily_HRU_glacier_evolution_df.to_csv(hru_glacier_fractions_path + "HRU_glacier_fractions_" + str(HRU_evolution_df.index.min()) + "_" + str(HRU_evolution_df.index.max()) + '.dat', sep=' ', index_label = 'date')
   
    
    
    
    