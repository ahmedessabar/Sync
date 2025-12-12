#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Analyse du drift en supposant que:
1. La durée TDMS est correcte (basée sur horloge cDAQ stable)
2. Le décalage au début et à la fin est le même (délai script constant)
3. On resample Xsens pour avoir le même nombre d'échantillons que TDMS
"""

import pandas as pd
import numpy as np
from nptdms import TdmsFile

print("=" * 80)
print("ANALYSE DU DRIFT AVEC RESAMPLING")
print("=" * 80)

# ============================================================================
# 1. CHARGER TDMS
# ============================================================================
print("\n📊 Chargement TDMS...")
tdms_file = TdmsFile.read("Moto_Chicane_100.tdms")
group = None
for g in tdms_file.groups():
    if 'P1' in g.name:
        group = g
        break
if group is None:
    group = tdms_file.groups()[0]

channel = group['Edges_RoueAR']
edges_cal = channel[:]
start_time = pd.to_datetime(channel.properties.get('wf_start_time')).tz_localize(None)
increment = channel.properties.get('wf_increment')

tdms_time = start_time + pd.to_timedelta(np.arange(len(edges_cal)) * increment, unit='s')
df_tdms = pd.DataFrame({'timestamp': tdms_time, 'Edges': edges_cal})

n_tdms = len(df_tdms)
tdms_start = df_tdms['timestamp'].min()
tdms_end = df_tdms['timestamp'].max()
tdms_duration = (tdms_end - tdms_start).total_seconds()
tdms_freq = n_tdms / tdms_duration

print(f"  Points: {n_tdms}")
print(f"  Durée: {tdms_duration:.6f} s")
print(f"  Fréquence: {tdms_freq:.2f} Hz")
print(f"  Start: {tdms_start}")
print(f"  End:   {tdms_end}")

# ============================================================================
# 2. CHARGER XSENS
# ============================================================================
print("\n📊 Chargement Xsens...")
df_txt = pd.read_csv("Moto_Chicane_100_P1.txt", sep='\t', skiprows=12)
df_txt.columns = df_txt.columns.str.strip()

req_cols = ['UTC_Year', 'UTC_Month', 'UTC_Day', 'UTC_Hour', 'UTC_Minute', 'UTC_Second', 'UTC_Nano']
df_txt = df_txt.dropna(subset=req_cols)

time_series = pd.to_datetime(df_txt[req_cols[:-1]].astype(int).rename(columns={
    'UTC_Year': 'year', 'UTC_Month': 'month', 'UTC_Day': 'day',
    'UTC_Hour': 'hour', 'UTC_Minute': 'minute', 'UTC_Second': 'second'
}))
df_txt['timestamp'] = time_series + pd.to_timedelta(df_txt['UTC_Nano'], unit='ns')

n_xsens_original = len(df_txt)
xsens_start_original = df_txt['timestamp'].min()
xsens_end_original = df_txt['timestamp'].max()
xsens_duration_original = (xsens_end_original - xsens_start_original).total_seconds()

print(f"  Points (original): {n_xsens_original}")
print(f"  Durée (original): {xsens_duration_original:.6f} s")
print(f"  Fréquence (original): {n_xsens_original/xsens_duration_original:.2f} Hz")
print(f"  Start: {xsens_start_original}")
print(f"  End:   {xsens_end_original}")

# ============================================================================
# 3. HYPOTHÈSE: Décalage constant au début et à la fin
# ============================================================================
print("\n" + "=" * 80)
print("HYPOTHÈSE: Décalage script constant")
print("=" * 80)

# Décalage observé au début
offset_start_observed = (xsens_start_original - tdms_start).total_seconds()
print(f"\nDécalage observé au début: {offset_start_observed:.6f} s")

# Si on suppose que le décalage au début = décalage à la fin (délai script)
# Alors la durée "réelle" de l'enregistrement Xsens devrait être:
xsens_duration_corrected = xsens_duration_original - offset_start_observed

print(f"\nDurée Xsens corrigée (en enlevant le décalage de début):")
print(f"  {xsens_duration_original:.6f} - {offset_start_observed:.6f} = {xsens_duration_corrected:.6f} s")

# ============================================================================
# 4. RESAMPLING: Même nombre d'échantillons que TDMS
# ============================================================================
print("\n" + "=" * 80)
print("RESAMPLING XSENS → même nombre d'échantillons que TDMS")
print("=" * 80)

print(f"\nNombre de points:")
print(f"  TDMS:  {n_tdms}")
print(f"  Xsens: {n_xsens_original} → {n_tdms} (resampling)")

# Créer un nouvel index temporel pour Xsens avec le même nombre de points que TDMS
# en gardant le même start et end
xsens_time_resampled = pd.date_range(
    start=xsens_start_original,
    end=xsens_end_original,
    periods=n_tdms
)

print(f"\nAprès resampling:")
print(f"  Durée: {(xsens_time_resampled[-1] - xsens_time_resampled[0]).total_seconds():.6f} s")
print(f"  Fréquence effective: {n_tdms / (xsens_time_resampled[-1] - xsens_time_resampled[0]).total_seconds():.2f} Hz")

# ============================================================================
# 5. CALCUL DU DRIFT AVEC RESAMPLING
# ============================================================================
print("\n" + "=" * 80)
print("CALCUL DU DRIFT (après resampling)")
print("=" * 80)

# Décalage au début (inchangé)
offset_start = (xsens_time_resampled[0] - tdms_start).total_seconds()

# Décalage à la fin (avec resampling)
offset_end = (xsens_time_resampled[-1] - tdms_end).total_seconds()

# Drift
drift = offset_end - offset_start

print(f"\n🔹 Décalage au début: {offset_start:+.6f} s")
print(f"🔹 Décalage à la fin:  {offset_end:+.6f} s")
print(f"🔹 DRIFT:              {drift:+.6f} s")

if abs(drift) < 0.001:
    print(f"\n✅ DRIFT NÉGLIGEABLE!")
    print(f"   → Hypothèse VALIDÉE: le décalage est constant (délai script)")
    print(f"   → Les horloges cDAQ et GPS sont bien synchronisées")
else:
    print(f"\n⚠️  DRIFT SIGNIFICATIF: {drift:.6f} s")
    drift_rate = drift / tdms_duration * 1e6  # ppm
    print(f"   → Taux de drift: {drift_rate:.2f} ppm")
    print(f"   → Il y a une dérive d'horloge entre cDAQ et GPS")

# ============================================================================
# 6. COMPARAISON
# ============================================================================
print("\n" + "=" * 80)
print("COMPARAISON: Avant vs Après resampling")
print("=" * 80)

offset_end_original = (xsens_end_original - tdms_end).total_seconds()
drift_original = offset_end_original - offset_start_observed

print(f"\nAVANT resampling:")
print(f"  Décalage fin: {offset_end_original:+.6f} s")
print(f"  Drift:        {drift_original:+.6f} s")

print(f"\nAPRÈS resampling:")
print(f"  Décalage fin: {offset_end:+.6f} s")
print(f"  Drift:        {drift:+.6f} s")

print(f"\nDifférence:")
print(f"  Réduction du drift: {drift_original - drift:.6f} s")

print("\n" + "=" * 80)
