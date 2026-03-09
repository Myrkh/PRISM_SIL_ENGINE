"""
PTC Knowledge Base — Extension Exhaustive v2.0
===============================================
Couvre l'intégralité de la taxonomie TOTAL GS RC INS 107 (Annexe 6)
+ IEC 61511 / IEC 61508-6 / OREDA 2015 / PDS 2013 / NAMUR NE-106

NOUVEAUX COMPOSANTS vs v1.0 :
  Capteurs niveau : GWR, ultrasonique, displacer, capacitif, bubbletube,
                    lame vibrante, conductivité, jauge magnétique
  Capteurs pression : pression absolue, manomètre différentiel
  Capteurs température : thermocouple TC, RTD duplex, thermocouple direct
  Capteurs débit : électromagnétique, Coriolis, vortex, turbine, ultrasonique
  Gaz toxiques : IR, électrochimique H2S / CO / O2 / NH3 / SO2
  Feu/flamme : UV/IR, détecteur fumée ionisation / optique, thermovélocimétrique
  Actionneurs : vanne fail-open, vanne de régulation FC/FO, disque de rupture,
                soupape de sécurité, solénoïde bistable
  Logique : bouton ESD PB, module d'alarme écart

NOUVEAU : champ "fail_safe" sur tous les capteurs
  → burn_to_low / burn_to_high / hold_last_value / configurable
  → comportement sur perte alimentation, perte signal, perte HART
  → configuration recommandée selon direction de sécurité
  → alarme écart (discrepancy alarm)
"""

import json
from typing import Any
from generate_kb import build_kb, TEST_TAXONOMY  # import base v1.0


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS — templates de failure modes réutilisables
# ─────────────────────────────────────────────────────────────────────────────

def analog_base_modes(
    lambda_frozen_high: int, lambda_frozen_low: int, lambda_frozen_mid: int,
    lambda_drift_pos: int, lambda_drift_neg: int, lambda_loop: int,
    source: str,
    dangerous_high: list[str], dangerous_low: list[str]
) -> list[dict]:
    """
    Modes de base communs à tout transmetteur 4-20 mA.
    """
    return [
        {
            "id": "frozen_output_high",
            "display_fr": "Sortie figée haute (burn-to-high / fail-to-high)",
            "display_en": "Output frozen high (fail high)",
            "lambda_fit": lambda_frozen_high, "lambda_source": source,
            "dangerous_for_function": dangerous_high,
            "safe_for_function": dangerous_low,
            "detected_online": True, "dc_online": 1.0,
            "comment": "Signal > 21 mA détecté par diagnostic câblage si burn-to-high configuré",
            "coverage": {
                "loop_min_check": 0.0, "loop_max_check": 0.0,
                "loop_full_range": 0.0, "setpoint_injection": 0.0,
                "zero_calibration_check": 0.2, "visual_inspection": 0.1,
            },
        },
        {
            "id": "frozen_output_low",
            "display_fr": "Sortie figée basse / perte signal (burn-to-low / fail-to-low)",
            "display_en": "Output frozen low / loss of signal (fail low)",
            "lambda_fit": lambda_frozen_low, "lambda_source": source,
            "dangerous_for_function": dangerous_low,
            "safe_for_function": dangerous_high,
            "detected_online": True, "dc_online": 0.9,
            "comment": "< 3.6 mA détecté par détecteur de rupture boucle",
            "coverage": {
                "loop_min_check": 1.0, "loop_full_range": 1.0,
                "setpoint_injection": 0.9, "alarm_console_check": 0.8,
                "power_supply_check": 0.3,
            },
        },
        {
            "id": "frozen_mid_range",
            "display_fr": "Sortie figée milieu gamme (frozen mid-range — non détectable en ligne)",
            "display_en": "Output frozen at mid-range value",
            "lambda_fit": lambda_frozen_mid, "lambda_source": source,
            "dangerous_for_function": dangerous_high + dangerous_low,
            "detected_online": False, "dc_online": 0.0,
            "comment": "Mode le plus insidieux. Invisible en ligne sans redondance.",
            "coverage": {
                "loop_min_check": 1.0, "loop_max_check": 0.8,
                "loop_full_range": 1.0, "setpoint_injection": 0.9,
                "alarm_console_check": 0.7, "zero_calibration_check": 0.6,
            },
        },
        {
            "id": "drift_positive",
            "display_fr": "Dérive positive (lecture haute / surévaluation)",
            "display_en": "Positive drift (over-reading)",
            "lambda_fit": lambda_drift_pos, "lambda_source": source,
            "dangerous_for_function": dangerous_high,
            "detected_online": False, "dc_online": 0.0,
            "comment": "Dérive lente. Invisible sans référence externe.",
            "coverage": {
                "setpoint_injection": 0.5, "zero_calibration_check": 0.9,
                "loop_full_range": 0.1,
            },
        },
        {
            "id": "drift_negative",
            "display_fr": "Dérive négative (lecture basse / sous-évaluation)",
            "display_en": "Negative drift (under-reading)",
            "lambda_fit": lambda_drift_neg, "lambda_source": source,
            "dangerous_for_function": dangerous_low,
            "detected_online": False, "dc_online": 0.0,
            "coverage": {
                "setpoint_injection": 0.5, "zero_calibration_check": 0.9,
            },
        },
        {
            "id": "loss_of_loop_current",
            "display_fr": "Rupture boucle courant (câble, borne, alimentation)",
            "display_en": "Loss of loop current",
            "lambda_fit": lambda_loop, "lambda_source": source,
            "dangerous_for_function": dangerous_low,
            "safe_for_function": dangerous_high,
            "detected_online": True, "dc_online": 0.95,
            "coverage": {
                "loop_min_check": 1.0, "loop_full_range": 1.0,
                "power_supply_check": 0.6, "alarm_console_check": 0.9,
            },
        },
    ]


def tor_base_modes(
    lambda_stuck_closed: int, lambda_stuck_open: int,
    lambda_setpoint_drift: int, source: str,
    dangerous_closed: list[str], dangerous_open: list[str]
) -> list[dict]:
    """Modes de base pour tout capteur TOR."""
    return [
        {
            "id": "contact_stuck_closed",
            "display_fr": "Contact soudé / bloqué fermé (ne peut pas s'ouvrir)",
            "lambda_fit": lambda_stuck_closed, "lambda_source": source,
            "dangerous_for_function": dangerous_closed,
            "safe_for_function": dangerous_open,
            "detected_online": False, "dc_online": 0.0,
            "comment": "Contact NF bloqué = perte de trip sur montée process",
            "coverage": {
                "setpoint_tor_check": 1.0, "setpoint_injection": 0.9,
                "alarm_console_check": 0.8, "contact_continuity_check": 0.0,
            },
        },
        {
            "id": "contact_stuck_open",
            "display_fr": "Contact bloqué ouvert (faux trip permanent / spurious)",
            "lambda_fit": lambda_stuck_open, "lambda_source": source,
            "dangerous_for_function": dangerous_open,
            "safe_for_function": dangerous_closed,
            "detected_online": True, "dc_online": 0.5,
            "comment": "Spurious trip — souvent détecté opérationnellement",
            "coverage": {
                "contact_continuity_check": 1.0, "setpoint_tor_check": 1.0,
            },
        },
        {
            "id": "setpoint_drift",
            "display_fr": "Dérive du point de commutation (seuil décalé)",
            "lambda_fit": lambda_setpoint_drift, "lambda_source": source,
            "dangerous_for_function": dangerous_closed + dangerous_open,
            "detected_online": False, "dc_online": 0.0,
            "comment": "Mode dominant pour tous les switchs mécaniques",
            "coverage": {
                "setpoint_tor_check": 1.0, "setpoint_injection": 0.9,
                "zero_calibration_check": 0.7,
            },
        },
    ]


def fail_safe_analog(
    direction: str = "configurable",
    burn_low_signal: str = "3.6 mA",
    burn_high_signal: str = "21.5 mA",
    hart_on_loss: str = "hold_last_value_then_alert",
    sil_high_recomm: str = "burn_to_high",
    sil_low_recomm: str = "burn_to_low",
    notes: str = "",
) -> dict:
    """Structure standard failsafe pour transmetteur 4-20mA."""
    return {
        "output_type": "4-20mA",
        "burn_direction": direction,
        "on_power_loss": f"Output → {burn_low_signal} (rupture boucle détectée < 3.6 mA)",
        "on_signal_failure_low": f"Output → {burn_low_signal}  (burn-to-low si configuré)",
        "on_signal_failure_high": f"Output → {burn_high_signal} (burn-to-high si configuré)",
        "on_hart_comm_loss": hart_on_loss,
        "alarm_discrepancy": {
            "supported": True,
            "description": "Alarme écart entre valeur SIS et valeur DCS (même mesurande). Détecte dérive insidieuse.",
            "threshold_typical": "±5% de la gamme ou ±2× incertitude instrument",
            "failure_mode_covered": ["drift_positive", "drift_negative", "frozen_mid_range"],
            "coverage_if_active": 0.5,
        },
        "recommended_for_sil_high_function": sil_high_recomm,
        "recommended_for_sil_low_function": sil_low_recomm,
        "notes": notes,
    }


def fail_safe_tor(contact_type: str, failsafe_state: str) -> dict:
    """Structure standard failsafe pour capteur TOR."""
    return {
        "output_type": "TOR / contact sec",
        "contact_type": contact_type,
        "failsafe_state_on_power_loss": failsafe_state,
        "alarm_discrepancy": {
            "supported": True,
            "description": "Alarme écart si état contact SIS ≠ état attendu selon valeur DCS process (ex: pressostat déclenché mais PT ne montre pas haute pression)",
            "failure_mode_covered": ["contact_stuck_closed", "contact_stuck_open", "setpoint_drift"],
            "coverage_if_active": 0.4,
        },
        "notes": "Préférer NF (NormallyFermé/NormallyClose) pour fail-safe sur perte alimentation",
    }


# ─────────────────────────────────────────────────────────────────────────────
# NOUVEAUX COMPOSANTS
# ─────────────────────────────────────────────────────────────────────────────

