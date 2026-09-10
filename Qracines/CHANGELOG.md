# CHANGELOG

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [V1.0.18] - Unreleased

### Ajouts

- Ajout du chargement des périmètres de protection des captages (PPI, PPR et PPE) depuis le service WFS Carteaux, avec authentification QGIS et filtrage par département.
- Ajout du module Pédologie permettant de créer, charger et combiner les GeoPackages QField

### Modifications

- Harmonisation de `FormBuilder` autour de `add_fields`, `add_group` et `add_relation`, avec prise en charge des alias de relation et des expressions de visibilité.

## [V1.0.17] - Unreleased

### Ajouts

- Paramétrage des essences, des hauteurs et des diamètres dans le module Expertise.
- Ajout automatique de la date au nom des fichiers générés pour QField.

### Modifications

- Précision à deux décimales pour le nombre de points des grilles Diagnostic et Expertise.
- Simplification des codes de type, de marque, de couleur et de marteau du module Martelage.
- Renommage de l'action « Combiner » en « Traiter » dans les menus des modules.

### Corrections

- Prise en charge des valeurs vides de `TR_DIAMETRE` et `TR_HAUTEUR` lors du traitement des données Expertise.

## [V1.0.16] - 2026-06-30

- Modification de l'opacité par défaut de la carte des peuplements au chargement des données de Martelage.
- Réarrangement des dialogues de création.
- Ajout du chargement du SCAN 25® par WMTS avec une configuration d'authentification QGIS.

## [V1.0.13] - 2026-06-08

- Automatisation de la symbology lors de l'import des données de martelage
- Possibilité de packager les couches Sequoia2 lors de la génération des projets QField Expertise, Diagnostic et Inventaire.

## [V1.0.12] - 2026-06-08

- Ajout de la couche ombrage dans expertise
- Ajout de la couche ombrage dans tree_marking
- Fix bug lors de la combinaison des inventaire

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
