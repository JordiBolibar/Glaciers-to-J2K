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
import matplotlib as mpl
import proplot as plot
import copy

# Paths

workspace = str(Path(os.getcwd()))
j2k_output_path = "C:\Jordi\PhD\Java\J2K\jamsmodeldata\Arvan_Amont_detaille_loc\output\current"
plots_path = os.path.join(workspace, 'plots')
j2k_updated_output_path = os.path.join(workspace, 'J2K_output')
arvan_obs_path = "C:\Jordi\PhD\J2K\Data\Arvan"
smb_path = os.path.join(arvan_obs_path, 'saint_sorlin')

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
time_loop.index =  pd.to_datetime(time_loop.index, infer_datetime_format=True)
#time_loop.index = time_loop.index.to_numpy()

# Open and parse Arvan hydrological observations
arvan_obs = pd.read_csv(os.path.join(arvan_obs_path, "W1055020_qj_hydro2.txt"), sep=";", skiprows=range(0,3), skipfooter=1, 
                        names=['freq', 'ID', 'date', 'runoff', 'mode', 'confidence'], index_col=2, usecols=range(0,6))

arvan_obs.index =  pd.to_datetime(arvan_obs.index, format='%Y%m%d')

### Fill empty dates with nan

idx = pd.date_range(arvan_obs.index[0], arvan_obs.index[-1])

arvan_obs.index = pd.DatetimeIndex(arvan_obs.index)

arvan_obs = arvan_obs.reindex(idx, fill_value=np.nan)

# We crop both dataframes for the same period
time_loop = time_loop.loc[arvan_obs.index[0]:arvan_obs.index[-1]]
arvan_obs = arvan_obs.loc[arvan_obs.index[0]:time_loop.index[-1]]

# Convert sim runoff to L/d
time_loop['catchmentSimRunoff'] = time_loop['catchmentSimRunoff']/86400
time_loop['glacierRunoff'] = time_loop['glacierRunoff']/86400

# Choose subset of dates for plots
time_loop = time_loop.loc[time_loop.index > '2000-10-01'][1:]
arvan_obs = arvan_obs.loc[arvan_obs.index > '2000-10-01']

# We load the season MB data for Saint Sorlin glacier
sorlin_seasonal_mb = pd.read_csv(os.path.join(smb_path, "st_sorlin_seasonal_mb.csv"), sep=";")

sorlin_seasonal_mb['summer L'] = sorlin_seasonal_mb['Summer']*sorlin_seasonal_mb['Surface (m2)']*1000
sorlin_seasonal_mb['winter L'] = sorlin_seasonal_mb['Winter']*sorlin_seasonal_mb['Surface (m2)']*1000

sorlin_seasonal_mb['annual L'] = sorlin_seasonal_mb['Annual']*sorlin_seasonal_mb['Surface (m2)']*1000

# De-accumulate massBalance and convert it to seasonal and annual series
#j2k_mb_non_cumulative = time_loop['massBalance'].diff()

time_loop['MB_nc'] = time_loop['massBalance']
#time_loop['MB_nc'] = j2k_mb_non_cumulative
#time_loop['MB_nc'] = time_loop['MB_nc'].interpolate()

SeasonDict = {11: 'Winter', 12: 'Winter', 1: 'Winter', 2: 'Winter', 3: 'Winter', 4: 'Summer', 5: 'Summer', 6: 'Summer', 7: 'Summer', \
8: 'Summer', 9: 'Summer', 10: 'Winter'}

j2k_seasonal_MB = time_loop['MB_nc'].groupby([lambda x: SeasonDict[x.month], time_loop.index.year]).sum()
j2k_annual_MB = time_loop['MB_nc'].groupby(time_loop.index.year).sum()
j2k_annual_MB = j2k_annual_MB.loc[j2k_annual_MB.index > 2000]

years = np.asarray(range(2000, 2013))    

# De-accumulate temperature
#j2k_tmean_non_cumulative = time_loop['tmean_glacier'].diff()
time_loop['tmean_nc'] = time_loop['tmean_glacier']

#time_loop['tmean_nc'] = j2k_tmean_non_cumulative
#time_loop['tmean_nc'] = time_loop['tmean_nc'].interpolate()

# Calculate seasonal snow and mean temperature
j2k_seasonal_snow = time_loop['netSnow_glacier'].groupby([lambda x: SeasonDict[x.month], time_loop.index.year]).sum()
j2k_seasonal_rain = time_loop['netRain_glacier'].groupby([lambda x: SeasonDict[x.month], time_loop.index.year]).sum()
j2k_seasonal_meanTemp = time_loop['tmean_nc'].groupby([lambda x: SeasonDict[x.month], time_loop.index.year]).mean()

