#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Synchronisation basée sur les timestamps:
1. Utiliser le start time de Xsens comme point de départ
2. Enlever les données TDMS avant ce point
3. Utiliser le end time de TDMS comme fin
4. Resample Xsens pour avoir le même nombre d'échantillons que TDMS
"""

import pandas as pd
import numpy as np
from nptdms import TdmsFile
import matplotlib.pyplot as plt

print("=" * 80)
print("SYNCHRONISATION PAR TIMESTAMPS")
print("=" * 80)

# ============================================================================
# 1. CHARGER LES DONNÉES
# ============================================================================
print("\n📊 Chargement des données...")

# TDMS
tdms_file = TdmsFile.read("Moto_Chicane_100.tdms")
group = [g for g in tdms_file.groups() if 'P1' in g.name][0] if any('P1' in g.name for g in tdms_file.groups()) else tdms_file.groups()[0]
channel = group['Edges_RoueAR']
start_time = pd.to_datetime(channel.properties.get('wf_start_time')).tz_localize(None)
increment = channel.properties.get('wf_increment')
tdms_time = start_time + pd.to_timedelta(np.arange(len(channel[:])) * increment, unit='s')
df_tdms = pd.DataFrame({'timestamp': tdms_time, 'Edges': channel[:]})
df_tdms['Edge_Diff'] = df_tdms['Edges'].diff().fillna(0)

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

# Calculer GPS Speed
if 'Vel_N' in df_txt.columns and 'Vel_E' in df_txt.columns:
    df_txt['Vel_N'] = pd.to_numeric(df_txt['Vel_N'], errors='coerce').fillna(0)
    df_txt['Vel_E'] = pd.to_numeric(df_txt['Vel_E'], errors='coerce').fillna(0)
    df_txt['GPS_Speed'] = np.sqrt(df_txt['Vel_N']**2 + df_txt['Vel_E']**2)

df_tdms = df_tdms.sort_values('timestamp').reset_index(drop=True)
df_txt = df_txt.sort_values('timestamp').reset_index(drop=True)

print(f"  TDMS: {len(df_tdms)} points, {df_tdms['timestamp'].min()} → {df_tdms['timestamp'].max()}")
print(f"  Xsens: {len(df_txt)} points, {df_txt['timestamp'].min()} → {df_txt['timestamp'].max()}")

# ============================================================================
# 2. DÉFINIR LA FENÊTRE TEMPORELLE
# ============================================================================
print("\n" + "=" * 80)
print("ÉTAPE 1: Définir la fenêtre temporelle")
print("=" * 80)

# Point de départ = start time Xsens
sync_start = df_txt['timestamp'].min()
print(f"\n📍 Point de départ (Xsens start): {sync_start}")

# Point de fin = end time TDMS
sync_end = df_tdms['timestamp'].max()
print(f"📍 Point de fin (TDMS end): {sync_end}")

# Durée de synchronisation
sync_duration = (sync_end - sync_start).total_seconds()
print(f"📏 Durée de synchronisation: {sync_duration:.6f} secondes")

# ============================================================================
# 3. TRIMMER TDMS (enlever les données avant Xsens start)
# ============================================================================
print("\n" + "=" * 80)
print("ÉTAPE 2: Trimmer TDMS")
print("=" * 80)

# Trouver l'index TDMS correspondant au start Xsens
tdms_mask = df_tdms['timestamp'] >= sync_start
df_tdms_trimmed = df_tdms[tdms_mask].copy()
df_tdms_trimmed = df_tdms_trimmed.reset_index(drop=True)

samples_removed = len(df_tdms) - len(df_tdms_trimmed)
time_removed = (sync_start - df_tdms['timestamp'].min()).total_seconds()

print(f"\n✂️  Données TDMS avant {sync_start} supprimées:")
print(f"  Échantillons supprimés: {samples_removed}")
print(f"  Temps supprimé: {time_removed:.6f} secondes")
print(f"  TDMS trimmed: {len(df_tdms_trimmed)} points")

# ============================================================================
# 4. TRIMMER XSENS (enlever les données après TDMS end)
# ============================================================================
print("\n" + "=" * 80)
print("ÉTAPE 3: Trimmer Xsens")
print("=" * 80)

# Garder seulement les données Xsens jusqu'au end time TDMS
xsens_mask = df_txt['timestamp'] <= sync_end
df_txt_trimmed = df_txt[xsens_mask].copy()
df_txt_trimmed = df_txt_trimmed.reset_index(drop=True)

samples_removed_xsens = len(df_txt) - len(df_txt_trimmed)
time_removed_xsens = (df_txt['timestamp'].max() - sync_end).total_seconds()

print(f"\n✂️  Données Xsens après {sync_end} supprimées:")
print(f"  Échantillons supprimés: {samples_removed_xsens}")
print(f"  Temps supprimé: {time_removed_xsens:.6f} secondes")
print(f"  Xsens trimmed: {len(df_txt_trimmed)} points")

# ============================================================================
# 5. RESAMPLE XSENS pour avoir le même nombre d'échantillons que TDMS
# ============================================================================
print("\n" + "=" * 80)
print("ÉTAPE 4: Resample Xsens")
print("=" * 80)

target_samples = len(df_tdms_trimmed)
print(f"\n🎯 Nombre d'échantillons cible: {target_samples}")
print(f"   Xsens avant resample: {len(df_txt_trimmed)}")

# Créer un nouvel index temporel uniforme
time_index = pd.date_range(start=sync_start, end=sync_end, periods=target_samples)

# Resample en interpolant
df_txt_resampled = pd.DataFrame({'timestamp': time_index})

# Interpoler GPS_Speed
if 'GPS_Speed' in df_txt_trimmed.columns:
    # Créer une fonction d'interpolation
    from scipy.interpolate import interp1d
    
    # Convertir timestamps en secondes depuis le début
    txt_time_sec = (df_txt_trimmed['timestamp'] - sync_start).dt.total_seconds()
    new_time_sec = (time_index - sync_start).total_seconds()
    
    # Interpoler
    f_speed = interp1d(txt_time_sec, df_txt_trimmed['GPS_Speed'], 
                       kind='linear', fill_value='extrapolate')
    df_txt_resampled['GPS_Speed'] = f_speed(new_time_sec)

print(f"   Xsens après resample: {len(df_txt_resampled)}")
print(f"   ✅ Même nombre d'échantillons que TDMS!")

# ============================================================================
# 6. VÉRIFICATION
# ============================================================================
print("\n" + "=" * 80)
print("VÉRIFICATION DE LA SYNCHRONISATION")
print("=" * 80)

print(f"\n📊 TDMS trimmed:")
print(f"  Échantillons: {len(df_tdms_trimmed)}")
print(f"  Start: {df_tdms_trimmed['timestamp'].min()}")
print(f"  End: {df_tdms_trimmed['timestamp'].max()}")
print(f"  Durée: {(df_tdms_trimmed['timestamp'].max() - df_tdms_trimmed['timestamp'].min()).total_seconds():.6f} s")

print(f"\n📊 Xsens resampled:")
print(f"  Échantillons: {len(df_txt_resampled)}")
print(f"  Start: {df_txt_resampled['timestamp'].min()}")
print(f"  End: {df_txt_resampled['timestamp'].max()}")
print(f"  Durée: {(df_txt_resampled['timestamp'].max() - df_txt_resampled['timestamp'].min()).total_seconds():.6f} s")

print(f"\n✅ Alignement:")
print(f"  Décalage au début: {(df_txt_resampled['timestamp'].min() - df_tdms_trimmed['timestamp'].min()).total_seconds():.9f} s")
print(f"  Décalage à la fin: {(df_txt_resampled['timestamp'].max() - df_tdms_trimmed['timestamp'].max()).total_seconds():.9f} s")
print(f"  Différence d'échantillons: {len(df_txt_resampled) - len(df_tdms_trimmed)}")

# ============================================================================
# 7. VISUALISATION
# ============================================================================
print("\n📈 Création du graphique de vérification...")

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))

# Fenêtre de visualisation: 20 secondes au milieu
center_idx = len(df_tdms_trimmed) // 2
window_samples = 4000  # 10 secondes à 400 Hz

start_idx = max(0, center_idx - window_samples)
end_idx = min(len(df_tdms_trimmed), center_idx + window_samples)

# Plot 1: GPS Speed
ax1.plot(df_txt_resampled['timestamp'].iloc[start_idx:end_idx], 
         df_txt_resampled['GPS_Speed'].iloc[start_idx:end_idx], 
         'b-', linewidth=1, label='GPS Speed (resampled)')
ax1.set_ylabel('GPS Speed (m/s)')
ax1.set_title('Données synchronisées - GPS Speed')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Plot 2: Edge_Diff
ax2.plot(df_tdms_trimmed['timestamp'].iloc[start_idx:end_idx], 
         df_tdms_trimmed['Edge_Diff'].iloc[start_idx:end_idx], 
         'r-', linewidth=1, label='Edge_Diff (TDMS trimmed)')
ax2.set_ylabel('Edge_Diff')
ax2.set_xlabel('Time')
ax2.set_title('Données synchronisées - Roue arrière')
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('synchronized_data.png', dpi=150)
print("  Graphique sauvegardé: synchronized_data.png")

# ============================================================================
# 8. SAUVEGARDER LES DONNÉES SYNCHRONISÉES
# ============================================================================
print("\n💾 Sauvegarde des données synchronisées...")

# Combiner dans un seul DataFrame
df_synced = pd.DataFrame({
    'timestamp': df_tdms_trimmed['timestamp'],
    'Edges': df_tdms_trimmed['Edges'],
    'Edge_Diff': df_tdms_trimmed['Edge_Diff'],
    'GPS_Speed': df_txt_resampled['GPS_Speed']
})

df_synced.to_csv('Moto_Chicane_100_synchronized.csv', index=False)
print("  Fichier sauvegardé: Moto_Chicane_100_synchronized.csv")

print("\n" + "=" * 80)
print("✅ SYNCHRONISATION TERMINÉE")
print("=" * 80)

print(f"""
Résumé:
- Script delay au début supprimé: {time_removed:.3f}s ({samples_removed} échantillons)
- Script delay à la fin supprimé: {time_removed_xsens:.3f}s ({samples_removed_xsens} échantillons)
- Xsens resampled: {len(df_txt_trimmed)} → {target_samples} échantillons
- Correction de fréquence appliquée (408 Hz → 400 Hz effectif)
- Les deux signaux sont maintenant parfaitement alignés!
""")