def add_all_components(components: dict) -> None:

    # =========================================================================
    # NIVEAU — GUIDED WAVE RADAR (GWR / RADAR FILOGUIDE)
    # =========================================================================
    components["level_transmitter_gwr"] = {
        "display_fr": "Transmetteur de niveau RADAR guidé (GWR / Radar filoguidé) — 4-20 mA",
        "display_en": "Guided Wave Radar (GWR) level transmitter — 4-20 mA",
        "category": "sensor",
        "technology": "GWR / Guided Wave Radar",
        "tag_codes": ["LT", "LI", "LA"],
        "total_ins107_function": "RADAR FILOGUIDE / GUIDED WAVE RADAR",
        "sif_roles": ["initiator"],
        "signal_type": "analog_4_20ma",
        "fail_safe": fail_safe_analog(
            direction="configurable",
            sil_high_recomm="burn_to_high",
            sil_low_recomm="burn_to_low",
            notes="GWR = meilleure technologie pour interfaces liquide/liquide. Sensible aux dépôts sur la tige."
        ),
        "lambda_total_fit": 230,
        "lambda_source": "OREDA2015 Table 6.20 + exida GWR FMEDA",
        "lambda_uncertainty": "Lognormal EF=3",
        "dc_auto": 0.65,
        "dc_source": "exida — GWR with HART diagnostics",
        "beta_typical": 0.02,
        "failure_modes": [
            *analog_base_modes(25, 35, 28, 28, 28, 30, "OREDA2015 Table 6.20",
                               ["LAHH", "LAH"], ["LALL", "LAL"]),
            {
                "id": "probe_coating_deposit",
                "display_fr": "Enrobage / dépôt sur tige guide d'onde",
                "display_en": "Probe coating / deposit on waveguide",
                "lambda_fit": 35, "lambda_source": "PDS2013 + Field experience",
                "dangerous_for_function": ["LAHH", "LALL"],
                "detected_online": False, "dc_online": 0.0,
                "comment": "Dépôt visqueux ou solide sur la tige → signal atténué → faux niveau bas. Fréquent en pétrochimie.",
                "coverage": {
                    "visual_inspection": 0.5, "zero_calibration_check": 0.3,
                    "setpoint_injection": 0.2,
                },
            },
            {
                "id": "probe_mechanical_damage",
                "display_fr": "Dommage mécanique tige (choc, corrosion, torsion)",
                "lambda_fit": 20, "lambda_source": "Field experience",
                "dangerous_for_function": ["ALL"],
                "detected_online": True, "dc_online": 0.6,
                "comment": "Signal hors gamme si tige cassée",
                "coverage": {
                    "visual_inspection": 0.7, "loop_full_range": 0.8,
                },
            },
            {
                "id": "interface_level_confusion",
                "display_fr": "Confusion interface liquide/liquide (mauvaise permittivité)",
                "lambda_fit": 15, "lambda_source": "Field experience — liquid/liquid interface",
                "dangerous_for_function": ["LAHH", "LALL"],
                "detected_online": False, "dc_online": 0.0,
                "comment": "Si ε1 ≈ ε2, interface mal détectée. Nécessite recalibration process.",
                "coverage": {
                    "zero_calibration_check": 0.5, "setpoint_injection": 0.3,
                },
            },
            {
                "id": "condensation_false_level",
                "display_fr": "Condensation sur tige (faux niveau haut)",
                "lambda_fit": 12, "lambda_source": "Field experience — cryogenic / steam service",
                "dangerous_for_function": ["LAHH"],
                "detected_online": False, "dc_online": 0.0,
                "coverage": {
                    "visual_inspection": 0.4, "zero_calibration_check": 0.2,
                },
            },
        ],
    }

    # =========================================================================
    # NIVEAU — ULTRASONIQUE (4-20mA)
    # =========================================================================
    components["level_transmitter_ultrasonic"] = {
        "display_fr": "Transmetteur de niveau ULTRASONIQUE — 4-20 mA",
        "display_en": "Ultrasonic level transmitter — 4-20 mA",
        "category": "sensor",
        "technology": "Ultrasonic",
        "tag_codes": ["LT", "LI", "LA"],
        "total_ins107_function": "NIVEAU ULTRASON / LEVEL ULTRASON",
        "sif_roles": ["initiator"],
        "signal_type": "analog_4_20ma",
        "fail_safe": fail_safe_analog(notes="Technologie non-contact. Très sensible mousse/vapeurs/turbulence."),
        "lambda_total_fit": 350,
        "lambda_source": "OREDA2015 Table 6.20 + SINTEF",
        "dc_auto": 0.50,
        "beta_typical": 0.02,
        "failure_modes": [
            *analog_base_modes(35, 50, 40, 35, 35, 40, "OREDA2015 Table 6.20",
                               ["LAHH", "LAH"], ["LALL", "LAL"]),
            {
                "id": "foam_echo_loss",
                "display_fr": "Perte d'écho — mousse / vapeur / turbulence",
                "lambda_fit": 60, "lambda_source": "OREDA2015 — dominant mode ultrasonic",
                "dangerous_for_function": ["LALL"],
                "detected_online": True, "dc_online": 0.7,
                "comment": "Perte écho → signal drop → erreur vers bas. Dominant en service process agité.",
                "coverage": {
                    "loop_min_check": 0.9, "setpoint_injection": 0.7,
                    "zero_calibration_check": 0.4,
                },
            },
            {
                "id": "transducer_scaling",
                "display_fr": "Encrassement / tartre sur transducteur",
                "lambda_fit": 40, "lambda_source": "PDS2013",
                "dangerous_for_function": ["LAHH", "LALL"],
                "detected_online": False, "dc_online": 0.0,
                "coverage": {
                    "visual_inspection": 0.6, "zero_calibration_check": 0.4,
                    "setpoint_injection": 0.2,
                },
            },
            {
                "id": "spurious_echo_false_level",
                "display_fr": "Écho parasite (obstacle interne, agitateur, entrée produit)",
                "lambda_fit": 30, "lambda_source": "Field experience",
                "dangerous_for_function": ["LAHH"],
                "detected_online": False, "dc_online": 0.0,
                "comment": "Écho parasite sur structure interne → faux niveau haut. Nécessite filtrage.",
                "coverage": {
                    "setpoint_injection": 0.5, "zero_calibration_check": 0.3,
                },
            },
            {
                "id": "temperature_compensation_error",
                "display_fr": "Erreur compensation température (vitesse son)",
                "lambda_fit": 20, "lambda_source": "OREDA2015",
                "dangerous_for_function": ["LAHH", "LALL"],
                "detected_online": False, "dc_online": 0.0,
                "coverage": {
                    "zero_calibration_check": 0.7, "setpoint_injection": 0.4,
                },
            },
        ],
    }

    # =========================================================================
    # NIVEAU — DISPLACER (displaceur, flotteur immergé) 4-20mA
    # =========================================================================
    components["level_transmitter_displacer"] = {
        "display_fr": "Transmetteur de niveau à displaceur (flotteur immergé) — 4-20 mA",
        "display_en": "Displacer level transmitter — 4-20 mA",
        "category": "sensor",
        "technology": "Displacer / Archimède",
        "tag_codes": ["LT", "LI", "LA"],
        "total_ins107_function": "LEVEL DISPLACER / NIVEAU CONTACT",
        "sif_roles": ["initiator"],
        "signal_type": "analog_4_20ma",
        "fail_safe": fail_safe_analog(
            notes="Technologie mécanique. Sensible aux dépôts sur le displaceur et à la densité du fluide."
        ),
        "lambda_total_fit": 380,
        "lambda_source": "OREDA2015 Table 6.20 + PDS2013 Table A.6",
        "dc_auto": 0.45,
        "beta_typical": 0.03,
        "failure_modes": [
            *analog_base_modes(30, 45, 35, 40, 40, 40, "OREDA2015",
                               ["LAHH", "LAH"], ["LALL", "LAL"]),
            {
                "id": "displacer_coating",
                "display_fr": "Enrobage displaceur (paraffine, polymère, calcaire)",
                "lambda_fit": 60, "lambda_source": "OREDA2015 — dominant mode displacer",
                "dangerous_for_function": ["LAHH"],
                "detected_online": False, "dc_online": 0.0,
                "comment": "Masse apparente augmentée → lecture haute fausse → danger LAHH. Très fréquent en crude oil.",
                "coverage": {
                    "visual_inspection": 0.6, "zero_calibration_check": 0.5,
                    "setpoint_injection": 0.3,
                },
            },
            {
                "id": "displacer_corrosion_hole",
                "display_fr": "Perforation displaceur par corrosion (remplissage liquide)",
                "lambda_fit": 25, "lambda_source": "PDS2013",
                "dangerous_for_function": ["LALL"],
                "detected_online": False, "dc_online": 0.0,
                "comment": "Displaceur percé → se remplit → poids augmente → lecture niveau bas fictive → dangereux pour LALL",
                "coverage": {
                    "visual_inspection": 0.3, "zero_calibration_check": 0.4,
                    "loop_min_check": 0.8,
                },
            },
            {
                "id": "density_change_process",
                "display_fr": "Changement de densité fluide process (non recalibré)",
                "lambda_fit": 30, "lambda_source": "Field experience",
                "dangerous_for_function": ["LAHH", "LALL"],
                "detected_online": False, "dc_online": 0.0,
                "comment": "Le displaceur est sensible à la densité. Un changement de fluide non recalibré = erreur systématique.",
                "coverage": {
                    "zero_calibration_check": 0.8, "setpoint_injection": 0.4,
                },
            },
            {
                "id": "torque_tube_failure",
                "display_fr": "Défaillance tube de torsion (fatigue, corrosion)",
                "lambda_fit": 30, "lambda_source": "OREDA2015",
                "dangerous_for_function": ["ALL"],
                "detected_online": True, "dc_online": 0.4,
                "coverage": {
                    "loop_min_check": 0.7, "visual_inspection": 0.3,
                    "zero_calibration_check": 0.3,
                },
            },
        ],
    }

    # =========================================================================
    # NIVEAU — CAPACITIF 4-20mA
    # =========================================================================
    components["level_transmitter_capacitive"] = {
        "display_fr": "Transmetteur de niveau capacitif — 4-20 mA",
        "display_en": "Capacitive level transmitter — 4-20 mA",
        "category": "sensor",
        "technology": "Capacitive",
        "tag_codes": ["LT", "LI"],
        "total_ins107_function": "CAPACITIVE / CAPACITIF",
        "sif_roles": ["initiator"],
        "signal_type": "analog_4_20ma",
        "fail_safe": fail_safe_analog(
            notes="Sensible au changement de constante diélectrique et aux dépôts conducteurs."
        ),
        "lambda_total_fit": 420,
        "lambda_source": "OREDA2015 Table 6.20 — capacitive sensor",
        "dc_auto": 0.40,
        "failure_modes": [
            *analog_base_modes(35, 50, 40, 45, 45, 45, "OREDA2015",
                               ["LAHH", "LAH"], ["LALL", "LAL"]),
            {
                "id": "dielectric_constant_change",
                "display_fr": "Changement constante diélectrique (produit différent, contamination)",
                "lambda_fit": 60, "lambda_source": "OREDA2015 — dominant mode capacitive",
                "dangerous_for_function": ["LAHH", "LALL"],
                "detected_online": False, "dc_online": 0.0,
                "comment": "εr du fluide change → erreur systématique. Nécessite recalibration.",
                "coverage": {
                    "zero_calibration_check": 0.8, "setpoint_injection": 0.4,
                },
            },
            {
                "id": "conductive_coating",
                "display_fr": "Dépôt conducteur sur sonde (eau, sels, particules)",
                "lambda_fit": 50, "lambda_source": "Field experience",
                "dangerous_for_function": ["LAHH"],
                "detected_online": False, "dc_online": 0.0,
                "comment": "Dépôt conducteur → capacité parasite → lecture haute fausse.",
                "coverage": {
                    "visual_inspection": 0.5, "zero_calibration_check": 0.5,
                    "setpoint_injection": 0.2,
                },
            },
            {
                "id": "moisture_electronics",
                "display_fr": "Humidité dans l'électronique (milieu sévère)",
                "lambda_fit": 30, "lambda_source": "OREDA2015",
                "dangerous_for_function": ["ALL"],
                "detected_online": False, "dc_online": 0.0,
                "coverage": {
                    "visual_inspection": 0.4, "loop_full_range": 0.7,
                },
            },
        ],
    }

    # =========================================================================
    # NIVEAU — BUBBLETUBE / BULLAGE
    # =========================================================================
    components["level_transmitter_bubbletube"] = {
        "display_fr": "Transmetteur de niveau à bullage (bubbletube) — 4-20 mA",
        "display_en": "Bubbletube / purge level transmitter — 4-20 mA",
        "category": "sensor",
        "technology": "Bubbletube / Air purge",
        "tag_codes": ["LT", "LI"],
        "total_ins107_function": "BUBLE TYPE / BULLAGE",
        "sif_roles": ["initiator"],
        "signal_type": "analog_4_20ma",
        "fail_safe": fail_safe_analog(
            notes="Dépend de l'alimentation en air instrument. Perte air = perte mesure."
        ),
        "lambda_total_fit": 500,
        "lambda_source": "OREDA2015 Table 6.20 + PDS2013 — bubbletube",
        "dc_auto": 0.35,
        "failure_modes": [
            *analog_base_modes(40, 55, 45, 40, 40, 50, "OREDA2015",
                               ["LAHH", "LAH"], ["LALL", "LAL"]),
            {
                "id": "purge_air_supply_failure",
                "display_fr": "Perte alimentation air de purge",
                "lambda_fit": 80, "lambda_source": "PDS2013 Table A.9",
                "dangerous_for_function": ["LALL"],
                "detected_online": True, "dc_online": 0.6,
                "comment": "Sans air de purge → pas de contre-pression → mesure = 0. Dangereux LALL.",
                "coverage": {
                    "instrument_air_check": 1.0, "visual_inspection": 0.3,
                    "loop_min_check": 0.9,
                },
            },
            {
                "id": "dip_tube_blockage",
                "display_fr": "Colmatage tube plongeur (dépôts, bouchon)",
                "lambda_fit": 70, "lambda_source": "OREDA2015 — dominant mode bubbletube",
                "dangerous_for_function": ["LALL"],
                "detected_online": False, "dc_online": 0.0,
                "comment": "Bouchage → pression mesurée erronée. Purge régulière obligatoire.",
                "coverage": {
                    "impulse_line_check": 0.9, "visual_inspection": 0.2,
                    "setpoint_injection": 0.3,
                },
            },
            {
                "id": "density_change",
                "display_fr": "Changement densité fluide (mesure indirect via pression)",
                "lambda_fit": 30, "lambda_source": "Field experience",
                "dangerous_for_function": ["LAHH", "LALL"],
                "detected_online": False, "dc_online": 0.0,
                "coverage": {
                    "zero_calibration_check": 0.7, "setpoint_injection": 0.4,
                },
            },
        ],
    }

    # =========================================================================
    # NIVEAU — LAME VIBRANTE / VIBRATING ROD (TOR)
    # =========================================================================
    components["level_switch_vibrating_rod"] = {
        "display_fr": "Détecteur de niveau à lame vibrante / barreau vibrant (TOR)",
        "display_en": "Vibrating rod / tuning fork level switch (TOR)",
        "category": "sensor",
        "technology": "Vibrating rod / tuning fork",
        "tag_codes": ["LSH", "LSL", "LSHH", "LSLL"],
        "total_ins107_function": "VIBRATING BLADE / BARREAU VIB / LAME VIB",
        "sif_roles": ["initiator"],
        "signal_type": "digital_tor",
        "fail_safe": fail_safe_tor("NF ou NO (configurable)", "NF = failsafe ouverture (trip)"),
        "lambda_total_fit": 400,
        "lambda_source": "OREDA2015 Table 6.20 + SINTEF A27482",
        "dc_auto": 0.40,
        "dc_source": "Autodiag fréquence vibration. Si fréquence OK mais amplitude faible → ND.",
        "beta_typical": 0.03,
        "failure_modes": [
            *tor_base_modes(80, 80, 120, "OREDA2015",
                            ["LALL", "LSLL"], ["LAHH", "LSHH"]),
            {
                "id": "tuning_fork_damping_coating",
                "display_fr": "Amortissement / enrobage fourche (dépôt visqueux)",
                "lambda_fit": 90, "lambda_source": "OREDA2015 — dominant mode vibrating rod",
                "dangerous_for_function": ["LAHH", "LSHH"],
                "detected_online": True, "dc_online": 0.5,
                "comment": "Dépôt visqueux amortit la vibration → détecté comme 'niveau atteint' → faux trip. Autodiag partiel.",
                "coverage": {
                    "setpoint_injection": 0.7, "visual_inspection": 0.5,
                    "setpoint_tor_check": 0.8,
                },
            },
            {
                "id": "tuning_fork_corrosion_thinning",
                "display_fr": "Amincissement lame par corrosion / érosion",
                "lambda_fit": 30, "lambda_source": "Field experience — corrosive service",
                "dangerous_for_function": ["ALL"],
                "detected_online": False, "dc_online": 0.0,
                "comment": "Fréquence de résonance change → risque de faux trip ou non-trip.",
                "coverage": {
                    "visual_inspection": 0.4, "setpoint_tor_check": 0.7,
                },
            },
        ],
    }

    # =========================================================================
    # NIVEAU — CONDUCTIVITÉ (TOR)
    # =========================================================================
    components["level_switch_conductivity"] = {
        "display_fr": "Détecteur de niveau par conductivité (TOR)",
        "display_en": "Conductivity level switch (TOR)",
        "category": "sensor",
        "technology": "Conductivity",
        "tag_codes": ["LSH", "LSL", "LSHH", "LSLL"],
        "total_ins107_function": "CONDUCTIVE / CONDUCTIVITE",
        "sif_roles": ["initiator"],
        "signal_type": "digital_tor",
        "fail_safe": fail_safe_tor("NF (recommandé)", "Ouverture = trip sur perte alimentation"),
        "lambda_total_fit": 500,
        "lambda_source": "PDS2013 Table A.3 — conductivity sensor",
        "dc_auto": 0.20,
        "failure_modes": [
            *tor_base_modes(100, 100, 150, "PDS2013",
                            ["LALL", "LSLL"], ["LAHH", "LSHH"]),
            {
                "id": "electrode_coating_non_conductive",
                "display_fr": "Dépôt non conducteur sur électrode (oxyde, graisse, polymère)",
                "lambda_fit": 120, "lambda_source": "OREDA2015 — dominant mode conductivity",
                "dangerous_for_function": ["LAHH", "LSHH"],
                "detected_online": False, "dc_online": 0.0,
                "comment": "Couche isolante → électrode 'ne voit pas' le liquide → non-détection niveau.",
                "coverage": {
                    "visual_inspection": 0.5, "setpoint_injection": 0.7,
                    "setpoint_tor_check": 0.8, "contact_continuity_check": 0.3,
                },
            },
            {
                "id": "liquid_conductivity_change",
                "display_fr": "Changement conductivité du liquide (dilution, contamination)",
                "lambda_fit": 30, "lambda_source": "Field experience",
                "dangerous_for_function": ["LAHH", "LSHH"],
                "detected_online": False, "dc_online": 0.0,
                "comment": "Si σ liquide chute sous seuil sensibilité → non détection.",
                "coverage": {
                    "setpoint_tor_check": 0.6, "zero_calibration_check": 0.4,
                },
            },
        ],
    }

    # =========================================================================
    # TEMPÉRATURE — THERMOCOUPLE (TC) — 4-20mA via transmetteur
    # =========================================================================
    components["temperature_transmitter_thermocouple"] = {
        "display_fr": "Transmetteur de température thermocouple (TC Type J/K/E/T/S) — 4-20 mA",
        "display_en": "Thermocouple temperature transmitter — 4-20 mA",
        "category": "sensor",
        "technology": "Thermocouple + transmetteur",
        "tag_codes": ["TT", "TI", "TA"],
        "total_ins107_function": "THERMOCOUPLE / THERMO DUPLEX / THERMO MULTI",
        "sif_roles": ["initiator"],
        "signal_type": "analog_4_20ma",
        "fail_safe": fail_safe_analog(
            notes="TC + transmetteur séparé. Soudure chaude sujette à dégradation. Compensation soudure froide critique."
        ),
        "lambda_total_fit": 280,
        "lambda_source": "OREDA2015 Table 6.16 + exida TC transmitter FMEDA",
        "dc_auto": 0.55,
        "failure_modes": [
            *analog_base_modes(30, 45, 30, 40, 40, 35, "OREDA2015 Table 6.16",
                               ["TAHH", "TAH"], ["TALL", "TAL"]),
            {
                "id": "thermocouple_open_circuit",
                "display_fr": "Circuit ouvert thermocouple (soudure cassée / câble coupé)",
                "lambda_fit": 55, "lambda_source": "OREDA2015 — dominant mode TC",
                "dangerous_for_function": ["ALL"],
                "detected_online": True, "dc_online": 0.9,
                "comment": "TC ouvert → upscale ou downscale selon type transmetteur. Généralement détecté.",
                "coverage": {
                    "loop_min_check": 1.0, "loop_full_range": 1.0,
                    "setpoint_injection": 0.9, "alarm_console_check": 0.9,
                },
            },
            {
                "id": "thermocouple_short_circuit",
                "display_fr": "Court-circuit thermocouple",
                "lambda_fit": 20, "lambda_source": "OREDA2015",
                "dangerous_for_function": ["TALL", "TAL"],
                "detected_online": True, "dc_online": 0.6,
                "coverage": {
                    "loop_min_check": 0.8, "setpoint_injection": 0.7,
                },
            },
            {
                "id": "cjc_error_cold_junction",
                "display_fr": "Erreur compensation soudure froide (CJC)",
                "lambda_fit": 20, "lambda_source": "exida FMEDA",
                "dangerous_for_function": ["TAHH", "TALL"],
                "detected_online": False, "dc_online": 0.0,
                "comment": "CJC incorrect → décalage systématique de la mesure. Invisible en ligne.",
                "coverage": {
                    "setpoint_injection": 0.5, "zero_calibration_check": 0.9,
                },
            },
            {
                "id": "thermocouple_aging_emf_drift",
                "display_fr": "Vieillissement / dérive FEM thermocouple (service haute T°)",
                "lambda_fit": 35, "lambda_source": "OREDA2015 + ISA-TR104.00.01",
                "dangerous_for_function": ["TAHH", "TALL"],
                "detected_online": False, "dc_online": 0.0,
                "comment": "Dérive lente inhérente. Plus rapide > 600°C. Recalibration nécessaire.",
                "coverage": {
                    "zero_calibration_check": 0.9, "setpoint_injection": 0.5,
                },
            },
            {
                "id": "sheath_corrosion_contamination",
                "display_fr": "Corrosion / contamination gaine de protection",
                "lambda_fit": 25, "lambda_source": "Field experience",
                "dangerous_for_function": ["TAHH", "TALL"],
                "detected_online": False, "dc_online": 0.0,
                "coverage": {
                    "visual_inspection": 0.5, "zero_calibration_check": 0.3,
                },
            },
        ],
    }

    # =========================================================================
    # DÉBIT — ÉLECTROMAGNÉTIQUE (4-20mA)
    # =========================================================================
    components["flow_transmitter_electromagnetic"] = {
        "display_fr": "Transmetteur de débit électromagnétique (Débitmètre EM) — 4-20 mA",
        "display_en": "Electromagnetic flow transmitter — 4-20 mA",
        "category": "sensor",
        "technology": "Electromagnetic / Magmeter",
        "tag_codes": ["FT", "FI", "FA"],
        "total_ins107_function": "ELECTRO MAGNETIC / ELECTROMAG",
        "sif_roles": ["initiator"],
        "signal_type": "analog_4_20ma",
        "fail_safe": fail_safe_analog(
            notes="Uniquement pour fluides conducteurs (σ > 5 μS/cm). Tuyau plein requis. Excellent DC avec vide détection."
        ),
        "lambda_total_fit": 250,
        "lambda_source": "OREDA2015 Table 6.18 — electromagnetic flowmeter",
        "dc_auto": 0.65,
        "dc_source": "Autodiag disponibles : empty pipe detection, coil check, electrode check",
        "failure_modes": [
            *analog_base_modes(25, 40, 35, 35, 35, 30, "OREDA2015 Table 6.18",
                               ["FAHH", "FAH"], ["FALL", "FAL"]),
            {
                "id": "empty_pipe_measurement",
                "display_fr": "Tuyau non plein (mesure invalide sur gaz/vapeur)",
                "lambda_fit": 30, "lambda_source": "Field experience",
                "dangerous_for_function": ["FAHH", "FALL"],
                "detected_online": True, "dc_online": 0.8,
                "comment": "Détection tuyau vide disponible sur transmetteurs modernes.",
                "coverage": {
                    "loop_full_range": 0.7, "zero_calibration_check": 0.5,
                    "alarm_console_check": 0.6,
                },
            },
            {
                "id": "electrode_coating_nonconductive",
                "display_fr": "Enrobage non conducteur électrodes (oxyde, polymère)",
                "lambda_fit": 40, "lambda_source": "OREDA2015 — dominant EM mode",
                "dangerous_for_function": ["FALL"],
                "detected_online": False, "dc_online": 0.0,
                "comment": "Diminution signal EMF → lecture sous-évaluée. Fréquent en service wastewater.",
                "coverage": {
                    "zero_calibration_check": 0.8, "setpoint_injection": 0.5,
                    "visual_inspection": 0.2,
                },
            },
            {
                "id": "low_conductivity_fluid",
                "display_fr": "Conductivité fluide trop basse (service mixte eau/HC)",
                "lambda_fit": 20, "lambda_source": "Field experience",
                "dangerous_for_function": ["FAHH", "FALL"],
                "detected_online": True, "dc_online": 0.5,
                "comment": "σ < seuil → signal bruit → mesure instable.",
                "coverage": {
                    "setpoint_injection": 0.4, "zero_calibration_check": 0.5,
                },
            },
            {
                "id": "grounding_failure",
                "display_fr": "Défaut mise à la terre (bruit électrique sur signal)",
                "lambda_fit": 20, "lambda_source": "OREDA2015",
                "dangerous_for_function": ["FAHH"],
                "detected_online": False, "dc_online": 0.0,
                "coverage": {
                    "visual_inspection": 0.4, "zero_calibration_check": 0.3,
                },
            },
        ],
    }

    # =========================================================================
    # DÉBIT — CORIOLIS (4-20mA)
    # =========================================================================
    components["flow_transmitter_coriolis"] = {
        "display_fr": "Transmetteur de débit / densité Coriolis — 4-20 mA",
        "display_en": "Coriolis mass flow / density transmitter — 4-20 mA",
        "category": "sensor",
        "technology": "Coriolis",
        "tag_codes": ["FT", "DT", "FI"],
        "total_ins107_function": "CORIOLIS",
        "sif_roles": ["initiator"],
        "signal_type": "analog_4_20ma",
        "fail_safe": fail_safe_analog(
            notes="Très haute précision. Autodiag avancés sur la plupart des modèles. Sensible aux vibrations externes."
        ),
        "lambda_total_fit": 180,
        "lambda_source": "exida FMEDA Coriolis + OREDA2015 Table 6.18",
        "dc_auto": 0.75,
        "dc_source": "Coriolis avec autodiag vibration, densité, température",
        "failure_modes": [
            *analog_base_modes(18, 28, 25, 25, 25, 20, "OREDA2015 Table 6.18",
                               ["FAHH", "FAH"], ["FALL", "FAL"]),
            {
                "id": "tube_vibration_external",
                "display_fr": "Vibrations externes perturbant la mesure",
                "lambda_fit": 30, "lambda_source": "Field experience",
                "dangerous_for_function": ["FAHH"],
                "detected_online": True, "dc_online": 0.6,
                "comment": "Vibrations mécaniques proches de la fréquence de résonance → erreur de mesure.",
                "coverage": {
                    "zero_calibration_check": 0.5, "setpoint_injection": 0.4,
                    "visual_inspection": 0.2,
                },
            },
            {
                "id": "tube_erosion_corrosion",
                "display_fr": "Érosion / corrosion tubes (fluide abrasif / corrosif)",
                "lambda_fit": 15, "lambda_source": "OREDA2015",
                "dangerous_for_function": ["ALL"],
                "detected_online": True, "dc_online": 0.5,
                "comment": "Modification épaisseur → déviation fréquence → alarme diagnostic.",
                "coverage": {
                    "visual_inspection": 0.3, "loop_full_range": 0.6,
                    "zero_calibration_check": 0.5,
                },
            },
            {
                "id": "gas_entrainment",
                "display_fr": "Entraînement gaz / deux phases (fluctuation mesure)",
                "lambda_fit": 20, "lambda_source": "Field experience",
                "dangerous_for_function": ["FAHH", "FALL"],
                "detected_online": True, "dc_online": 0.7,
                "comment": "Présence gaz dans liquide → oscillation → alarme drive gain.",
                "coverage": {
                    "setpoint_injection": 0.3, "alarm_console_check": 0.5,
                },
            },
        ],
    }

    # =========================================================================
    # DÉBIT — VORTEX (4-20mA)
    # =========================================================================
    components["flow_transmitter_vortex"] = {
        "display_fr": "Transmetteur de débit à effet vortex — 4-20 mA",
        "display_en": "Vortex flow transmitter — 4-20 mA",
        "category": "sensor",
        "technology": "Vortex",
        "tag_codes": ["FT", "FI", "FA"],
        "total_ins107_function": "VORTEX",
        "sif_roles": ["initiator"],
        "signal_type": "analog_4_20ma",
        "fail_safe": fail_safe_analog(
            notes="Débit minimum requis (Reynolds > 20000). Très sensible aux vibrations pipeline."
        ),
        "lambda_total_fit": 320,
        "lambda_source": "OREDA2015 Table 6.18 — vortex meter",
        "dc_auto": 0.50,
        "failure_modes": [
            *analog_base_modes(30, 45, 38, 35, 35, 40, "OREDA2015",
                               ["FAHH", "FAH"], ["FALL", "FAL"]),
            {
                "id": "bluff_body_fouling",
                "display_fr": "Encrassement corps déflecteur (bluff body)",
                "lambda_fit": 50, "lambda_source": "OREDA2015 — dominant vortex mode",
                "dangerous_for_function": ["FALL"],
                "detected_online": False, "dc_online": 0.0,
                "comment": "Dépôt sur le corps déflecteur → atténuation signal vortex → sous-évaluation débit.",
                "coverage": {
                    "zero_calibration_check": 0.7, "visual_inspection": 0.3,
                    "setpoint_injection": 0.4,
                },
            },
            {
                "id": "vibration_induced_false_flow",
                "display_fr": "Vibrations pipeline induisant signal parasite (faux débit)",
                "lambda_fit": 40, "lambda_source": "Field experience",
                "dangerous_for_function": ["FAHH"],
                "detected_online": False, "dc_online": 0.0,
                "comment": "Vibrations mécaniques à la fréquence des vortex → lecture positive en débit nul.",
                "coverage": {
                    "zero_calibration_check": 0.6, "setpoint_injection": 0.5,
                },
            },
            {
                "id": "low_flow_no_measurement",
                "display_fr": "Débit trop faible (en-dessous du seuil de mesure)",
                "lambda_fit": 25, "lambda_source": "Field experience",
                "dangerous_for_function": ["FALL"],
                "detected_online": False, "dc_online": 0.0,
                "coverage": {
                    "setpoint_injection": 0.4, "loop_min_check": 0.7,
                },
            },
        ],
    }

    # =========================================================================
    # DÉBIT — TURBINE (4-20mA/impulsion)
    # =========================================================================
    components["flow_transmitter_turbine"] = {
        "display_fr": "Débitmètre turbine — sortie impulsion / 4-20 mA",
        "display_en": "Turbine flow meter — pulse / 4-20 mA",
        "category": "sensor",
        "technology": "Turbine",
        "tag_codes": ["FT", "FI", "FA"],
        "total_ins107_function": "TURBINE",
        "sif_roles": ["initiator"],
        "signal_type": "pulse_or_4_20ma",
        "fail_safe": fail_safe_analog(
            notes="Pièces mécaniques tournantes = usure. Contaminants solides critique."
        ),
        "lambda_total_fit": 450,
        "lambda_source": "OREDA2015 Table 6.18 — turbine meter",
        "dc_auto": 0.35,
        "failure_modes": [
            *analog_base_modes(40, 55, 45, 40, 40, 50, "OREDA2015 Table 6.18",
                               ["FAHH", "FAH"], ["FALL", "FAL"]),
            {
                "id": "rotor_bearing_wear",
                "display_fr": "Usure roulements / paliers rotor",
                "lambda_fit": 80, "lambda_source": "OREDA2015 — dominant turbine mode",
                "dangerous_for_function": ["FALL"],
                "detected_online": False, "dc_online": 0.0,
                "comment": "Usure → frottement → sous-comptage. Invisible sans comparaison.",
                "coverage": {
                    "visual_inspection": 0.2, "zero_calibration_check": 0.7,
                    "setpoint_injection": 0.5,
                },
            },
            {
                "id": "rotor_damage_contamination",
                "display_fr": "Dommage rotor (corps étranger, érosion, cavitation)",
                "lambda_fit": 50, "lambda_source": "OREDA2015",
                "dangerous_for_function": ["FALL"],
                "detected_online": True, "dc_online": 0.4,
                "comment": "Casse pale → signal impulsion absent.",
                "coverage": {
                    "loop_min_check": 0.8, "visual_inspection": 0.3,
                    "zero_calibration_check": 0.5,
                },
            },
            {
                "id": "pickup_coil_failure",
                "display_fr": "Défaillance bobine de détection magnétique",
                "lambda_fit": 40, "lambda_source": "OREDA2015",
                "dangerous_for_function": ["FALL"],
                "detected_online": True, "dc_online": 0.7,
                "comment": "Pas d'impulsion → détecté comme débit nul.",
                "coverage": {
                    "contact_continuity_check": 0.8,
                    "loop_min_check": 0.9, "visual_inspection": 0.2,
                },
            },
        ],
    }

    # =========================================================================
    # DÉBIT — ULTRASONIQUE (4-20mA)
    # =========================================================================
    components["flow_transmitter_ultrasonic"] = {
        "display_fr": "Débitmètre ultrasonique (transit time) — 4-20 mA",
        "display_en": "Ultrasonic flow transmitter (transit time) — 4-20 mA",
        "category": "sensor",
        "technology": "Ultrasonic transit time",
        "tag_codes": ["FT", "FI", "FA"],
        "total_ins107_function": "DEBIT ULTRASON / FLOW ULTRASONIC",
        "sif_roles": ["initiator"],
        "signal_type": "analog_4_20ma",
        "fail_safe": fail_safe_analog(
            notes="Technologie non intrusive possible (clamp-on). Sensible profil d'écoulement, dépôts transducteurs."
        ),
        "lambda_total_fit": 280,
        "lambda_source": "OREDA2015 Table 6.18 + exida",
        "dc_auto": 0.60,
        "failure_modes": [
            *analog_base_modes(28, 42, 35, 32, 32, 35, "OREDA2015",
                               ["FAHH", "FAH"], ["FALL", "FAL"]),
            {
                "id": "transducer_scaling_deposit",
                "display_fr": "Dépôt / entartrages sur transducteurs",
                "lambda_fit": 45, "lambda_source": "OREDA2015 — dominant US mode",
                "dangerous_for_function": ["FALL"],
                "detected_online": False, "dc_online": 0.0,
                "coverage": {
                    "visual_inspection": 0.5, "zero_calibration_check": 0.6,
                    "setpoint_injection": 0.4,
                },
            },
            {
                "id": "signal_attenuation_gas_bubbles",
                "display_fr": "Atténuation signal — bulles de gaz / deux phases",
                "lambda_fit": 30, "lambda_source": "Field experience",
                "dangerous_for_function": ["FALL"],
                "detected_online": True, "dc_online": 0.6,
                "coverage": {
                    "loop_min_check": 0.7, "alarm_console_check": 0.5,
                },
            },
            {
                "id": "flow_profile_distortion",
                "display_fr": "Distorsion profil écoulement (coudes proches, obstruction)",
                "lambda_fit": 25, "lambda_source": "Field experience",
                "dangerous_for_function": ["FAHH", "FALL"],
                "detected_online": False, "dc_online": 0.0,
                "coverage": {
                    "zero_calibration_check": 0.5, "setpoint_injection": 0.3,
                },
            },
        ],
    }

    # =========================================================================
    # PRESSION — TRANSMETTEUR PRESSION ABSOLUE (4-20mA)
    # =========================================================================
    components["pressure_transmitter_absolute_4_20ma"] = {
        "display_fr": "Transmetteur de pression absolue (ABS) — 4-20 mA",
        "display_en": "Absolute pressure transmitter — 4-20 mA",
        "category": "sensor",
        "technology": "4-20mA",
        "tag_codes": ["PT", "PI", "PA"],
        "total_ins107_function": "PRESSURE ABS / PRESSION ABS",
        "sif_roles": ["initiator"],
        "signal_type": "analog_4_20ma",
        "fail_safe": fail_safe_analog(
            notes="Pression absolue : référence vide. Erreur zéro plus critique que relatif."
        ),
        "lambda_total_fit": 310,
        "lambda_source": "OREDA2015 Table 6.15 — absolute pressure transmitter",
        "dc_auto": 0.50,
        "failure_modes": [
            *analog_base_modes(32, 52, 42, 38, 38, 42, "OREDA2015 Table 6.15",
                               ["PAHH", "PAH"], ["PALL", "PAL"]),
            {
                "id": "reference_vacuum_degradation",
                "display_fr": "Dégradation vide de référence (fuite capsule)",
                "lambda_fit": 15, "lambda_source": "exida — absolute pressure specific",
                "dangerous_for_function": ["PAHH"],
                "detected_online": False, "dc_online": 0.0,
                "comment": "Pénétration atmosphère → lecture systématiquement haute.",
                "coverage": {
                    "zero_calibration_check": 0.8, "setpoint_injection": 0.5,
                },
            },
            {
                "id": "impulse_line_blockage",
                "display_fr": "Colmatage ligne d'impulsion",
                "lambda_fit": 20, "lambda_source": "PDS2013",
                "dangerous_for_function": ["PAHH", "PALL"],
                "detected_online": False, "dc_online": 0.0,
                "coverage": {
                    "impulse_line_check": 0.9, "setpoint_injection": 0.3,
                },
            },
        ],
    }

    # =========================================================================
    # GAZ — INFRAROUGE (IR) — HC / CO2 / CH4
    # =========================================================================
    components["gas_detector_infrared"] = {
        "display_fr": "Détecteur de gaz infrarouge (IR) — gaz combustibles HC / CO2",
        "display_en": "Infrared gas detector — HC / CO2",
        "category": "sensor",
        "technology": "Infrared absorption (NDIR)",
        "tag_codes": ["GD", "GA", "GT"],
        "total_ins107_function": "GAS DETECTOR HC / DETECTEUR GAZ HC / GAS DETECTOR CO",
        "sif_roles": ["initiator"],
        "signal_type": "analog_4_20ma",
        "fail_safe": fail_safe_analog(
            notes="Technologie de référence SIL pour gaz combustibles. Moins sujet empoisonnement que catalytique."
        ),
        "lambda_total_fit": 800,
        "lambda_source": "OREDA2015 Table 6.25 + SINTEF A27482",
        "dc_auto": 0.65,
        "failure_modes": [
            *analog_base_modes(80, 100, 90, 70, 70, 80, "OREDA2015 Table 6.25",
                               ["GAHH"], ["GALL"]),
            {
                "id": "optical_path_contamination",
                "display_fr": "Contamination chemin optique (poussière, condensation, pellicule)",
                "lambda_fit": 150, "lambda_source": "OREDA2015 — dominant IR mode",
                "dangerous_for_function": ["GAHH"],
                "detected_online": True, "dc_online": 0.7,
                "comment": "Optique sale → absorption apparente → faux positif OU atténuation → faux négatif. Autodiag référence optique.",
                "coverage": {
                    "visual_inspection": 0.7, "gas_detector_bump_test": 0.9,
                    "zero_calibration_check": 0.5,
                },
            },
            {
                "id": "source_lamp_degradation",
                "display_fr": "Vieillissement source IR / lampe",
                "lambda_fit": 80, "lambda_source": "OREDA2015",
                "dangerous_for_function": ["GAHH"],
                "detected_online": True, "dc_online": 0.8,
                "comment": "Intensité source diminue → span réduit → sous-estimation concentration.",
                "coverage": {
                    "gas_detector_bump_test": 0.9, "zero_calibration_check": 0.5,
                    "visual_inspection": 0.2,
                },
            },
            {
                "id": "optical_window_failure",
                "display_fr": "Défaillance fenêtre optique (fissure, dépôt permanent)",
                "lambda_fit": 50, "lambda_source": "Field experience",
                "dangerous_for_function": ["GAHH"],
                "detected_online": True, "dc_online": 0.6,
                "coverage": {
                    "visual_inspection": 0.7, "gas_detector_bump_test": 0.8,
                },
            },
            {
                "id": "frozen_zero",
                "display_fr": "Sortie figée à zéro (faux négatif total)",
                "lambda_fit": 100, "lambda_source": "OREDA2015",
                "dangerous_for_function": ["GAHH"],
                "detected_online": True, "dc_online": 0.7,
                "coverage": {
                    "gas_detector_bump_test": 1.0, "loop_min_check": 0.5,
                    "alarm_console_check": 0.7,
                },
            },
        ],
    }

    # =========================================================================
    # GAZ — ÉLECTROCHIMIQUE H2S
    # =========================================================================
    components["gas_detector_electrochemical_h2s"] = {
        "display_fr": "Détecteur de gaz électrochimique — H2S (Sulfure d'hydrogène)",
        "display_en": "Electrochemical gas detector — H2S",
        "category": "sensor",
        "technology": "Electrochemical cell",
        "tag_codes": ["GD", "GA", "GT"],
        "total_ins107_function": "GAS DETECTOR H2S / DETECTEUR GAZ H2S",
        "sif_roles": ["initiator"],
        "signal_type": "analog_4_20ma",
        "fail_safe": fail_safe_analog(
            notes="Cellule électrochimique à durée de vie limitée (2-3 ans). Très sensible températures extrêmes."
        ),
        "lambda_total_fit": 2000,
        "lambda_source": "OREDA2015 Table 6.25 — H2S specific + SINTEF A27482",
        "dc_auto": 0.55,
        "beta_typical": 0.05,
        "failure_modes": [
            *analog_base_modes(150, 200, 180, 150, 150, 200, "OREDA2015",
                               ["H2S_AHH"], ["H2S_ALL"]),
            {
                "id": "cell_exhaustion_aging",
                "display_fr": "Épuisement cellule / vieillissement (fin de vie réactif)",
                "lambda_fit": 400, "lambda_source": "OREDA2015 — dominant EC mode",
                "dangerous_for_function": ["H2S_AHH"],
                "detected_online": True, "dc_online": 0.6,
                "comment": "Réactif consommé → sensibilité chute → non-détection. Durée vie ~2-3 ans. REMPLACEMENT OBLIGATOIRE.",
                "coverage": {
                    "gas_detector_bump_test": 1.0, "zero_calibration_check": 0.7,
                    "visual_inspection": 0.2,
                },
            },
            {
                "id": "cross_sensitivity_so2",
                "display_fr": "Interférence SO2 / autres gaz acides (faux positif)",
                "lambda_fit": 100, "lambda_source": "Field experience — H2S specific",
                "dangerous_for_function": ["H2S_AHH"],
                "detected_online": False, "dc_online": 0.0,
                "comment": "Cellule H2S sensible au SO2, NO2, Cl2. Faux positif en milieu corrosif.",
                "coverage": {
                    "zero_calibration_check": 0.4, "gas_detector_bump_test": 0.3,
                },
            },
            {
                "id": "temperature_extremes_effect",
                "display_fr": "Effet températures extrêmes sur cellule",
                "lambda_fit": 80, "lambda_source": "SINTEF A27482",
                "dangerous_for_function": ["H2S_AHH"],
                "detected_online": False, "dc_online": 0.0,
                "comment": "Sensibilité ±25% par tranche de 10°C hors plage nominale.",
                "coverage": {
                    "gas_detector_bump_test": 0.8, "zero_calibration_check": 0.5,
                },
            },
        ],
    }

    # =========================================================================
    # GAZ — ÉLECTROCHIMIQUE CO
    # =========================================================================
    components["gas_detector_electrochemical_co"] = {
        "display_fr": "Détecteur de gaz électrochimique — CO (Monoxyde de carbone)",
        "display_en": "Electrochemical gas detector — CO",
        "category": "sensor",
        "technology": "Electrochemical cell",
        "tag_codes": ["GD", "GA"],
        "total_ins107_function": "GAS DETECTOR CO / DETECTEUR GAZ CO",
        "sif_roles": ["initiator"],
        "signal_type": "analog_4_20ma",
        "fail_safe": fail_safe_analog(
            notes="CO = gaz inodore, invisible. Détection critique espaces confinés."
        ),
        "lambda_total_fit": 1800,
        "lambda_source": "OREDA2015 Table 6.25",
        "dc_auto": 0.55,
        "failure_modes": [
            *analog_base_modes(140, 180, 160, 140, 140, 180, "OREDA2015",
                               ["CO_AHH"], ["CO_ALL"]),
            {
                "id": "cell_exhaustion_aging",
                "display_fr": "Épuisement cellule / vieillissement",
                "lambda_fit": 360, "lambda_source": "OREDA2015",
                "dangerous_for_function": ["CO_AHH"],
                "detected_online": True, "dc_online": 0.6,
                "coverage": {
                    "gas_detector_bump_test": 1.0, "zero_calibration_check": 0.7,
                },
            },
            {
                "id": "cross_sensitivity_h2",
                "display_fr": "Interférence H2 (faux positif en milieu hydrogène)",
                "lambda_fit": 80, "lambda_source": "Field experience",
                "dangerous_for_function": ["CO_AHH"],
                "detected_online": False, "dc_online": 0.0,
                "coverage": {
                    "zero_calibration_check": 0.3, "gas_detector_bump_test": 0.3,
                },
            },
        ],
    }

    # =========================================================================
    # GAZ — ÉLECTROCHIMIQUE O2 (déficience en oxygène)
    # =========================================================================
    components["gas_detector_electrochemical_o2"] = {
        "display_fr": "Détecteur d'oxygène électrochimique (déficience O2) — 4-20 mA",
        "display_en": "Electrochemical oxygen detector (O2 deficiency) — 4-20 mA",
        "category": "sensor",
        "technology": "Electrochemical cell (galvanic)",
        "tag_codes": ["GD", "GA"],
        "total_ins107_function": "GAS DETECTOR O2 / DETECTEUR GAZ O2",
        "sif_roles": ["initiator"],
        "signal_type": "analog_4_20ma",
        "fail_safe": fail_safe_analog(
            notes="O2 déficience : trippage à < 19.5% vol. Cellule galvanique, durée vie ~2 ans."
        ),
        "lambda_total_fit": 1600,
        "lambda_source": "OREDA2015 Table 6.25",
        "dc_auto": 0.55,
        "failure_modes": [
            *analog_base_modes(130, 160, 140, 130, 130, 160, "OREDA2015",
                               ["O2_AHH_enrichment"], ["O2_ALL_deficiency"]),
            {
                "id": "cell_exhaustion",
                "display_fr": "Épuisement cellule galvanique",
                "lambda_fit": 350, "lambda_source": "OREDA2015",
                "dangerous_for_function": ["O2_ALL_deficiency"],
                "detected_online": True, "dc_online": 0.6,
                "comment": "Cellule épuisée → signal haut (air frais factice) → non-détection déficience.",
                "coverage": {
                    "gas_detector_bump_test": 1.0, "zero_calibration_check": 0.6,
                },
            },
        ],
    }

    # =========================================================================
    # FEU — DÉTECTEUR UV/IR FLAMME
    # =========================================================================
    components["fire_detector_uv_ir_flame"] = {
        "display_fr": "Détecteur de flamme UV/IR (ou IR/IR)",
        "display_en": "UV/IR (or IR/IR) flame detector",
        "category": "sensor",
        "technology": "UV/IR or IR/IR optical",
        "tag_codes": ["FD", "FA"],
        "total_ins107_function": "FLAME DETECTOR / DETECTEUR FLAMME / DET. FLAMME PILOT",
        "sif_roles": ["initiator"],
        "signal_type": "digital_tor",
        "fail_safe": fail_safe_tor("NF (recommandé SIL)", "Ouverture = alarme sur perte alimentation"),
        "lambda_total_fit": 600,
        "lambda_source": "SINTEF A27482 + OREDA2015 Table 6.25",
        "dc_auto": 0.60,
        "failure_modes": [
            *tor_base_modes(80, 80, 100, "SINTEF A27482",
                            ["NO_FLAME"], ["FALSE_FLAME"]),
            {
                "id": "optical_lens_contamination",
                "display_fr": "Contamination optique (poussière, graisses, condensation)",
                "lambda_fit": 150, "lambda_source": "OREDA2015",
                "dangerous_for_function": ["NO_FLAME"],
                "detected_online": True, "dc_online": 0.7,
                "comment": "Atténuation signal → faux négatif flamme. Autodiag LED test interne.",
                "coverage": {
                    "fire_detector_test": 0.9, "visual_inspection": 0.6,
                    "zero_calibration_check": 0.3,
                },
            },
            {
                "id": "solar_blind_failure_uv",
                "display_fr": "Défaillance filtre solar-blind (faux positifs soleil)",
                "lambda_fit": 50, "lambda_source": "Field experience",
                "dangerous_for_function": ["FALSE_FLAME"],
                "detected_online": False, "dc_online": 0.0,
                "coverage": {
                    "fire_detector_test": 0.5, "visual_inspection": 0.3,
                },
            },
            {
                "id": "steam_water_spray_nuisance",
                "display_fr": "Nuisance vapeur / spray eau (faux déclenchement)",
                "lambda_fit": 60, "lambda_source": "Field experience",
                "dangerous_for_function": ["FALSE_FLAME"],
                "detected_online": False, "dc_online": 0.0,
                "coverage": {
                    "visual_inspection": 0.2,
                },
            },
            {
                "id": "field_of_view_obstruction",
                "display_fr": "Obstruction du champ de vision (structure, équipement ajouté)",
                "lambda_fit": 60, "lambda_source": "Field experience",
                "dangerous_for_function": ["NO_FLAME"],
                "detected_online": False, "dc_online": 0.0,
                "coverage": {
                    "visual_inspection": 0.8, "fire_detector_test": 0.4,
                },
            },
        ],
    }

    # =========================================================================
    # FEU — DÉTECTEUR FUMÉE (IONISATION ou OPTIQUE)
    # =========================================================================
    components["fire_detector_smoke"] = {
        "display_fr": "Détecteur de fumée (ionisation ou optique / photoélectrique)",
        "display_en": "Smoke detector (ionisation or optical / photoelectric)",
        "category": "sensor",
        "technology": "Ionization or Optical scatter",
        "tag_codes": ["FD", "SD", "FA"],
        "total_ins107_function": "SMOKE DETECT / DETECTION FUMEE",
        "sif_roles": ["initiator"],
        "signal_type": "digital_tor",
        "fail_safe": fail_safe_tor("NF", "Ouverture = alarme sur perte alimentation"),
        "lambda_total_fit": 500,
        "lambda_source": "OREDA2015 Table 6.25 + SINTEF",
        "dc_auto": 0.40,
        "failure_modes": [
            *tor_base_modes(80, 80, 120, "OREDA2015",
                            ["NO_SMOKE"], ["FALSE_SMOKE"]),
            {
                "id": "dust_contamination_chamber",
                "display_fr": "Encrassement chambre de détection (poussière, insectes)",
                "lambda_fit": 120, "lambda_source": "OREDA2015 — dominant smoke mode",
                "dangerous_for_function": ["FALSE_SMOKE"],
                "detected_online": False, "dc_online": 0.0,
                "comment": "Poussière → faux déclenchement (optique) ou insensibilisation (ionisation).",
                "coverage": {
                    "visual_inspection": 0.6, "fire_detector_test": 0.7,
                },
            },
            {
                "id": "sensing_element_aging",
                "display_fr": "Vieillissement élément sensible",
                "lambda_fit": 100, "lambda_source": "Field experience",
                "dangerous_for_function": ["NO_SMOKE"],
                "detected_online": False, "dc_online": 0.0,
                "coverage": {
                    "fire_detector_test": 0.9, "zero_calibration_check": 0.3,
                },
            },
        ],
    }

    # =========================================================================
    # FEU — DÉTECTEUR THERMIQUE / THERMOSTAT D'ALARME
    # =========================================================================
    components["fire_detector_heat"] = {
        "display_fr": "Détecteur thermique / thermostat de feu (déclenchement T° fixe ou vélocimétrique)",
        "display_en": "Heat detector / fire thermostat (fixed temp or rate-of-rise)",
        "category": "sensor",
        "technology": "Thermal / bimetallic or thermistor",
        "tag_codes": ["FD", "TS", "FA"],
        "total_ins107_function": "THERMIC DETECTOR / DETECT THERMIQUE",
        "sif_roles": ["initiator"],
        "signal_type": "digital_tor",
        "fail_safe": fail_safe_tor("NF", "Ouverture = alarme sur perte alimentation"),
        "lambda_total_fit": 400,
        "lambda_source": "SINTEF A27482",
        "dc_auto": 0.20,
        "failure_modes": [
            *tor_base_modes(70, 70, 150, "SINTEF A27482",
                            ["NO_FIRE"], ["FALSE_FIRE"]),
            {
                "id": "bimetallic_fatigue",
                "display_fr": "Fatigue lame bimétallique (dérive seuil)",
                "lambda_fit": 110, "lambda_source": "SINTEF A27482",
                "dangerous_for_function": ["NO_FIRE"],
                "detected_online": False, "dc_online": 0.0,
                "coverage": {
                    "fire_detector_test": 0.8, "setpoint_tor_check": 0.7,
                    "visual_inspection": 0.1,
                },
            },
        ],
    }

    # =========================================================================
    # VANNE — FAIL OPEN (SRO — Spring Return to Open)
    # =========================================================================
    components["shutdown_valve_pneumatic_sro"] = {
        "display_fr": "Vanne d'isolement pneumatique — rappel ressort à l'ouverture (SRO / fail-open)",
        "display_en": "Pneumatic shutdown valve — spring return to open (SRO / fail-open)",
        "category": "final_element",
        "technology": "pneumatic_spring_return",
        "tag_codes": ["XV", "BV", "EV"],
        "total_ins107_function": "ON OFF CONTROL (A OUVERTURE) / SOLENOID SPRING (A OUVERTURE)",
        "sif_roles": ["final_element"],
        "signal_type": "digital_do",
        "fail_safe_position": "OPEN (spring opens on de-energize). Used for cooling water, purge, quench.",
        "lambda_total_fit": 4200,
        "lambda_source": "OREDA2015 Table 6.30 — same data as SRC, different failure direction",
        "dc_auto": 0.50,
        "beta_typical": 0.05,
        "failure_modes": [
            {
                "id": "fails_to_open_solenoid",
                "display_fr": "Solénoïde collé sous tension (vanne ne s'ouvre pas)",
                "lambda_fit": 600, "lambda_source": "OREDA2015",
                "dangerous_for_function": ["ALL_SRO"],
                "detected_online": False, "dc_online": 0.0,
                "coverage": {
                    "actuation_solenoid_test": 1.0, "full_stroke_test": 1.0,
                    "partial_stroke_test": 0.9, "response_time_measurement": 0.8,
                },
            },
            {
                "id": "fails_to_open_stem_friction",
                "display_fr": "Friction tige — vanne ne s'ouvre pas",
                "lambda_fit": 800, "lambda_source": "OREDA2015",
                "dangerous_for_function": ["ALL_SRO"],
                "detected_online": False, "dc_online": 0.5,
                "coverage": {
                    "full_stroke_test": 1.0, "position_feedback_check": 0.7,
                    "response_time_measurement": 0.6, "partial_stroke_test": 0.5,
                },
            },
            {
                "id": "spring_failure",
                "display_fr": "Défaillance ressort",
                "lambda_fit": 200, "lambda_source": "OREDA2015",
                "dangerous_for_function": ["ALL_SRO"],
                "detected_online": False, "dc_online": 0.0,
                "coverage": {
                    "full_stroke_test": 1.0, "actuation_solenoid_test": 0.8,
                    "response_time_measurement": 0.7,
                },
            },
            {
                "id": "instrument_air_failure",
                "display_fr": "Perte air instrument (vanne reste en position courante)",
                "lambda_fit": 300, "lambda_source": "PDS2013",
                "dangerous_for_function": ["ALL_SRO"],
                "detected_online": True, "dc_online": 0.7,
                "coverage": {
                    "instrument_air_check": 1.0, "actuation_solenoid_test": 0.8,
                    "full_stroke_test": 0.7,
                },
            },
            {
                "id": "seat_leakage_major",
                "display_fr": "Fuite siège majeure",
                "lambda_fit": 200, "lambda_source": "OREDA2015",
                "dangerous_for_function": ["ALL_WITH_TIGHT_SHUTOFF"],
                "detected_online": False, "dc_online": 0.0,
                "coverage": {
                    "seat_leak_test": 0.95, "full_stroke_test": 0.2,
                },
            },
            {
                "id": "position_feedback_failure",
                "display_fr": "Défaillance retour de position",
                "lambda_fit": 200, "lambda_source": "OREDA2015",
                "dangerous_for_function": ["ALL_WITH_FEEDBACK_REQUIRED"],
                "detected_online": True, "dc_online": 0.8,
                "coverage": {
                    "position_feedback_check": 1.0, "full_stroke_test": 0.9,
                },
            },
        ],
    }

    # =========================================================================
    # VANNE — SOLÉNOÏDE BISTABLE
    # =========================================================================
    components["solenoid_valve_bistable"] = {
        "display_fr": "Électrovanne bistable (solénoïde double bobine — mémorisation position)",
        "display_en": "Bistable solenoid valve (dual coil — position memory)",
        "category": "final_element",
        "technology": "electrical_solenoid_bistable",
        "tag_codes": ["EV", "XV"],
        "total_ins107_function": "SOLENOID BISTABLE / EV BISTABLE",
        "sif_roles": ["final_element"],
        "lambda_total_fit": 900,
        "lambda_source": "OREDA2015 + PDS2013 — bistable solenoid",
        "dc_auto": 0.40,
        "comment": "Pas de position failsafe sur perte alimentation. DANGEREUX pour SIS si non justifié.",
        "failure_modes": [
            {
                "id": "coil_open_circuit_close",
                "display_fr": "Circuit ouvert bobine fermeture",
                "lambda_fit": 200, "lambda_source": "OREDA2015",
                "dangerous_for_function": ["ALL"],
                "detected_online": True, "dc_online": 0.8,
                "coverage": {
                    "actuation_solenoid_test": 1.0, "contact_continuity_check": 0.8,
                },
            },
            {
                "id": "coil_open_circuit_open",
                "display_fr": "Circuit ouvert bobine ouverture",
                "lambda_fit": 200, "lambda_source": "OREDA2015",
                "dangerous_for_function": ["ALL"],
                "detected_online": True, "dc_online": 0.8,
                "coverage": {
                    "actuation_solenoid_test": 1.0, "full_stroke_test": 0.9,
                },
            },
            {
                "id": "plunger_jam_bistable",
                "display_fr": "Blocage plongeur (position intermédiaire)",
                "lambda_fit": 300, "lambda_source": "OREDA2015 — dominant bistable mode",
                "dangerous_for_function": ["ALL"],
                "detected_online": False, "dc_online": 0.0,
                "comment": "Pas de failsafe → position indéterminée. Critique SIS.",
                "coverage": {
                    "full_stroke_test": 1.0, "position_feedback_check": 0.9,
                    "actuation_solenoid_test": 0.7,
                },
            },
        ],
    }

    # =========================================================================
    # VANNE DE RÉGULATION — FAIL CLOSE (contrôle 4-20mA)
    # =========================================================================
    components["control_valve_fail_close"] = {
        "display_fr": "Vanne de régulation pneumatique — fail fermeture (FC / ATC)",
        "display_en": "Pneumatic control valve — fail close (FC / Air-to-Close)",
        "category": "final_element",
        "technology": "pneumatic_positioner",
        "tag_codes": ["FV", "LV", "PV", "TV", "XV"],
        "total_ins107_function": "CONTROL VALVE / VANNE REGUL",
        "sif_roles": ["final_element"],
        "signal_type": "analog_4_20ma",
        "fail_safe_position": "CLOSED on loss of signal (4mA) or air failure",
        "lambda_total_fit": 5000,
        "lambda_source": "OREDA2015 Table 6.30 — control valve",
        "dc_auto": 0.45,
        "beta_typical": 0.04,
        "failure_modes": [
            {
                "id": "fails_to_close_on_trip",
                "display_fr": "Vanne ne se ferme pas sur demande de trip (friction, actuateur)",
                "lambda_fit": 900, "lambda_source": "OREDA2015",
                "dangerous_for_function": ["ALL_FC"],
                "detected_online": False, "dc_online": 0.5,
                "coverage": {
                    "full_stroke_test": 1.0, "position_feedback_check": 0.8,
                    "response_time_measurement": 0.7,
                },
            },
            {
                "id": "positioner_failure",
                "display_fr": "Défaillance positionneur (boucle ouverte, erreur position)",
                "lambda_fit": 500, "lambda_source": "OREDA2015",
                "dangerous_for_function": ["ALL_FC"],
                "detected_online": True, "dc_online": 0.6,
                "coverage": {
                    "positioner_check": 1.0, "full_stroke_test": 0.8,
                    "position_feedback_check": 0.7,
                },
            },
            {
                "id": "seat_leakage_major",
                "display_fr": "Fuite siège majeure (étanchéité insuffisante en position fermée)",
                "lambda_fit": 600, "lambda_source": "OREDA2015",
                "dangerous_for_function": ["ALL_FC"],
                "detected_online": False, "dc_online": 0.0,
                "coverage": {
                    "seat_leak_test": 0.95, "full_stroke_test": 0.15,
                },
            },
            {
                "id": "stem_packing_leakage",
                "display_fr": "Fuite presse-étoupe tige",
                "lambda_fit": 400, "lambda_source": "OREDA2015",
                "dangerous_for_function": ["FUGITIVE_EMISSION"],
                "detected_online": False, "dc_online": 0.0,
                "coverage": {
                    "visual_inspection": 0.8, "seat_leak_test": 0.3,
                },
            },
            {
                "id": "instrument_air_failure",
                "display_fr": "Perte alimentation air instrument",
                "lambda_fit": 300, "lambda_source": "PDS2013",
                "dangerous_for_function": ["ALL"],
                "detected_online": True, "dc_online": 0.7,
                "coverage": {
                    "instrument_air_check": 1.0, "full_stroke_test": 0.6,
                },
            },
            {
                "id": "partial_stroke_sticking",
                "display_fr": "Collage / course partielle (vanne s'ouvre ou se ferme partiellement)",
                "lambda_fit": 700, "lambda_source": "OREDA2015",
                "dangerous_for_function": ["ALL_FC"],
                "detected_online": False, "dc_online": 0.3,
                "comment": "Vanne 'stuck' à position intermédiaire. Non détectable sans test pleine course.",
                "coverage": {
                    "full_stroke_test": 0.9, "partial_stroke_test": 0.4,
                    "position_feedback_check": 0.5, "response_time_measurement": 0.6,
                },
            },
        ],
    }

    # =========================================================================
    # DISQUE DE RUPTURE
    # =========================================================================
    components["rupture_disk"] = {
        "display_fr": "Disque de rupture (élément de protection pression ultime)",
        "display_en": "Rupture disk (ultimate pressure protection element)",
        "category": "final_element",
        "technology": "Mechanical passive",
        "tag_codes": ["RD", "PSE"],
        "total_ins107_function": "RUPTURE DISK / DISQUE RUPTURE",
        "sif_roles": ["final_element"],
        "signal_type": "passive",
        "fail_safe_position": "Rupture à la pression de consigne — passif, irréversible",
        "lambda_total_fit": 200,
        "lambda_source": "PDS2013 Table A.10 + ASME PTC 25",
        "dc_auto": 0.0,
        "comment": "Composant passif. Basse λ mais non réinitialisable. Couverture uniquement par inspection.",
        "failure_modes": [
            {
                "id": "premature_rupture",
                "display_fr": "Rupture prématurée (en-dessous de la pression de consigne)",
                "lambda_fit": 50, "lambda_source": "PDS2013 Table A.10",
                "dangerous_for_function": ["FALSE_TRIP"],
                "detected_online": True, "dc_online": 0.9,
                "comment": "Détecté immédiatement (pression chute, alarme flow process).",
                "coverage": {
                    "visual_inspection": 1.0, "alarm_console_check": 0.9,
                },
            },
            {
                "id": "fails_to_rupture",
                "display_fr": "Non rupture à la pression nominale (disque dégradé)",
                "lambda_fit": 100, "lambda_source": "PDS2013 Table A.10",
                "dangerous_for_function": ["ALL"],
                "detected_online": False, "dc_online": 0.0,
                "comment": "Corrosion, fatigue cyclique, mauvaise installation → seuil de rupture dérivé.",
                "coverage": {
                    "visual_inspection": 0.6,
                },
            },
            {
                "id": "corrosion_perforation_pinhole",
                "display_fr": "Corrosion / perforation avant rupture (fuite lente)",
                "lambda_fit": 30, "lambda_source": "PDS2013",
                "dangerous_for_function": ["LEAK"],
                "detected_online": False, "dc_online": 0.0,
                "coverage": {
                    "visual_inspection": 0.7,
                },
            },
            {
                "id": "wrong_installation",
                "display_fr": "Mauvais sens d'installation",
                "lambda_fit": 20, "lambda_source": "Human factors / Field experience",
                "dangerous_for_function": ["ALL"],
                "detected_online": False, "dc_online": 0.0,
                "coverage": {
                    "visual_inspection": 1.0, "return_to_service": 1.0,
                },
            },
        ],
    }

    # =========================================================================
    # SOUPAPE DE SÉCURITÉ (RELIEF VALVE)
    # =========================================================================
    components["relief_valve_mechanical"] = {
        "display_fr": "Soupape de sécurité / soupape de surpression (mécanique)",
        "display_en": "Safety relief valve / pressure relief valve (mechanical)",
        "category": "final_element",
        "technology": "Spring-loaded mechanical",
        "tag_codes": ["PSV", "PRV", "SV"],
        "total_ins107_function": "RELIEF VALVE / SOUPAPE / SOUPAPE EXP THERM",
        "sif_roles": ["final_element"],
        "signal_type": "passive",
        "fail_safe_position": "Ouverture sur pression ≥ Pconsigne. Fermeture en dessous.",
        "lambda_total_fit": 600,
        "lambda_source": "PDS2013 Table A.10 + API 521",
        "dc_auto": 0.0,
        "comment": "Passif. Aucun DC automatique. Protection ultime. Couverture = test lift.",
        "failure_modes": [
            {
                "id": "fails_to_open",
                "display_fr": "Non ouverture à la pression de consigne (siège collé, corrosion)",
                "lambda_fit": 200, "lambda_source": "PDS2013 Table A.10 — dominant",
                "dangerous_for_function": ["ALL"],
                "detected_online": False, "dc_online": 0.0,
                "comment": "Mode le plus dangereux. Siège collé par corrosion ou polymère.",
                "coverage": {
                    "full_stroke_test": 1.0,
                },
            },
            {
                "id": "set_pressure_drift_high",
                "display_fr": "Dérive pression de consigne vers le haut",
                "lambda_fit": 100, "lambda_source": "PDS2013",
                "dangerous_for_function": ["ALL"],
                "detected_online": False, "dc_online": 0.0,
                "coverage": {
                    "setpoint_tor_check": 0.9, "full_stroke_test": 0.8,
                },
            },
            {
                "id": "leakage_below_set_pressure",
                "display_fr": "Fuite siège en dessous de la pression de consigne",
                "lambda_fit": 200, "lambda_source": "OREDA2015",
                "dangerous_for_function": ["PROCESS_LOSS"],
                "detected_online": False, "dc_online": 0.0,
                "comment": "Fuite chronique. Perte produit + risque environnemental.",
                "coverage": {
                    "seat_leak_test": 0.9, "visual_inspection": 0.4,
                },
            },
            {
                "id": "fails_to_reclose",
                "display_fr": "Non fermeture après ouverture (siège endommagé)",
                "lambda_fit": 100, "lambda_source": "PDS2013",
                "dangerous_for_function": ["PROCESS_LOSS"],
                "detected_online": True, "dc_online": 0.7,
                "comment": "Détecté par perte pression process.",
                "coverage": {
                    "full_stroke_test": 0.8, "alarm_console_check": 0.7,
                },
            },
        ],
    }

    # =========================================================================
    # BOUTON ESD / ARRÊT D'URGENCE (ESD PB)
    # =========================================================================
    components["esd_push_button"] = {
        "display_fr": "Bouton d'arrêt d'urgence (ESD PB / TPL F)",
        "display_en": "Emergency shutdown push button (ESD PB / TPL F)",
        "category": "sensor",
        "technology": "Electromechanical contact",
        "tag_codes": ["PB", "HS", "ESD"],
        "total_ins107_function": "ESD PB / TPL F / BP ACCROCHAGE",
        "sif_roles": ["initiator"],
        "signal_type": "digital_tor",
        "fail_safe": fail_safe_tor("NF (Normalement Fermé)", "Contact NF = Ouverture sur actionnement = trip"),
        "lambda_total_fit": 300,
        "lambda_source": "OREDA2015 Table 6.10 + MIL-HDBK-217F",
        "dc_auto": 0.30,
        "failure_modes": [
            {
                "id": "contact_stuck_closed",
                "display_fr": "Contact soudé fermé (actionnement sans effet)",
                "lambda_fit": 60, "lambda_source": "OREDA2015",
                "dangerous_for_function": ["ESD_MANUAL"],
                "detected_online": False, "dc_online": 0.0,
                "coverage": {
                    "esd_push_button_test": 1.0, "contact_continuity_check": 0.5,
                    "trip_output_check": 0.9,
                },
            },
            {
                "id": "contact_corrosion_high_resistance",
                "display_fr": "Corrosion / résistance contact élevée",
                "lambda_fit": 80, "lambda_source": "OREDA2015",
                "dangerous_for_function": ["ESD_MANUAL"],
                "detected_online": False, "dc_online": 0.0,
                "coverage": {
                    "esd_push_button_test": 1.0, "contact_continuity_check": 0.7,
                },
            },
            {
                "id": "mechanical_jam_button",
                "display_fr": "Blocage mécanique bouton (encastrement, peinture, obstacle)",
                "lambda_fit": 60, "lambda_source": "Field experience",
                "dangerous_for_function": ["ESD_MANUAL"],
                "detected_online": False, "dc_online": 0.0,
                "coverage": {
                    "esd_push_button_test": 1.0, "visual_inspection": 0.7,
                },
            },
            {
                "id": "mushroom_not_released_after_test",
                "display_fr": "Bouton champignon non réarmé après test",
                "lambda_fit": 50, "lambda_source": "Human factors",
                "dangerous_for_function": ["SPURIOUS_TRIP"],
                "detected_online": True, "dc_online": 0.8,
                "comment": "Bouton non tourné pour réarmement → trip permanent → process indisponible.",
                "coverage": {
                    "return_to_service": 1.0, "alarm_console_check": 0.9,
                },
            },
            {
                "id": "wiring_failure",
                "display_fr": "Défaut câblage (coupure, court-circuit)",
                "lambda_fit": 50, "lambda_source": "OREDA2015",
                "dangerous_for_function": ["ESD_MANUAL"],
                "detected_online": True, "dc_online": 0.6,
                "coverage": {
                    "contact_continuity_check": 0.9, "esd_push_button_test": 0.8,
                },
            },
        ],
    }

    # =========================================================================
    # ALARME ÉCART (DISCREPANCY ALARM) — module logique
    # Ce n'est pas un composant physique mais une fonction de comparaison
    # =========================================================================
    components["logic_discrepancy_alarm"] = {
        "display_fr": "Alarme de discordance / écart (comparaison SIS vs DCS ou vote logique)",
        "display_en": "Discrepancy alarm / deviation alarm (SIS vs DCS or vote logic comparison)",
        "category": "logic_function",
        "technology": "Software logic function",
        "tag_codes": ["DA", "XA"],
        "total_ins107_function": "N/A — fonction logique de comparaison",
        "sif_roles": ["diagnostic"],
        "signal_type": "digital_logic",
        "description": """
        Fonction qui compare deux mesures redondantes (ou SIS vs DCS) et génère une alarme
        si l'écart dépasse un seuil. Permet de détecter dérive insidieuse et frozen mid-range
        sans action sur le process.

        IMPLÉMENTATIONS TYPIQUES :
          - Comparaison SIS input vs DCS input (même mesurande, instruments différents)
          - Comparaison deux sorties vote 1oo2 : si les deux diffèrent > seuil → alarme
          - Comparaison SIS output vs état équipement final (position vanne, etc.)

        SEUIL TYPIQUE : ±5% de la gamme (pression, niveau) ou ±2°C (température)
        """,
        "lambda_total_fit": 10,
        "lambda_source": "IEC 61511 — software function, assumed high reliability",
        "dc_auto": 0.0,
        "failure_modes": [
            {
                "id": "alarm_not_configured",
                "display_fr": "Alarme écart non configurée (PTC=1 assumé à tort)",
                "lambda_fit": 5, "lambda_source": "IEC 61511-1 Clause 9.5 — systematic failure",
                "dangerous_for_function": ["ALL"],
                "detected_online": False, "dc_online": 0.0,
                "comment": "Non détectable sans audit. Cause principale de PTC surévalué.",
                "coverage": {
                    "logic_function_test": 1.0, "bypass_check": 0.5,
                },
            },
            {
                "id": "alarm_threshold_wrong",
                "display_fr": "Seuil d'alarme mal paramétré (trop large → non détection dérive)",
                "lambda_fit": 3, "lambda_source": "IEC 61511-1",
                "dangerous_for_function": ["ALL"],
                "detected_online": False, "dc_online": 0.0,
                "coverage": {
                    "logic_function_test": 0.8, "zero_calibration_check": 0.4,
                },
            },
        ],
    }


