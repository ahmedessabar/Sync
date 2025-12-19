
import time
from pathlib import Path
from pywinauto import Application
from pywinauto.keyboard import send_keys
import sys
import os

# ==============================
# CONFIGURATION
# ==============================
# Dossier contenant les fichiers mtb à exporter
MBT_FOLDER = Path(r"c:\Users\es-sabar\Documents\PreTest\Moto_Freinage_mouille\Xsens")

EXPORT_TIMEOUT = 10  # secondes max par export

# ==============================
# CONNEXION MT MANAGER EXISTANT
# ==============================
print("▶ Connexion à Xsens MT Manager (déjà ouvert)...")
log_file = open("debug_extract.log", "w", encoding="utf-8")

try:
    from pywinauto import Desktop
    
    # Tentative connexion
    app = Application(backend="uia").connect(title_re=".*MT Manager.*", timeout=5)
    main_window = app.top_window()
    main_window.set_focus()
    print(f"   [OK] Connecté à : {main_window.window_text()}")
    log_file.write(f"SUCCESS: Connected to {main_window.window_text()}\n")
    
except Exception as e:
    err_msg = f"❌ Erreur Connexion: {e}\n"
    print(err_msg)
    log_file.write(err_msg)
    
    # List windows to debug
    print("   Fenêtres visibles :")
    log_file.write("VISIBLE WINDOWS:\n")
    try:
        windows = Desktop(backend="uia").windows()
        for w in windows:
            t = w.window_text()
            if t: 
                print(f"   - {t}")
                log_file.write(f"   - {t}\n")
    except Exception as e2:
        log_file.write(f"Could not list windows: {e2}\n")
        
    log_file.close()
    sys.exit(1)
    
log_file.close()
time.sleep(1)

# ==============================
# BOUCLE SUR LES FICHIERS MBT
# ==============================
files = list(MBT_FOLDER.glob("*.mtb"))
print(f"Fichiers trouvés : {len(files)}")

for mbt_file in files:
    print(f"\n📂 Traitement : {mbt_file.name}")

    # --- Ouvrir le fichier (Ctrl+O) ---
    send_keys("^o")
    time.sleep(1)
    
    # Taper le chemin complet + Entrée
    send_keys(str(mbt_file).replace(" ", "{SPACE}") + "{ENTER}")
    time.sleep(5) # Attente chargement

    # --- Export (Ctrl+E) ---
    print("📤 Lancement export...")
    send_keys("^e")
    time.sleep(2)
    
    # Valider la fenetre d'export (Entrée)
    send_keys("{ENTER}")

    print("⏳ Attente fin export...")
    # On attend un peu que l'export se fasse
    # (Idéalement on détecterait la fenetre de fin, mais sleep est plus simple ici)
    time.sleep(EXPORT_TIMEOUT) 
    
    print(f"✅ Export terminé (supposé) : {mbt_file.name}")

    # --- Fermer le fichier (Ctrl+W ou autre méthode pour revenir à l'état propre) ---
    # Souvent Ctrl+F4 ou Ctrl+W ferme le fichier courant
    send_keys("^w")
    time.sleep(2)

print("\n🎉 Tous les fichiers ont été traités.")
