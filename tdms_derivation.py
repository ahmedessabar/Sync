
# 3. Derive Speed/Acceleration (Edge-Step Method)
# LOGIC FROM Merge_Data.ipynb (Adapted)

import numpy as np
from scipy import signal
import pandas as pd

derived_speed_mps = None
derived_acc_mps2 = None

# Ensure we have time and edges
if 'tdms_time' not in locals() or tdms_time is None:
    # Try to construct if missing (copy of logic just in case)
    if 'edges_ch' in locals():
        try:
            props = edges_ch.properties
            start_time = props.get('wf_start_time')
            increment = props.get('wf_increment')
            if start_time and increment:
                start_dt = pd.to_datetime(start_time).tz_localize(None)
                seconds = np.arange(len(edges_data)) * increment
                tdms_time = start_dt + pd.to_timedelta(seconds, unit='s')
        except:
            pass

if 'tdms_time' in locals() and tdms_time is not None and 'edges_data' in locals():
    try:
        # Parameters
        WHEEL_DIA_INCH = 17.0 # User preference (was 18.0 in old code)
        EDGES_PER_REV = 50.0
        STEP_EDGES = 150
        
        wheel_circum_m = WHEEL_DIA_INCH * 0.0254 * np.pi
        meters_per_edge = wheel_circum_m / EDGES_PER_REV
        
        # Create DataFrame for derivation
        df_t = pd.DataFrame({'Edges': edges_data, 'Time': tdms_time})
        df_t['Time_ns'] = df_t['Time'].astype(np.int64)
        
        # 1. Unique edges
        df_unique = df_t.drop_duplicates(subset=['Edges'], keep='first')
        
        if len(df_unique) > 100:
            u_counts = df_unique['Edges'].values
            u_times_ns = df_unique['Time_ns'].values
            
            # 2. Grid of edges
            min_edge = u_counts.min()
            max_edge = u_counts.max()
            edge_grid = np.arange(np.ceil(min_edge/STEP_EDGES)*STEP_EDGES, max_edge, STEP_EDGES)
            
            # 3. Interpolate Time
            t_grid_ns = np.interp(edge_grid, u_counts, u_times_ns)
            
            # 4. Calc Speed
            dt_grid_s = np.diff(t_grid_ns) * 1e-9
            # Avoid divide by zero
            dt_grid_s[dt_grid_s == 0] = 1e-9
            
            speed_grid_edges_s = STEP_EDGES / dt_grid_s
            speed_grid_mps = speed_grid_edges_s * meters_per_edge
            
            # Map back to full time
            t_mid_ns = (t_grid_ns[:-1] + t_grid_ns[1:]) / 2
            
            full_time_ns = df_t['Time_ns'].values
            derived_speed_mps = np.interp(full_time_ns, t_mid_ns, speed_grid_mps, left=0, right=0)
            
            # Calc Accel
            fs = 1.0 / (pd.to_timedelta(increment, unit='s').total_seconds() if 'increment' in locals() else 0.0025)
            if 'increment' in locals() and increment: fs = 1.0/increment
            
            acc_raw = np.diff(derived_speed_mps, prepend=derived_speed_mps[0]) * fs
            
            # Filter
            b, a = signal.butter(2, 5, fs=fs, btype='low')
            derived_acc_mps2 = signal.filtfilt(b, a, acc_raw)
            
            print(f'Derivation Complete. Mean Speed: {np.mean(derived_speed_mps):.2f} m/s')
        else:
            print('Not enough unique edges for derivation')
    except Exception as e:
        print(f'Derivation Error: {e}')
else:
    print("Cannot derive: Missing 'tdms_time' or 'edges_data'")
