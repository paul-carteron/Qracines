HUMUS_CHOICES = {
    "Amphimull": "amphimull",
    "Eumull": "eumull",
    "Mesomull": "mesomull",
    "Oligomull": "oligomull",
    "Dysmull": "dysmull",
    "Eumoder": "eumoder",
    "Hemimoder": "hemimoder",
    "Dysmoder": "dysmoder",
    "Mor": "mor",
}

TOPOGRAPHY_CHOICES = {
    "Plateau": "plateau",
    "Rupture de pente": "rupture_de_pente",
    "Haut de versant": "haut_de_versant",
    "Milieu de versant": "milieu_de_versant",
    "Replat de versant": "replat_de_versant",
    "Bas de versant": "bas_de_versant",
    "Fond de vallon": "fond_de_vallon",
    "Dépression de plateau": "depression_de_plateau",
}

EXPOSURE_CHOICES = {
    "Nord": "nord",
    "Nord-Est": "nord_est",
    "Est": "est",
    "Sud-Est": "sud_est",
    "Sud": "sud",
    "Sud-Ouest": "sud_ouest",
    "Ouest": "ouest",
    "Nord-Ouest": "nord_ouest",
}

STOP_CHOICES = {
    "Roche": "roche",
    "Éléments grossiers": "elements_grossiers",
    "Argile lourde": "argile_lourde",
    "Volontaire": "volontaire",
}

THICKNESS_CHOICES = list(range(5, 130, 5))

SOIL_MOISTURE_CHOICES = {
    "Noyé": "noye",
    "Humide": "humide",
    "Frais": "frais",
    "Sec": "sec",
}

TEXTURE_CHOICES = {
    "Argile lourde": "AA",
    "Argileux": "A",
    "Argile sableuse": "As",
    "Argile limono-sableuse": "Als",
    "Argile limoneuse": "Al",
    "Argilo-sableux": "AS",
    "Limon argilo-sableux": "LAS",
    "Limon argileux": "La",
    "Sable argileux": "Sa",
    "Sable argilo-limoneux": "Sal",
    "Limon sablo-argileux": "Lsa",
    "Limon": "L",
    "Sableux": "S",
    "Sable": "SS",
    "Sable limoneux": "Sl",
    "Limon sableux": "Ls",
    "LL": "Limon pur",
}

STRUCTURE_CHOICES = {
    "Particulaire": "particulaire",
    "Grumeuleuse": "grumeuleuse",
    "Polyédrique": "polyedrique",
    "Massive": "massive",
}

COMPACTNESS_CHOICES = {
    "Meuble (sans effort)": "meuble",
    "Peu compact (léger effort)": "peu_compact",
    "Compact (Difficile, avec efforts)": "compact",
    "Très compact (Presque impossible)": "tres_compact",
}

COARSE_FRAGMENT_SIZE_CHOICES = {
    "Gravier (0,2 à 2 cm)": "gravier",
    "Cailloux (2 à 7,5 cm)": "cailloux",
    "Pierres (7,5 à 25 cm)": "pierres",
    "Blocs (>25 cm)": "blocs",
}

PROPORTION_CHOICES = [5, 10, 15, 20, 25, 30, 40, 50, 75]

HYDROMORPHY_CHOICES = {
    "Oxydation seule": "oxydatation_seule",
    "Réduction seule": "reduction_seule",
    "Décoloration seule": "decoloration_seule",
    "Concrétion seule": "concretion_seule",
    "Oxydation + Décoloration": "oxydation_decoloration",
    "Oxydation + Concrétion": "oxydation_concretion",
    "Oxydation + Décoloration + Concrétion": "oxydation_decoloration_concretion"
}

CARBONATION_LOCATION_CHOICES = {
    "Localisée sur EG": "localisee_eg",
    "Localisée sur TF": "localisee_tf",
    "Généralisée": "generalisee",
    "Négative": "negative",
}

CARBONATION_POWER_CHOICES = {
    "Nulle": "nulle",
    "Faible (bulles)": "faible",
    "Moyenne (couches de bulles)": "moyenne",
    "Forte (plusieurs couches)": "forte",
}
