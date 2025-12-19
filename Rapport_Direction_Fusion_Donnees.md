# Rapport de Synthèse : Résolution des Problèmes de Synchronisation (Campagne Moto)

**Destinataires** : Direction & Équipe de Recherche (Postdoc)
**Objet** : Validation de la fusion des données Xsens / LabVIEW et mise à disposition des jeux de données synchronisés.

---

## 1. Contexte et Enjeux

Dans le cadre des essais moto, l'exploitation scientifique des données reposait sur la capacité à croiser deux sources d'information critiques : la dynamique du véhicule (Xsens, 400Hz) et les capteurs instrumentés (LabVIEW/TDMS, 400Hz).

Ces données, capturées par deux systèmes indépendants, présentaient des défauts de synchronisation majeurs qui rendaient jusqu'ici leur fusion impossible (échec des tentatives précédentes). 

**Ce rapport confirme que ces verrous technologiques ont été levés. L'intégralité des 3 jeux de données ("Chicane Mouillé", "Chicane Sec", "Freinage") est désormais traitée, synchronisée et disponible pour analyse.**

---

## 2. Diagnostic des Bloquages (Pourquoi cela ne marchait pas)

L'analyse approfondie des fichiers bruts a permis d'identifier trois anomalies critiques qui empêchaient toute méthode de synchronisation standard :

### A. La "Rupture Temporelle" (Resets Cachés)
Certains fichiers LabVIEW (ex: essais 80 km/h) contenaient des segments de données invalides en début d'enregistrement, suivis d'une réinitialisation brutale ("Reset") du compteur temporel.
*   **Conséquence** : Les méthodes classiques se calaient sur le "faux" début, engendrant un décalage temporel aléatoire rendant les courbes incohérentes.
*   **Solution** : Développement d'un algorithme de **"Smart Detection"** qui identifie la signature du reset dans le signal, coupe automatiquement les données corrompues et recale l'horloge avec une précision millimétrique.

### B. La Dérive d'Horloge (Le "Time Rift" de 4 minutes)
Sur les essais sur sol sec (50 km/h), une dérive majeure de l'horloge interne des PC a été détectée (plus de 4 minutes d'écart entre le GPS et le système d'acquisition).
*   **Conséquence** : Fichiers déclarés "sans chevauchement" (No Overlap) et rejetés par les scripts standards.
*   **Solution** : Implémentation d'un protocole de **"Fallback Force Sync"**. En l'absence de concordance temporelle (métadonnées), l'algorithme vérifie la cohérence géométrique des fichiers (durée, nombre de points) et force l'alignement, sauvant ainsi des essais qui auraient été considérés comme perdus.

### C. L'Opacité du Format Propriétaire (.mtb)
Le dossier "Freinage" était inexploitable en l'état car stocké dans un format binaire propriétaire Xsens (.mtb).
*   **Solution** : Création d'un automate logiciel simulant les actions humaines pour piloter le logiciel constructeur et convertir massivement les données en format ouvert, sans intervention manuelle.

---

## 3. Bilan et Nouvelle Architecture

Nous avons mis en place une chaîne de traitement automatisée et robuste (**Pipeline V2**) qui garantit la qualité des données pour les travaux futurs.

*   **Robustesse** : Le système gère désormais automatiquement les erreurs d'horloge et les fichiers corrompus.
*   **Traçabilité** : Chaque fusion génère un rapport de qualité certifiant l'alignement des données.
*   **Exhaustivité** : 
    *   **Mouille** : 100% traité.
    *   **Sec** : 100% traité (sauvetage des fichiers à dérive).
    *   **Freinage** : 100% traité.

## 4. Accès aux Données

Pour le Postdoc en charge de l'analyse, les données sont désormais prêtes à l'emploi. Il n'est plus nécessaire de se soucier du pré-traitement ou de la synchronisation.

*   **Emplacement** : Sous-dossiers `Merged_CSV` dans chaque répertoire d'essai.
*   **Format** : Fichiers `.csv` standards, contenant sur une même ligne temporelle (Time Stamp unique) les données GPS/IMU et les données Capteurs.

Cette résolution technique débloque la phase d'analyse scientifique du projet.

---
*Réalisé et Validé le 19/12/2025*