# ─────────────────────────────────────────────────────────────────────────────
# EXTENSION TAXONOMIE — nouveaux types de test
# ─────────────────────────────────────────────────────────────────────────────

TAXONOMY_EXTENSION = {
    "esd_push_button_test": {
        "display_fr": "Test bouton d'arrêt d'urgence (ESD PB)",
        "display_en": "Emergency shutdown push button test",
        "keywords_fr": ["bouton esd", "arrêt urgence", "esd pb", "tpl f",
                        "test bouton champignon", "appuyer urgence",
                        "arrêt d'urgence", "test esd pb", "bouton d arrêt"],
        "keywords_en": ["esd button", "emergency stop", "esd pb test",
                        "push button test", "emergency shutdown pb"],
        "applicable_to": ["esd_push_button"],
    },
    "gas_detector_zero_check": {
        "display_fr": "Vérification zéro détecteur gaz (air frais, gaz zéro)",
        "display_en": "Gas detector zero check (fresh air, zero gas)",
        "keywords_fr": ["vérifier zéro détecteur", "air frais détecteur",
                        "gaz zéro", "purger capteur gaz", "zéro gaz",
                        "vérifier 0% lie", "vérification zéro"],
        "keywords_en": ["zero gas", "fresh air check", "zero detector",
                        "purge detector", "0% LEL check"],
        "applicable_to": ["gas_detector"],
    },
    "impulse_line_flush_test": {
        "display_fr": "Purge / chasse ligne d'impulsion (décolmatage)",
        "display_en": "Impulse line flush / blowdown",
        "keywords_fr": ["purger ligne impulsion", "chasser ligne", "décolmater",
                        "purge manifold", "blowdown ligne", "vérifier circulation",
                        "flux passage ligne"],
        "keywords_en": ["impulse line flush", "blowdown", "purge line",
                        "flush line", "line blowdown"],
        "applicable_to": ["sensor_4_20ma", "dp_transmitter"],
    },
    "seat_leak_pneumatic_test": {
        "display_fr": "Test étanchéité siège vanne avec air/N2",
        "display_en": "Valve seat leak test with air/N2",
        "keywords_fr": ["test étanchéité vanne", "test fuite siège",
                        "pression air vanne fermée", "nitrogen leak test",
                        "test siège", "mesure fuite vanne"],
        "keywords_en": ["seat leak test", "valve tightness", "air test valve",
                        "nitrogen test", "seat tightness test"],
        "applicable_to": ["shutdown_valve", "control_valve", "relief_valve"],
    },
    "lift_test_relief": {
        "display_fr": "Test de soulèvement soupape (lift test)",
        "display_en": "Relief valve lift test",
        "keywords_fr": ["test soulèvement", "lift test", "test soupape",
                        "vérifier ouverture soupape", "test pression ouverture",
                        "pop test soupape"],
        "keywords_en": ["lift test", "pop test", "relief valve test",
                        "set pressure test"],
        "applicable_to": ["relief_valve"],
    },
    "calibration_span_check": {
        "display_fr": "Vérification étendue de calibration (span check / calibration points)",
        "display_en": "Span calibration check (multi-point)",
        "keywords_fr": ["vérifier étendue", "calibration multipoint",
                        "vérifier span", "calibration 25%", "calibration 50%",
                        "calibration 75%", "étalonnage multipoint", "test span"],
        "keywords_en": ["span check", "multi-point calibration", "calibrate span",
                        "25% calibration", "50% calibration", "75% calibration"],
        "applicable_to": ["sensor_4_20ma", "transmitter"],
    },
    "discrepancy_alarm_check": {
        "display_fr": "Vérification alarme de discordance / écart SIS-DCS",
        "display_en": "Discrepancy alarm check (SIS vs DCS deviation)",
        "keywords_fr": ["alarme écart", "alarme discordance", "vérifier écart",
                        "alarme déviation", "comparer valeurs sis dcs",
                        "alarme comparaison", "écart capteur"],
        "keywords_en": ["discrepancy alarm", "deviation alarm", "sis dcs compare",
                        "comparison alarm", "deviation check"],
        "applicable_to": ["logic_discrepancy_alarm", "logic_solver"],
    },
    "hart_diagnostic_check": {
        "display_fr": "Lecture diagnostic HART (statut, alertes, configuration)",
        "display_en": "Read HART diagnostics (status, alerts, configuration)",
        "keywords_fr": ["lecture hart", "diagnostic hart", "lire statut hart",
                        "vérifier statut hart", "communication hart",
                        "hart configurator", "configuration hart"],
        "keywords_en": ["hart diagnostics", "read hart", "hart status",
                        "hart communicator", "hart check"],
        "applicable_to": ["sensor_4_20ma", "transmitter"],
    },
    "density_compensation_check": {
        "display_fr": "Vérification compensation densité (displacer, bubbletube, DP niveau)",
        "display_en": "Density compensation check",
        "keywords_fr": ["compensation densité", "vérifier densité",
                        "densité fluide", "recalibrer densité"],
        "keywords_en": ["density compensation", "check density", "density calibration"],
        "applicable_to": ["level_transmitter_displacer", "level_transmitter_bubbletube"],
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# MAIN — Générer la KB complète
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Charger KB v1.0
    kb = build_kb()

    # Étendre la taxonomie
    kb["test_taxonomy"].update(TAXONOMY_EXTENSION)

    # Ajouter tous les nouveaux composants
    add_all_components(kb["components"])

    # Stats
    total_modes = sum(
        len(c.get("failure_modes", []))
        for c in kb["components"].values()
    )
    print(f"{'='*60}")
    print(f"  PTC Knowledge Base v2.0 — EXHAUSTIVE")
    print(f"{'='*60}")
    print(f"  Components   : {len(kb['components'])}")
    print(f"  Failure modes: {total_modes}")
    print(f"  Test types   : {len(kb['test_taxonomy'])}")

    # Validation
    valid_tests = set(kb["test_taxonomy"].keys())
    errors = []
    for comp_id, comp in kb["components"].items():
        for fm in comp.get("failure_modes", []):
            for test_id in fm.get("coverage", {}).keys():
                if test_id not in valid_tests:
                    errors.append(f"{comp_id}/{fm['id']}: unknown test '{test_id}'")

    if errors:
        print(f"\n⚠ VALIDATION ERRORS ({len(errors)}):")
        for e in errors: print(f"  {e}")
    else:
        print(f"\n  ✓ All {total_modes} failure mode coverage references are valid")

    # Coverage stats par composant
    print(f"\n  COMPONENTS OVERVIEW :")
    for comp_id, comp in kb["components"].items():
        n = len(comp.get("failure_modes", []))
        cat = comp.get("category", "?")
        tech = comp.get("technology", "?")
        has_fs = "✓FS" if "fail_safe" in comp else "   "
        print(f"  {has_fs}  {comp_id:<55} [{cat}] {n:>3} modes")

    # Export
    outpath = "/home/claude/ptc-knowledge-base/knowledge_base_v2.json"
    with open(outpath, "w", encoding="utf-8") as f:
        json.dump(kb, f, indent=2, ensure_ascii=False)

    size_kb = len(json.dumps(kb, ensure_ascii=False)) / 1024
    print(f"\n  ✓ Exported: {outpath}  ({size_kb:.0f} KB)")
    print(f"{'='*60}")
