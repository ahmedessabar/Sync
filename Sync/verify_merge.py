
import pandas as pd
from nptdms import TdmsFile
import numpy as np
from scipy import signal
import sys

# Suppress plots for script run
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def run_verification():
    print("Starting Verification...")
    txt_path = 'Moto_chicane_50_P1.txt'
    tdms_path = 'Moto_chicane_50.tdms'

    # 1. Load Xsens
    try:
        df_txt = pd.read_csv(txt_path, sep='\t', skiprows=12)
        df_txt.columns = df_txt.columns.str.strip()
        req_cols = ['UTC_Year', 'UTC_Month', 'UTC_Day', 'UTC_Hour', 'UTC_Minute', 'UTC_Second', 'UTC_Nano']
        df_txt = df_txt.dropna(subset=req_cols)
        time_series = pd.to_datetime(df_txt[['UTC_Year', 'UTC_Month', 'UTC_Day', 'UTC_Hour', 'UTC_Minute', 'UTC_Second']].astype(int).rename(columns={
            'UTC_Year': 'year', 'UTC_Month': 'month', 'UTC_Day': 'day',
            'UTC_Hour': 'hour', 'UTC_Minute': 'minute', 'UTC_Second': 'second'
        }))
        df_txt['AbsoluteTime'] = time_series + pd.to_timedelta(df_txt['UTC_Nano'], unit='ns')
        df_txt['Acc_X'] = pd.to_numeric(df_txt['Acc_X'], errors='coerce').fillna(0)
        print("Xsens Loaded.")
    except Exception as e:
        print(f"Xsens Load Failed: {e}")
        return

    # 2. Load TDMS
    try:
        tdms_file = TdmsFile.read(tdms_path)
        group = tdms_file['P1']
        df_tdms = group.as_dataframe()
        properties = group.channels()[0].properties
        start_time = properties.get('wf_start_time')
        increment = properties.get('wf_increment')
        if start_time and increment:
            start_time_pd = pd.to_datetime(start_time).tz_localize(None)
            df_tdms['AbsoluteTime'] = start_time_pd + pd.to_timedelta(np.arange(len(df_tdms)) * increment, unit='s')
        
        edges = df_tdms['Edges_RoueAR']
        if edges.is_monotonic_increasing:
             speed_signal = edges.diff().fillna(0).rolling(window=10, center=True).mean().fillna(0)
        else:
             speed_signal = edges
        
        acc_derived = speed_signal.diff().fillna(0) / increment
        b, a = signal.butter(2, 5, fs=1/increment, btype='low')
        df_tdms['Derived_Acc'] = signal.filtfilt(b, a, acc_derived)
        print("TDMS Loaded & Derived Acc Calculated.")
    except Exception as e:
        print(f"TDMS Process Failed: {e}")
        return

    # 3. Correlation
    try:
        fs_common = 100.0
        common_dt = 1.0 / fs_common
        t_start = min(df_txt['AbsoluteTime'].min(), df_tdms['AbsoluteTime'].min())
        t_end = max(df_txt['AbsoluteTime'].max(), df_tdms['AbsoluteTime'].max())
        
        time_grid = pd.date_range(start=t_start, end=t_end, freq=f'{int(1000/fs_common)}ms')
        df_common = pd.DataFrame({'AbsoluteTime': time_grid})

        def to_numeric_time(dt_series):
            return (dt_series - t_start).dt.total_seconds()

        xsens_time_num = to_numeric_time(df_txt['AbsoluteTime'])
        tdms_time_num = to_numeric_time(df_tdms['AbsoluteTime'])
        grid_time_num = to_numeric_time(df_common['AbsoluteTime'])

        xsens_acc_interp = np.interp(grid_time_num, xsens_time_num, df_txt['Acc_X'])
        tdms_acc_interp = np.interp(grid_time_num, tdms_time_num, df_tdms['Derived_Acc'])

        def normalize(x):
            return (x - np.mean(x)) / (np.std(x) + 1e-6)

        s1 = normalize(xsens_acc_interp)
        s2 = normalize(tdms_acc_interp)

        correlation = signal.correlate(s1, s2, mode='full')
        lags = signal.correlation_lags(len(s1), len(s2), mode='full')
        lag = lags[np.argmax(correlation)]
        time_shift = lag * common_dt
        
        print(f"Computed Time Shift: {time_shift:.3f} s")
        print(f"Max Correlation: {np.max(correlation)}")
    except Exception as e:
        print(f"Correlation Failed: {e}")
        return

if __name__ == "__main__":
    with open("verification_log.txt", "w") as f:
        sys.stdout = f
        sys.stderr = f
        try:
            run_verification()
        except Exception as e:
            print(f"Script Crashed: {e}")
            import traceback
            traceback.print_exc()
