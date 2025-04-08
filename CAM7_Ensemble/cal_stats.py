import xarray as xr
import matplotlib.pyplot as plt
import numpy as np
import glob
import re
import pandas as pd
import os
import warnings

data = xr.open_dataset('path/to/data')

# resample to monthly frequency.
zonal_wind = data.U.resample(time='1ME').mean()

# zonal mean
u_znlmn = zonal_wind.mean('lon').compute()

# Define the months and level range
months = [6, 7, 8]
level_range = u_znlmn.sel(lev=slice(1, 100)).lev  # Selecting levels from 100 to 1

stats = np.zeros((len(months), level_range.shape[0], 2))

for i, month in enumerate(months):
    # Select the specific month and level range
    ds_month = u_znlmn.sel(time=u_znlmn.time.dt.month == month, lev=level_range)
    
    # Compute max U along latitude axis
    U_max = ds_month.max(dim="lat")  # Max U at each (time, level)
    
    # Find latitude index where U is maximum
    lat_idx = ds_month.argmax(dim="lat")  # Index of max U along latitude
    
    # Extract the corresponding latitude value
    lat_max = ds_month.lat.isel(lat=lat_idx)

    # 1st dimension is lat_max and 2nd dimension is u_max.
    stats[i, :, 0] = lat_max.values[0]
    stats[i, :, 1] = U_max.values[0]

np.save('stats_version_xx.npy', stats)