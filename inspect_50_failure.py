
import pandas as pd
import numpy as np
from nptdms import TdmsFile
import os

# PATHS
BASE = r"c:\Users\es-sabar\Documents\PreTest\Moto_04112025_chicane_sec"
TDMS_PATH = os.path.join(BASE, "labview_data", "Moto_Chicane_50.tdms")
XSENS_P1 = os.path.join(BASE, "Moto_chicane_TXT", "Moto_Chicane_50_P1.txt")
XSENS_P2 = os.path.join(BASE, "Moto_chicane_TXT", "Moto_Chicane_50_P2.txt")

def load_xsens_head(path):
    # Quick Start Time Extract
    try:
        h_idx = None
        with open(path, 'r', errors='ignore') as f:
            for i, l in enumerate(f):
                if 'UTC_Year' in l: h_idx=i; break
        if h_idx is None: return None
        
        df = pd.read_csv(path, sep=None, header=h_idx, nrows=5, engine='python')
        df.columns = df.columns.str.strip()
        
        req = ['UTC_Year', 'UTC_Month', 'UTC_Day', 'UTC_Hour', 'UTC_Minute', 'UTC_Second', 'UTC_Nano']
        ts = pd.to_datetime(df[req[:-1]].astype(int).rename(columns={'UTC_Year':'year','UTC_Month':'month','UTC_Day':'day','UTC_Hour':'hour','UTC_Minute':'minute','UTC_Second':'second'}))
        ts += pd.to_timedelta(df['UTC_Nano'], unit='ns')
        return ts.min()
    except Exception as e:
        print(e)
        return None

def inspect_tdms_group(path, group_name):
    tdms = TdmsFile.read(path)
    found = False
    for g in tdms.groups():
        if g.name == group_name:
            found = True
            print(f"--- Group: {group_name} ---")
            
            # 1. Properties
            print("Group Properties:", g.properties)
            
            # 2. Channel Properties
            if 'Edges_RoueAR' in g:
                c = g['Edges_RoueAR']
                print("Channel 'Edges_RoueAR' Props:", c.properties)
                data = c[:]
                print(f"Data Length: {len(data)}")
                print(f"First 10 values: {data[:10]}")
                print(f"Last 10 values: {data[-10:]}")
                
                # Check Reset manual
                diffs = np.diff(data)
                resets = np.where(diffs < -100)[0]
                print(f"Diffs < -100 found at: {resets}")
            else:
                print("Channel Edges_RoueAR NOT FOUND")
                
            # 3. Root Props
            # print("Root Props:", tdms.properties)

print("=== XSENS STARTED TIMES ===")
print("P1:", load_xsens_head(XSENS_P1))
print("P2:", load_xsens_head(XSENS_P2))

print("\n=== TDMS INSPECTION ===")
inspect_tdms_group(TDMS_PATH, "P1")
print("\n")
inspect_tdms_group(TDMS_PATH, "P2")
