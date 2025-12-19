
import sys

# 1. IMPORTS
try:
    import pandas as pd
    import numpy as np
    from nptdms import TdmsFile
    from scipy.interpolate import interp1d
    from datetime import datetime, timedelta
    import os
    import glob
    import re
except Exception as e:
    with open("script_error.log", "w") as f:
        f.write(f"IMPORT ERROR: {e}")
    sys.exit(1)

# 2. CONFIGURATION
BASE_DIR = r'Moto_Freinage_mouille'
DIR_TXT = os.path.join(BASE_DIR, 'Moto_Freinage_mouille_TXT')
DIR_TDMS = os.path.join(BASE_DIR, 'LabviewData')
DIR_OUT = os.path.join(BASE_DIR, 'Merged_CSV')

TDMS_FREQ = 400.0
MAGIC_OFFSET = 0.2679

try:
    os.makedirs(DIR_OUT, exist_ok=True)
except Exception as e:
    with open("script_error.log", "w") as f:
        f.write(f"CONFIG ERROR (makedirs): {e}")
    sys.exit(1)

# 3. FUNCTIONS
def load_xsens(path):
    h_idx = None
    try:
        with open(path, 'r', errors='ignore') as f:
            for i, l in enumerate(f):
                if l.strip().startswith('PacketCounter'): h_idx=i; break
        if h_idx is None:
             with open(path, 'r', errors='ignore') as f:
                for i, l in enumerate(f): 
                    if 'UTC_Year' in l: h_idx=i; break
        if h_idx is None: return pd.DataFrame()
        
        try: df = pd.read_csv(path, sep='\t', header=h_idx)
        except: df = pd.read_csv(path, sep=r'\s+', header=h_idx)
        
        df.columns = df.columns.str.strip()
        # Cleaning Ghost Packets
        check_cols = [c for c in ['Acc_X', 'FreeAcc_E', 'Gyr_X'] if c in df.columns]
        if check_cols:
            df.dropna(subset=check_cols, how='all', inplace=True)
            
        req = ['UTC_Year', 'UTC_Month', 'UTC_Day', 'UTC_Hour', 'UTC_Minute', 'UTC_Second', 'UTC_Nano']
        if set(req).issubset(df.columns):
            df.dropna(subset=req, inplace=True)
            ts = pd.to_datetime(df[req[:-1]].astype(int).rename(columns={'UTC_Year':'year','UTC_Month':'month','UTC_Day':'day','UTC_Hour':'hour','UTC_Minute':'minute','UTC_Second':'second'}))
            df['TS_UTC'] = ts + pd.to_timedelta(df['UTC_Nano'], unit='ns')
            df.drop(columns=req, inplace=True)
            df.sort_values('TS_UTC', inplace=True)
            df.drop_duplicates(subset=['TS_UTC'], inplace=True)
            return df
    except: return pd.DataFrame()

