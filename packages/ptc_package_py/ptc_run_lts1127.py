"""
ptc_run_lts1127.py
==================
Exécute l'analyse PTC sur la procédure LTS1127 (TotalEnergies BCUC).

Procédure : NOR-MET-SEI-INST-PM-00042_002
Tag       : Radar AOPS LTS 1127 — Bac TK1112 Toit flottant
Fonction  : LSHH = LAHH (Niveau Très Haut → fermeture ROV 11510 / 11511)
Rédigée   : Y.DUMONT, 18/03/2020
Unité     : BCUC — Plateforme Normandie TotalEnergies
"""

import sys
import os
sys.path.insert(0, "/home/claude")

from ptc_engine import load_kb, ProcedureParser, ProcedureStep, PTCCalculator, generate_report

# ─────────────────────────────────────────────────────────────────────────────
# 1. CHARGEMENT KB
# ─────────────────────────────────────────────────────────────────────────────
kb = load_kb()

# ─────────────────────────────────────────────────────────────────────────────
# 2. DÉFINITION DES ÉTAPES DE PROCÉDURE
#    Saisies fidèlement depuis le PDF, sans modification.
#    "section" = numéro de paragraphe de la procédure originale.
# ─────────────────────────────────────────────────────────────────────────────
STEPS = [
    # §1 — Actions préliminaires
    ProcedureStep("P01", "Poser une inhibition sur le LTS 1127",
                  location="SdC", section="§1 - Actions préliminaires"),
    ProcedureStep("P02", "Prévenir la SdC BCUC BACS DE STOCKAGE du début du test",
                  location="SdC", section="§1 - Actions préliminaires"),
    ProcedureStep("P03", "S assurer que le bac n est ni en coulage ni en reprise - Niveau stable",
                  location="SdC", section="§1 - Actions préliminaires"),
    ProcedureStep("P04", "Relever la valeur du niveau du Radar LTS 1127",
                  location="SdC", expected_result="NRadar = m",
                  section="§1 - Actions préliminaires"),
    ProcedureStep("P05", "Contrôler le bon état du LTS 1127",
                  location="L", section="§1 - Actions préliminaires"),
    ProcedureStep("P06", "Brancher le PC sur le capteur au bornier 90BNMS009 1-2",
                  location="LT BCUC", section="§1 - Actions préliminaires"),
    ProcedureStep("P07", "Noter la valeur du 1er écho - Si inférieur à 20 dB arrêter la procédure",
                  location="LT BCUC", expected_result="1er écho = dB",
                  section="§1 - Actions préliminaires"),

    # §2 — Test de fonctionnement - Redémarrage
    ProcedureStep("P08", "Relever la valeur du courant avant coupure",
                  location="LT BCUC", expected_result="A = mA",
                  section="§2 - Test fonctionnement redémarrage"),
    ProcedureStep("P09", "Couper l alimentation du radar en ouvrant les barettes au bornier 90BNMS009 1-2",
                  location="LT BCUC", section="§2 - Test fonctionnement redémarrage"),
    ProcedureStep("P10", "Après 10 secondes remettre le radar sous tension",
                  location="LT BCUC", section="§2 - Test fonctionnement redémarrage"),
    ProcedureStep("P11", "Attendre 60 secondes que le radar s auto-teste électronique et signal de sortie",
                  location="LT BCUC", section="§2 - Test fonctionnement redémarrage"),
    ProcedureStep("P12", "Relever la valeur du courant après remise en marche",
                  location="LT BCUC", expected_result="B = mA",
                  section="§2 - Test fonctionnement redémarrage"),
    ProcedureStep("P13", "Calculer la différence de valeur du courant C = |A-B| - Ecart <= 0,32 mA = Bon",
                  location="LT BCUC", expected_result="C = mA - Ecart <= 0,32 mA Bon",
                  section="§2 - Test fonctionnement redémarrage"),

    # §3 — Simulation niveau à 4 mA
    ProcedureStep("P14", "Forcer la valeur de simulation sur 0 % avec PACTWARE",
                  location="LT BCUC", section="§3 - Simulation niveau 4mA"),
    ProcedureStep("P15", "Relever la valeur du courant de sortie I 4mA",
                  location="LT BCUC", expected_result="I 4mA = mA",
                  section="§3 - Simulation niveau 4mA"),
    ProcedureStep("P16", "Contrôler la valeur du courant de sortie I 4mA - 3,68 mA <= I 4mA <= 4,32 mA",
                  location="LT BCUC", expected_result="3,68 mA <= I 4mA <= 4,32 mA Bon",
                  section="§3 - Simulation niveau 4mA"),
    ProcedureStep("P17", "Contrôler la valeur du niveau Radar LTS 1127 à 0 m sur le SNCC",
                  location="SdC", expected_result="0 m",
                  section="§3 - Simulation niveau 4mA"),

    # §4 — Simulation niveau à 20 mA
    ProcedureStep("P18", "Forcer la valeur de simulation sur 100 % avec PACTWARE",
                  location="LT BCUC", section="§4 - Simulation niveau 20mA"),
    ProcedureStep("P19", "Relever la valeur du courant de sortie I 20mA",
                  location="LT BCUC", expected_result="I 20mA = mA",
                  section="§4 - Simulation niveau 20mA"),
    ProcedureStep("P20", "Contrôler la valeur du courant de sortie I 20mA - 19,68 mA <= I 20mA <= 20,32 mA",
                  location="LT BCUC", expected_result="19,68 mA <= I 20mA <= 20,32 mA Bon",
                  section="§4 - Simulation niveau 20mA"),
    ProcedureStep("P21", "Contrôler la valeur du niveau Radar LTS 1127 à 14 m sur le SNCC",
                  location="SdC", expected_result="14 m",
                  section="§4 - Simulation niveau 20mA"),

    # §5 — Test de sécurité LSHH
    ProcedureStep("P22", "Régler la valeur de simulation sur 15 mA",
                  location="LT BCUC", section="§5 - Test sécurité LSHH"),
    ProcedureStep("P23", "Déposer l inhibition sur le LTS 1127",
                  location="SdC", section="§5 - Test sécurité LSHH"),
    ProcedureStep("P24", "Contrôler sur le SNCC que le seuil LSHH1127 est inactif",
                  location="SdC", expected_result="OUI",
                  section="§5 - Test sécurité LSHH"),
    ProcedureStep("P25", "Vérifier que la séquence XS-1112 est inactif",
                  location="SdC", expected_result="OUI",
                  section="§5 - Test sécurité LSHH"),
    ProcedureStep("P26", "Vérifier que les vannes ROV 11510 pipe 94 et ROV 11511 pipe 95 soient ouvertes",
                  location="L & SdC", expected_result="OUI",
                  section="§5 - Test sécurité LSHH"),
    ProcedureStep("P27", "Vérifier que les fins de course ZSH11510 et ZSH11511 ouverture vanne sont actifs",
                  location="SdC BCUC", expected_result="OUI",
                  section="§5 - Test sécurité LSHH"),
    ProcedureStep("P28", "Vérifier que les fins de course ZSL11510 et ZSL11511 sont inactifs",
                  location="SdC BCUC", expected_result="OUI",
                  section="§5 - Test sécurité LSHH"),
    ProcedureStep("P29", "Augmenter lentement la valeur de simulation sur le Radar LTS 1127",
                  location="LT BCUC", section="§5 - Test sécurité LSHH"),
    ProcedureStep("P30", "Donner un TOP à l apparition du seuil LSHH1127 sur le SNCC",
                  location="SdC", expected_result="TOP",
                  section="§5 - Test sécurité LSHH"),
    ProcedureStep("P31", "Au TOP relever la valeur du courant correspondante - R = 17,68 mA attendu",
                  location="LT BCUC", expected_result="R = 17,68 mA",
                  section="§5 - Test sécurité LSHH"),
    ProcedureStep("P32", "Au TOP relever la valeur du niveau Radar LTS 1127 - R = 11,97 m attendu",
                  location="SdC", expected_result="R = 11,97 m",
                  section="§5 - Test sécurité LSHH"),
    ProcedureStep("P33", "Vérifier que la séquence XS-1112 est actif",
                  location="SdC", expected_result="OUI",
                  section="§5 - Test sécurité LSHH"),
    ProcedureStep("P34", "Vérifier que les vannes ROV 11510 et ROV 11511 soient fermées",
                  location="L & SdC", expected_result="OUI",
                  section="§5 - Test sécurité LSHH"),
    ProcedureStep("P35", "Vérifier que les fins de course ZSH11510 et ZSH11511 sont inactifs",
                  location="SdC BCUC", expected_result="OUI",
                  section="§5 - Test sécurité LSHH"),
    ProcedureStep("P36", "Vérifier que les fins de course ZSL11510 et ZSL11511 fermeture vanne sont actifs",
                  location="SdC BCUC", expected_result="OUI",
                  section="§5 - Test sécurité LSHH"),
    ProcedureStep("P37", "Actionner la commande SOFT réarmement XS-1112_R",
                  location="SdC BCUC", section="§5 - Test sécurité LSHH"),
    ProcedureStep("P38", "Vérifier que la séquence XS-1112 est inactif après réarmement",
                  location="SdC BCUC", expected_result="OUI",
                  section="§5 - Test sécurité LSHH"),
    ProcedureStep("P39", "Vérifier que les vannes ROV 11510 et ROV 11511 soient ouvertes après réarmement",
                  location="L & SdC", expected_result="OUI",
                  section="§5 - Test sécurité LSHH"),

    # §6 — Test défaut capteur
    ProcedureStep("P40", "Régler la valeur de simulation sur 5 mA",
                  location="LT BCUC", section="§6 - Test défaut capteur"),
    ProcedureStep("P41", "Vérifier que le seuil LSHH1127 est inactif",
                  location="SdC", expected_result="OUI",
                  section="§6 - Test défaut capteur"),
    ProcedureStep("P42", "Vérifier que la séquence XS-1112 est toujours inactif",
                  location="SdC", expected_result="OUI",
                  section="§6 - Test défaut capteur"),
    ProcedureStep("P43", "Vérifier que le voyant pupitre XA041_2 est éteint",
                  location="SDC BUTA", expected_result="OUI",
                  section="§6 - Test défaut capteur"),
    ProcedureStep("P44", "Diminuer lentement la valeur de simulation sur le radar LTS 1127",
                  location="LT BCUC", section="§6 - Test défaut capteur"),
    ProcedureStep("P45", "Donner un TOP à l apparition du seuil LSHH1127 en diminuant",
                  location="SdC", expected_result="TOP",
                  section="§6 - Test défaut capteur"),
    ProcedureStep("P46", "Au TOP relever la valeur de la simulation - R = >= 3,6 mA attendu",
                  location="LT BCUC", expected_result="R = >=3,6 mA",
                  section="§6 - Test défaut capteur"),
    ProcedureStep("P47", "Vérifier que la séquence XS-1112 est actif",
                  location="SdC", expected_result="OUI",
                  section="§6 - Test défaut capteur"),
    ProcedureStep("P48", "Vérifier que le voyant pupitre XA041_2 est allumé",
                  location="SDC BUTA", expected_result="OUI",
                  section="§6 - Test défaut capteur"),

    # §7 — Remise en service
    ProcedureStep("P49", "Désactiver la simulation",
                  location="LT BCUC", section="§7 - Remise en service"),
    ProcedureStep("P50", "Contrôler sur le SNCC que le seuil LSHH1127 est inactif",
                  location="SdC", expected_result="OUI",
                  section="§7 - Remise en service"),
    ProcedureStep("P51", "Actionner la commande SOFT XS-1112_R réarmement séquence XS-1112",
                  location="SdC", section="§7 - Remise en service"),
    ProcedureStep("P52", "Vérifier que la séquence XS-1112 est inactif",
                  location="SdC", expected_result="OUI",
                  section="§7 - Remise en service"),
    ProcedureStep("P53", "Contrôler le retour à la normale du niveau du Radar LTS 1127",
                  location="SdC", expected_result="NRadar OUI",
                  section="§7 - Remise en service"),
    ProcedureStep("P54", "Vérifier que les vannes ROV 11510 et ROV 11511 soient ouvertes",
                  location="L & SdC", expected_result="OUI",
                  section="§7 - Remise en service"),
    ProcedureStep("P55", "Prévenir le CDQ de la fin des essais",
                  location="SdC", section="§7 - Remise en service"),
]

# ─────────────────────────────────────────────────────────────────────────────
# 3. CLASSIFICATION DES ÉTAPES — ProcedureParser
# ─────────────────────────────────────────────────────────────────────────────
parser = ProcedureParser(kb)
classifications = parser.classify_procedure(STEPS)

# ─────────────────────────────────────────────────────────────────────────────
# 4. CALCUL PTC — PTCCalculator
# ─────────────────────────────────────────────────────────────────────────────
calculator = PTCCalculator(kb)
result = calculator.compute_component_ptc(
    component_id="level_transmitter_radar",
    component=kb["components"]["level_transmitter_radar"],
    classifications=classifications,
    sif_function="LAHH",   # LSHH1127 → action sur niveau très haut
)

# ─────────────────────────────────────────────────────────────────────────────
# 5. RAPPORT — PTCReporter
# ─────────────────────────────────────────────────────────────────────────────
report = generate_report(
    procedure_id="NOR-MET-SEI-INST-PM-00042_002",
    procedure_title="Radar AOPS LTS 1127 — Contrôle sécurité niveau très haut TK1112",
    classifications=classifications,
    result=result,
    T1_hours=8760,
)

print(report)