j2k_annual_snow = time_loop['netSnow_glacier'].groupby(time_loop.index.year).sum()
j2k_annual_snow = j2k_annual_snow.loc[j2k_annual_snow.index > 2000]
j2k_annual_rain = time_loop['netRain_glacier'].groupby(time_loop.index.year).sum()
j2k_annual_rain = j2k_annual_rain.loc[j2k_annual_rain.index > 2000]
j2k_annual_meanTemp = time_loop['tmean_nc'].groupby(time_loop.index.year).mean()
j2k_annual_meanTemp = j2k_annual_meanTemp.loc[j2k_annual_meanTemp.index > 2000]

##### SEASONAL RUNOFF COMPUTATION  #####

#import pdb; pdb.set_trace()

time_loop['noGlacierRunoff'] = time_loop['catchmentSimRunoff'] - time_loop['glacierRunoff']

j2k_seasonal_total_runoff = time_loop['catchmentSimRunoff'].groupby([lambda x: SeasonDict[x.month], time_loop.index.year]).mean()
j2k_seasonal_noGlacier_runoff = time_loop['noGlacierRunoff'].groupby([lambda x: SeasonDict[x.month], time_loop.index.year]).mean()
j2k_seasonal_glacier_runoff = time_loop['glacierRunoff'].groupby([lambda x: SeasonDict[x.month], time_loop.index.year]).mean()
j2k_seasonal_glacier_contribution = (j2k_seasonal_glacier_runoff/j2k_seasonal_total_runoff)*100

j2K_daily_glacier_contribution = (time_loop['glacierRunoff']/time_loop['catchmentSimRunoff'])*100
j2K_monthly_glacier_contribution = j2K_daily_glacier_contribution.resample('M').mean()
j2k_annual_glacier_contribution = j2K_daily_glacier_contribution.resample('Y').mean()

#import pdb; pdb.set_trace()

####################################################################################
####  PLOT J2K VS OBS RUNOFF  ######################################################
####################################################################################

fig1, axs1 = plot.subplots(ncols=1, nrows=3, aspect=3, axwidth=6)

axs1[0].plot(time_loop.index, arvan_obs['runoff'], linewidth=0.1, c='black', label="Observations", legend='ur')
axs1[0].plot(time_loop.index, time_loop['catchmentSimRunoff'], linewidth=0.1, c='sienna', label="J2K", legend='ur')
#axs1[0].set_ylim(0, 15000)

axs1[1].plot(time_loop.index, time_loop['catchmentSimRunoff'].values - arvan_obs['runoff'].values, linewidth=0.1, c='darkred', label="J2K daily bias", legend='ur')
#axs1[1].set_ylim(-10000, 10000)

axs1[2].plot(time_loop.index, time_loop['catchmentSimRunoff'].values, linewidth=0.1, c='sienna', label="J2K daily bias", legend='ur')
axs1[2].plot(time_loop.index, time_loop['glacierRunoff'], linewidth=0.5, c='denim', label="J2K glacier runoff", legend='ur')

axs1.format(
            abc=True, abcloc='ul',
            ygridminor=True,
            ytickloc='both', yticklabelloc='left',
            xlabel='Date', ylabel='Runoff (L/s)'
            )

fig1.savefig(os.path.join(plots_path, 'arvan_j2k_vs_obs_runoff.pdf'))
#subprocess.Popen(os.path.join(plots_path, 'arvan_j2k_vs_obs_runoff.pdf'),shell=True)

######  PLOT DAILY MASS BALANCE  #################

fig2, axs2 = plot.subplots(ncols=1, nrows=4, axwidth=2, aspect=2, share=1)

axs2[0].plot(time_loop.index, np.cumsum(time_loop['massBalance'].values), linewidth=1, c='steelblue')
axs2[0].set_ylabel('m.w.e.')
axs2[0].format(title='Cumulative daily MB')
axs2[1].plot(j2k_annual_MB.index, j2k_seasonal_MB['Winter'][1:] + j2k_seasonal_MB['Summer'], linewidth=1, c='steelblue')
axs2[1].set_ylabel('m.w.e. d$^{-1}$')
axs2[1].axhline(y=0, color='black', linewidth=0.7, linestyle='-')
axs2[1].format(title='Annual MB')
axs2[2].plot(j2k_annual_meanTemp.index.values[1:-1], j2k_seasonal_meanTemp['Winter'][2:-1] + j2k_seasonal_meanTemp['Summer'].values[1:-1], linewidth=1, c='darkred')
axs2[2].set_ylabel('°C')
axs2[2].format(title='Annual mean temperature')
axs2[3].plot(j2k_annual_snow.index.values[1:-1], j2k_seasonal_snow['Winter'][2:-1] + j2k_seasonal_snow['Summer'][1:-1], linewidth=1, c='skyblue')
axs2[3].set_ylabel('mm')
axs2[3].format(title='Annual snowfall')

