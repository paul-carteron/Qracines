STADE_CHOICES = {
    'RSF': 'En régé. Semis / Fourré',
    'RGP': 'En régé. Gaulis / Perchis',
    'JEU': 'Jeune',
    'ADU': 'Adulte',
    'MAT': 'Mature',
    'SFO': 'Semis / Fourré',
    'GPE': 'Gaulis / Perchis',
    'EXP': 'Exploitable',
    'NEX': 'Non exploitable'
}

RICHESSE_CHOICES = {
    'TRI': 'Très riche',
    'RRI': 'Riche',
    'MRI': 'Moy. riche',
    'PPA': 'Pauvre',
    'TPA': 'Ruiné'
}

STRUCTURE_CHOICES = {
    "PB": "Petits Bois",
    "BM": "Bois Moyens",  
    "GB": "Gros Bois",
    "TGB": "Très Gros Bois",
    "PB_BM": "Petits Bois / Bois Moyens",
    "BM_GB": "Bois Moyens / Gros Bois",
    "GB_TGB": "Gros Bois / Très Gros Bois",
    "IRR": "Irrégulière"
}

ELAGAGE_CHOICES = {
  '2m':'2m',
  '4m': '4m',
  '6m': '6m'
}

SANITAIRE_CHOICES = {
    'AFF_EPARS': 'Affaiblissements épars',
    'AFF_GEN': 'Affaiblissements généralisés',
    'DEP_EPARS': 'Dépérissements épars',
    'DEP_GEN': 'Dépérissements généralisés'
}

CLOISO_CHOICES = {
    'Irrégulier': 'Irrégulier',
    '7m': '7m',
    '12m': '12m',
    '15m': '15m',
    '20m': '20m',
    '25m': '25m',
    '30m': '30m',
}

MECANISABLE_CHOICES = {
    'M': 'Mécanisable',
    'M_SEMI': 'Semi-mécanisable',
    'M_PARTIE': 'Mécanisable en partie',
    'M_TREUIL': 'Mécanisable - Treuil',
    'NM_PENTE': 'Non mécanisable - Pente',
    'NM_ROCHE': 'Non mécanisable - Roches',
    'NM_HUMIDE': 'Non mécanisable - Humide'
}

TX_TROUEE_CHOICES = {         
    '0': '<10% (1/10)',
    '10': '10% (1/10)',
    '20': '20% (1/5)',
    '25': '25% (1/4)',
    '33': '33% (1/3)',
    '50': '50% (1/2)',
    '66': '66% (2/3)',
    '100': '+ de 66% (2/3)',
}

VEG_CON_CHOICES = {
    '2': 'Dense / Nettoyage urgent',
    '1': 'Moyenne / Nettoyage à programmer',
    '0': 'Maitrisée / Pas de nettoyage',
}

TX_DEG_CHOICES = {         
    '0': '<10% (1/10)',
    '10': '10% (1/10)',
    '20': '20% (1/5)',
    '25': '25% (1/4)',
    '33': '33% (1/3)',
    '50': '50% (1/2)',
    '66': '66% (2/3)',
    '100': '+ de 66% (2/3)',
}

PROTECT_CHOICES = {
    'CLOTURE': 'Clôture',
    'INDIV_MECA': 'Individuelle méca',
    'INDIV_CHIMIQUE': 'Individuelle chimique',
}

DENSITE_CHOICES = {
    'tres_dense': 'Très dense',
    'dense': 'Dense',
    'moyennement_dense': 'Moyennement dense',
    'peu_dense': 'Peu dense',
    'absent': 'Absent',
}

TSE_VOL_CHOICES = {
    "25": "25",
    "50": "50",
    "75": "75",
    "100": "100",
    "125": "125",
    "150": "150",
    "200": "200",
    "250": "250",
    "300": "300",
    "350": "350",
    "400": "400",
}

TSE_NATURE_CHOICES = {
    "BI_BE": "BI/BE",
    "BC": "BC"
}