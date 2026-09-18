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
    "Sable (A:5% L:5% S:90%)" :"S",
    "Sable limoneux (A:5% L:25% S:70%)": "SL",
    "Sable argileux (A:20% L:10% S:70%)": "SA",
    "Limon léger sableux (A:5% L:5% S:40%)":" LLS",
    "Limon sableux (A:10% L:45% S:45%)": "LS",
    "Limon moyennement sableux (A:10% L:65% S:25%)":" LMS",
    "Limon sablo-argileux (A:25% L:35% S:40%)":" LSA",
    "Limon argilo-sableux (A:25% L:50% S:25%)":" LAS",
    "Limon léger (A:5% L:90% S:5%)": "LL",
    "Limon moyen (A:15% L:80% S:5%)": "LM",
    "Limon argileux (A:25% L:70% S:5%)": "LA",
    "Argile sableuse (A:35% L:10% S:55%)": "AS",
    "Argile (A:40% L:30% S:30%)" :"A",
    "Argile limoneuse (A:40% L:50% S:10%)": "AL",
    "Argile lourde (A:70% L:15% S:15%)":" ALO",
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