axs2.format(
#            abc=True, abcloc='ul',
            ygridminor=True,
            ytickloc='both', yticklabelloc='left',
            xlabel='Date'
            )

fig2.savefig(os.path.join(plots_path, 'arvan_runoff_mb_climate.pdf'))
#subprocess.Popen(os.path.join(plots_path, 'arvan_runoff_mb_climate.pdf'),shell=True)

######  PLOT SEASONAL MASS BALANCE VALIDATION #################

fig3, axs3 = plot.subplots([[1, 1],[2, 3],[4, 5],[6, 7],[8, 9]], ncols=2, nrows=5, aspect=4, axwidth=4, spany=0)

axs3[0].format(title='Annual glacier-wide MB')
axs3[0].set_ylabel('L')
axs3[0].axhline(y=0, color='black', linewidth=0.7, linestyle='-')
h5 = axs3[0].plot(sorlin_seasonal_mb['Year'].values, sorlin_seasonal_mb['annual L'].values, linewidth=3, c='black', label="GLACIOCLIM annual MB")
h6 = axs3[0].plot(j2k_annual_MB.index.values[1:-1], j2k_annual_MB.values[1:-1], linewidth=3, c='olive', label="J2K annual MB")

axs3[1].axhline(y=0, color='black', linewidth=0.7, linestyle='-')
axs3[1].format(title='Winter MB')
axs3[1].set_ylabel('L')
h1 = axs3[1].plot(sorlin_seasonal_mb['Year'].values[1:-1], sorlin_seasonal_mb['winter L'].values[1:-1], linewidth=3, c='darkblue', label="GLACIOCLIM winter MB")
h2 = axs3[1].plot(j2k_seasonal_MB['Winter'].index.values[1:-1], j2k_seasonal_MB['Winter'].values[1:-1], linewidth=3, c='skyblue', label="J2K winter MB")
axs3[3].format(title='Winter snowfall')
axs3[3].set_ylabel('mm')
axs3[3].plot(j2k_annual_MB.index.values[:-1], j2k_seasonal_snow['Winter'].values[1:-1], linewidth=2, c='skyblue')
axs3[5].format(title='Winter rainfall')
axs3[5].set_ylabel('mm')
axs3[5].plot(j2k_annual_MB.index.values[:-1], j2k_seasonal_rain['Winter'].values[1:-1], linewidth=2, c='steelblue')
axs3[7].format(title='Winter mean temperature')
axs3[7].set_ylabel('°C')
axs3[7].axhline(y=0, color='black', linewidth=0.7, linestyle='-')
axs3[7].plot(j2k_annual_meanTemp.index.values[:-1], j2k_seasonal_meanTemp['Winter'].values[1:-1], linewidth=2, c='crimson')

axs3[2].axhline(y=0, color='black', linewidth=0.7, linestyle='-')
axs3[2].format(title='Summer MB')
axs3[2].set_ylabel('L')
h3 = axs3[2].plot(sorlin_seasonal_mb['Year'].values[1:-1], sorlin_seasonal_mb['summer L'].values[1:-1], linewidth=3, c='darkred', label="GLACIOCLIM summer MB")
h4 = axs3[2].plot(j2k_seasonal_MB['Summer'].index.values[:-1], j2k_seasonal_MB['Summer'].values[:-1], linewidth=3, c='sienna', label="J2K summer MB")
axs3[4].format(title='Summer snowfall')
axs3[4].set_ylabel('mm')
axs3[4].plot(j2k_annual_MB.index.values[:-1], j2k_seasonal_snow['Summer'].values[:-1], linewidth=2, c='skyblue')
axs3[6].format(title='Summer rainfall')
axs3[6].set_ylabel('mm')
axs3[6].plot(j2k_annual_MB.index.values[:-1], j2k_seasonal_rain['Summer'].values[:-1], linewidth=2, c='steelblue')
axs3[8].format(title='Summer mean temperature')
axs3[8].set_ylabel('°C')
axs3[8].axhline(y=0, color='black', linewidth=0.7, linestyle='-')
axs3[8].plot(j2k_annual_meanTemp.index.values[:-1], j2k_seasonal_meanTemp['Summer'].values[:-1], linewidth=2, c='crimson')

