import os
import time
import numpy as np
import pandas
import pandas as pd
import xarray as xr
import datetime as dt
import cartopy as ccrs
import matplotlib.pyplot as plt
import util
#import imageio.v2 as imageio
import os
import glob
import netCDF4 as nc

extent = [-106, -89, 42.0, 30] #Lat and Long extent of map

# //ourdisk/hpc/ai2es/hail/nldn/raw/
#filenames = ["TestData.txt", "TestData2.txt", "TestData3.csv"] #Dest datasets
filenames = ["McGovern1.asc", "McGovern2.asc", "McGovern3.asc", "McGovern4.asc", "McGovern5.asc"]
columns = ["Date", "Time", "Lat", "Lon", "Magnitude", "Type"] #Input dataframe columns

print("Reading in files...")

runStart = time.time() #Get run start time
os.makedirs(f'output/{runStart}') #Create output directory

xedge = np.arange(-106, -88, 0.02083333) #Get edges with gridrad
yedge = np.arange(30, 42, 0.02083333) #Get edges with gridrad
xmid = [] #Blank array
ymid = [] #Blank array



i=0
while(i < len(xedge)-1):
    xmid.append((xedge[i]+xedge[i+1])/2) #Calculate and append midpoints
    i+=1
i=0
while(i < len(yedge)-1):
    ymid.append((yedge[i]+yedge[i+1])/2) #Calculate and append midpoints
    i+=1


for filename in filenames: #Do individually for each file
    df = pandas.read_csv(f'//ourdisk/hpc/ai2es/hail/nldn/raw/{filename}',header=None,delim_whitespace=True, names=columns) #Read in dataframe

    df['datetime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])  #Create datetime column
    df.drop('Date', inplace=True, axis=1) #Drop date axis
    df.drop('Time', inplace=True, axis=1) #Drop time axis
    df.sort_values(by='datetime', inplace=True)  # Sort by time
    startTime = df['datetime'][0].replace(hour=0, minute=0, second=0, microsecond=0) #Get start time of file
    endTime = startTime.replace(hour=0, minute=0, second=0, microsecond=0) + dt.timedelta(0, 86400) #Get end of first day
    lastTime = df['datetime'][len(df) - 1].replace(second=0, microsecond=0) #Get last time in file
    df = df.set_index('datetime') #Set index to datetime in dataframe

    tempArray = xr.Dataset()  # Create temp xarray
    while (startTime <= lastTime): #Loop through entire file
        currentTime = startTime #Get current time within dataframe
        tempArrayList = []
        tempArrayTimeList = []
        while currentTime < endTime: #Loop through each day
            temp = df[slice(currentTime, currentTime+dt.timedelta(0, 300))] #Slice on 5 minutes
            C = util.boxbin(temp['Lon'], temp['Lat'], xedge, yedge, mincnt=0) #Create mesh (Randy's code)
            tempArray = xr.Dataset(
                data_vars=dict(strikes=(["x", "y"], C)),
                coords=dict(
                    lon=(["x"], xmid),
                    lat=(["y"], ymid),
                ),
                attrs=dict(description="Lightning data"),
            )  # Create dataset

            tempArrayList.append(tempArray)
            tempArrayTimeList.append(currentTime)
            currentTime = currentTime+dt.timedelta(0, 300) #Increase current time by 5 minutes

        tempArray = xr.concat(tempArrayList, data_vars='all', dim='time')



        tempArray = tempArray.assign_coords(time=tempArrayTimeList)
        tempArray = tempArray.fillna(0)

        tempArray.to_netcdf(path=f'output/{runStart}/lightningData{str(startTime).split(" ")[0]}.nc') #Save
        print(f"Saved netcdf lightningData{str(startTime).split(' ')[0]}.nc") #Print save message
        startTime = endTime #Reset start time
        endTime = endTime + dt.timedelta(0, 86400) #Increase end time by one day