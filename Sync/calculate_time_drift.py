#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Calcul du décalage temporel entre TDMS et TXT au début et à la fin
"""

import pandas as pd
import numpy as np
from nptdms import TdmsFile

# Chemins des fichiers
tdms_path = "Moto_Chicane_100.tdms"
txt_path = "Moto_Chicane_100_P1.txt"

print("=" * 80)
print("ANALYSE DU DÉCALAGE TEMPOREL - Début et Fin")
print("=" * 80)

# ============================================================================
# 1. CHARGER TDMS
# ============================================================================
print("\n📊 Chargement TDMS...")
tdms_file = TdmsFile.read(tdms_path)
group = None
for g in tdms_file.groups():
    if 'P1' in g.name:
        group = g
        break
if group is None:
    group = tdms_file.groups()[0]

channel = group['Edges_RoueAR']
edges_cal = channel[:]

start_time = channel.properties.get('wf_start_time')
increment = channel.properties.get('wf_increment')

start_time = pd.to_datetime(start_time).tz_localize(None)
tdms_time = start_time + pd.to_timedelta(np.arange(len(edges_cal)) * increment, unit='s')
df_tdms = pd.DataFrame({'timestamp': tdms_time, 'Edges': edges_cal})

tdms_start = df_tdms['timestamp'].min()
tdms_end = df_tdms['timestamp'].max()
tdms_duration = (tdms_end - tdms_start).total_seconds()

print(f"  Nombre de points: {len(df_tdms)}")
print(f"  Start: {tdms_start}")
print(f"  End:   {tdms_end}")
print(f"  Durée: {tdms_duration:.3f} secondes")

# ============================================================================
# 2. CHARGER TXT
# ============================================================================
print("\n📊 Chargement TXT (GPS/Xsens)...")
df_txt = pd.read_csv(txt_path, sep='\t', skiprows=12)
df_txt.columns = df_txt.columns.str.strip()

req_cols = ['UTC_Year', 'UTC_Month', 'UTC_Day', 'UTC_Hour', 'UTC_Minute', 'UTC_Second', 'UTC_Nano']
df_txt = df_txt.dropna(subset=req_cols)

time_series = pd.to_datetime(df_txt[req_cols[:-1]].astype(int).rename(columns={
    'UTC_Year': 'year', 'UTC_Month': 'month', 'UTC_Day': 'day',
    'UTC_Hour': 'hour', 'UTC_Minute': 'minute', 'UTC_Second': 'second'
}))
df_txt['timestamp'] = time_series + pd.to_timedelta(df_txt['UTC_Nano'], unit='ns')

txt_start = df_txt['timestamp'].min()
txt_end = df_txt['timestamp'].max()
txt_duration = (txt_end - txt_start).total_seconds()

print(f"  Nombre de points: {len(df_txt)}")
print(f"  Start: {txt_start}")
print(f"  End:   {txt_end}")
print(f"  Durée: {txt_duration:.3f} secondes")

# ============================================================================
# 3. CALCUL DES DÉCALAGES
# ============================================================================
print("\n" + "=" * 80)
print("📏 DÉCALAGES TEMPORELS (TXT - TDMS)")
print("=" * 80)

offset_start = (txt_start - tdms_start).total_seconds()
offset_end = (txt_end - tdms_end).total_seconds()
drift = offset_end - offset_start

print(f"\n🔹 DÉCALAGE AU DÉBUT:")
print(f"   TXT Start - TDMS Start = {offset_start:+.6f} secondes")
if offset_start > 0:
    print(f"   → Le fichier TXT commence {offset_start:.6f}s APRÈS le TDMS")
else:
    print(f"   → Le fichier TXT commence {abs(offset_start):.6f}s AVANT le TDMS")

print(f"\n🔹 DÉCALAGE À LA FIN:")
print(f"   TXT End - TDMS End = {offset_end:+.6f} secondes")
if offset_end > 0:
    print(f"   → Le fichier TXT se termine {offset_end:.6f}s APRÈS le TDMS")
else:
    print(f"   → Le fichier TXT se termine {abs(offset_end):.6f}s AVANT le TDMS")

print(f"\n🔹 DÉRIVE TEMPORELLE (Drift):")
print(f"   Offset_End - Offset_Start = {drift:+.6f} secondes")
if abs(drift) < 0.001:
    print(f"   → Dérive négligeable : les horloges sont bien synchronisées")
elif drift > 0:
    print(f"   → Le fichier TXT accumule un retard de {drift:.6f}s")
else:
    print(f"   → Le fichier TXT accumule une avance de {abs(drift):.6f}s")

print(f"\n🔹 DIFFÉRENCE DE DURÉE:")
duration_diff = txt_duration - tdms_duration
print(f"   TXT Duration - TDMS Duration = {duration_diff:+.3f} secondes")

print("\n" + "=" * 80)
print("FIN DE L'ANALYSE")
print("=" * 80)