def load_tdms_smart(path, group_name, xsens_start_ref):
    stats = {
        "TDMS_Found": False, "Reset_Detected": False, "Reset_Index": 0,
        "Sync_Method": "Unknown", "TDMS_Start_Time": None, "TDMS_Points_Valid": 0
    }
    
    try:
        tdms = TdmsFile.read(path)
        stats["TDMS_Found"] = True
        
        target_group = None
        for g in tdms.groups():
            if g.name == group_name: target_group = g; break
        if not target_group: return pd.DataFrame(), stats
        
        # 1. Données Brutes
        data = {}
        for c in target_group.channels(): data[c.name] = c[:]
        if not data: return pd.DataFrame(), stats
        l_min = min(len(v) for v in data.values())
        data = {k: v[:l_min] for k,v in data.items()}
        df = pd.DataFrame(data)
        
        base_start_time = None
        
        # 2. Detection Reset
        start_index = 0
        if 'Edges_RoueAR' in df.columns:
            diffs = np.diff(df['Edges_RoueAR'].values)
            resets = np.where(diffs < -100)[0]
            if len(resets) > 0:
                start_index = resets[0] + 1
                stats["Reset_Detected"] = True
                stats["Reset_Index"] = int(start_index)

        # 3. Stratégie Timestamp
        if stats["Reset_Detected"]:
            # FORCED SYNC
            base_start_time = xsens_start_ref + timedelta(seconds=MAGIC_OFFSET)
            stats["Sync_Method"] = "Forced (Xsens+Offset)"
        else:
            # METADATA SYNC
            try:
                if 'Edges_RoueAR' in target_group:
                    chan = target_group['Edges_RoueAR']
                    if 'wf_start_time' in chan.properties:
                         base_start_time = pd.to_datetime(chan.properties['wf_start_time']).tz_localize(None)
                if not base_start_time and 'wf_start_time' in tdms.properties:
                     base_start_time = pd.to_datetime(tdms.properties['wf_start_time']).tz_localize(None)
            except: pass
            
            stats["Sync_Method"] = "Metadata"
            
        stats["TDMS_Start_Time"] = base_start_time
        
        # 4. Slice if reset
        if start_index > 0:
            df = df.iloc[start_index:].copy().reset_index(drop=True)
            
        stats["TDMS_Points_Valid"] = len(df)
            
        # 5. Index Create
        if base_start_time:
            time_index = pd.date_range(start=base_start_time, periods=len(df), freq=f'{1000/TDMS_FREQ}ms')
            df['TDMS_Timestamp'] = time_index
            df.set_index('TDMS_Timestamp', inplace=True)
            df.columns = [f"TDMS_{c}" for c in df.columns]
            return df, stats
        else:
            stats["Sync_Method"] = "FAILED (No Time)"
            return pd.DataFrame(), stats

    except Exception as e: 
        stats["Error"] = str(e)
        return pd.DataFrame(), stats

