from nptdms import TdmsFile
import datetime

path = r'Moto_Chicane_mouille_80.tdms'

print(f"--- Inspection Métadonnées : {path} ---")
try:
    tdms = TdmsFile.read(path)
    
    # 1. Properties Root
    print("\n[ROOT PROPERTIES]")
    for k, v in tdms.properties.items():
        print(f"  {k}: {v} (Type: {type(v)})")
        
    # 2. Properties Group 'P1'
    print("\n[GROUP 'P1' PROPERTIES]")
    if 'P1' in tdms:
        group = tdms['P1']
        for k, v in group.properties.items():
            print(f"  {k}: {v}")
            
        # 3. Channel Properties (Sample)
        if 'Edges_RoueAR' in group:
            chan = group['Edges_RoueAR']
            print(f"\n[CHANNEL 'Edges_RoueAR' PROPERTIES]")
            for k, v in chan.properties.items():
                print(f"  {k}: {v}")
    else:
        print("Groupe P1 non trouvé.")

except Exception as e:
    print(f"Erreur : {e}")
