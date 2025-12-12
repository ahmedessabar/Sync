#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Analyse de la détection de mouvement GPS vs TDMS
"""

import pandas as pd
import numpy as np
from nptdms import TdmsFile
import matplotlib.pyplot as plt

print("=" * 80)
print("ANALYSE DE LA DÉTECTION DE MOUVEMENT")
print("=" * 80)

# Charger TDMS
tdms_file = TdmsFile.read("Moto_Chicane_100.tdms")
group = [g for g in tdms_file.groups() if 'P1' in g.name][0] if any('P1' in g.name for g in tdms_file.groups()) else tdms_file.groups()[0]
channel = group['Edges_RoueAR']
start_time = pd.to_datetime(channel.properties.get('wf_start_time')).tz_localize(None)
increment = channel.properties.get('wf_increment')
tdms_time = start_time + pd.to_timedelta(np.arange(len(channel[:])) * increment, unit='s')
df_tdms = pd.DataFrame({'timestamp': tdms_time, 'Edges': channel[:]})
df_tdms['Edge_Diff'] = df_tdms['Edges'].diff().fillna(0)

# Charger Xsens
df_txt = pd.read_csv("Moto_Chicane_100_P1.txt", sep='\t', skiprows=12)
df_txt.columns = df_txt.columns.str.strip()
req_cols = ['UTC_Year', 'UTC_Month', 'UTC_Day', 'UTC_Hour', 'UTC_Minute', 'UTC_Second', 'UTC_Nano']
df_txt = df_txt.dropna(subset=req_cols)
time_series = pd.to_datetime(df_txt[req_cols[:-1]].astype(int).rename(columns={
    'UTC_Year': 'year', 'UTC_Month': 'month', 'UTC_Day': 'day',
    'UTC_Hour': 'hour', 'UTC_Minute': 'minute', 'UTC_Second': 'second'
}))
df_txt['timestamp'] = time_series + pd.to_timedelta(df_txt['UTC_Nano'], unit='ns')

# Calculer GPS Speed
if 'Vel_N' in df_txt.columns and 'Vel_E' in df_txt.columns:
    df_txt['Vel_N'] = pd.to_numeric(df_txt['Vel_N'], errors='coerce').fillna(0)
    df_txt['Vel_E'] = pd.to_numeric(df_txt['Vel_E'], errors='coerce').fillna(0)
    df_txt['GPS_Speed'] = np.sqrt(df_txt['Vel_N']**2 + df_txt['Vel_E']**2)

# Trier
df_tdms = df_tdms.sort_values('timestamp').reset_index(drop=True)
df_txt = df_txt.sort_values('timestamp').reset_index(drop=True)

print("\n📊 Statistiques GPS Speed (premiers 10 secondes):")
mask_10s = df_txt['timestamp'] < df_txt['timestamp'].min() + pd.Timedelta(seconds=10)
print(f"  Min: {df_txt[mask_10s]['GPS_Speed'].min():.4f} m/s")
print(f"  Max: {df_txt[mask_10s]['GPS_Speed'].max():.4f} m/s")
print(f"  Moyenne: {df_txt[mask_10s]['GPS_Speed'].mean():.4f} m/s")
print(f"  Std: {df_txt[mask_10s]['GPS_Speed'].std():.4f} m/s")

# Détection avec différents seuils
print("\n" + "=" * 80)
print("DÉTECTION AVEC DIFFÉRENTS SEUILS GPS")
print("=" * 80)

thresholds = [0.1, 0.3, 0.5, 1.0, 2.0]
for thresh in thresholds:
    gps_idx = df_txt[df_txt['GPS_Speed'] > thresh].index.min()
    if pd.notna(gps_idx):
        gps_time = df_txt.loc[gps_idx, 'timestamp']
        gps_speed = df_txt.loc[gps_idx, 'GPS_Speed']
        print(f"\nSeuil {thresh:.1f} m/s:")
        print(f"  Index: {gps_idx}")
        print(f"  Time: {gps_time}")
        print(f"  Speed: {gps_speed:.4f} m/s")

# Détection TDMS
print("\n" + "=" * 80)
print("DÉTECTION TDMS (Edge_Diff > 0)")
print("=" * 80)

tdms_idx = df_tdms[df_tdms['Edge_Diff'] > 0].index.min()
tdms_time = df_tdms.loc[tdms_idx, 'timestamp']
print(f"  Index: {tdms_idx}")
print(f"  Time: {tdms_time}")
print(f"  Edge_Diff: {df_tdms.loc[tdms_idx, 'Edge_Diff']:.4f}")

# Visualisation
print("\n📈 Création du graphique de comparaison...")
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))

# Zone d'intérêt : 10 secondes avant et après le début détecté
center_time = tdms_time
window = pd.Timedelta(seconds=10)

mask_tdms = (df_tdms['timestamp'] >= center_time - window) & (df_tdms['timestamp'] <= center_time + window)
mask_gps = (df_txt['timestamp'] >= center_time - window) & (df_txt['timestamp'] <= center_time + window)

# Plot 1: GPS Speed
ax1.plot(df_txt[mask_gps]['timestamp'], df_txt[mask_gps]['GPS_Speed'], 'b-', linewidth=1, label='GPS Speed')
ax1.axhline(y=0.5, color='orange', linestyle='--', alpha=0.5, label='Seuil 0.5 m/s')
ax1.axhline(y=1.0, color='red', linestyle='--', alpha=0.5, label='Seuil 1.0 m/s')
ax1.axvline(tdms_time, color='green', linestyle='--', linewidth=2, label='Détection TDMS')
ax1.set_ylabel('GPS Speed (m/s)')
ax1.set_title('Détection de mouvement - GPS Speed')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Plot 2: Edge_Diff
ax2.plot(df_tdms[mask_tdms]['timestamp'], df_tdms[mask_tdms]['Edge_Diff'], 'r-', linewidth=1, label='Edge_Diff (TDMS)')
ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
ax2.axvline(tdms_time, color='green', linestyle='--', linewidth=2, label='Détection TDMS')
ax2.set_ylabel('Edge_Diff')
ax2.set_xlabel('Time')
ax2.set_title('Détection de mouvement - Roue arrière (TDMS)')
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('movement_detection_analysis.png', dpi=150)
print("  Graphique sauvegardé: movement_detection_analysis.png")

print("\n" + "=" * 80)
print("PROBLÈMES POTENTIELS AVEC GPS")
print("=" * 80)

print("""
⚠️  Le GPS peut avoir des problèmes:

1. BRUIT GPS:
   - Le GPS peut montrer une vitesse > 0 même à l'arrêt
   - Précision typique: ±0.1-0.5 m/s
   - Peut fluctuer avant le vrai démarrage

2. LATENCE GPS:
   - Le GPS peut avoir un délai de réponse
   - Peut détecter le mouvement après que la roue a commencé à tourner

3. SEUIL ARBITRAIRE:
   - Le choix de 0.5 m/s est arbitraire
   - Peut être trop sensible ou pas assez

✅ SOLUTION ALTERNATIVE:
   - Utiliser UNIQUEMENT la détection TDMS (Edge_Diff)
   - Aligner les timestamps en utilisant le start time brut + offset fixe
   - Ou utiliser l'accélération au lieu de la vitesse GPS
""")

print("\n" + "=" * 80)