fig3.legend(((h5,h6,h1,h2,h3,h4)), loc='r', ncols=1, frame=True)

axs3.format(
            abc=True, abcloc='ur',
            ygridminor=True,
            ytickloc='both', yticklabelloc='left',
            xlabel='Year'
            )

fig3.savefig(os.path.join(plots_path, 'seasonal_mb.pdf'))
#subprocess.Popen(os.path.join(plots_path, 'seasonal_mb.pdf'),shell=True)

#########################################

### ANNUAL MASS BALANCES  #################

#import pdb; pdb.set_trace()

fig4, axs4 = plot.subplots(ncols=1, nrows=1, aspect=1.2, axwidth=3)

axs4.plot(time_loop.index.values, time_loop['glacierArea'].values/1000000, linewidth=3, c='denim')

axs4.format(
#            abc=True, abcloc='ul',
            ygridminor=True,
            ytickloc='both', yticklabelloc='left',
            xlabel='Date', ylabel='Glacier area (km$^{2}$)'
            )

fig4.savefig(os.path.join(plots_path, 'arvan_j2k_vs_GLACIOCLIM_MB.pdf'))
#subprocess.Popen(os.path.join(plots_path, 'arvan_j2k_vs_GLACIOCLIM_MB.pdf'),shell=True)

##########################################################

fig5, axs5 = plot.subplots(ncols=1, nrows=2, aspect=2, axwidth=5, share=0)

axs5[0].format(title='Daily temperature')
axs5[0].plot(time_loop.index, time_loop['tmean_nc'], linewidth=1, c='darkred')
axs5[0].set_ylabel('°C')
axs5[1].format(title='Daily snowfall')
axs5[1].plot(time_loop.index, time_loop['snow'], linewidth=1, c='skyblue')
axs5[1].set_ylabel('mm')


axs5.format(
            abc=True, abcloc='ul',
            ygridminor=True,
            ytickloc='both', yticklabelloc='left',
            xlabel='Date'
            )

fig5.savefig(os.path.join(plots_path, 'arvan_j2K_daily_meteo.pdf'))

####################################################################################
##########  PLOT J2K RUNOFF  ######################################################
####################################################################################


#j2k_seasonal_total_runoff = time_loop['catchmentSimRunoff'].groupby([lambda x: SeasonDict[x.month], time_loop.index.year]).mean()
#j2k_seasonal_noGlacier_runoff = time_loop['noGlacierRunoff'].groupby([lambda x: SeasonDict[x.month], time_loop.index.year]).mean()
#j2k_seasonal_glacier_runoff = time_loop['glacierRunoff'].groupby([lambda x: SeasonDict[x.month], time_loop.index.year]).mean()
#j2k_seasonal_glacier_contribution = (j2k_seasonal_glacier_runoff/j2k_seasonal_total_runoff)*100
#
#j2K_daily_glacier_contribution = (time_loop['glacierRunoff']/time_loop['catchmentSimRunoff'])*100
#j2K_monthly_glacier_contribution = j2K_daily_glacier_contribution.resample('M').mean()

fig6, axs6 = plot.subplots(ncols=1, nrows=3, aspect=3, axwidth=6, spany=0)

axs6.format(
            abc=True, abcloc='ul',
            ygridminor=True,
            ytickloc='both', yticklabelloc='left',
            xlabel='Date',
            suptitle="Glacier runoff contribution"
            )

axs6[0].plot(j2K_daily_glacier_contribution.index, j2K_daily_glacier_contribution.values, linewidth=0.2, c='skyblue')
axs6[0].set_ylabel('Daily contribution (%)')
#axs6[0].set_ylim(0, 15000)

axs6[1].plot(j2K_monthly_glacier_contribution.index, j2K_monthly_glacier_contribution.values, c='skyblue')
axs6[1].set_ylabel('Monthly contribution (%)')
#axs6[1].set_ylim(-10000, 10000)

#import pdb; pdb.set_trace()

axs6[2].plot(j2k_annual_glacier_contribution.index, j2k_annual_glacier_contribution.values, linewidth=4, color='ocean blue')
axs6[2].set_ylabel('Annual contribution (%)')

#fig6.savefig(os.path.join(plots_path, 'arvan_j2k_glacier_runoff_contribution.pdf'))
#subprocess.Popen(os.path.join(plots_path, 'arvan_j2k_vs_obs_runoff.pdf'),shell=

fig6.savefig(os.path.join(plots_path, 'arvan_j2K_glacier_runoff_contribution.pdf'))

plt.show()

