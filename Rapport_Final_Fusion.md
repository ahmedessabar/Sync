# Rapport Final : Fusion de Données Xsens / TDMS

**Date** : 19/12/2025
**Projet** : Synchronisation et Fusion de données moto (GPS/IMU + Capteurs LabVIEW)

---

## 1. Objectif
L'objectif du projet était de fusionner deux sources de données hétérogènes pour une analyse synchronisée :
*   **Maitre (Référence)** : Données Xsens (`.txt` ou `.mtb`), échantillonnées à ~400Hz.
*   **Esclave** : Données LabVIEW (`.tdms`), échantillonnées à 400Hz.

## 2. Défis Techniques & Solutions

Nous avons rencontré et résolu trois défis majeurs lors du traitement des différents dossiers.

### A. Données Invalides (Resets Compteur)
*   **Problème** : Certains fichiers TDMS commençaient par des données invalides avant un "reset" du compteur `Edges_RoueAR`, faussant la synchronisation temporelle via les métadonnées.
*   **Solution** : Implémentation d'une logique **"Smart Detect"**.
    *   Analyse du signal `Edges_RoueAR`.
    *   Détection du saut négatif (`diff < -100`).
    *   Suppression automatique de la partie pré-reset.
    *   **Synchronisation Forcée** : Utilisation du temps de début Xsens + Offset calibré (`0.2679s`).

### B. Dérive d'Horloge (Désynchronisation UTC)
*   **Problème** : Sur le dossier "Sec" (essais 50km/h), les horloges des deux systèmes avaient 4 minutes d'écart, rendant la fusion par métadonnées impossible ("No Overlap").
*   **Solution** : Ajout d'un mode **"Fallback Force Sync"**.
    *   Si les métadonnées indiquent une absence de chevauchement...
    *   Vérification de la compatibilité des durées (Tolérance < 15%).
    *   Alignement forcé sur le début du fichier Xsens.

### C. Format Binaire (.mtb)
*   **Problème** : Le dossier "Freinage" ne contenait que des fichiers bruts `.mtb`.
*   **Solution** : Création d'un **script d'automatisation GUI**.
    *   Utilisation de `pywinauto` pour piloter le logiciel *MT Manager*.
    *   Export automatique par lot vers le format `.txt`.

---

## 3. Résultats par Dossier

### 🟢 1. Moto_06112025_Chicane_Mouille
*   **Statut** : 100% Traité.
*   **Particularité** : Validation de la logique de gestion des resets (fichiers 80km/h).
*   **Sortie** : `Merged_CSV/`

### 🟢 2. Moto_04112025_chicane_sec
*   **Statut** : 100% Traité.
*   **Particularité** : Sauvetage des fichiers `50_P1` et `50_P2` grâce au *Fallback Force Sync*.
*   **Sortie** : `Merged_CSV/`

### 🟢 3. Moto_Freinage_mouille
*   **Statut** : 100% Traité (21 fichiers).
*   **Particularité** : Export automatisé réussi. Fusion standard sans erreur.
*   **Sortie** : `Merged_CSV/`

---

## 4. Livrables Techniques

Trois notebooks de traitement par lot ont été créés pour pérenniser le travail :

1.  `Batch_Process_Mouille.ipynb`
2.  `Batch_Process_Sec.ipynb`
3.  `Batch_Process_Freinage.ipynb` (inclut l'automatisation d'export dans un notebook annexe `Extract_Freinage.ipynb`)

Chaque notebook génère un rapport de qualité (`Batch_Report_*.csv`) certifiant le succès de chaque fusion.
