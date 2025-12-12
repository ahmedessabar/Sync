#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Estimation séparée du drift de script et du drift d'horloge
"""

import pandas as pd
import numpy as np
from nptdms import TdmsFile

print("=" * 80)
print("ESTIMATION: DRIFT SCRIPT vs DRIFT HORLOGE")
print("=" * 80)

# ============================================================================
# 1. CHARGER LES DONNÉES
# ============================================================================
print("\n📊 Chargement des données...")

# TDMS
tdms_file = TdmsFile.read("Moto_Chicane_100.tdms")
group = None
for g in tdms_file.groups():
    if 'P1' in g.name:
        group = g
        break
if group is None:
    group = tdms_file.groups()[0]

channel = group['Edges_RoueAR']
start_time = pd.to_datetime(channel.properties.get('wf_start_time')).tz_localize(None)
increment = channel.properties.get('wf_increment')
edges_cal = channel[:]

tdms_time = start_time + pd.to_timedelta(np.arange(len(edges_cal)) * increment, unit='s')
df_tdms = pd.DataFrame({'timestamp': tdms_time, 'Edges': edges_cal})

# Xsens
df_txt = pd.read_csv("Moto_Chicane_100_P1.txt", sep='\t', skiprows=12)
df_txt.columns = df_txt.columns.str.strip()
req_cols = ['UTC_Year', 'UTC_Month', 'UTC_Day', 'UTC_Hour', 'UTC_Minute', 'UTC_Second', 'UTC_Nano']
df_txt = df_txt.dropna(subset=req_cols)
time_series = pd.to_datetime(df_txt[req_cols[:-1]].astype(int).rename(columns={
    'UTC_Year': 'year', 'UTC_Month': 'month', 'UTC_Day': 'day',
    'UTC_Hour': 'hour', 'UTC_Minute': 'minute', 'UTC_Second': 'second'
}))
df_txt['timestamp'] = time_series + pd.to_timedelta(df_txt['UTC_Nano'], unit='ns')

# ============================================================================
# 2. DONNÉES OBSERVÉES
# ============================================================================
tdms_start = df_tdms['timestamp'].min()
tdms_end = df_tdms['timestamp'].max()
xsens_start = df_txt['timestamp'].min()
xsens_end = df_txt['timestamp'].max()

offset_start = (xsens_start - tdms_start).total_seconds()
offset_end = (xsens_end - tdms_end).total_seconds()
drift_total = offset_end - offset_start

tdms_duration = (tdms_end - tdms_start).total_seconds()

print(f"\n📏 Mesures observées:")
print(f"  Décalage au début:  {offset_start:.6f} s")
print(f"  Décalage à la fin:  {offset_end:.6f} s")
print(f"  Drift total:        {drift_total:.6f} s")
print(f"  Durée TDMS:         {tdms_duration:.3f} s")

# ============================================================================
# 3. MODÈLE: offset = script_delay + clock_drift(t)
# ============================================================================
print("\n" + "=" * 80)
print("MODÈLE DE DÉCOMPOSITION")
print("=" * 80)

print("""
Hypothèses:
1. SCRIPT DELAY (δ_script):
   - Constant au début ET à la fin
   - Temps pour activer MT Manager + Ctrl+R
   
2. CLOCK DRIFT (δ_clock):
   - Proportionnel au temps écoulé
   - Dérive entre horloge cDAQ et GPS
   
Modèle:
   offset(t) = δ_script + δ_clock × t
   
Au début (t=0):
   offset_start = δ_script + 0 = δ_script
   
À la fin (t=T):
   offset_end = δ_script + δ_clock × T
""")

# ============================================================================
# 4. CALCUL
# ============================================================================
print("\n" + "=" * 80)
print("ESTIMATION DES PARAMÈTRES")
print("=" * 80)

# Script delay = offset au début (quand t=0, pas de drift d'horloge encore)
script_delay = offset_start

# Clock drift = (offset_end - offset_start) / durée
clock_drift_total = drift_total
clock_drift_rate = clock_drift_total / tdms_duration  # secondes de drift par seconde

print(f"\n🔹 SCRIPT DELAY (δ_script):")
print(f"   {script_delay:.6f} secondes")
print(f"   → Temps constant de démarrage du script")

print(f"\n🔹 CLOCK DRIFT (δ_clock):")
print(f"   Total sur {tdms_duration:.1f}s: {clock_drift_total:.6f} secondes")
print(f"   Taux: {clock_drift_rate:.9f} s/s")
print(f"   Taux: {clock_drift_rate * 1e6:.2f} ppm (parties par million)")
print(f"   Taux: {clock_drift_rate * 100:.4f} %")

# ============================================================================
# 5. VÉRIFICATION
# ============================================================================
print("\n" + "=" * 80)
print("VÉRIFICATION DU MODÈLE")
print("=" * 80)

offset_start_model = script_delay
offset_end_model = script_delay + clock_drift_rate * tdms_duration

print(f"\nDécalage au début:")
print(f"  Observé: {offset_start:.6f} s")
print(f"  Modèle:  {offset_start_model:.6f} s")
print(f"  Erreur:  {abs(offset_start - offset_start_model):.9f} s ✓")

print(f"\nDécalage à la fin:")
print(f"  Observé: {offset_end:.6f} s")
print(f"  Modèle:  {offset_end_model:.6f} s")
print(f"  Erreur:  {abs(offset_end - offset_end_model):.9f} s ✓")

# ============================================================================
# 6. INTERPRÉTATION
# ============================================================================
print("\n" + "=" * 80)
print("INTERPRÉTATION")
print("=" * 80)

print(f"\n📌 SCRIPT DELAY: {script_delay:.3f} secondes")
print(f"   - Délai constant pour démarrer/arrêter l'enregistrement Xsens")
print(f"   - Inclut: activation fenêtre + envoi Ctrl+R + traitement MT Manager")

print(f"\n📌 CLOCK DRIFT: {clock_drift_rate * 1e6:.2f} ppm")
if clock_drift_rate * 1e6 < 100:
    print(f"   - Drift faible: horloges bien synchronisées")
elif clock_drift_rate * 1e6 < 1000:
    print(f"   - Drift modéré: typique pour horloge matérielle standard")
else:
    print(f"   - Drift élevé: horloge cDAQ dérive significativement vs GPS")

print(f"\n📌 IMPACT sur {tdms_duration:.1f}s d'enregistrement:")
print(f"   - Décalage dû au script: {script_delay:.3f} s")
print(f"   - Décalage dû au drift:  {clock_drift_total:.3f} s")
print(f"   - Total:                 {offset_end:.3f} s")

# ============================================================================
# 7. ÉCHANTILLONS SUPPLÉMENTAIRES
# ============================================================================
print("\n" + "=" * 80)
print("ÉCHANTILLONS SUPPLÉMENTAIRES DANS XSENS")
print("=" * 80)

freq = 400  # Hz configuré
samples_script = script_delay * freq * 2  # ×2 car début + fin
samples_drift = clock_drift_total * freq

print(f"\nÀ 400 Hz:")
print(f"  Échantillons dus au script (début+fin): {samples_script:.0f}")
print(f"  Échantillons dus au drift d'horloge:    {samples_drift:.0f}")
print(f"  Total théorique:                        {samples_script + samples_drift:.0f}")
print(f"  Total observé:                          {len(df_txt) - len(df_tdms)}")
print(f"  Différence:                             {abs((samples_script + samples_drift) - (len(df_txt) - len(df_tdms))):.0f}")

print("\n" + "=" * 80)
