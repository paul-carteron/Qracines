# CHANGELOG

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).


## [V1.0.10 - Unreleased] - 2026-06-08

- Ajout de la couche ombrage dans expertise


## [V1.0.9] - 2026-05-04

### General

- Les fichiers sélectionnés lors de la combinaison de GeoPackages sont désormais réinitialisés à chaque ouverture de l’outil

### Diagnostic

- Les attributs du taillis `TSE_DENS` (Densité), `TSE_VOL` (Volume) et `TSE_NATURE` (Ecplpoitabilité) acceptent maintenant une valeur <NULL> ;
- L'attribut `PLT_PARCELLE` (Parcelle) a été supprimé, c'est le SIG qui fait foi ;
- Ajout de l'attribut `PLT_STRUCTURE` (Structure) pour les peuplements boisés (PB, BM, GB, TGB, PB/BM, ...)

### Martelage

- Correction d'un bug : mise à jour du dossier sequoia lors du chargement des .gpkg ;
- Regroupement des parcelles par lot dans la liste déroulante ;
- Ajout du type de marque "Corps" uniquement ;
- Ajout d'une couche "Lot" dédiée à la création des lots ;
- Modification de la couche "Param" maintenant dédiée uniquement aux paramètres dendro