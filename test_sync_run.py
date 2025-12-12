import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from nptdms import TdmsFile
from datetime import timedelta
import sys
import os

# File Paths
txt_path = 'Moto_Chicane_100_P1.txt'
tdms_path = 'Moto_Chicane_100.tdms'

print("Libraries loaded.")

# 1. Load Xsens GPS Data
print("Loading Xsens Data...")
try:
    if not os.path.exists(txt_path):
        print(f"Error: {txt_path} not found.")
        sys.exit(1)
        
    # Skip header
    # Note: original notebook used skiprows=12. 
    df_txt = pd.read_csv(txt_path, sep='\t', skiprows=12)
    df_txt.columns = df_txt.columns.str.strip()

    # Parse Time
    req_cols = ['UTC_Year', 'UTC_Month', 'UTC_Day', 'UTC_Hour', 'UTC_Minute', 'UTC_Second', 'UTC_Nano']
    # Filter valid rows
    df_txt = df_txt.dropna(subset=req_cols)
    
    time_series = pd.to_datetime(df_txt[req_cols[:-1]].astype(int).rename(columns={
        'UTC_Year': 'year', 'UTC_Month': 'month', 'UTC_Day': 'day',
        'UTC_Hour': 'hour', 'UTC_Minute': 'minute', 'UTC_Second': 'second'
    }))
    df_txt['timestamp'] = time_series + pd.to_timedelta(df_txt['UTC_Nano'], unit='ns')

    # Calculate GPS Speed (m/s) if not present, or use Vel_N/Vel_E
    if 'Vel_N' in df_txt.columns and 'Vel_E' in df_txt.columns:
         df_txt['Vel_N'] = pd.to_numeric(df_txt['Vel_N'], errors='coerce').fillna(0)
         df_txt['Vel_E'] = pd.to_numeric(df_txt['Vel_E'], errors='coerce').fillna(0)
         df_txt['GPS_Speed'] = np.sqrt(df_txt['Vel_N']**2 + df_txt['Vel_E']**2)
    elif 'Velocity' in df_txt.columns:
         df_txt['GPS_Speed'] = pd.to_numeric(df_txt['Velocity'], errors='coerce').fillna(0)
    
    print(f"Xsens Loaded: {len(df_txt)} rows. Time Range: {df_txt['timestamp'].min()} - {df_txt['timestamp'].max()}")
    
except Exception as e:
    print(f"Error loading TXT: {e}")
    # print traceback
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 2. Load TDMS Edge Data
print("Loading TDMS Data...")
try:
    if not os.path.exists(tdms_path):
        print(f"Error: {tdms_path} not found.")
        sys.exit(1)

    tdms_file = TdmsFile.read(tdms_path)
    groups = tdms_file.groups()
    if len(groups) > 0:
        group = groups[0] 
        for g in groups:
            if 'P1' in g.name:
                group = g
                break
        
        channel_name = 'Edges_RoueAR'
        if channel_name in group:
            channel = group[channel_name]
            edges_cal = channel[:]
            
            # Time vector for TDMS
            start_time = channel.properties.get('wf_start_time')
            increment = channel.properties.get('wf_increment')
            if start_time and increment:
                # Handle tz naive - forcing to naive to match xsens usually
                start_time = pd.to_datetime(start_time).tz_localize(None) 
                # Create time array
                # Using numpy for speed
                tdms_time = start_time + pd.to_timedelta(np.arange(len(edges_cal)) * increment, unit='s')
                df_tdms = pd.DataFrame({'timestamp': tdms_time, 'Edges': edges_cal})
            else:
                 df_tdms = pd.DataFrame({'Edges': edges_cal})
            
            print(f"TDMS Loaded: {len(df_tdms)} rows. Time Range: {df_tdms['timestamp'].min()} - {df_tdms['timestamp'].max()}")

            df_tdms['Edge_Diff'] = df_tdms['Edges'].diff().fillna(0)
            
        else:
            print(f"Channel {channel_name} not found in group {group.name}")
            sys.exit(1)
    else:
        print("No groups found in TDMS")
        sys.exit(1)

except Exception as e:
    print(f"Error loading TDMS: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 3. Detect Start of Movement
print("Detecting Start...")
gps_speed_threshold = 0.5 # m/s roughly
df_txt_sorted = df_txt.sort_values('timestamp').reset_index(drop=True)

# Find where speed > threshold
gps_moving = df_txt_sorted[df_txt_sorted['GPS_Speed'] > gps_speed_threshold]

if gps_moving.empty:
    print("No GPS movement detected based on speed threshold.")
    gps_start_time = df_txt_sorted.iloc[0]['timestamp'] 
else:
    gps_start_idx = gps_moving.index.min()
    gps_start_time = df_txt_sorted.iloc[gps_start_idx]['timestamp']
    print(f"GPS Start Detected at: {gps_start_time} (Index {gps_start_idx}, Speed={df_txt_sorted.iloc[gps_start_idx]['GPS_Speed']:.2f} m/s)")


# TDMS Start: When Edge_Diff > 0
df_tdms_sorted = df_tdms.sort_values('timestamp').reset_index(drop=True)
tdms_moving = df_tdms_sorted[df_tdms_sorted['Edge_Diff'] > 0]

if tdms_moving.empty:
    print("No Edge movement detected.")
    tdms_start_time = df_tdms_sorted.iloc[0]['timestamp']
else:
    tdms_start_idx = tdms_moving.index.min()
    tdms_start_time = df_tdms_sorted.iloc[tdms_start_idx]['timestamp']
    print(f"TDMS Start Detected at: {tdms_start_time} (Index {tdms_start_idx})")

time_offset = gps_start_time - tdms_start_time
print(f"Calculated Time Offset to add to TDMS: {time_offset}")

# Plotting to verify
print("Saving plot to sync_test_plot.png")
df_tdms_sorted['aligned_timestamp'] = df_tdms_sorted['timestamp'] + time_offset

view_window = pd.Timedelta(seconds=10)
center_time = gps_start_time

mask_gps = (df_txt_sorted['timestamp'] >= center_time - view_window) & (df_txt_sorted['timestamp'] <= center_time + view_window*5)
mask_tdms = (df_tdms_sorted['aligned_timestamp'] >= center_time - view_window) & (df_tdms_sorted['aligned_timestamp'] <= center_time + view_window*5)

subset_gps = df_txt_sorted[mask_gps]
subset_tdms = df_tdms_sorted[mask_tdms]

scale_factor = 5

plt.figure(figsize=(15, 6))
plt.plot(subset_gps['timestamp'], subset_gps['GPS_Speed'], label='GPS Speed (m/s)', marker='.', linestyle='-')
plt.plot(subset_tdms['aligned_timestamp'], subset_tdms['Edge_Diff'] * scale_factor, label='Edge Diff (Scaled)', alpha=0.7)

plt.axvline(gps_start_time, color='red', linestyle='--', label='Start Trigger')
plt.title(f"Sync Verification (Offset: {time_offset})")
plt.xlabel("Time")
plt.ylabel("Signal")
plt.legend()
plt.grid(True)
plt.savefig('sync_test_plot.png')
print("Plot saved.")
