# -*- coding: utf-8 -*-

"""
@author: Jordi Bolibar
Institut des Géosciences de l'Environnement (Université Grenoble Alpes)
jordi.bolibar@univ-grenoble-alpes.fr

PLOTTING RESULTS OF ALPGM-J2K SIMULATIONS FOR THE ARVAN GLACIERIZED CATCHMENT

"""

from pathlib import Path
import os
import numpy as np
import pandas as pd
import subprocess
import matplotlib.pyplot as plt
import proplot as plot

# Paths

workspace = str(Path(os.getcwd()))
j2k_output_path = "C:\Jordi\PhD\Java\J2K\jamsmodeldata\Arvan_Amont_detaille_loc\output\current"
plots_path = os.path.join(workspace, 'plots')
j2k_updated_output_path = os.path.join(workspace, 'J2K_output')
arvan_obs_path = "C:\Jordi\PhD\J2K\Data\Arvan"

###############################################################################
###                           FUNCTIONS                                     ###
###############################################################################



###############################################################################
###                           MAIN                                          ###
###############################################################################

# Read TimeLoop J2K output
# Remove useless header lines
raw_time_loop = pd.read_csv(os.path.join(j2k_output_path, 'TimeLoop.dat'), sep="\t", skiprows=[0,1,2,3,4,6,7,8,9,10], skipfooter=1)
n_cols = raw_time_loop.columns.size
raw_time_loop.to_csv(os.path.join(j2k_updated_output_path, "TimeLoop_clean.dat"), sep="\t")

# Parse cleaned up version
time_loop = pd.read_csv(os.path.join(j2k_updated_output_path, "TimeLoop_clean.dat"), sep="\t", index_col=1, usecols=range(0,n_cols))
time_loop.index =  pd.to_datetime(time_loop.index).date
#time_loop.index = time_loop.index.to_numpy()

# Open and parse Arvan hydrological observations
arvan_obs = pd.read_csv(os.path.join(arvan_obs_path, "W1055020_qj_hydro2.txt"), sep=";", skiprows=range(0,3), skipfooter=1, 
                        names=['freq', 'ID', 'date', 'runoff', 'mode', 'confidence'], index_col=2, usecols=range(0,6))
arvan_obs.index =  pd.to_datetime(arvan_obs.index, format='%Y%m%d')

arvan_j2k_and_obs = pd.merge(time_loop, arvan_obs, left_index=True, right_index=True)

# Convert sim runoff to L/d
arvan_j2k_and_obs['catchmentSimRunoff'] = arvan_j2k_and_obs['catchmentSimRunoff']/100000

# Choose subset of dates for plots
arvan_j2k_and_obs = arvan_j2k_and_obs.loc[arvan_j2k_and_obs.index > '2008-08-01']

#import pdb; pdb.set_trace()

####  PLOT J2K VS OBS RUNOFF  #####

fig1, axs1 = plot.subplots(ncols=1, nrows=1, aspect=2, axwidth=10)

axs1.plot(arvan_j2k_and_obs.index, arvan_j2k_and_obs['runoff'], linewidth=0.5, c='midnightblue', label="Observations", legend='ul')
axs1.plot(arvan_j2k_and_obs.index, arvan_j2k_and_obs['catchmentSimRunoff'], linewidth=0.5, c='sienna', label="ALPGM-J2K simulations", legend='ul')

axs1.format(
#            abc=True, abcloc='ul',
            ygridminor=True,
            ytickloc='both', yticklabelloc='left',
            xlabel='Date', ylabel='Runoff (L/d)'
            )

fig1.savefig(os.path.join(plots_path, 'arvan_j2k_vs_obs_runoff.pdf'))

subprocess.Popen(os.path.join(plots_path, 'arvan_j2k_vs_obs_runoff.pdf'),shell=True)

#plt.show()

