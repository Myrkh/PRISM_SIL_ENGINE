"""
ptc_engine.kb — Knowledge Base Loader
======================================
Charge knowledge_base_v2.json et applique les enrichissements
de taxonomie nécessaires pour le matching FR industriel.

Ce module ne contient AUCUNE logique de scoring.
Il est la seule source de vérité sur les données.
"""

import json
import os
from pathlib import Path

# Chemin par défaut vers la KB (relatif à ce fichier)
_DEFAULT_KB_PATH = Path(__file__).parent.parent / "ptc-knowledge-base" / "knowledge_base_v2.json"


def load(kb_path: str | Path | None = None) -> dict:
    """
    Charge la KB et applique les enrichissements de taxonomie.
    Retourne le dict KB complet (components + test_taxonomy).
    """
    path = Path(kb_path) if kb_path else _DEFAULT_KB_PATH
    with open(path, encoding="utf-8") as f:
        kb = json.load(f)

    _enrich_taxonomy(kb["test_taxonomy"])
    return kb


def _enrich_taxonomy(tax: dict) -> None:
    """
    Enrichit la taxonomie avec des mots-clés FR industriels
    non présents dans la KB de base (couvrent la terminologie
    Total / TotalEnergies / ARTELIA / procédures MMRI/FAS).
    Ces enrichissements sont versionnés ici, pas dans le JSON.
    """

    # ── loop_min_check ────────────────────────────────────────────────────────
    tax["loop_min_check"]["keywords_fr"] += [
        "simulation 0%",
        "forcer 0%",
        "simulation sur 0",
        "courant 4 ma",
        "courant 4ma",
        "i 4ma",
        "valeur 4 ma",
        "4 ma bas echelle",
        "niveau 0 m",
        "niveau 0m",
        "bas echelle",
        "0 pourcent",
    ]

    # ── loop_max_check ────────────────────────────────────────────────────────
    tax["loop_max_check"]["keywords_fr"] += [
        "simulation 100%",
        "forcer 100%",
        "simulation sur 100",
        "courant 20 ma",
        "courant 20ma",
        "i 20ma",
        "valeur 20 ma",
        "20 ma haut echelle",
        "niveau 14 m",
        "100 pourcent",
        "haut echelle",
    ]

    # ── setpoint_injection ────────────────────────────────────────────────────
    tax["setpoint_injection"]["keywords_fr"] += [
        "augmenter simulation",
        "augmenter lentement simulation",
        "valeur simulation 15",
        "regler simulation 15",
        "regler 15 ma",
        "simulation 15 ma",
        "monter simulation",
        "donner top apparition seuil",
        "top apparition lshh",
        "top apparition lahh",
        "top apparition seuil",
        "relever valeur correspondante",
        "relever valeur declenchement",
        "apparition seuil lshh",
        "apparition seuil lsll",
        "pactware simulation",
        "forcer valeur simulation",
        "forcer simulation",
        "simulation radar",
    ]

    # ── alarm_console_check ───────────────────────────────────────────────────
    tax["alarm_console_check"]["keywords_fr"] += [
        "contrôler sncc seuil inactif",
        "contrôler sur sncc",
        "verifier sncc seuil",
        "seuil lshh inactif",
        "seuil lshh actif",
        "lshh1127",
        "lshh inactif",
        "lshh actif",
        "sequence xs inactif",
        "sequence xs actif",
        "xs-1112",
        "xs 1112",
        "sncc seuil",
        "alarme derangement",
        "yahh",
        "ya 1072",
        "hsa 9100",
        "sncc feu gaz",
    ]

    # ── trip_output_check ─────────────────────────────────────────────────────
    tax["trip_output_check"]["keywords_fr"] += [
        "sequence xs-1112 actif",
        "sequence xs actif",
        "verifier sequence active",
        "xS-1112 actif",
        "xs 1112 actif",
        "sequence securite active",
        "verifier action securite",
    ]

    # ── position_feedback_check ───────────────────────────────────────────────
    tax["position_feedback_check"]["keywords_fr"] += [
        "verifier vannes fermees",
        "verifier vannes ouvertes",
        "rov ferme",
        "rov ouvert",
        "fins de course",
        "fin de course",
        "zsh",
        "zsl",
        "ouverture vanne rov",
        "fermeture vanne rov",
        "vanne rov 11510",
        "vanne rov 11511",
        "zsh11510",
        "zsl11510",
    ]

    # ── full_stroke_test ──────────────────────────────────────────────────────
    tax["full_stroke_test"]["keywords_fr"] += [
        "vannes soient fermees",
        "vannes suivantes soient fermees",
        "vannes suivantes soient ouvertes",
        "rov11510 ferme",
        "rov11511 ferme",
        "fermeture rov",
        "course complete",
        "deplace vanne",
    ]

    # ── power_supply_check ────────────────────────────────────────────────────
    tax["power_supply_check"]["keywords_fr"] += [
        "couper alimentation radar",
        "couper alimentation",
        "ouvrir barrettes bornier",
        "couper tension",
        "coupure alimentation",
        "remettre radar sous tension",
        "remettre sous tension",
        "alimentation radar",
        "courant avant coupure",
        "courant apres remise",
        "courant avant",
        "courant apres",
        "ecart courant",
        "calculer difference courant",
        "relever courant",
    ]

    # ── watchdog_test ─────────────────────────────────────────────────────────
    tax["watchdog_test"]["keywords_fr"] += [
        "auto-teste",
        "autoteste",
        "s auto-teste",
        "radar s auto",
        "attendre 60 secondes",
        "attendre autotest",
        "signal de sortie autotest",
        "electronique signal sortie",
        "redemarrage",
        "redemarrer radar",
    ]

    # ── calibration_span_check ────────────────────────────────────────────────
    tax["calibration_span_check"]["keywords_fr"] += [
        "1er echo",
        "premier echo",
        "valeur echo",
        "echo db",
        "noter 1er echo",
        "noter premier echo",
        "echo inferieur 20 db",
        "echo superieur 20 db",
        "pactware dB",
        "signal radar",
    ]

    # ── bypass_check ──────────────────────────────────────────────────────────
    tax["bypass_check"]["keywords_fr"] += [
        "poser inhibition",
        "poser une inhibition",
        "inhibition sur le lts",
        "deposer inhibition",
        "lever inhibition",
        "retirer inhibition",
        "inhibition lts",
        "inhibition klaxon",
        "commutateur inhibition",
        "position inhibition",
    ]

    # ── return_to_service ─────────────────────────────────────────────────────
    tax["return_to_service"]["keywords_fr"] += [
        "desactiver simulation",
        "desactiver la simulation",
        "fin de simulation",
        "retour normale niveau",
        "retour a la normale",
        "retour service",
        "prévenir cdq",
        "prevenir cdq",
        "fin des essais",
        "remise en service",
        "actionner commande soft rearmement",
        "rearmement sequence",
        "xs-1112_r",
    ]

    # ── visual_inspection ─────────────────────────────────────────────────────
    tax["visual_inspection"]["keywords_fr"] += [
        "contrôler bon etat",
        "contrôler etat radar",
        "etat radar",
        "bon etat lts",
        "voyant pupitre",
        "voyant xa041",
        "xa041 allume",
        "xa041 eteint",
        "voyant clignote",
        "voyant fixe",
        "feu eclats",
        "avertisseur sonore",
    ]

    # ── zero_calibration_check ────────────────────────────────────────────────
    tax["zero_calibration_check"]["keywords_fr"] += [
        "diminuer lentement simulation",
        "diminuer simulation",
        "valeur simulation declenchement",
        "3,6 ma",
        "3.6 ma",
        "seuil declenchement",
        "valeur declenchement",
        "seuil bas capteur",
        "defaut capteur",
        "test defaut capteur",
        "3 6 ma",
    ]