# 4. MAIN EXECUTION
try:
    print(f"Searching in: {os.path.abspath(DIR_TXT)}")
    txt_files = glob.glob(os.path.join(DIR_TXT, "*.txt"))
    print(f"Fichiers trouvés : {len(txt_files)}")

    LOG_DATA = []

    for f_txt in txt_files:
        basename = os.path.basename(f_txt)
        
        entry = {
            "File_Name": basename,
            "Status": "Init",
            "Reset_Detected": False, 
            "Sync_Strategy": None,
            "Xsens_Start": None, 
            "TDMS_Start": None,
            "Xsens_Points": 0,
            "TDMS_Points": 0,
            "Reset_Index": 0
        }
        
        # REGEX Freinage : Moto_Freinage_mouille_80_P1.txt
        match = re.search(r'Moto_Freinage_mouille_(\d+)_(\w+)\.txt$', basename)
        if not match:
            print(f"[SKIP] Format nom incorrect : {basename}")
            entry["Status"] = "Skipped (Name Format)"
            LOG_DATA.append(entry)
            continue
            
        speed = match.group(1)
        group = match.group(2)
        
        tdms_name = f"Moto_Freinage_mouille_{speed}.tdms"
        f_tdms = os.path.join(DIR_TDMS, tdms_name)
        
        print(f"Traitement : {basename} <-> {tdms_name} [{group}] ...", end='')
        sys.stdout.flush()
        
        if not os.path.exists(f_tdms):
            print(f" [ERR TDMS MISSING]")
            entry["Status"] = "Missing TDMS"
            LOG_DATA.append(entry)
            continue
        
        # 1. Load Xsens
        df_xsens = load_xsens(f_txt)
        if df_xsens.empty:
            print(" [ERR Xsens]")
            entry["Status"] = "Error Xsens Load"
            LOG_DATA.append(entry)
            continue
        
        entry["Xsens_Start"] = df_xsens['TS_UTC'].min()
        entry["Xsens_Points"] = len(df_xsens)
            
        # 2. Load TDMS (Smart)
        xsens_start = df_xsens['TS_UTC'].min()
        df_tdms, stats = load_tdms_smart(f_tdms, group, xsens_start)
        
        entry["TDMS_Start"] = stats.get("TDMS_Start_Time")
        entry["TDMS_Points"] = stats.get("TDMS_Points_Valid")
        entry["Reset_Detected"] = stats.get("Reset_Detected")
        entry["Reset_Index"] = stats.get("Reset_Index")
        entry["Sync_Strategy"] = stats.get("Sync_Method")
        
        if df_tdms.empty:
            print(f" [ERR TDMS: {stats.get('Error', 'Unknown')}]")
            entry["Status"] = "Error TDMS Load"
            LOG_DATA.append(entry)
            continue
            
        # 3. Merge
        t_start = max(df_xsens['TS_UTC'].min(), df_tdms.index.min())
        t_end = min(df_xsens['TS_UTC'].max(), df_tdms.index.max())
        
        # --- CHECK OVERLAP & RETRY ---
        overlap_ok = True
        if t_end < t_start: overlap_ok = False
        
        if not overlap_ok:
            print(f" [WARN No Overlap] -> Metadata: {stats['TDMS_Start_Time']} vs Xsens: {xsens_start}")
            
            # VALIDATION LONGUEUR
            len_xs = len(df_xsens)
            len_td = len(df_tdms)
            diff_rel = abs(len_xs - len_td) / max(len_xs, 1)
            
            if diff_rel > 0.15: # 15% Tolérrance
                print(f"   -> [ERR] Length Mismatch ({len_xs} vs {len_td}). Diff={diff_rel:.1%}. ABORT.")
                entry["Status"] = f"Invalid (Length Mismatch {diff_rel:.0%})"
                LOG_DATA.append(entry)
                continue
                
            print("   -> RETRY with Forced Sync (Xsens + Offset)...", end='')
            
            # FALLBACK FORCE SYNC
            forced_start = entry["Xsens_Start"] + timedelta(seconds=MAGIC_OFFSET)
            
            # Re-index TDMS
            time_index = pd.date_range(start=forced_start, periods=len(df_tdms), freq=f'{1000/TDMS_FREQ}ms')
            df_tdms = df_tdms.reset_index(drop=True)
            df_tdms['TDMS_Timestamp'] = time_index
            df_tdms.set_index('TDMS_Timestamp', inplace=True)
            
            # Update Stats
            entry["Sync_Strategy"] += " + FALLBACK (Force)"
            stats["TDMS_Start_Time"] = forced_start
            entry["TDMS_Start"] = forced_start
            
            # Re-calc Interval
            t_start = max(df_xsens['TS_UTC'].min(), df_tdms.index.min())
            t_end = min(df_xsens['TS_UTC'].max(), df_tdms.index.max())
            
            if t_end < t_start:
                print(" [ERR SYNC FAILED AGAIN]")
                entry["Status"] = "Sync Error (Even after Force)"
                LOG_DATA.append(entry)
                continue

        df_merged = df_xsens[(df_xsens['TS_UTC'] >= t_start) & (df_xsens['TS_UTC'] <= t_end)].copy()
        df_merged.set_index('TS_UTC', inplace=True)
        
        try:
            t_slave = (df_tdms.index - pd.Timestamp("1970-01-01")) // pd.Timedelta('1ns') / 1e9
            t_master = (df_merged.index - pd.Timestamp("1970-01-01")) // pd.Timedelta('1ns') / 1e9
            
            for col in df_tdms.columns:
                f = interp1d(t_slave, df_tdms[col].values, kind='linear', fill_value="extrapolate")
                df_merged[col] = f(t_master)
                
            out_name = basename.replace('.txt', '_merged.csv')
            out_path = os.path.join(DIR_OUT, out_name)
            df_merged.to_csv(out_path, date_format='%d/%m/%Y %H:%M:%S.%f')
            
            print(f" [OK] -> {entry['Sync_Strategy']}")
            entry["Status"] = "Success"
            
        except Exception as e:
            print(f" [ERR MERGE: {e}]")
            entry["Status"] = f"Merge Exception: {e}"

        LOG_DATA.append(entry)

    # SAVE LOG REPORT
    df_log = pd.DataFrame(LOG_DATA)
    log_path = os.path.join(DIR_OUT, 'Batch_Report_Freinage.csv')
    df_log.to_csv(log_path, index=False)
    print(f"\nRapport généré : {log_path}")
    if not df_log.empty:
        print(df_log[['File_Name', 'Status', 'Reset_Detected', 'Sync_Strategy']].to_string())
    else:
        print("Empty log.")

except Exception as e:
    import traceback
    err = traceback.format_exc()
    print(f"CRASH: {err}")
    with open("script_error.log", "w") as f:
        f.write(f"RUNTIME ERROR:\n{err}")
    sys.exit(1)
