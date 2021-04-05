
import os
import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math

def plotmeltonset(stats, weather, i, year):

    tavg = weather['TAVG']
    
    datew = pd.to_datetime(weather["DATE"], format="%m/%d/%Y")
    doyw = [d.dayofyear for d in datew]
    stats['s0'] = [10*math.log10(x) for x in stats['mean']]
    
    band_1 = stats.loc[stats['band'] == 1]
    band_1 = band_1.loc[band_1['obj'] == 17]
    #band_2 = stats.loc[stats['band'] == 2]
    #band_2 = band_2.loc[band_2['obj'] == 1]
    
    doys1 = np.unique(band_1['doy'].values)
    #doys2 = np.unique(band_2['doy'].values)
    
    band_1_avg = []
    #band_2_avg = []
    for doy in doys1:
        band_1_rows = band_1.loc[band_1['doy'] == doy]        
        band_1_avg.append(np.median(band_1_rows["s0"].values))
    #for doy in doys2:
    #    band_2_rows = band_2.loc[band_2['doy'] == doy]        
    #    band_2_avg.append(np.mean(band_2_rows["s0"].values))
    
    ax[i].title.set_text(year)
    
    yt = ax[i].twinx()
    ax[i].set_xlabel("DOY")
    ax[i].set_ylabel("s0")
    yt.set_ylabel("Tavg")
    
    s, = ax[i].plot(band_1['doy'], band_1['s0'], '.', label="s0")
    t, = yt.plot(doyw, tavg, 'k--', label="tavg")
    #ax[i].plot(band_2['doy'], band_2['s0'], '.')
    sm, = ax[i].plot(doys1, band_1_avg, label="median s0")
    #ax[i].plot(doys2, band_2_avg)
    ax[i].legend(handles=[s,t,sm])
    #yt.legend()
    

if __name__ == "__main__":
    
    filenames = {"2013":['admiraltyInlet_2013.csv','admiraltyInlet_weather_2013.csv'],
                 "2012":['admiraltyInlet_2012.csv','admiraltyInlet_weather_2012.csv']}
                 #"2013":['admiraltyInlet_2011.csv','admiraltyInlet_weather_2011.csv']}

    
    n = len(filenames)
    fig, ax = plt.subplots(n)
    i = 0
    for year, files in filenames.items():
        stats = pd.read_csv(files[0])
        weather = pd.read_csv(files[1])
        plotmeltonset(stats, weather, i, year)
        i += 1
    plt.show()
    
    
    
    
    
    
    