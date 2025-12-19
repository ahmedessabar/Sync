import time
from pathlib import Path
from pywinauto import Application
from pywinauto.keyboard import send_keys
import keyboard
import sys


# ==============================
# CONFIGURATION
# ==============================
MT_MANAGER_PATH = r"" # <-- Chemin du MT Manager.exe, mettre en commentaire la section en dessous si deja ouvert
MBT_FOLDER = Path(r"") # <-- Chemin du dossier qui contient les fichiers mtb à exporter

EXPORT_TIMEOUT = 10  # secondes max par export

# Arrêt d'urgence
keyboard.add_hotkey("esc", lambda: sys.exit("⛔ Arrêt manuel"))


# ==============================
# LANCEMENT MT MANAGER
# ==============================
print("▶ Lancement de Xsens MT Manager...")
app = Application(backend="uia").start(MT_MANAGER_PATH)

time.sleep(2)
main_window = app.top_window()
main_window.set_focus()

# ==============================
# BOUCLE SUR LES FICHIERS MBT
# ==============================
for mbt_file in MBT_FOLDER.glob("*.m*t*b*"):
    print(f"\n📂 Traitement : {mbt_file.name}")

    # --- Ouvrir le fichier ---
    send_keys("^o")
    time.sleep(0.5)
    send_keys(str(mbt_file) + "{ENTER}")
    time.sleep(4)

    # --- Export ---
    print("📤 Lancement export...")
    send_keys("^e")
    time.sleep(1)
    send_keys("{ENTER}")

    print("⏳ Attente fin export...")
    time.sleep(EXPORT_TIMEOUT)
    print(f"✅ Export terminé : {mbt_file.name}")

    # --- Fermer le fichier ---
    send_keys("^w")
    
    time.sleep(1)


print("\n🎉 Tous les fichiers ont été traités.")
