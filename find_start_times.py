#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour trouver les start times des fichiers TDMS et TXT pour Moto_Chicane_100
"""

import pandas as pd
from nptdms import TdmsFile
from datetime import datetime

# Chemins des fichiers
tdms_path = "Moto_Chicane_100.tdms"
txt_path = "Moto_Chicane_100_P1.txt"

print("=" * 70)
print("ANALYSE DES START TIMES - Moto_Chicane_100")
print("=" * 70)

# ============================================================================
# 1. ANALYSE DU FICHIER TDMS
# ============================================================================
print("\n📊 FICHIER TDMS: Moto_Chicane_100.tdms")
print("-" * 70)

try:
    tdms = TdmsFile.read(tdms_path)
    
    # Parcourir tous les groupes et channels
    for group in tdms.groups():
        print(f"\n  Groupe: {group.name}")
        for channel in group.channels():
            channel_name = channel.name
            
            # Récupérer les propriétés temporelles
            start_time = channel.properties.get('wf_start_time')
            increment = channel.properties.get('wf_increment')
            
            if start_time:
                print(f"    📍 Channel: {channel_name}")
                print(f"       Start Time: {start_time}")
                
                if increment:
                    # Convertir en datetime
                    dt_start = pd.to_datetime(start_time).tz_localize(None)
                    print(f"       Start Time (datetime): {dt_start}")
                    print(f"       Increment: {increment} seconds")
                    print(f"       Nombre de points: {len(channel)}")
                    
                    # Calculer le temps de fin
                    duration = increment * len(channel)
                    print(f"       Durée totale: {duration:.2f} secondes")
                    
except FileNotFoundError:
    print(f"  ❌ Fichier non trouvé: {tdms_path}")
except Exception as e:
    print(f"  ❌ Erreur lors de la lecture: {e}")

# ============================================================================
# 2. ANALYSE DU FICHIER TXT (GPS/Xsens)
# ============================================================================
print("\n\n📊 FICHIER TXT: Moto_Chicane_100_P1.txt")
print("-" * 70)

try:
    # Lire le fichier TXT - skip les lignes de commentaire
    # Les données commencent après les lignes de commentaire (//)
    df_txt = pd.read_csv(txt_path, delimiter='\t', skiprows=11, low_memory=False)
    df_txt.columns = df_txt.columns.str.strip()
    
    # Créer le timestamp
    df_txt['timestamp'] = pd.to_datetime(
        df_txt['Date'] + ' ' + df_txt['Time'],
        format='%d/%m/%Y %H:%M:%S.%f',
        errors='coerce'
    ).fillna(
        pd.to_datetime(
            df_txt['Date'] + ' ' + df_txt['Time'],
            format='%d/%m/%Y %H:%M:%S',
            errors='coerce'
        )
    )
    
    # Nettoyer et trier
    df_txt = df_txt.dropna(subset=['timestamp'])
    df_txt = df_txt.sort_values('timestamp').reset_index(drop=True)
    
    # Informations sur le fichier
    print(f"  Nombre total de lignes: {len(df_txt)}")
    print(f"  Colonnes: {', '.join(df_txt.columns[:10])}...")
    
    # Start time
    start_time_txt = df_txt['timestamp'].min()
    end_time_txt = df_txt['timestamp'].max()
    duration_txt = (end_time_txt - start_time_txt).total_seconds()
    
    print(f"\n  📍 Start Time: {start_time_txt}")
    print(f"  📍 End Time: {end_time_txt}")
    print(f"  📍 Durée totale: {duration_txt:.2f} secondes")
    
    # Détecter le démarrage (quand la vitesse GPS dépasse un seuil)
    if 'GPS_Speed' in df_txt.columns:
        gps_speed_threshold = 0.5  # m/s
        df_txt['GPS_Speed'] = pd.to_numeric(df_txt['GPS_Speed'], errors='coerce').fillna(0)
        
        gps_start_idx = df_txt[df_txt['GPS_Speed'] > gps_speed_threshold].index.min()
        
        if pd.notna(gps_start_idx):
            gps_start_time = df_txt.loc[gps_start_idx, 'timestamp']
            gps_start_speed = df_txt.loc[gps_start_idx, 'GPS_Speed']
            
            print(f"\n  🚀 DÉMARRAGE DÉTECTÉ (GPS_Speed > {gps_speed_threshold} m/s):")
            print(f"     Index: {gps_start_idx}")
            print(f"     Time: {gps_start_time}")
            print(f"     Speed: {gps_start_speed:.2f} m/s")
            print(f"     Délai depuis le début: {(gps_start_time - start_time_txt).total_seconds():.2f} secondes")
    
except FileNotFoundError:
    print(f"  ❌ Fichier non trouvé: {txt_path}")
except Exception as e:
    print(f"  ❌ Erreur lors de la lecture: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("FIN DE L'ANALYSE")
print("=" * 70)
