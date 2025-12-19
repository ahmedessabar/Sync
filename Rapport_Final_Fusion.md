# Rapport Final : Fusion de Données Xsens / TDMS

**Date** : 19/12/2025
**Projet** : Synchronisation et Fusion de données moto (GPS/IMU + Capteurs LabVIEW)

---

## 1. Objectif
Fusionner deux sources de données hétérogènes pour une analyse synchronisée :
*   **Maitre (Référence)** : Données Xsens (`.txt` ou `.mtb`), échantillonnées à ~400Hz.
*   **Esclave** : Données LabVIEW (`.tdms`), échantillonnées à 400Hz.

---

## 2. Architecture Logicielle & Inventaire des Scripts

Nous avons séparé les scripts en deux catégories : l'exploration (comprendre et déboguer) et la production (traiter massivement).

### A. Phase d'Exploration & Débogage
*Ces scripts ont servi à analyser les anomalies et prototyper les algorithmes de correction. Ils ne sont plus nécessaires pour le traitement courant mais restent utiles pour comprendre la logique.*

*   **`Analysis_Invalid_Trials.ipynb`** :
    *   **But** : Comprendre pourquoi la synchronisation échouait sur certains fichiers "Mouille" (80km/h).
    *   **Découverte** : Identification du phénomène de "Reset" du compteur `Edges_RoueAR` en milieu de fichier. A permis de calibrer l'offset de temps (`0.2679s`).
*   **`Debug_50.ipynb`** & **`inspect_50_failure.py`** :
    *   **But** : Diagnostiquer l'erreur "No Overlap" sur les fichiers du dossier "Sec" (50km/h).
    *   **Découverte** : Mise en évidence d'une dérive d'horloge majeure (4 minutes) entre le PC Xsens et le système LabVIEW.
*   **`inspect_tdms_props.py`** :
    *   **But** : Explorer la structure interne des fichiers TDMS pour localiser les métadonnées de temps (`wf_start_time`) qui étaient cachées dans des propriétés de channel spécifiques.
*   **`extract_freinage.py` (Script Python)** :
    *   **But** : Prototype pour l'automatisation de l'interface graphique MT Manager. A servi de base pour le notebook d'extraction final.

### B. Phase de Production (Batch Processing)
*Ces notebooks contiennent la logique finale, robuste et standardisée. Ce sont les seuls fichiers à exécuter pour traiter les données.*

#### 1. Scripts de Fusion (Data Fusion)
Tous ces notebooks utilisent désormais la norme **V2** (Nettoyage Ghost, Smart Detect Reset, Fallback Force Sync, Validation Longueur).

*   **`Batch_Process_Mouille.ipynb`** :
    *   **Cible** : `Moto_06112025_Chicane_Mouille`
    *   **Spécificité** : Gère automatiquement les fichiers avec "Reset" (80km/h).
*   **`Batch_Process_Sec.ipynb`** :
    *   **Cible** : `Moto_04112025_chicane_sec`
    *   **Spécificité** : Active automatiquement le *Fallback Force Sync* pour sauver les fichiers désynchronisés (50km/h).
*   **`Batch_Process_Freinage.ipynb`** :
    *   **Cible** : `Moto_Freinage_mouille`
    *   **Spécificité** : Fusion standard.

#### 2. Utilitaires
*   **`Extract_Freinage.ipynb`** :
    *   **But** : Automatise l'ouverture de MT Manager et simule les touches clavier pour convertir massivement les fichiers `.mtb` (binaires) en `.txt`. Indispensable car Xsens ne fournit pas de convertisseur en ligne de commande simple.

---

## 3. Défis Techniques & Solutions Intégrées

Les scripts de production intègrent désormais des solutions automatiques pour les 3 problèmes majeurs rencontrés :

1.  **Données invalides (Resets)** : Détection auto du saut négatif et recalage temporel -> *Intégré dans tous les Batchs.*
2.  **Dérive d'Horloge (4 min)** : Détection de non-chevauchement et synchronisation forcée sur le début du fichier -> *Intégré dans tous les Batchs.*
3.  **Format Binaire (.mtb)** : Automatisation GUI via `pywinauto` -> *Géré par Extract_Freinage.ipynb.*

---

## 4. Résultats par Dossier

*   **`Moto_06112025_Chicane_Mouille`** : 🟢 100% Succès (y compris resets).
*   **`Moto_04112025_chicane_sec`** : 🟢 100% Succès (y compris dérive horloge).
*   **`Moto_Freinage_mouille`** : 🟢 100% Succès (21 fichiers extraits et fusionnés).

Les fichiers fusionnés (`_merged.csv`) et les rapports de qualité (`Batch_Report.csv`) sont disponibles dans le sous-dossier `Merged_CSV` de chaque répertoire de données.
