"""
PRISM SIL Engine — Lambda Database
Sprint G — v0.7.0

Source : PDS Data Handbook, 2021 Edition
         SINTEF Digital, Trondheim, May 2021
         ISBN/DOI : see handbook preface

Toutes les valeurs de taux de défaillance sont stockées en [1/h].
Les tableaux PDS expriment les λ en [10⁻⁶/h] — conversion appliquée à l'entrée.

Usage typique :
    from lambda_db import get_lambda, make_subsystem_params
    entry = get_lambda("pressure_transmitter")
    params = make_subsystem_params(entry, T1=8760.0, MTTR=8.0, architecture="1oo2")

Structure d'une entrée (PDSEntry) :
    key             str     — identifiant unique snake_case
    description     str     — libellé complet
    category        str     — catégorie d'équipement
    lambda_crit     float|None  — taux total de défaillances critiques [1/h]
    lambda_S        float|None  — taux défaillances sûres [1/h]
    lambda_D        float|None  — taux défaillances dangereuses [1/h]
    lambda_DU       float   — taux DU (principal paramètre PRISM) [1/h]
    lambda_DU_70    float|None  — borne supérieure 70% de λ_DU [1/h]
    lambda_DU_90_lo float|None  — borne inférieure IC 90% de λ_DU [1/h]
    lambda_DU_90_hi float|None  — borne supérieure IC 90% de λ_DU [1/h]
    lambda_DD       float   — calculé : lambda_D - lambda_DU [1/h]
    DC              float   — couverture diagnostique (0-1)
    SFF             float|None  — fraction de défaillance sûre (0-1)
    beta            float|None  — facteur CCF (PDS Table 3.12)
    RHF             float|None  — fraction de défaillances aléatoires hardware (Table 3.14)
    section         str     — section de référence dans le handbook
    notes           str     — conditions particulières / footnotes
    source          str     — "PDS2021"

Changelog :
    v0.7.1 (2026-03-12) — Sprint G : pages 25-55 PDS 2021
                          Ajout champs RHF (Table 3.14) et IC 90% (Tables 3.15–3.18)
                          Corrections λ_DU : ir_point_gas 0.30→0.25, line_gas 0.40→0.44,
                          pa_loudspeakers 0.20→0.23 ; λ_DU_70 : circuit_breaker, water_mist,
                          process_control_valve_shutdown
                          Nouveaux sous-types : level_transmitter ×4 (principe de mesure),
                          DHSV ×4 (topside/subsea wells), pressure_transmitter_piezoresistive
    v0.7.0 (2026-03-12) — Sprint G : création initiale, pages 4-24 PDS 2021
                          Tables 3.1–3.12 intégrées (topside + subsea + downhole + forage)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Dict


# ─────────────────────────────────────────────────────────────────
# Dataclass
# ─────────────────────────────────────────────────────────────────

@dataclass
class PDSEntry:
    key: str
    description: str
    category: str
    lambda_DU: float                    # [1/h] — paramètre principal
    DC: float                           # (0-1)
    lambda_crit: Optional[float] = None # [1/h]
    lambda_S: Optional[float] = None    # [1/h]
    lambda_D: Optional[float] = None    # [1/h]
    lambda_DU_70: Optional[float] = None    # [1/h]
    lambda_DU_90_lo: Optional[float] = None # [1/h] — borne basse IC 90%
    lambda_DU_90_hi: Optional[float] = None # [1/h] — borne haute IC 90%
    SFF: Optional[float] = None             # (0-1)
    beta: Optional[float] = None            # CCF factor
    RHF: Optional[float] = None             # Random Hardware Failure Fraction (Table 3.14)
    section: str = ""
    notes: str = ""
    source: str = "PDS2021"

    @property
    def lambda_DD(self) -> float:
        """lambda_DD = lambda_D - lambda_DU  (ou DC * lambda_D si lambda_D connu)"""
        if self.lambda_D is not None:
            return max(0.0, self.lambda_D - self.lambda_DU)
        return self.DC * self.lambda_DU / max(1e-9, 1.0 - self.DC) if self.DC < 1.0 else 0.0


# ─────────────────────────────────────────────────────────────────
# Facteurs C_MooN (Table 2.2 PDS 2021 = Table D.5 IEC 61508-6)
# ─────────────────────────────────────────────────────────────────
# Clé : (M, N)  — β_MooN = β × C_MooN

C_MOON: Dict[tuple, float] = {
    (1, 2): 1.0,  (1, 3): 0.5,  (1, 4): 0.3,  (1, 5): 0.2,  (1, 6): 0.15,
    (2, 3): 2.0,  (2, 4): 1.1,  (2, 5): 0.8,  (2, 6): 0.6,
    (3, 4): 2.8,  (3, 5): 1.6,  (3, 6): 1.2,
    (4, 5): 3.6,  (4, 6): 1.9,
    (5, 6): 4.5,
}


def beta_moon(beta: float, M: int, N: int) -> float:
    """β_MooN = β × C_MooN  (PDS §2.4.1)"""
    if M == N:
        return beta  # 1oo1 : C = 1 par convention
    c = C_MOON.get((M, N))
    if c is None:
        raise ValueError(f"C_MooN non défini pour M={M}, N={N}")
    return beta * c


# ─────────────────────────────────────────────────────────────────
# Helper de conversion
# ─────────────────────────────────────────────────────────────────

def _e6(val) -> Optional[float]:
    """Convertit une valeur PDS [10⁻⁶/h] → [1/h]. None si None ou '-'."""
    if val is None:
        return None
    return val * 1e-6


# ─────────────────────────────────────────────────────────────────
# BASE DE DONNÉES
# ─────────────────────────────────────────────────────────────────

_RAW: List[dict] = [

    # ══════════════════════════════════════════════════════════════
    # TABLE 3.1 — TRANSMETTEURS ET SWITCHES TOPSIDE
    # ══════════════════════════════════════════════════════════════
    {
        "key": "position_switch",
        "description": "Position switch (proximity or limit)",
        "category": "topside_input",
        "lambda_crit": 1.9, "lambda_S": 0.7, "lambda_D": 1.2,
        "lambda_DU": 1.1, "lambda_DU_70": 1.3,
        "DC": 0.05, "SFF": 0.41, "beta": 0.10,
        "section": "4.2.1", "notes": "",
    },
    {
        "key": "aspirator_system_flow_switch",
        "description": "Aspirator system including flow switch (excl. detector)",
        "category": "topside_input",
        "lambda_crit": 4.6, "lambda_S": 1.9, "lambda_D": 2.6,
        "lambda_DU": 2.5, "lambda_DU_70": 3.0,
        "DC": 0.05, "SFF": 0.46, "beta": 0.10,
        "section": "4.2.2", "notes": "",
    },
    {
        "key": "pressure_transmitter",
        "description": "Pressure transmitter (topside)",
        "category": "topside_input",
        "lambda_crit": 1.95, "lambda_S": 0.58, "lambda_D": 1.36,
        "lambda_DU": 0.48, "lambda_DU_70": 0.52,
        "DC": 0.65, "SFF": 0.75, "beta": 0.10,
        "section": "4.2.3", "notes": "Détails par principe de mesure en §4.2.3 (D)",
    },
    {
        "key": "level_transmitter",
        "description": "Level transmitter (topside)",
        "category": "topside_input",
        "lambda_crit": 10.0, "lambda_S": 4.2, "lambda_D": 6.3,
        "lambda_DU": 1.9, "lambda_DU_70": 2.5,
        "DC": 0.70, "SFF": 0.82, "beta": 0.10,
        "section": "4.2.4",
        "notes": "λ_DU varie significativement avec la complexité de l'application — voir §4.2.4",
    },
    {
        "key": "temperature_transmitter",
        "description": "Temperature transmitter (topside)",
        "category": "topside_input",
        "lambda_crit": 0.7, "lambda_S": 0.3, "lambda_D": 0.4,
        "lambda_DU": 0.1, "lambda_DU_70": 0.2,
        "DC": 0.70, "SFF": 0.82, "beta": 0.10,
        "section": "4.2.5", "notes": "",
    },
    {
        "key": "flow_transmitter",
        "description": "Flow transmitter (topside)",
        "category": "topside_input",
        "lambda_crit": 6.6, "lambda_S": 2.7, "lambda_D": 4.0,
        "lambda_DU": 1.4, "lambda_DU_70": 1.8,
        "DC": 0.65, "SFF": 0.79, "beta": 0.10,
        "section": "4.2.6", "notes": "",
    },

    # ══════════════════════════════════════════════════════════════
    # TABLE 3.2 — DÉTECTEURS TOPSIDE
    # ══════════════════════════════════════════════════════════════
    {
        "key": "catalytic_point_gas_detector",
        "description": "Catalytic point gas detector",
        "category": "topside_detector",
        "lambda_crit": 5.2, "lambda_S": 1.6, "lambda_D": 3.6,
        "lambda_DU": 1.5, "lambda_DU_70": 1.6,
        "DC": 0.60, "SFF": 0.72, "beta": 0.10,
        "section": "4.2.7", "notes": "",
    },
    {
        "key": "ir_point_gas_detector",
        "description": "IR point gas detector",
        "category": "topside_detector",
        "lambda_crit": 3.2, "lambda_S": 1.5, "lambda_D": 1.7,
        "lambda_DU": 0.25, "lambda_DU_70": 0.27,
        "lambda_DU_90_lo": 0.21, "lambda_DU_90_hi": 0.30,
        "DC": 0.85, "SFF": 0.92, "beta": 0.10,
        "RHF": 0.40,
        "section": "4.2.8", "notes": "Large amount of data available. §3.8.2",
    },
    {
        "key": "aspirated_ir_point_gas_detector",
        "description": "Aspirated IR point gas detector system",
        "category": "topside_detector",
        "lambda_crit": 6.6, "lambda_S": 3.1, "lambda_D": 3.5,
        "lambda_DU": 2.9, "lambda_DU_70": 3.6,
        "DC": 0.16, "SFF": 0.56, "beta": 0.10,
        "section": "4.2.9", "notes": "DC faible — système aspiré avec contraintes opérationnelles",
    },
    {
        "key": "line_gas_detector",
        "description": "Line gas detector",
        "category": "topside_detector",
        "lambda_crit": 6.7, "lambda_S": 2.3, "lambda_D": 4.4,
        "lambda_DU": 0.44, "lambda_DU_70": 0.47,
        "lambda_DU_90_lo": 0.36, "lambda_DU_90_hi": 0.53,
        "DC": 0.90, "SFF": 0.94, "beta": 0.10,
        "RHF": 0.40,
        "section": "4.2.10", "notes": "Large amount of data available. §3.8.2",
    },
    {
        "key": "electrochemical_detector",
        "description": "Electrochemical detector",
        "category": "topside_detector",
        "lambda_crit": 6.0, "lambda_S": 1.8, "lambda_D": 4.2,
        "lambda_DU": 1.7, "lambda_DU_70": 1.9,
        "DC": 0.60, "SFF": 0.68, "beta": 0.10,
        "section": "4.2.11", "notes": "",
    },
    {
        "key": "smoke_detector",
        "description": "Smoke detector",
        "category": "topside_detector",
        "lambda_crit": 2.0, "lambda_S": 1.2, "lambda_D": 0.8,
        "lambda_DU": 0.16, "lambda_DU_70": 0.17,
        "DC": 0.80, "SFF": 0.92, "beta": 0.10,
        "section": "4.2.12", "notes": "",
    },
    {
        "key": "heat_detector",
        "description": "Heat detector",
        "category": "topside_detector",
        "lambda_crit": 2.29, "lambda_S": 1.37, "lambda_D": 0.92,
        "lambda_DU": 0.37, "lambda_DU_70": 0.43,
        "DC": 0.60, "SFF": 0.84, "beta": 0.10,
        "section": "4.2.13", "notes": "",
    },
    {
        "key": "flame_detector",
        "description": "Flame detector",
        "category": "topside_detector",
        "lambda_crit": 3.53, "lambda_S": 2.12, "lambda_D": 1.41,
        "lambda_DU": 0.35, "lambda_DU_70": 0.37,
        "DC": 0.75, "SFF": 0.90, "beta": 0.10,
        "section": "4.2.14", "notes": "",
    },

    # ══════════════════════════════════════════════════════════════
    # TABLE 3.3 — BOUTONS / CALL POINTS
    # ══════════════════════════════════════════════════════════════
    {
        "key": "manual_pushbutton_outdoor",
        "description": "Manual pushbutton / call point (outdoor)",
        "category": "topside_input",
        "lambda_crit": 0.35, "lambda_S": 0.11, "lambda_D": 0.23,
        "lambda_DU": 0.19, "lambda_DU_70": 0.53,
        "DC": 0.20, "SFF": 0.46, "beta": 0.05,
        "section": "4.2.15", "notes": "",
    },
    {
        "key": "cap_switch_indoor",
        "description": "CAP switch (indoor)",
        "category": "topside_input",
        "lambda_crit": 0.21, "lambda_S": 0.07, "lambda_D": 0.14,
        "lambda_DU": 0.11, "lambda_DU_70": 0.20,
        "DC": 0.20, "SFF": 0.46, "beta": 0.05,
        "section": "4.2.16", "notes": "",
    },

    # ══════════════════════════════════════════════════════════════
    # TABLE 3.4 — UNITÉS DE LOGIQUE (TOPSIDE)
    # ══════════════════════════════════════════════════════════════

    # --- PLC Standard industriel ---
    {
        "key": "std_plc_analog_input",
        "description": "Standard industrial PLC — Analogue input (single channel)",
        "category": "control_logic",
        "lambda_crit": 3.6, "lambda_S": 1.8, "lambda_D": 1.8,
        "lambda_DU": 0.7, "lambda_DU_70": None,
        "DC": 0.60, "SFF": 0.80, "beta": 0.07,
        "section": "4.3.1.1",
        "notes": "λ_DU_70% non disponible pour les unités logiques topside",
    },
    {
        "key": "std_plc_cpu",
        "description": "Standard industrial PLC — CPU / logic solver (1oo1)",
        "category": "control_logic",
        "lambda_crit": 17.5, "lambda_S": 8.8, "lambda_D": 8.8,
        "lambda_DU": 3.5, "lambda_DU_70": None,
        "DC": 0.60, "SFF": 0.80, "beta": 0.07,
        "section": "4.3.1.2", "notes": "λ_DU_70% non disponible",
    },
    {
        "key": "std_plc_digital_output",
        "description": "Standard industrial PLC — Digital output (single channel)",
        "category": "control_logic",
        "lambda_crit": 3.6, "lambda_S": 1.8, "lambda_D": 1.8,
        "lambda_DU": 0.7, "lambda_DU_70": None,
        "DC": 0.60, "SFF": 0.80, "beta": 0.07,
        "section": "4.3.1.3", "notes": "λ_DU_70% non disponible",
    },

    # --- PSS Programmable Safety System ---
    {
        "key": "pss_analog_input",
        "description": "Programmable safety system (PSS) — Analogue input (single channel)",
        "category": "control_logic",
        "lambda_crit": 2.8, "lambda_S": 1.4, "lambda_D": 1.4,
        "lambda_DU": 0.1, "lambda_DU_70": None,
        "DC": 0.90, "SFF": 0.95, "beta": 0.05,
        "section": "4.3.2.1", "notes": "λ_DU_70% non disponible",
    },
    {
        "key": "pss_cpu",
        "description": "Programmable safety system (PSS) — CPU / logic solver (1oo1)",
        "category": "control_logic",
        "lambda_crit": 5.4, "lambda_S": 2.7, "lambda_D": 2.7,
        "lambda_DU": 0.3, "lambda_DU_70": None,
        "DC": 0.90, "SFF": 0.95, "beta": 0.05,
        "section": "4.3.2.2", "notes": "λ_DU_70% non disponible",
    },
    {
        "key": "pss_digital_output",
        "description": "Programmable safety system (PSS) — Digital output (single channel)",
        "category": "control_logic",
        "lambda_crit": 3.20, "lambda_S": 1.60, "lambda_D": 1.60,
        "lambda_DU": 0.16, "lambda_DU_70": None,
        "DC": 0.90, "SFF": 0.95, "beta": 0.05,
        "section": "4.3.2.3", "notes": "λ_DU_70% non disponible",
    },

    # --- Hardwired Safety System ---
    {
        "key": "hardwired_analog_input",
        "description": "Hardwired safety system — Analogue input / trip amplifier (single)",
        "category": "control_logic",
        "lambda_crit": 0.44, "lambda_S": 0.40, "lambda_D": 0.04,
        "lambda_DU": 0.04, "lambda_DU_70": None,
        "DC": 0.00, "SFF": 0.91, "beta": 0.03,
        "section": "4.3.3.1",
        "notes": "DC=0 : hypothèse que toute défaillance DD conduit à un trip (défaillance sûre)",
    },
    {
        "key": "hardwired_logic",
        "description": "Hardwired safety system — Logic (1oo1)",
        "category": "control_logic",
        "lambda_crit": 0.33, "lambda_S": 0.30, "lambda_D": 0.03,
        "lambda_DU": 0.03, "lambda_DU_70": None,
        "DC": 0.00, "SFF": 0.91, "beta": 0.03,
        "section": "4.3.3.2", "notes": "DC=0 par hypothèse — voir §4.3.3",
    },
    {
        "key": "hardwired_digital_output",
        "description": "Hardwired safety system — Digital output (single)",
        "category": "control_logic",
        "lambda_crit": 0.44, "lambda_S": 0.40, "lambda_D": 0.04,
        "lambda_DU": 0.04, "lambda_DU_70": None,
        "DC": 0.00, "SFF": 0.91, "beta": 0.03,
        "section": "4.3.3.3", "notes": "DC=0 par hypothèse — voir §4.3.3",
    },

    # --- Autres unités logiques ---
    {
        "key": "fire_central",
        "description": "Fire central including I/O",
        "category": "control_logic",
        "lambda_crit": 13.2, "lambda_S": 6.6, "lambda_D": 6.6,
        "lambda_DU": 0.7, "lambda_DU_70": None,
        "DC": 0.90, "SFF": 0.95, "beta": 0.05,
        "section": "4.3.4.1", "notes": "",
    },
    {
        "key": "galvanic_barrier",
        "description": "Intrinsic safety isolator (galvanic isolation / galvanic barrier)",
        "category": "control_logic",
        "lambda_crit": 0.2, "lambda_S": 0.1, "lambda_D": 0.1,
        "lambda_DU": 0.1, "lambda_DU_70": None,
        "DC": 0.00, "SFF": 0.50, "beta": None,
        "section": "4.3.4.2", "notes": "",
    },

    # ══════════════════════════════════════════════════════════════
    # TABLE 3.5 — VANNES TOPSIDE
    # ══════════════════════════════════════════════════════════════
    {
        "key": "topside_esv_xv",
        "description": "Topside ESV and XV — generic (excl. solenoid/pilot)",
        "category": "topside_valve",
        "lambda_crit": 4.5, "lambda_S": 2.0, "lambda_D": 2.5,
        "lambda_DU": 2.3, "lambda_DU_70": 2.6,
        "DC": 0.05, "SFF": 0.48, "beta": 0.08,
        "section": "4.4.1",
        "notes": "λ_DU = 2.3 pour vanne avec critère d'étanchéité ; 2.0×10⁻⁶ si sans critère",
    },
    {
        "key": "topside_esv_xv_ball",
        "description": "Topside ESV and XV — ball valves (excl. solenoid/pilot)",
        "category": "topside_valve",
        "lambda_crit": 4.0, "lambda_S": 1.8, "lambda_D": 2.2,
        "lambda_DU": 2.1, "lambda_DU_70": 2.2,
        "DC": 0.05, "SFF": 0.48, "beta": 0.08,
        "section": "4.4.1.1", "notes": "",
    },
    {
        "key": "topside_esv_xv_gate",
        "description": "Topside ESV and XV — gate valves (excl. solenoid/pilot)",
        "category": "topside_valve",
        "lambda_crit": 6.4, "lambda_S": 2.9, "lambda_D": 3.5,
        "lambda_DU": 3.3, "lambda_DU_70": 3.6,
        "DC": 0.05, "SFF": 0.48, "beta": 0.08,
        "section": "4.4.1.2", "notes": "",
    },
    {
        "key": "riser_esv",
        "description": "Riser ESV (excl. solenoid/pilot)",
        "category": "topside_valve",
        "lambda_crit": 3.6, "lambda_S": 1.6, "lambda_D": 2.0,
        "lambda_DU": 1.9, "lambda_DU_70": 2.6,
        "DC": 0.05, "SFF": 0.48, "beta": 0.08,
        "section": "4.4.2", "notes": "",
    },
    {
        "key": "topside_xt_pmv_pwv",
        "description": "Topside XT valve — PMV and PWV (excl. solenoid/pilot)",
        "category": "topside_valve",
        "lambda_crit": 4.5, "lambda_S": 2.0, "lambda_D": 2.5,
        "lambda_DU": 2.3, "lambda_DU_70": 3.2,
        "DC": 0.05, "SFF": 0.48, "beta": 0.08,
        "section": "4.4.3", "notes": "",
    },
    {
        "key": "topside_xt_hascv",
        "description": "Topside XT valve — HASCV (hydraulically actuated safety check valve)",
        "category": "topside_valve",
        "lambda_crit": 5.2, "lambda_S": 0.7, "lambda_D": 4.5,
        "lambda_DU": 4.2, "lambda_DU_70": 5.2,
        "DC": 0.05, "SFF": 0.48, "beta": 0.08,
        "section": "4.4.4", "notes": "SFF assumé identique à PMV/PWV (note ²)",
    },
    {
        "key": "topside_xt_glesdv",
        "description": "Topside XT valve — GLESDV, gas lift ESD valve (excl. solenoid/pilot)",
        "category": "topside_valve",
        "lambda_crit": 0.5, "lambda_S": 0.0, "lambda_D": 0.2,
        "lambda_DU": 0.2, "lambda_DU_70": 0.5,
        "DC": 0.05, "SFF": 0.48, "beta": 0.08,
        "section": "4.4.5", "notes": "SFF assumé identique à PMV/PWV (note ²)",
    },
    {
        "key": "topside_xt_ciesdv",
        "description": "Topside XT valve — CIESDV, chemical injection ESD valve (incl. solenoid/pilot)",
        "category": "topside_valve",
        "lambda_crit": 1.9, "lambda_S": 0.0, "lambda_D": 1.9,
        "lambda_DU": 1.8, "lambda_DU_70": 3.2,
        "DC": 0.05, "SFF": 0.48, "beta": 0.08,
        "section": "4.4.6", "notes": "Inclut solénoïde/pilote. SFF assumé identique à PMV/PWV (note ²)",
    },
    {
        "key": "topside_hipps_valve",
        "description": "Topside HIPPS valve (excl. solenoid/pilot)",
        "category": "topside_valve",
        "lambda_crit": 1.2, "lambda_S": 0.7, "lambda_D": 0.5,
        "lambda_DU": 0.5, "lambda_DU_70": 0.9,
        "DC": 0.05, "SFF": 0.57, "beta": 0.08,
        "section": "4.4.7", "notes": "",
    },
    {
        "key": "blowdown_valve",
        "description": "Blowdown valve (excl. solenoid/pilot)",
        "category": "topside_valve",
        "lambda_crit": 5.3, "lambda_S": 2.2, "lambda_D": 3.1,
        "lambda_DU": 2.8, "lambda_DU_70": 3.2,
        "DC": 0.05, "SFF": 0.48, "beta": 0.08,
        "section": "4.4.8", "notes": "",
    },
    {
        "key": "fast_opening_valve_fov",
        "description": "Fast opening valve — FOV (in closed flare, excl. solenoid/pilot)",
        "category": "topside_valve",
        "lambda_crit": 11.0, "lambda_S": 4.1, "lambda_D": 6.6,
        "lambda_DU": 6.3, "lambda_DU_70": 7.6,
        "DC": 0.05, "SFF": 0.41, "beta": 0.08,
        "section": "4.4.9", "notes": "",
    },
    {
        "key": "solenoid_pilot_valve",
        "description": "Solenoid or pilot valve (single)",
        "category": "topside_valve",
        "lambda_crit": 0.8, "lambda_S": 0.5, "lambda_D": 0.3,
        "lambda_DU": 0.3, "lambda_DU_70": 0.34,
        "DC": 0.05, "SFF": 0.62, "beta": 0.10,
        "section": "4.4.10",
        "notes": "Pour config avec solénoïde ET pilote, utiliser λ_DU = 0.6×10⁻⁶ (2 vannes)",
    },
    {
        "key": "process_control_valve_frequent",
        "description": "Process control valve — frequently operated (excl. solenoid/pilot)",
        "category": "topside_valve",
        "lambda_crit": 6.3, "lambda_S": 2.7, "lambda_D": 3.6,
        "lambda_DU": 2.5, "lambda_DU_70": 3.8,
        "DC": 0.30, "SFF": 0.60, "beta": 0.08,
        "section": "4.4.11",
        "notes": "Vanne utilisée en contrôle ET en arrêt d'urgence. Ajouter solénoïde/pilote séparément.",
    },
    {
        "key": "process_control_valve_shutdown",
        "description": "Process control valve — shutdown service only (excl. solenoid/pilot)",
        "category": "topside_valve",
        "lambda_crit": None, "lambda_S": None, "lambda_D": None,
        "lambda_DU": 3.5, "lambda_DU_70": 5.5,
        "DC": 0.05, "SFF": 0.60, "beta": 0.08,
        "section": "4.4.11",
        "notes": "Vanne normalement non actionnée (arrêt seul). λ_crit/S/D non fournis. Ajouter solénoïde séparément.",
    },
    {
        "key": "pressure_relief_valve_psv",
        "description": "Pressure relief valve — PSV",
        "category": "topside_valve",
        "lambda_crit": 2.8, "lambda_S": 0.9, "lambda_D": 1.9,
        "lambda_DU": 1.9, "lambda_DU_70": 2.2,
        "DC": 0.00, "SFF": 0.33, "beta": 0.07,
        "section": "4.4.12",
        "notes": "λ_DU pour fail-to-open dans les 20% du setpoint. Voir note ⁶ pour critères alternatifs.",
    },
    {
        "key": "deluge_valve",
        "description": "Deluge valve (incl. solenoid and pilot)",
        "category": "topside_valve",
        "lambda_crit": 2.2, "lambda_S": 0.8, "lambda_D": 1.4,
        "lambda_DU": 1.4, "lambda_DU_70": 2.0,
        "DC": 0.00, "SFF": 0.37, "beta": 0.08,
        "section": "4.4.13", "notes": "Inclut solénoïde et pilote",
    },
    {
        "key": "fire_water_monitor_valve",
        "description": "Fire water monitor valve (incl. solenoid/pilot)",
        "category": "topside_valve",
        "lambda_crit": 3.6, "lambda_S": 1.3, "lambda_D": 2.2,
        "lambda_DU": 2.2, "lambda_DU_70": 2.9,
        "DC": 0.00, "SFF": 0.37, "beta": 0.08,
        "section": "4.4.14", "notes": "",
    },
    {
        "key": "water_mist_valve",
        "description": "Water mist valve (incl. solenoid/pilot)",
        "category": "topside_valve",
        "lambda_crit": 1.2, "lambda_S": 0.5, "lambda_D": 0.8,
        "lambda_DU": 0.8, "lambda_DU_70": 1.1,
        "DC": 0.00, "SFF": 0.37, "beta": 0.08,
        "section": "4.4.16", "notes": "",
    },
    {
        "key": "sprinkler_valve",
        "description": "Sprinkler valve (incl. solenoid/pilot)",
        "category": "topside_valve",
        "lambda_crit": 2.1, "lambda_S": 0.8, "lambda_D": 1.3,
        "lambda_DU": 1.3, "lambda_DU_70": 4.9,
        "DC": 0.00, "SFF": 0.38, "beta": 0.08,
        "section": "4.4.17",
        "notes": "Borne supérieure 70% élevée — forte incertitude sur les données",
    },
    {
        "key": "foam_valve",
        "description": "Foam valve (incl. solenoid/pilot)",
        "category": "topside_valve",
        "lambda_crit": 6.5, "lambda_S": 2.4, "lambda_D": 4.1,
        "lambda_DU": 4.1, "lambda_DU_70": 5.2,
        "DC": 0.00, "SFF": 0.37, "beta": 0.08,
        "section": "4.4.18", "notes": "",
    },
    {
        "key": "ballast_water_valve",
        "description": "Ballast water valve (excl. solenoid/pilot)",
        "category": "topside_valve",
        "lambda_crit": 1.0, "lambda_S": 0.4, "lambda_D": 0.6,
        "lambda_DU": 0.5, "lambda_DU_70": 0.7,
        "DC": 0.05, "SFF": 0.43, "beta": 0.08,
        "section": "4.4.19", "notes": "",
    },

    # ══════════════════════════════════════════════════════════════
    # TABLE 3.6 — ÉLÉMENTS FINAUX DIVERS (TOPSIDE)
    # ══════════════════════════════════════════════════════════════
    {
        "key": "fire_water_monitor",
        "description": "Fire water monitor",
        "category": "topside_final",
        "lambda_crit": 1.5, "lambda_S": 0.0, "lambda_D": 1.5,
        "lambda_DU": 1.5, "lambda_DU_70": 3.6,
        "DC": 0.00, "SFF": 0.00, "beta": None,
        "section": "4.4.15", "notes": "",
    },
    {
        "key": "fire_water_pump_diesel_electric",
        "description": "Fire water pump system (complete) — diesel electric",
        "category": "topside_final",
        "lambda_crit": 28.0, "lambda_S": 2.8, "lambda_D": 25.0,
        "lambda_DU": 25.0, "lambda_DU_70": 28.0,
        "DC": 0.00, "SFF": 0.10, "beta": None,
        "section": "4.4.20", "notes": "Système complet (pompe + moteur + démarrage)",
    },
    {
        "key": "fire_water_pump_diesel_hydraulic",
        "description": "Fire water pump system (complete) — diesel hydraulic",
        "category": "topside_final",
        "lambda_crit": 24.0, "lambda_S": 2.4, "lambda_D": 21.0,
        "lambda_DU": 21.0, "lambda_DU_70": 26.0,
        "DC": 0.00, "SFF": 0.10, "beta": None,
        "section": "4.4.21", "notes": "Système complet",
    },
    {
        "key": "fire_water_pump_diesel_mechanical",
        "description": "Fire water pump system (complete) — diesel mechanical",
        "category": "topside_final",
        "lambda_crit": 16.0, "lambda_S": 1.6, "lambda_D": 14.0,
        "lambda_DU": 14.0, "lambda_DU_70": 16.0,
        "DC": 0.00, "SFF": 0.10, "beta": None,
        "section": "4.4.22", "notes": "Système complet",
    },
    {
        "key": "fire_gas_damper",
        "description": "Fire & gas damper (incl. solenoid)",
        "category": "topside_final",
        "lambda_crit": 5.4, "lambda_S": 2.3, "lambda_D": 3.1,
        "lambda_DU": 3.1, "lambda_DU_70": 3.2,
        "DC": 0.00, "SFF": 0.42, "beta": 0.12,
        "section": "4.4.23", "notes": "",
    },
    {
        "key": "rupture_disc",
        "description": "Rupture disc",
        "category": "topside_final",
        "lambda_crit": 0.2, "lambda_S": 0.1, "lambda_D": 0.1,
        "lambda_DU": 0.1, "lambda_DU_70": 0.3,
        "DC": 0.00, "SFF": 0.50, "beta": None,
        "section": "4.4.24", "notes": "",
    },
    {
        "key": "circuit_breaker",
        "description": "Circuit breaker",
        "category": "topside_final",
        "lambda_crit": 1.0, "lambda_S": 0.6, "lambda_D": 0.4,
        "lambda_DU": 0.4, "lambda_DU_70": 1.1,
        "lambda_DU_90_lo": 0.02, "lambda_DU_90_hi": 2.1,
        "DC": 0.00, "SFF": 0.60, "beta": 0.05,
        "RHF": 0.60,
        "section": "4.4.25", "notes": "Limited operational experience. Large CI reflects high uncertainty.",
    },
    {
        "key": "relay_contactor",
        "description": "Relay, contactor",
        "category": "topside_final",
        "lambda_crit": 0.2, "lambda_S": 0.1, "lambda_D": 0.1,
        "lambda_DU": 0.1, "lambda_DU_70": 0.2,
        "DC": 0.00, "SFF": 0.60, "beta": 0.05,
        "section": "4.4.26", "notes": "",
    },
    {
        "key": "fire_door",
        "description": "Fire door",
        "category": "topside_final",
        "lambda_crit": 4.6, "lambda_S": 1.9, "lambda_D": 2.7,
        "lambda_DU": 2.7, "lambda_DU_70": 2.8,
        "DC": 0.00, "SFF": 0.42, "beta": None,
        "section": "4.4.27", "notes": "",
    },
    {
        "key": "watertight_door",
        "description": "Watertight door",
        "category": "topside_final",
        "lambda_crit": 5.1, "lambda_S": 2.1, "lambda_D": 3.0,
        "lambda_DU": 3.0, "lambda_DU_70": 3.5,
        "DC": 0.00, "SFF": 0.42, "beta": None,
        "section": "4.4.28", "notes": "",
    },
    {
        "key": "emergency_generator",
        "description": "Emergency generator",
        "category": "topside_final",
        "lambda_crit": 10.0, "lambda_S": 1.0, "lambda_D": 8.6,
        "lambda_DU": 8.6, "lambda_DU_70": 12.0,
        "DC": 0.00, "SFF": 0.10, "beta": None,
        "section": "4.4.29", "notes": "",
    },
    {
        "key": "lifeboat_engines",
        "description": "Lifeboat engines",
        "category": "topside_final",
        "lambda_crit": 12.0, "lambda_S": 1.2, "lambda_D": 11.0,
        "lambda_DU": 11.0, "lambda_DU_70": 14.0,
        "DC": 0.00, "SFF": 0.10, "beta": None,
        "section": "4.4.30", "notes": "",
    },
    {
        "key": "ups_battery_package",
        "description": "UPS and battery package",
        "category": "topside_final",
        "lambda_crit": 2.6, "lambda_S": 0.0, "lambda_D": 2.6,
        "lambda_DU": 0.5, "lambda_DU_70": 1.3,
        "DC": 0.80, "SFF": 0.80, "beta": None,
        "section": "4.4.31", "notes": "",
    },
    {
        "key": "emergency_lights",
        "description": "Emergency lights",
        "category": "topside_final",
        "lambda_crit": 3.7, "lambda_S": 0.0, "lambda_D": 3.7,
        "lambda_DU": 3.7, "lambda_DU_70": 3.9,
        "DC": 0.00, "SFF": 0.00, "beta": None,
        "section": "4.4.32", "notes": "",
    },
    {
        "key": "flashing_beacons",
        "description": "Flashing beacons",
        "category": "topside_final",
        "lambda_crit": 0.2, "lambda_S": 0.0, "lambda_D": 0.2,
        "lambda_DU": 0.2, "lambda_DU_70": 0.24,
        "DC": 0.00, "SFF": 0.00, "beta": None,
        "section": "4.4.33", "notes": "",
    },
    {
        "key": "lifeboat_radio",
        "description": "Lifeboat radio",
        "category": "topside_final",
        "lambda_crit": 12.0, "lambda_S": 0.0, "lambda_D": 12.0,
        "lambda_DU": 12.0, "lambda_DU_70": 15.0,
        "DC": 0.00, "SFF": 0.00, "beta": None,
        "section": "4.4.34", "notes": "",
    },
    {
        "key": "pa_loudspeakers",
        "description": "PA loudspeakers",
        "category": "topside_final",
        "lambda_crit": 0.2, "lambda_S": 0.0, "lambda_D": 0.2,
        "lambda_DU": 0.23, "lambda_DU_70": 0.25,
        "lambda_DU_90_lo": 0.20, "lambda_DU_90_hi": 0.30,
        "DC": 0.00, "SFF": 0.00, "beta": None,
        "RHF": None,
        "section": "4.4.35", "notes": "Large amount of data available. §3.8.2",
    },

    # ══════════════════════════════════════════════════════════════
    # TABLE 3.7 — ÉQUIPEMENTS D'ENTRÉE SUBSEA
    # ══════════════════════════════════════════════════════════════
    {
        "key": "subsea_pressure_sensor",
        "description": "Subsea pressure sensor",
        "category": "subsea_input",
        "lambda_crit": 2.0, "lambda_S": 0.8, "lambda_D": 1.2,
        "lambda_DU": 0.4, "lambda_DU_70": 0.8,
        "DC": 0.65, "SFF": 0.79, "beta": None,
        "section": "4.5.1",
        "notes": "β et DC indicatifs — voir §3.2. Utiliser valeurs topside comme point de départ.",
    },
    {
        "key": "subsea_temperature_sensor",
        "description": "Subsea temperature sensor",
        "category": "subsea_input",
        "lambda_crit": 1.0, "lambda_S": 0.4, "lambda_D": 0.6,
        "lambda_DU": 0.2, "lambda_DU_70": None,
        "DC": 0.65, "SFF": 0.79, "beta": None,
        "section": "4.5.2", "notes": "λ_DU_70% non disponible",
    },
    {
        "key": "subsea_pressure_temperature_sensor",
        "description": "Combined subsea pressure and temperature sensor",
        "category": "subsea_input",
        "lambda_crit": 2.2, "lambda_S": 0.9, "lambda_D": 1.3,
        "lambda_DU": 0.4, "lambda_DU_70": 0.8,
        "DC": 0.70, "SFF": 0.82, "beta": None,
        "section": "4.5.3", "notes": "",
    },
    {
        "key": "subsea_flow_sensor",
        "description": "Subsea flow sensor",
        "category": "subsea_input",
        "lambda_crit": 6.2, "lambda_S": 2.5, "lambda_D": 3.7,
        "lambda_DU": 1.3, "lambda_DU_70": 2.1,
        "DC": 0.65, "SFF": 0.79, "beta": None,
        "section": "4.5.4", "notes": "",
    },
    {
        "key": "subsea_sand_detector",
        "description": "Subsea sand detector",
        "category": "subsea_input",
        "lambda_crit": 9.5, "lambda_S": 3.8, "lambda_D": 5.7,
        "lambda_DU": 2.0, "lambda_DU_70": None,
        "DC": 0.65, "SFF": 0.79, "beta": None,
        "section": "4.5.5", "notes": "λ_DU_70% non disponible",
    },

    # ══════════════════════════════════════════════════════════════
    # TABLE 3.8 — LOGIQUE ET OMBILICAUX SUBSEA
    # ══════════════════════════════════════════════════════════════
    {
        "key": "subsea_mcs",
        "description": "MCS — Master control station (located topside)",
        "category": "subsea_logic",
        "lambda_crit": 15.0, "lambda_S": 7.7, "lambda_D": 7.7,
        "lambda_DU": 3.1, "lambda_DU_70": None,
        "DC": 0.60, "SFF": 0.80, "beta": None,
        "section": "4.5.6", "notes": "",
    },
    {
        "key": "umbilical_hydraulic_chemical",
        "description": "Umbilical hydraulic/chemical line (per line)",
        "category": "subsea_logic",
        "lambda_crit": 0.60, "lambda_S": 0.30, "lambda_D": 0.30,
        "lambda_DU": 0.06, "lambda_DU_70": None,
        "DC": 0.80, "SFF": 0.90, "beta": None,
        "section": "4.5.7", "notes": "Par ligne individuelle",
    },
    {
        "key": "umbilical_power_signal",
        "description": "Umbilical power/signal line (per line)",
        "category": "subsea_logic",
        "lambda_crit": 0.55, "lambda_S": 0.28, "lambda_D": 0.28,
        "lambda_DU": 0.06, "lambda_DU_70": None,
        "DC": 0.80, "SFF": 0.90, "beta": None,
        "section": "4.5.8", "notes": "Par ligne individuelle",
    },
    {
        "key": "subsea_sem",
        "description": "SEM — Subsea electronic module",
        "category": "subsea_logic",
        "lambda_crit": 5.3, "lambda_S": 2.6, "lambda_D": 2.6,
        "lambda_DU": 1.1, "lambda_DU_70": 1.5,
        "DC": 0.60, "SFF": 0.80, "beta": None,
        "section": "4.5.9", "notes": "",
    },
    {
        "key": "subsea_solenoid_control_valve",
        "description": "Subsea solenoid control valve (in subsea control module)",
        "category": "subsea_logic",
        "lambda_crit": 0.4, "lambda_S": 0.2, "lambda_D": 0.2,
        "lambda_DU": 0.2, "lambda_DU_70": None,
        "DC": 0.00, "SFF": 0.60, "beta": None,
        "section": "4.5.10", "notes": "λ_DU_70% non disponible",
    },

    # ══════════════════════════════════════════════════════════════
    # TABLE 3.9 — ÉLÉMENTS FINAUX SUBSEA
    # ══════════════════════════════════════════════════════════════
    {
        "key": "subsea_manifold_isolation_valve",
        "description": "Subsea manifold isolation valve",
        "category": "subsea_valve",
        "lambda_crit": 0.5, "lambda_S": 0.3, "lambda_D": 0.2,
        "lambda_DU": 0.2, "lambda_DU_70": None,
        "DC": 0.00, "SFF": None, "beta": None,
        "section": "4.5.11", "notes": "SFF indicatif uniquement pour éléments finaux subsea",
    },
    {
        "key": "subsea_xt_pmv_pwv",
        "description": "Subsea XT valve — PMV, PWV",
        "category": "subsea_valve",
        "lambda_crit": 0.9, "lambda_S": 0.3, "lambda_D": 0.6,
        "lambda_DU": 0.6, "lambda_DU_70": 0.7,
        "DC": 0.00, "SFF": None, "beta": None,
        "section": "4.5.12", "notes": "",
    },
    {
        "key": "subsea_xt_xov",
        "description": "Subsea XT valve — XOV (crossover valve)",
        "category": "subsea_valve",
        "lambda_crit": 0.13, "lambda_S": 0.05, "lambda_D": 0.08,
        "lambda_DU": 0.08, "lambda_DU_70": 0.14,
        "DC": 0.00, "SFF": None, "beta": None,
        "section": "4.5.13", "notes": "",
    },
    {
        "key": "subsea_xt_amv",
        "description": "Subsea XT valve — AMV (annulus master valve)",
        "category": "subsea_valve",
        "lambda_crit": 0.16, "lambda_S": 0.04, "lambda_D": 0.12,
        "lambda_DU": 0.12, "lambda_DU_70": 0.19,
        "DC": 0.00, "SFF": None, "beta": None,
        "section": "4.5.14", "notes": "",
    },
    {
        "key": "subsea_xt_civ_miv",
        "description": "Subsea XT valve — CIV, MIV (chemical/methanol injection valve)",
        "category": "subsea_valve",
        "lambda_crit": 0.30, "lambda_S": 0.06, "lambda_D": 0.24,
        "lambda_DU": 0.24, "lambda_DU_70": 0.4,
        "DC": 0.00, "SFF": None, "beta": None,
        "section": "4.5.15", "notes": "",
    },
    {
        "key": "subsea_ssiv",
        "description": "Subsea isolation valve — SSIV",
        "category": "subsea_valve",
        "lambda_crit": 0.9, "lambda_S": 0.5, "lambda_D": 0.4,
        "lambda_DU": 0.4, "lambda_DU_70": None,
        "DC": 0.00, "SFF": None, "beta": None,
        "section": "4.5.16", "notes": "λ_DU_70% non disponible",
    },

    # ══════════════════════════════════════════════════════════════
    # TABLE 3.10 — VANNES DOWNHOLE / WELL COMPLETION
    # ══════════════════════════════════════════════════════════════
    {
        "key": "dhsv_generic",
        "description": "Downhole safety valve (DHSV) — generic",
        "category": "downhole",
        "lambda_crit": 19.0, "lambda_S": 11.0, "lambda_D": 7.5,
        "lambda_DU": 7.5, "lambda_DU_70": None,
        "DC": 0.00, "SFF": None, "beta": None,
        "section": "4.6.1", "notes": "Catégorie générique — voir sous-types TRSCSSV et WRSCSSV",
    },
    {
        "key": "dhsv_trscssv",
        "description": "Downhole safety valve — TRSCSSV (tubing retrievable surface-controlled)",
        "category": "downhole",
        "lambda_crit": 4.4, "lambda_S": 0.4, "lambda_D": 4.0,
        "lambda_DU": 4.0, "lambda_DU_70": None,
        "DC": 0.00, "SFF": None, "beta": None,
        "section": "4.6.2", "notes": "",
    },
    {
        "key": "dhsv_wrscssv",
        "description": "Downhole safety valve — WRSCSSV (wireline retrievable surface-controlled)",
        "category": "downhole",
        "lambda_crit": 19.0, "lambda_S": 4.3, "lambda_D": 15.0,
        "lambda_DU": 15.0, "lambda_DU_70": None,
        "DC": 0.00, "SFF": None, "beta": None,
        "section": "4.6.3", "notes": "",
    },
    {
        "key": "trscassv_type_a",
        "description": "Annulus subsurface safety valve — TRSCASSV, type A",
        "category": "downhole",
        "lambda_crit": 4.3, "lambda_S": 0.6, "lambda_D": 3.6,
        "lambda_DU": 3.6, "lambda_DU_70": 3.9,
        "DC": 0.00, "SFF": None, "beta": None,
        "section": "4.6.4", "notes": "",
    },
    {
        "key": "trscassv_type_b",
        "description": "Annulus subsurface safety valve — TRSCASSV, type B",
        "category": "downhole",
        "lambda_crit": 4.7, "lambda_S": 0.8, "lambda_D": 3.9,
        "lambda_DU": 3.9, "lambda_DU_70": 4.4,
        "DC": 0.00, "SFF": None, "beta": None,
        "section": "4.6.5", "notes": "",
    },
    {
        "key": "wrciv",
        "description": "Wire retrievable chemical injection valve — WRCIV",
        "category": "downhole",
        "lambda_crit": 1.8, "lambda_S": 0.1, "lambda_D": 1.8,
        "lambda_DU": 1.8, "lambda_DU_70": 2.1,
        "DC": 0.00, "SFF": None, "beta": None,
        "section": "4.6.6", "notes": "",
    },
    {
        "key": "trciv",
        "description": "Tubing retrievable chemical injection valve — TRCIV",
        "category": "downhole",
        "lambda_crit": 0.4, "lambda_S": 0.1, "lambda_D": 0.3,
        "lambda_DU": 0.3, "lambda_DU_70": 0.7,
        "DC": 0.00, "SFF": None, "beta": None,
        "section": "4.6.7", "notes": "",
    },
    {
        "key": "gas_lift_valve_glv",
        "description": "Gas lift valve — GLV",
        "category": "downhole",
        "lambda_crit": 13.0, "lambda_S": 0.2, "lambda_D": 13.0,
        "lambda_DU": 13.0, "lambda_DU_70": 14.0,
        "DC": 0.00, "SFF": None, "beta": None,
        "section": "4.6.8", "notes": "",
    },

    # ══════════════════════════════════════════════════════════════
    # TABLE 3.11 — ÉQUIPEMENTS DE FORAGE
    # ══════════════════════════════════════════════════════════════
    {
        "key": "annular_preventer",
        "description": "Annular preventer (BOP)",
        "category": "drilling",
        "lambda_crit": 45.0, "lambda_S": 35.0, "lambda_D": 9.8,
        "lambda_DU": 9.8, "lambda_DU_70": None,
        "DC": 0.00, "SFF": 0.80, "beta": None,
        "section": "4.7.1",
        "notes": "λ_DU_70% non disponible pour les équipements de forage. β spécifique non disponible.",
    },
    {
        "key": "ram_preventer",
        "description": "Ram preventer (BOP)",
        "category": "drilling",
        "lambda_crit": 3.8, "lambda_S": 0.4, "lambda_D": 3.4,
        "lambda_DU": 3.4, "lambda_DU_70": None,
        "DC": 0.00, "SFF": 0.10, "beta": None,
        "section": "4.7.2", "notes": "",
    },
    {
        "key": "choke_kill_valve",
        "description": "Choke and kill valve",
        "category": "drilling",
        "lambda_crit": 0.9, "lambda_S": 0.2, "lambda_D": 0.8,
        "lambda_DU": 0.8, "lambda_DU_70": None,
        "DC": 0.00, "SFF": 0.20, "beta": None,
        "section": "4.7.3", "notes": "",
    },
    {
        "key": "choke_kill_line",
        "description": "Choke and kill line",
        "category": "drilling",
        "lambda_crit": 24.0, "lambda_S": 2.0, "lambda_D": 22.0,
        "lambda_DU": 22.0, "lambda_DU_70": None,
        "DC": 0.00, "SFF": 0.10, "beta": None,
        "section": "4.7.4", "notes": "",
    },
    {
        "key": "hydraulic_connector",
        "description": "Hydraulic connector (BOP/riser)",
        "category": "drilling",
        "lambda_crit": 4.1, "lambda_S": 1.0, "lambda_D": 3.1,
        "lambda_DU": 3.1, "lambda_DU_70": None,
        "DC": 0.00, "SFF": 0.25, "beta": None,
        "section": "4.7.5", "notes": "",
    },
    {
        "key": "multiplex_control_system",
        "description": "Multiplex control system (BOP, with redundant pods)",
        "category": "drilling",
        "lambda_crit": 124.0, "lambda_S": 0.0, "lambda_D": 124.0,
        "lambda_DU": 62.0, "lambda_DU_70": None,
        "DC": 0.50, "SFF": 0.50, "beta": None,
        "section": "4.7.6",
        "notes": "Taux total pour TOUTES les fonctions du système (pods redondants inclus). "
                 "Pour un pod individuel, utiliser approximativement la moitié.",
    },
    {
        "key": "pilot_control_system",
        "description": "Pilot control system (BOP)",
        "category": "drilling",
        "lambda_crit": 102.0, "lambda_S": 0.0, "lambda_D": 102.0,
        "lambda_DU": 102.0, "lambda_DU_70": None,
        "DC": 0.00, "SFF": 0.00, "beta": None,
        "section": "4.7.7", "notes": "",
    },
    {
        "key": "acoustic_backup_control",
        "description": "Acoustic backup control system (BOP)",
        "category": "drilling",
        "lambda_crit": 37.0, "lambda_S": 0.0, "lambda_D": 37.0,
        "lambda_DU": 37.0, "lambda_DU_70": None,
        "DC": 0.00, "SFF": 0.00, "beta": None,
        "section": "4.7.8", "notes": "",
    },
]


# ─────────────────────────────────────────────────────────────────
# Construction du dictionnaire (conversion 10⁻⁶/h → 1/h)
# ─────────────────────────────────────────────────────────────────

_DB: Dict[str, PDSEntry] = {}

for _r in _RAW:
    _entry = PDSEntry(
        key=_r["key"],
        description=_r["description"],
        category=_r["category"],
        lambda_crit=_e6(_r.get("lambda_crit")),
        lambda_S=_e6(_r.get("lambda_S")),
        lambda_D=_e6(_r.get("lambda_D")),
        lambda_DU=_e6(_r["lambda_DU"]),
        lambda_DU_70=_e6(_r.get("lambda_DU_70")),
        lambda_DU_90_lo=_e6(_r.get("lambda_DU_90_lo")),
        lambda_DU_90_hi=_e6(_r.get("lambda_DU_90_hi")),
        DC=_r["DC"],
        SFF=_r.get("SFF"),
        beta=_r.get("beta"),
        RHF=_r.get("RHF"),
        section=_r.get("section", ""),
        notes=_r.get("notes", ""),
        source="PDS2021",
    )
    _DB[_entry.key] = _entry


# ─────────────────────────────────────────────────────────────────
# Patch RHF (Table 3.14) et intervalles de confiance (Tables 3.15–3.18)
# appliqués sur les entrées déjà construites
# ─────────────────────────────────────────────────────────────────

_RHF_PATCH: Dict[str, float] = {
    # Transmetteurs process
    "level_transmitter": 0.20,
    "level_transmitter_displacer": 0.20,
    "level_transmitter_diff_pressure": 0.20,
    "level_transmitter_radar": 0.20,
    "level_transmitter_nuclear": 0.20,
    "pressure_transmitter": 0.30,
    "pressure_transmitter_piezoresistive": 0.30,
    "flow_transmitter": 0.20,
    "temperature_transmitter": 0.30,
    # Détecteurs F&G
    "smoke_detector": 0.60,
    "heat_detector": 0.60,
    "catalytic_point_gas_detector": 0.60,
    "ir_point_gas_detector": 0.40,
    "aspirated_ir_point_gas_detector": 0.40,
    "line_gas_detector": 0.40,
    "electrochemical_detector": 0.40,
    "flame_detector": 0.40,
    # Pushbuttons
    "manual_pushbutton_outdoor": 0.60,
    "cap_switch_indoor": 0.60,
    # NOTE: position_switch et aspirator_system_flow_switch ABSENTS de Table 3.14
    # → RHF non attribué (None) — valeurs précédentes de 0.60 étaient inventées
    # Logique
    "std_plc_analog_input": 0.10,
    "std_plc_cpu": 0.10,
    "std_plc_digital_output": 0.10,
    "pss_analog_input": 0.40,
    "pss_cpu": 0.40,
    "pss_digital_output": 0.40,
    "hardwired_analog_input": 0.80,
    "hardwired_logic": 0.80,
    "hardwired_digital_output": 0.80,
    # Vannes topside arrêt
    "topside_esv_xv": 0.30,
    "topside_esv_xv_ball": 0.30,
    "topside_esv_xv_gate": 0.30,
    "riser_esv": 0.50,
    "topside_xt_pmv_pwv": 0.30,
    "topside_xt_hascv": 0.30,
    "topside_xt_glesdv": 0.30,
    "topside_xt_ciesdv": 0.30,
    "topside_hipps_valve": 0.50,
    "blowdown_valve": 0.30,
    "fast_opening_valve_fov": 0.30,
    "solenoid_pilot_valve": 0.30,
    "process_control_valve_frequent": 0.40,
    "process_control_valve_shutdown": 0.40,
    "pressure_relief_valve_psv": 0.50,  # spring operated
    "deluge_valve": 0.50,
    "fire_water_monitor_valve": 0.50,
    "water_mist_valve": 0.50,
    "sprinkler_valve": 0.50,
    "foam_valve": 0.50,
    "ballast_water_valve": 0.30,
    # Éléments finaux divers
    "fire_gas_damper": 0.30,
    "circuit_breaker": 0.60,
    "relay_contactor": 0.60,
}

# IC 90% [λ_DU_90_lo, λ_DU_90_hi] en ×10⁻⁶/h → converti ci-dessous
_CI_PATCH: Dict[str, tuple] = {
    # Table 3.15 — topside input devices
    "position_switch": (0.8, 1.7),
    "aspirator_system_flow_switch": (1.6, 3.8),
    "pressure_transmitter": (0.37, 0.61),
    "level_transmitter": (1.4, 3.2),
    "temperature_transmitter": (0.05, 0.26),
    "flow_transmitter": (0.7, 2.4),
    "catalytic_point_gas_detector": (1.0, 2.0),
    "aspirated_ir_point_gas_detector": (1.7, 4.7),
    "electrochemical_detector": (1.1, 2.4),
    "smoke_detector": (0.14, 0.32),
    "heat_detector": (0.2, 0.5),
    "flame_detector": (0.3, 0.4),
    "manual_pushbutton_outdoor": (0.05, 0.70),
    "cap_switch_indoor": (0.02, 0.35),
    # Table 3.16 — topside final elements
    "topside_esv_xv": (1.9, 2.8),
    "riser_esv": (0.7, 3.9),
    "topside_xt_pmv_pwv": (0.8, 4.8),
    "topside_xt_hascv": (2.4, 6.9),
    "topside_xt_glesdv": (0.01, 0.92),
    "topside_xt_ciesdv": (0.3, 5.6),
    "topside_hipps_valve": (0.1, 1.6),
    "blowdown_valve": (2.1, 4.1),
    "fast_opening_valve_fov": (3.7, 10.0),
    "solenoid_pilot_valve": (0.2, 0.4),
    "pressure_relief_valve_psv": (1.5, 2.4),
    "deluge_valve": (0.8, 2.5),
    "fire_water_monitor_valve": (0.5, 4.4),
    "fire_water_monitor": (0.1, 6.9),
    "water_mist_valve": (0.3, 1.6),
    "sprinkler_valve": (0.5, 8.3),
    "foam_valve": (2.1, 7.1),
    "ballast_water_valve": (0.2, 1.1),
    "fire_water_pump_diesel_electric": (18.0, 33.0),
    "fire_water_pump_diesel_hydraulic": (14.0, 34.0),
    "fire_water_pump_diesel_mechanical": (11.0, 18.0),
    "fire_gas_damper": (2.8, 3.5),
    "rupture_disc": (0.0, 0.5),
    "relay_contactor": (0.0, 0.4),
    "fire_door": (2.3, 3.1),
    "watertight_door": (1.9, 4.5),
    "emergency_generator": (3.4, 18.0),
    "lifeboat_engines": (5.5, 20.0),
    "ups_battery_package": (0.03, 2.5),
    "emergency_lights": (3.4, 4.1),
    "flashing_beacons": (0.1, 0.3),
    "lifeboat_radio": (6.2, 21.0),
    # Table 3.17 — subsea
    "subsea_pressure_sensor": (0.2, 1.3),
    "subsea_pressure_temperature_sensor": (0.1, 1.4),
    "subsea_flow_sensor": (0.3, 3.4),
    "subsea_sem": (0.1, 1.9),
    "subsea_xt_pmv_pwv": (0.5, 0.8),
    "subsea_xt_xov": (0.01, 0.25),
    "subsea_xt_amv": (0.03, 0.31),
    "subsea_xt_civ_miv": (0.1, 0.7),
    # Table 3.18 — downhole
    "trscassv_type_a": (3.0, 4.4),
    "trscassv_type_b": (2.8, 5.3),
    "wrciv": (1.1, 2.8),
    "trciv": (0.02, 1.4),
    "gas_lift_valve_glv": (12.0, 14.0),
    "dhsv_trscssv_topside": (5.7, 6.7),
    "dhsv_trscssv_subsea": (1.3, 1.8),
    "dhsv_wrscssv_topside": (14.0, 17.0),
    "dhsv_wrscssv_subsea": (2.1, 10.0),
}

for _key, _rhf in _RHF_PATCH.items():
    if _key in _DB:
        _DB[_key].RHF = _rhf

for _key, (_lo, _hi) in _CI_PATCH.items():
    if _key in _DB:
        _DB[_key].lambda_DU_90_lo = _lo * 1e-6
        _DB[_key].lambda_DU_90_hi = _hi * 1e-6


# ─────────────────────────────────────────────────────────────────
# Sous-types level transmitter (§4.2.4, Table 3.18-like breakdown)
# ─────────────────────────────────────────────────────────────────

_LEVEL_SUBTYPES = [
    {
        "key": "level_transmitter_displacer",
        "description": "Level transmitter — measuring principle: displacer",
        "category": "topside_input",
        "lambda_DU": 0.7, "lambda_DU_70": 1.1,
        "lambda_DU_90_lo": 0.2, "lambda_DU_90_hi": 1.9,
        "DC": 0.70, "SFF": 0.82, "beta": 0.10, "RHF": 0.20,
        "section": "4.2.4",
        "notes": "Typiquement utilisé pour tanks de stockage simples (moins de problèmes d'interface/mousse). "
                 "λ_DU inférieur à la moyenne générique.",
    },
    {
        "key": "level_transmitter_diff_pressure",
        "description": "Level transmitter — measuring principle: differential pressure",
        "category": "topside_input",
        "lambda_DU": 3.2, "lambda_DU_70": 3.7,
        "lambda_DU_90_lo": 2.2, "lambda_DU_90_hi": 4.6,
        "DC": 0.70, "SFF": 0.82, "beta": 0.10, "RHF": 0.20,
        "section": "4.2.4",
        "notes": "λ_DU > moyenne générique. Variabilité avec application (interface, gravité variable).",
    },
    {
        "key": "level_transmitter_radar",
        "description": "Level transmitter — measuring principle: free space radar",
        "category": "topside_input",
        "lambda_DU": 2.7, "lambda_DU_70": 3.7,
        "lambda_DU_90_lo": 1.2, "lambda_DU_90_hi": 5.4,
        "DC": 0.70, "SFF": 0.82, "beta": 0.10, "RHF": 0.20,
        "section": "4.2.4", "notes": "",
    },
    {
        "key": "level_transmitter_nuclear",
        "description": "Level transmitter — measuring principle: nuclear (gamma)",
        "category": "topside_input",
        "lambda_DU": 4.1, "lambda_DU_70": 6.1,
        "lambda_DU_90_lo": 1.4, "lambda_DU_90_hi": 9.4,
        "DC": 0.70, "SFF": 0.82, "beta": 0.10, "RHF": 0.20,
        "section": "4.2.4",
        "notes": "Grande incertitude (faible expérience opérationnelle). Applications souvent difficiles.",
    },
]

for _r2 in _LEVEL_SUBTYPES:
    _e2 = PDSEntry(
        key=_r2["key"],
        description=_r2["description"],
        category=_r2["category"],
        lambda_DU=_r2["lambda_DU"] * 1e-6,
        lambda_DU_70=_r2.get("lambda_DU_70", 0) * 1e-6 if _r2.get("lambda_DU_70") else None,
        lambda_DU_90_lo=_r2.get("lambda_DU_90_lo", 0) * 1e-6 if _r2.get("lambda_DU_90_lo") is not None else None,
        lambda_DU_90_hi=_r2.get("lambda_DU_90_hi", 0) * 1e-6 if _r2.get("lambda_DU_90_hi") is not None else None,
        DC=_r2["DC"],
        SFF=_r2.get("SFF"),
        beta=_r2.get("beta"),
        RHF=_r2.get("RHF"),
        section=_r2.get("section", ""),
        notes=_r2.get("notes", ""),
        source="PDS2021",
    )
    _DB[_e2.key] = _e2


# ─────────────────────────────────────────────────────────────────
# Pression transmitter piezorésistif (§4.2.3)
# ─────────────────────────────────────────────────────────────────

_DB["pressure_transmitter_piezoresistive"] = PDSEntry(
    key="pressure_transmitter_piezoresistive",
    description="Pressure transmitter — measuring principle: piezoresistive",
    category="topside_input",
    lambda_DU=0.2e-6,
    lambda_DU_70=0.4e-6,
    lambda_DU_90_lo=0.01e-6,
    lambda_DU_90_hi=0.74e-6,
    DC=0.65, SFF=0.75, beta=0.10, RHF=0.30,
    section="4.2.3",
    notes="Basé sur 1 seule observation — forte incertitude. Utiliser valeur générique si insuffisant.",
    source="PDS2021",
)


# ─────────────────────────────────────────────────────────────────
# Temperature transmitter thermocouple (§4.2.5)
# λ_DU identique à la moyenne générique (0.1) — thermocouple domine la population
# (407 tags / 7 installations / 4 opérateurs — 2009-2019 — T=1.4×10⁷ h — 2 DU obs)
# ─────────────────────────────────────────────────────────────────
_DB["temperature_transmitter_thermocouple"] = PDSEntry(
    key="temperature_transmitter_thermocouple",
    description="Temperature transmitter — measuring principle: thermocouple",
    category="topside_input",
    lambda_DU=0.1e-6,
    lambda_DU_70=0.3e-6,
    lambda_DU_90_lo=0.03e-6,
    lambda_DU_90_hi=0.46e-6,
    DC=0.70, SFF=0.82, beta=0.10, RHF=0.30,
    section="4.2.5",
    notes="Basé sur 2 observations (faible expérience). IC très large [0.03–0.46]. "
          "Utiliser valeur générique temperature_transmitter si données insuffisantes.",
    source="PDS2021",
)


# ─────────────────────────────────────────────────────────────────
# DHSV sous-types par emplacement du puits (Table 3.18)
# ─────────────────────────────────────────────────────────────────
# Remplace les entrées génériques dhsv_trscssv / dhsv_wrscssv qui
# ne correspondent ni à topside (6.2) ni à subsea (1.55)

_DB["dhsv_trscssv_topside"] = PDSEntry(
    key="dhsv_trscssv_topside",
    description="Downhole safety valve — TRSCSSV, topside-located wells",
    category="downhole",
    lambda_crit=4.4e-6, lambda_S=0.4e-6, lambda_D=4.0e-6,
    lambda_DU=6.2e-6, lambda_DU_70=6.3e-6,
    lambda_DU_90_lo=5.7e-6, lambda_DU_90_hi=6.7e-6,
    DC=0.00, SFF=None, beta=None,
    section="4.6.2",
    notes="Puits localisés topside. Différences selon type de service — voir §4.6.1 et §4.6.2.",
    source="PDS2021",
)

_DB["dhsv_trscssv_subsea"] = PDSEntry(
    key="dhsv_trscssv_subsea",
    description="Downhole safety valve — TRSCSSV, subsea-located wells",
    category="downhole",
    lambda_crit=None, lambda_S=None, lambda_D=None,
    lambda_DU=1.55e-6, lambda_DU_70=1.64e-6,
    lambda_DU_90_lo=1.3e-6, lambda_DU_90_hi=1.8e-6,
    DC=0.00, SFF=None, beta=None,
    section="4.6.2",
    notes="Puits localisés subsea. λ_DU notablement inférieur aux puits topside.",
    source="PDS2021",
)

_DB["dhsv_wrscssv_topside"] = PDSEntry(
    key="dhsv_wrscssv_topside",
    description="Downhole safety valve — WRSCSSV, topside-located wells",
    category="downhole",
    lambda_crit=19.0e-6, lambda_S=4.3e-6, lambda_D=15.0e-6,
    lambda_DU=15.0e-6, lambda_DU_70=16.0e-6,
    lambda_DU_90_lo=14.0e-6, lambda_DU_90_hi=17.0e-6,
    DC=0.00, SFF=None, beta=None,
    section="4.6.3",
    notes="Puits localisés topside.",
    source="PDS2021",
)

_DB["dhsv_wrscssv_subsea"] = PDSEntry(
    key="dhsv_wrscssv_subsea",
    description="Downhole safety valve — WRSCSSV, subsea-located wells",
    category="downhole",
    lambda_crit=None, lambda_S=None, lambda_D=None,
    lambda_DU=4.8e-6, lambda_DU_70=6.5e-6,
    lambda_DU_90_lo=2.1e-6, lambda_DU_90_hi=10.0e-6,
    DC=0.00, SFF=None, beta=None,
    section="4.6.3",
    notes="Puits localisés subsea. Données limitées — IC large. Voir §4.6.1 et §4.6.3.",
    source="PDS2021",
)


# ─────────────────────────────────────────────────────────────────
# API publique
# ─────────────────────────────────────────────────────────────────

def get_lambda(key: str, source: str = "PDS2021") -> PDSEntry:
    """
    Retourne l'entrée de la base de données pour l'équipement donné.

    Paramètres
    ----------
    key    : identifiant snake_case (ex. "pressure_transmitter")
    source : source de données — seul "PDS2021" est disponible en v0.7.0

    Exceptions
    ----------
    KeyError si la clé n'existe pas — utiliser list_equipment() pour explorer.
    """
    if source != "PDS2021":
        raise ValueError(f"Source '{source}' non disponible. Sources : ['PDS2021']")
    if key not in _DB:
        close = [k for k in _DB if key.split("_")[0] in k]
        hint = f" Suggestions : {close[:5]}" if close else ""
        raise KeyError(f"Équipement '{key}' non trouvé dans PDS2021.{hint}")
    return _DB[key]


def list_equipment(category: Optional[str] = None, source: str = "PDS2021") -> List[PDSEntry]:
    """
    Liste tous les équipements disponibles, optionnellement filtrés par catégorie.

    Catégories disponibles :
        topside_input, topside_detector, control_logic,
        topside_valve, topside_final,
        subsea_input, subsea_logic, subsea_valve,
        downhole, drilling
    """
    entries = list(_DB.values())
    if category:
        entries = [e for e in entries if e.category == category]
    return entries


def search_equipment(keyword: str) -> List[PDSEntry]:
    """Recherche par mot-clé dans la description ou la clé."""
    kw = keyword.lower()
    return [e for e in _DB.values()
            if kw in e.description.lower() or kw in e.key.lower()]


def make_subsystem_params(
    entry: PDSEntry,
    T1: float,
    MTTR: float,
    architecture: str,
    M: int = 1,
    N: int = 1,
    MTTR_DU: float = -1.0,
    PTC: float = 1.0,
    T2: float = 0.0,
    lambda_SO: float = 0.0,
    beta_SO: float = 0.0,
    MTTR_SO: float = 0.0,
    lambda_FD: float = 0.0,
    beta_override: Optional[float] = None,
) -> dict:
    """
    Construit un dictionnaire de paramètres compatible SubsystemParams (PRISM).

    Paramètres opérationnels à fournir par l'utilisateur
    ---------------------------------------------------
    T1            : intervalle de test de preuve [h]
    MTTR          : temps moyen de réparation [h]
    architecture  : "1oo1", "1oo2", "2oo3", etc.
    M, N          : configuration MooN
    MTTR_DU       : MTTR spécifique DU (-1 → utiliser MTTR)
    PTC           : couverture du test de preuve (0-1, défaut 1.0)
    T2            : intervalle de test complet [h] (0 → PTC=1 implicite)
    lambda_SO, beta_SO, MTTR_SO : paramètres de défaillance sortie
    lambda_FD     : taux de défaillance dangereuse détectée finale
    beta_override : si fourni, remplace le β de la base de données

    Retourne un dict prêt pour SubsystemParams(**result).
    """
    beta_val = beta_override if beta_override is not None else entry.beta
    if beta_val is None:
        raise ValueError(
            f"β non défini pour '{entry.key}'. "
            "Fournir beta_override= ou utiliser la Table 3.12 PDS 2021."
        )

    lambda_DD = entry.lambda_DD  # calculé depuis la property

    return {
        "lambda_DU": entry.lambda_DU,
        "lambda_DD": lambda_DD,
        "lambda_S": entry.lambda_S if entry.lambda_S is not None else 0.0,
        "DC": entry.DC,
        "beta": beta_val,
        "beta_D": beta_val,          # convention PDS : β_D = β pour simplification
        "MTTR": MTTR,
        "MTTR_DU": MTTR_DU,
        "T1": T1,
        "PTC": PTC,
        "T2": T2,
        "architecture": architecture,
        "M": M,
        "N": N,
        "lambda_SO": lambda_SO,
        "beta_SO": beta_SO,
        "MTTR_SO": MTTR_SO,
        "lambda_FD": lambda_FD,
    }


# ─────────────────────────────────────────────────────────────────
# Récap rapide
# ─────────────────────────────────────────────────────────────────

def summary() -> str:
    """Affiche un résumé de la base de données."""
    from collections import Counter
    cats = Counter(e.category for e in _DB.values())
    lines = [
        "=" * 60,
        "  PRISM Lambda DB — PDS Data Handbook 2021",
        f"  {len(_DB)} équipements indexés",
        "=" * 60,
    ]
    for cat, count in sorted(cats.items()):
        lines.append(f"  {cat:<30} {count:>3} entrées")
    lines.append("=" * 60)
    return "\n".join(lines)


if __name__ == "__main__":
    print(summary())
    print()
    # Exemple d'utilisation
    e = get_lambda("pressure_transmitter")
    print(f"Équipement : {e.description}")
    print(f"  λ_DU     = {e.lambda_DU:.3e} /h")
    print(f"  λ_DD     = {e.lambda_DD:.3e} /h")
    print(f"  DC       = {e.DC:.0%}")
    print(f"  SFF      = {e.SFF:.0%}")
    print(f"  β        = {e.beta}")
    print(f"  Section  : PDS 2021 §{e.section}")
