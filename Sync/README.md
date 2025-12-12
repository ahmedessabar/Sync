# Projet de Synchronisation TDMS - Xsens

Ce projet contient des outils pour synchroniser les données d'acquisition TDMS (LabVIEW + cDAQ-9174) avec les données GPS/Xsens (MTi-680).

##  Configuration sur un nouveau PC

### 1. Cloner le repository

```bash
git clone https://github.com/ahmedessabar/Sync.git
cd Sync
```

### 2. Installer Anaconda

- Télécharger et installer Anaconda
- Vérifier l'installation : `conda --version`

### 3. Créer l'environnement virtuel

```bash
# Avec Anaconda Python (adapter le chemin selon votre installation)
C:\Users\[votre_nom]\anaconda3\python.exe -m venv .venv

# Activer l'environnement
.venv\Scripts\activate
```

### 4. Installer les dépendances

```bash
# Mettre à jour pip
python -m pip install --upgrade pip

# Installer les packages
pip install -r requirements.txt
pip install ipykernel
```

### 5. Enregistrer le kernel Jupyter

```bash
python -m ipykernel install --user --name=sync-env --display-name="Sync Project (.venv)"
```

### 6. Ouvrir dans VS Code

1. Ouvrir VS Code
2. Ouvrir le dossier du projet
3. Sélectionner le kernel "Sync Project (.venv)" pour les notebooks Jupyter

---

##  Structure du projet

### Notebooks Jupyter

- **`Synchronisation_TDMS_Xsens.ipynb`** : Notebook pédagogique
- **`Test_Sync_100.ipynb`** : Notebook de test

### Scripts Python

- **`sync_by_timestamps.py`** : Script principal de synchronisation
- **`test_sync_run.py`** : Script de test avec détection de mouvement

---

##  Méthode de synchronisation

### Principe

1. **Point de départ** : Start time Xsens (référence GPS)
2. **Point de fin** : End time TDMS
3. **Trimmer TDMS** : Enlever les données avant le start Xsens
4. **Trimmer Xsens** : Enlever les données après le end TDMS
5. **Resample Xsens** : Même nombre d'échantillons que TDMS

### Résultats

- **Alignement parfait** : 0.000s de décalage
- **Script delay éliminé** : 0.561s au début, 0.756s à la fin
- **Clock drift corrigé** : 3545 ppm (0.195s sur 55s)

---

##  Utilisation

```bash
# Activer l'environnement
.venv\Scripts\activate

# Exécuter le script
python sync_by_timestamps.py
```

Ou utiliser le notebook `Synchronisation_TDMS_Xsens.ipynb`

---

##  Workflow Git

```bash
# Récupérer les modifications
git pull origin main

# Envoyer vos modifications
git add .
git commit -m "Description"
git push origin main
```
