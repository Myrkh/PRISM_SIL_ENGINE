"""
IEC 61508-6 Annexe B — Formules analytiques + Corrections académiques.

Sources primaires :
  - IEC 61508-6:2010 Annexe B §B.3.2/B.3.3 — formules PFD/PFH simplifiées
  - IEC 61508-2:2010 §6.7.4 Table 2 — Safe Failure Fraction (SFF), Route 1H
  - Omeiri, Innal, Liu (2021) JESA 54(6):871-879 — PFH corrigé terme DU→DD
  - Rausand & Lundteigen, NTNU RAMS Group, Ch.8 «Calculation of PFH» (v0.1)
    slides 24-26 (DD inclusion), 28 (CCF), 31 (tCE), 35-37 (Markov)
  - Uberti M. (2024) «Functional Safety: RBD and Markov for SIS», Politecnico
    Milano, §3.4 Eq.3.9 (décomposition λ), §3.5 Eq.3.13 (SFF), §6.1 Eq.6.3 (tCE)

Moteur 1 : IEC simplifié — valide pour λ×T1 << 1 (erreur < 1% si λ×T1 < 0.05).
"""

import math
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SubsystemParams:
    """
    Paramètres d'un sous-système SIF.

    Décomposition des taux de défaillance (IEC 61508-2 §3.6, Uberti 2024 Eq.3.9) :
        λ_total = λ_SD + λ_SU + λ_DD + λ_DU  (+λ_NE ignoré pour la sécurité)

    Défaillances dangereuses (λ_D = λ_DU + λ_DD) :
        λ_DU  — Dangerous Undetected : latente, révélée au proof test uniquement.
        λ_DD  — Dangerous Detected   : détectée par diagnostics, EUC mis en sécurité.

    Défaillances sûres (λ_S = λ_SD + λ_SU) :
        λ_SD  — Safe Detected   : trip immédiat, détecté par diagnostics.
        λ_SU  — Safe Undetected : latente, révélée au proof test (pattern ≈ DU).
        λ_S   — Total safe = λ_SD + λ_SU  [rétrocompatibilité : champ legacy].

    CONVENTION : si seul lambda_S est fourni (workflow legacy), les champs
    lambda_SD et lambda_SU valent 0 et lambda_S est utilisé tel quel pour SFF.
    Si lambda_SD et/ou lambda_SU sont fournis, lambda_S est recalculé en __post_init__.

    Temps de réparation (Uberti 2024 Eq.6.3, NTNU Ch.8 slide 31) :
        MTTR     — Mean Time To Repair pour λ_DD (déclenché immédiatement).
        MTTR_DU  — Mean Repair Time pour λ_DU (réparation après découverte au
                   proof test). Physiquement distinct de MTTR même si souvent
                   égal en pratique. Par défaut = MTTR.
                   [remplace le getattr(p, 'MRT', MTTR) fragile antérieur]
    """
    # ── Paramètres obligatoires ────────────────────────────────────────────────
    lambda_DU: float       # Taux défaillance dangereuse non détectée [1/h]
    lambda_DD: float       # Taux défaillance dangereuse détectée [1/h]

    # ── Défaillances sûres — décomposition λSD + λSU (Uberti 2024 §3.4) ───────
    lambda_S: float = 0.0   # Taux total défaillances sûres = λ_SD + λ_SU [1/h]
                             # (legacy : valeur directe si λ_SD/λ_SU non renseignés)
    lambda_SD: float = 0.0  # Safe Detected   — trip immédiat via diagnostics [1/h]
    lambda_SU: float = 0.0  # Safe Undetected — latente, détectée au proof test [1/h]

    # ── Paramètres diagnostics & architecture ─────────────────────────────────
    DC: float = 0.0         # Diagnostic Coverage (0–1)
    beta: float = 0.02      # Facteur CCF pour λ_DU (IEC 61508-6 §B.3.2)
    beta_D: float = 0.01    # Facteur CCF pour λ_DD
    MTTR: float = 8.0       # Mean Time To Repair — λ_DD (détections immédiates) [h]
    MTTR_DU: float = -1.0   # Mean Repair Time — λ_DU (après proof test) [h]
                             # Convention : -1 → utilise MTTR (identiques par défaut)
    T1: float = 8760.0      # Intervalle proof test [h]
    PTC: float = 1.0        # Proof Test Coverage (0–1)
    T2: float = 87600.0     # Intervalle proof test complet si PTC < 1 [h]
    architecture: str = "1oo1"
    M: int = 1              # M dans MooN
    N: int = 1              # N dans MooN

    # ── STR — Spurious Trip Rate (NTNU Ch.12) ─────────────────────────────────
    lambda_SO: float = 0.0  # Spurious operation rate total [1/h]
    beta_SO: float = 0.02   # Facteur CCF pour SO
    MTTR_SO: float = 8.0    # Temps réparation spurious trip [h]
    lambda_FD: float = 0.0  # Fausses demandes [1/h]

    def __post_init__(self) -> None:
        """
        Cohérence et rétrocompatibilité des paramètres de défaillances sûres
        et des temps de réparation.

        Règles appliquées :
          1. λ_S = λ_SD + λ_SU si au moins l'un est fourni (> 0).
             Sinon λ_S est conservé tel quel (workflow legacy).
          2. MTTR_DU ← MTTR si MTTR_DU == -1 (sentinel valeur par défaut).
        """
        # Règle 1 : cohérence lambda_S / lambda_SD / lambda_SU
        if self.lambda_SD > 0.0 or self.lambda_SU > 0.0:
            computed = self.lambda_SD + self.lambda_SU
            if self.lambda_S > 0.0 and abs(self.lambda_S - computed) > 1e-15:
                raise ValueError(
                    f"SubsystemParams: incohérence — lambda_S={self.lambda_S:.3e} "
                    f"≠ lambda_SD + lambda_SU = {computed:.3e}. "
                    "Fournissez soit lambda_S seul, soit lambda_SD et lambda_SU."
                )
            self.lambda_S = computed

        # Règle 2 : MTTR_DU par défaut = MTTR
        if self.MTTR_DU < 0.0:
            self.MTTR_DU = self.MTTR


# ─────────────────────────────────────────────────────────────────────────────
# PFD mode basse demande — IEC 61508-6 Annexe B §B.3.2
# Source : MD 11_IEC_FORMULAS_COMPLETE
# ─────────────────────────────────────────────────────────────────────────────

def pfd_1oo1(p: SubsystemParams) -> float:
    """IEC 61508-6 §B.3.2.2.1 — PFDavg = λ_DU×T1/2 + λ_DD×MTTR."""
    return p.lambda_DU * p.T1 / 2.0 + p.lambda_DD * p.MTTR


def pfd_1oo2(p: SubsystemParams) -> float:
    """IEC 61508-6 §B.3.2.2.2 — 1oo2 avec CCF."""
    ldu = p.lambda_DU * (1 - p.beta)
    ldd = p.lambda_DD * (1 - p.beta_D)
    # MD11: PFD_G(1oo2) = 2×[(1-β_D)λ_DD+(1-β)λ_DU]²×tCE×tGE + β_D×λ_DD×MTTR + β×λ_DU×(T1/2+MRT)
    # Simplified IEC form (tCE×tGE ≈ T1²/3 for DU-dominant):
    pfd_indep = ldu ** 2 * p.T1 ** 2 / 3.0 + ldd * p.MTTR * ldu * p.T1
    pfd_ccf = p.beta * p.lambda_DU * p.T1 / 2.0 + p.beta_D * p.lambda_DD * p.MTTR
    return pfd_indep + pfd_ccf


def pfd_2oo2(p: SubsystemParams) -> float:
    """IEC 61508-6 §B.3.2.2.3 — 2oo2 (série)."""
    return 2.0 * (p.lambda_DU * p.T1 / 2.0 + p.lambda_DD * p.MTTR)


def pfd_2oo3(p: SubsystemParams) -> float:
    """IEC 61508-6 §B.3.2.2.5 — 2oo3 avec CCF."""
    ldu = p.lambda_DU * (1 - p.beta)
    ldd = p.lambda_DD * (1 - p.beta_D)
    pfd_indep = 3.0 * ldu ** 2 * p.T1 ** 2 / 3.0 + 3.0 * ldd * p.MTTR * ldu * p.T1
    pfd_ccf = p.beta * p.lambda_DU * p.T1 / 2.0 + p.beta_D * p.lambda_DD * p.MTTR
    return pfd_indep + pfd_ccf


def pfd_1oo2d(p: SubsystemParams) -> float:
    """IEC 61508-6 §B.3.2.2.4 — 1oo2D (diagnostics croisés). K=0.98."""
    K = 0.98
    ldu = p.lambda_DU * (1 - p.beta)
    ldd = p.lambda_DD * (1 - p.beta_D)
    ls = p.lambda_S if p.lambda_S > 0 else p.lambda_DD
    pfd_du2 = ldu ** 2 * p.T1 ** 2 / 3.0
    pfd_ccf = p.beta * p.lambda_DU * p.T1 / 2.0
    pfd_cross = (1 - K) * (ldd + ls) * ldu * p.T1 * p.MTTR
    return pfd_du2 + pfd_ccf + pfd_cross


def pfd_1oo3(p: SubsystemParams) -> float:
    """IEC 61508-6 §B.3.2.2.6 — 1oo3 avec CCF."""
    ldu = p.lambda_DU * (1 - p.beta)
    pfd_indep = ldu ** 3 * p.T1 ** 3 / 4.0
    pfd_ccf = p.beta * p.lambda_DU * p.T1 / 2.0
    return pfd_indep + pfd_ccf


def pfd_moon(p: SubsystemParams) -> float:
    """Dispatch MooN vers formule spécifique ou approximation générique."""
    m, n = p.M, p.N
    dispatch = {(1, 1): pfd_1oo1, (1, 2): pfd_1oo2, (2, 2): pfd_2oo2,
                (2, 3): pfd_2oo3, (1, 3): pfd_1oo3}
    fn = dispatch.get((m, n))
    if fn:
        return fn(p)
    # Approximation générique
    n_fail = n - m + 1
    ldu = p.lambda_DU * (1 - p.beta)
    pfd_indep = (ldu * p.T1) ** n_fail / (n_fail + 1)
    pfd_ccf = p.beta * p.lambda_DU * p.T1 / 2.0
    return pfd_indep + pfd_ccf


def pfd_imperfect_test(p: SubsystemParams, arch: str = "1oo2") -> float:
    """IEC 61508-6 §B.3.3 — Essai imparfait (PTC < 1). T_eff = PTC×T1 + (1-PTC)×T2."""
    if p.PTC >= 1.0:
        return pfd_arch(p, arch)
    T_eff = p.PTC * p.T1 + (1.0 - p.PTC) * p.T2
    from copy import copy
    p_eff = copy(p)
    p_eff.T1 = T_eff
    p_eff.PTC = 1.0
    return pfd_arch(p_eff, arch)


def pfd_arch(p: SubsystemParams, arch: Optional[str] = None) -> float:
    """Dispatch vers la formule PFD appropriée."""
    a = arch or p.architecture
    dispatch = {"1oo1": pfd_1oo1, "1oo2": pfd_1oo2, "2oo2": pfd_2oo2,
                "2oo3": pfd_2oo3, "1oo2D": pfd_1oo2d, "1oo3": pfd_1oo3, "MooN": pfd_moon}
    fn = dispatch.get(a)
    if fn is None:
        raise ValueError(f"Architecture inconnue: {a}")
    return fn(p)


# ─────────────────────────────────────────────────────────────────────────────
# PFH mode haute demande — IEC 61508-6 Annexe B §B.3.3
# Source : MD 11 (IEC) + MD 22 (Omeiri/Innal corrections) + MD 24 (NTNU Ch.9)
# ─────────────────────────────────────────────────────────────────────────────

def pfh_1oo1(p: SubsystemParams) -> float:
    """IEC 61508-6 §B.3.3.2.1 — PFH = λ_DU."""
    return p.lambda_DU


def pfh_1oo2(p: SubsystemParams) -> float:
    """
    PFH 1oo2 — IEC 61508-6 §B.3.3.2.2 (hypothèse IEC : DD-dernier → état sûr).

    Formule :
        PFH_G = 2 × λ_D^(i) × (1-β)λ_DU × t_CE + β×λ_DU

    t_CE (Uberti 2024 Eq.6.3, NTNU Ch.8 slide 31) :
        t_CE = (λ_DU/λ_D)×(T1/2 + MTTR_DU) + (λ_DD/λ_D)×MTTR

    Avec :
        λ_D^(i) = (1-β_D)λ_DD + (1-β)λ_DU  [taux indépendant total]
        MTTR_DU = Mean Repair Time pour λ_DU (réparation post-proof-test)
        MTTR    = Mean Time To Repair pour λ_DD (déclenchement immédiat)

    Hypothèse IEC (NTNU Ch.8 slide 29) :
        Si la DERNIÈRE défaillance est DD → EUC mis en sécurité → DGF annulé.
        ⟹ Le terme (λ_DU × λ_DD × T1) est intentionnellement absent.

    NTNU Ch.8 slide 26 (formula plus conservatrice incluant ce terme) :
        voir pfh_1oo2_ntnu().

    CCF (NTNU Ch.8 slide 28) :
        β_D×λ_DD omis car double DD → safe state commandé.
        Seul β×λ_DU contribue.
    """
    ldu = p.lambda_DU * (1 - p.beta)
    ldd = p.lambda_DD * (1 - p.beta_D)
    lD = p.lambda_DU + p.lambda_DD
    mrt_du = p.MTTR_DU   # Mean Repair Time DU — champ explicite (≠ MTTR en général)
    if lD > 0:
        tce = (p.lambda_DU / lD) * (p.T1 / 2.0 + mrt_du) + (p.lambda_DD / lD) * p.MTTR
    else:
        tce = 0.0
    pfh_indep = 2.0 * (ldd + ldu) * ldu * tce
    pfh_ccf = p.beta * p.lambda_DU
    return pfh_indep + pfh_ccf


def pfh_1oo2_ntnu(p: SubsystemParams) -> float:
    """
    PFH 1oo2 — Dérivation NTNU Ch.8 slides 24-26 (conservatrice, inclut DD→DU).

    Formule complète (tous les scénarios DGF — NTNU slide 26) :
        PFH = λ_DU²×τ + λ_DU×λ_DD×τ + 2×λ_DU×λ_DD×MTTR + β×λ_DU

    Comparaison avec la version IEC (pfh_1oo2) :
        IEC omet le terme (λ_DU×λ_DD×τ) car hypothèse DD-dernier → safe.
        Cette version inclut le scénario DU-premier → DD (état critique maintenu).

    Quand utiliser :
        - Borne supérieure conservatrice (PFH plus élevé).
        - Éléments finaux mécaniques où DD ≠ toujours safe (ex. : vanne bloquée).
        - Validation vs exSILentia ou GRIF en mode conservatif.

    Source : Rausand & Lundteigen, NTNU RAMS Group, «Calculation of PFH» Ch.8 (v0.1),
             slides 24-26 (options a et b combinées, approximation Maple).
    """
    ldu = p.lambda_DU * (1 - p.beta)
    ldd = p.lambda_DD * (1 - p.beta_D)
    pfh_indep = ldu**2 * p.T1 + ldu * ldd * p.T1 + 2.0 * ldu * ldd * p.MTTR
    pfh_ccf = p.beta * p.lambda_DU
    return pfh_indep + pfh_ccf


def pfh_2oo2(p: SubsystemParams) -> float:
    """IEC 61508-6 §B.3.3.2.3 — PFH 2oo2 = 2×λ_DU."""
    return 2.0 * p.lambda_DU


def pfh_2oo3(p: SubsystemParams) -> float:
    """
    PFH 2oo3 — IEC 61508-6 §B.3.3.2.5 (hypothèse IEC : DD-dernier → état sûr).

    Formule :
        PFH_G = 6 × λ_D^(i) × (1-β)λ_DU × t_CE + β×λ_DU

    t_CE (Uberti 2024 Eq.6.3, NTNU Ch.8 slide 31) :
        t_CE = (λ_DU/λ_D)×(T1/2 + MTTR_DU) + (λ_DD/λ_D)×MTTR

    Avec λ_D^(i) = (1-β_D)λ_DD + (1-β)λ_DU.

    Hypothèse IEC (NTNU Ch.8 slide 29) : DD-dernier → safe → terme DU→DD absent.
    Le terme manquant (Omeiri 2021) est inclus dans pfh_2oo3_corrected().

    CCF (NTNU Ch.8 slide 28) : β_D×λ_DD omis (double DD → safe commandé).

    HISTORIQUE :
        v3.0 : utilisait 6×ldu²×T1 (approximation valide DC=0% uniquement, +99%).
        v3.1 : t_CE conforme IEC §B.3.2.2.
    """
    ldu = p.lambda_DU * (1 - p.beta)
    ldd = p.lambda_DD * (1 - p.beta_D)
    lD = p.lambda_DU + p.lambda_DD
    mrt_du = p.MTTR_DU   # Mean Repair Time DU — champ explicite
    if lD > 0:
        tce = (p.lambda_DU / lD) * (p.T1 / 2.0 + mrt_du) + (p.lambda_DD / lD) * p.MTTR
    else:
        tce = 0.0
    pfh_indep = 6.0 * (ldd + ldu) * ldu * tce
    pfh_ccf = p.beta * p.lambda_DU
    return pfh_indep + pfh_ccf


def pfh_1oo3(p: SubsystemParams) -> float:
    """
    PFH 1oo3 — IEC 61508-6 §B.3.3.2.6.

    Formule :
        PFH_G = 6 × [λ_D^(i)]² × (1-β)λ_DU × t_CE × t_GE + β×λ_DU

    t_CE = (λ_DU/λ_D)×(T1/2 + MTTR_DU) + (λ_DD/λ_D)×MTTR  [NTNU Ch.8 slide 31]
    t_GE = (λ_DU/λ_D)×(T1/3 + MTTR_DU) + (λ_DD/λ_D)×MTTR  [IEC §B.3.2.2.2]

    Note sur t_GE : T1/3 car 3 composants — le temps d'exposition moyen d'un
    composant défaillant dans un groupe de 3 est τ/3 (NTNU Ch.8 slide 32,
    NTNU slide 34 formule générale kooN avec t_GEi).

    CCF (NTNU Ch.8 slide 28) : seul β×λ_DU inclus.

    HISTORIQUE :
        v3.0 : utilisait 3×ldu³×T1². Erreur structurelle masquée par β×λ_DU.
        v3.1 : t_CE et t_GE conformes IEC §B.3.2.2.
    """
    ldu = p.lambda_DU * (1 - p.beta)
    ldd = p.lambda_DD * (1 - p.beta_D)
    lD = p.lambda_DU + p.lambda_DD
    mrt_du = p.MTTR_DU   # Mean Repair Time DU — champ explicite
    if lD > 0:
        tce = (p.lambda_DU / lD) * (p.T1 / 2.0 + mrt_du) + (p.lambda_DD / lD) * p.MTTR
        tge = (p.lambda_DU / lD) * (p.T1 / 3.0 + mrt_du) + (p.lambda_DD / lD) * p.MTTR
    else:
        tce = tge = 0.0
    pfh_indep = 6.0 * (ldd + ldu) ** 2 * ldu * tce * tge
    pfh_ccf = p.beta * p.lambda_DU
    return pfh_indep + pfh_ccf


# ── PFH CORRIGÉ (Omeiri/Innal 2021) — MD 22_PFH_CORRECTED ──────────────

def pfh_1oo2_corrected(p: SubsystemParams) -> float:
    """
    PFH 1oo2 corrige - Omeiri, Innal, Liu (2021) Eq.17.
    Source : JESA Vol.54 No.6 pp.871-879 (open access iieta.org).

    Terme manquant IEC : 2*(1-beta)*lDU*(T1/2+MRT)*lDD

    BUG CORRIGE v0.3.4 (Bug #6) : MRT etait p.T1/2.0 au lieu de p.MTTR_DU.
    Avec T1=8760h, MTTR=8h : resultat etait x547 trop grand.

    BUG CORRIGE v0.4.2 (Bug #7a) : MRT etait p.MTTR au lieu de p.MTTR_DU.
    Omeiri 2021 §2.2 définit MRT = Mean Repair Time pour DU (≠ MTTR pour DD).
    L'ancien commentaire «MRT = MTTR» était une mauvaise lecture de la section 4
    où MTTR = MRT = 8h sont des PARAMETRES NUMERIQUES, pas une définition.
    Source : Omeiri 2021 §2.2 p.872 ; Uberti 2024 Eq.6.3 ; NTNU Ch.8 slide 31.
    """
    ldu = (1 - p.beta) * p.lambda_DU
    ldd = (1 - p.beta_D) * p.lambda_DD
    ld_ind = ldu + ldd
    MRT = p.MTTR_DU   # Mean Repair Time DU (Omeiri 2021 §2.2) ≠ MTTR (pour DD)

    if ld_ind > 0:
        t_CE1 = (ldu / ld_ind) * (p.T1 / 2.0 + MRT) + (ldd / ld_ind) * p.MTTR
    else:
        t_CE1 = p.T1 / 2.0

    pfh_main    = 2.0 * (ldd + ldu) * t_CE1 * ldu
    pfh_ccf     = p.beta * p.lambda_DU
    pfh_missing = 2.0 * ldu * (p.T1 / 2.0 + MRT) * p.lambda_DD
    return pfh_main + pfh_ccf + pfh_missing


def pfh_2oo3_corrected(p: SubsystemParams) -> float:
    """
    PFH 2oo3 corrigé — Omeiri, Innal, Liu (2021) Eq.22.
    Source : JESA Vol.54 No.6 pp.871-879 (open access iieta.org).
    
    L'IEC sous-estime : ignore la séquence DU→DD (état 1→3→7).
    Δ = 6×(1-β)×λ_DU × (T1/2 + MRT) × (1-β_D)×λ_DD
    """
    ldu = (1 - p.beta) * p.lambda_DU
    ldd = (1 - p.beta_D) * p.lambda_DD
    ld_ind = ldu + ldd
    MRT = p.MTTR_DU  # Mean Repair Time DU (Omeiri 2021 §2.2) != MTTR (pour DD)
                     # BUG #7b corrige v0.4.2 : etait p.MTTR (mauvaise lecture Omeiri §4)

    if ld_ind > 0:
        t_CE1 = (ldu / ld_ind) * (p.T1 / 2.0 + MRT) + (ldd / ld_ind) * p.MTTR
    else:
        t_CE1 = p.T1 / 2.0

    pfh_main = 6.0 * (ldd + ldu) * t_CE1 * ldu
    pfh_ccf = p.beta * p.lambda_DU
    # TERME MANQUANT #1 (Omeiri 2021 Eq.22, p.876 — critique, sequence DU->DD etat 1->3->7)
    pfh_missing_1 = 6.0 * ldu * (p.T1 / 2.0 + MRT) * ldd
    # TERME MANQUANT #2 (Omeiri 2021 Eq.22, p.876 — peut etre neglige mais inclus)
    pfh_missing_2 = 3.0 * (ldd * p.MTTR + ldu * (p.T1 / 2.0 + MRT)) * p.beta * p.lambda_DU
    return pfh_main + pfh_ccf + pfh_missing_1 + pfh_missing_2


def pfh_arch(p: SubsystemParams, arch: Optional[str] = None) -> float:
    """Dispatch PFH (IEC standard)."""
    a = arch or p.architecture
    dispatch = {"1oo1": pfh_1oo1, "1oo2": pfh_1oo2, "2oo2": pfh_2oo2,
                "2oo3": pfh_2oo3, "1oo3": pfh_1oo3}
    fn = dispatch.get(a, pfh_1oo1)
    return fn(p)


def pfh_1oo3_corrected(p: SubsystemParams) -> float:
    """
    PFH 1oo3 exact — Moteur 2B Time-Domain CTMC (PRISM v0.5.0, Bug #11).

    POURQUOI une formule analytique (comme Omeiri Eq.27) ne suffit pas :
    ─────────────────────────────────────────────────────────────────────
    Pour 1oo2 et 2oo3 (N-M=1), le terme manquant IEC est un produit λ_DU × λ_DD
    d'ordre 2, addable à la formule IEC existante (Omeiri 2021 Eq.17, Eq.22).

    Pour 1oo3 (N-M=2), l'erreur est structurellement différente :
    Le steady-state Markov modélise μ_DU = 2/T1 (renouvellement moyen),
    ce qui est valide pour l'ordre 1 (N-M=1) mais INCORRECT pour l'ordre 2+.
    L'accumulation de 2 canaux DU simultanément suit une distribution triangulaire
    sur [0,T1]², et la correction n'est pas un simple terme additif mais un
    changement du modèle d'accumulation.

    Preuve numérique (PRISM v0.5.0 §Bug#11) :
        PFH_SS / PFH_exact = 2^p/(p+1) avec p = N-M
        p=2 → ratio = 4/3 : SS sous-estime de 25% pour tout DC ∈ [0,1]
        Validation : Time-Domain = Table 5 Omeiri 2021 (MPM) à < 0.01%

    MÉTHODE : CTMC avec DU absorbant sur [0, T1]
    ─────────────────────────────────────────────
    Les canaux DU s'accumulent sans restauration intermédiaire (proof test en fin
    de période). La réparation DD (μ_DD=1/MTTR) est conservée.
    PFH = (1/T1) × ∫₀^T₁ flux(t→états_dangereux) dt

    Sources :
        Omeiri, Innal, Liu (2021) JESA 54(6):871-879 — Table 5 (β=0, DC=0.6/0.9/0.99)
        NTNU Ch.8 §PFH calculation — flux moyen vers états dangereux
        PRISM v0.5.0 Bug #11 — loi 2^p/(p+1) démontrée analytiquement
        PRISM v0.5.0 Bug #11 — TD = MPM Omeiri à 0.01% (validation)

    Performance : ~35ms (intégration ODE Radau + quadrature).
    Pour calculs batch (Sprint B), utiliser pfh_1oo3 + facteur ×4/3 comme borne.
    """
    from sil_engine.markov import MarkovSolver
    import copy
    p3 = copy.copy(p)
    p3.architecture = "1oo3"
    p3.N = 3
    p3.M = 1
    return MarkovSolver(p3).compute_pfh_timedomain()


def pfh_arch_corrected(p: SubsystemParams, arch: Optional[str] = None) -> float:
    """Dispatch PFH corrigé (Omeiri/Innal 2021 + NTNU Ch.9 + PRISM Bug#11)."""
    a = arch or p.architecture
    dispatch = {"1oo1": pfh_1oo1, "1oo2": pfh_1oo2_corrected,
                "2oo2": pfh_2oo2, "2oo3": pfh_2oo3_corrected, "1oo3": pfh_1oo3_corrected}
    fn = dispatch.get(a, pfh_1oo1)
    return fn(p)


# ─────────────────────────────────────────────────────────────────────────────
# STR — Spurious Trip Rate (analytique)
# Source : NTNU Ch.12 — MD 21_STR_SPURIOUS_TRIP
# ─────────────────────────────────────────────────────────────────────────────

def str_analytical(p: SubsystemParams) -> dict:
    """
    STR analytique pour architecture koon.
    Source : NTNU Ch.12 slides 22-28.
    
    STR_G = STR_IF + STR_DD + STR_FD
    """
    k, n = p.M, p.N
    from math import comb

    # ── STR_IF : Spurious Operation — NTNU Ch.12 slide 24
    if k == 1:
        str_if = n * p.lambda_SO  # 1oon : tout SO → trip
    else:
        lso_ind = (1 - p.beta_SO) * p.lambda_SO
        str_if = (n * comb(n - 1, k - 1) * lso_ind ** k
                  * p.MTTR_SO ** (k - 1) + p.beta_SO * p.lambda_SO)

    # ── STR_DD : DD failures → safe state — NTNU Ch.12 slide 27
    n_fail_dd = n - k + 1  # nb DD needed for trip
    if n_fail_dd <= 0:
        str_dd = 0.0
    elif n == k:  # noon (série) : tout DD → trip
        str_dd = n * p.lambda_DD
    else:
        ldd_ind = (1 - p.beta_D) * p.lambda_DD
        str_dd = (n * comb(n - 1, n_fail_dd - 1) * ldd_ind ** n_fail_dd
                  * p.MTTR ** (n_fail_dd - 1) + p.beta_D * p.lambda_DD)

    # ── STR_FD : False Demands — NTNU Ch.12 slide 26
    str_fd = p.lambda_FD

    str_total = str_if + str_dd + str_fd
    mttfs = 1.0 / str_total if str_total > 0 else float('inf')

    return {
        "str_total": str_total,
        "str_if": str_if,
        "str_dd": str_dd,
        "str_fd": str_fd,
        "mttfs_hours": mttfs,
        "mttfs_years": mttfs / 8760.0,
        "trips_per_year": str_total * 8760.0,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Utilitaires
# ─────────────────────────────────────────────────────────────────────────────

def lambda_T1_product(p: SubsystemParams) -> float:
    """λ_D × T1 — critère Markov requis si > 0.1."""
    return (p.lambda_DU + p.lambda_DD) * p.T1


def markov_required(
    p: SubsystemParams,
    threshold: float = None,
) -> bool:
    """
    True si le Markov TD exact est requis (formule Omeiri corrigée insuffisante).

    Utilise par défaut le seuil adaptatif par (architecture, DC) calculé dans
    error_surface.py (Sprint D), critère 5% d'erreur résiduelle.
    Si threshold est fourni explicitement, utilise cette valeur fixe.

    Seuil adaptatif vs seuil IEC §B.1 (0.1 fixe) :
        1oo1 DC=0   : 0.101 ≈ IEC §B.1 (cohérent)
        1oo1 DC=0.9 : 0.986 (IEC §B.1 dix fois trop conservatif)
        2oo3 DC=0   : 0.033 (IEC §B.1 trois fois trop permissif)
        1oo3        : ∞     (pfh_1oo3_corrected = TD exact)

    Sources :
        PRISM v0.5.0 Sprint D.5 — seuils adaptatifs (arch, DC)
        IEC 61508-6 §B.1 — seuil historique λT1 < 0.1 (superseded)
        error_surface.adaptive_iec_threshold() — interpolation linéaire par morceaux
    """
    lT1 = lambda_T1_product(p)
    if threshold is None:
        # Calcul du DC effectif à partir des taux de défaillance
        lD = p.lambda_DU + p.lambda_DD
        DC_eff = (p.lambda_DD / lD) if lD > 0 else 0.0
        try:
            from .error_surface import adaptive_iec_threshold
            threshold = adaptive_iec_threshold(p.architecture, DC_eff)
        except Exception:
            threshold = 0.1  # fallback conservatif IEC §B.1
    return lT1 > threshold


def sil_from_pfd(pfd: float) -> int:
    """Classification SIL depuis PFDavg."""
    if pfd < 1e-4: return 4
    if pfd < 1e-3: return 3
    if pfd < 1e-2: return 2
    if pfd < 1e-1: return 1
    return 0


def sil_from_pfh(pfh: float) -> int:
    """Classification SIL depuis PFH."""
    if pfh < 1e-8: return 4
    if pfh < 1e-7: return 3
    if pfh < 1e-6: return 2
    if pfh < 1e-5: return 1
    return 0


def route1h_constraint(p: SubsystemParams, arch: str) -> dict:
    """
    Contrainte architecturale SIL max — Route 1H (IEC 61508-2 Table 2).

    Safe Failure Fraction (SFF) — IEC 61508-2 §6.7.4, Uberti 2024 Eq.3.13 :

        SFF = (λ_SD + λ_SU + λ_DD) / (λ_SD + λ_SU + λ_DD + λ_DU)
            = (λ_S + λ_DD) / (λ_S + λ_DD + λ_DU)

    Avec λ_S = λ_SD + λ_SU (total défaillances sûres).
    Les défaillances sans effet (λ_NE) sont exclues (Uberti 2024 §3.5 — note).

    Cas particulier électromécanique (Uberti 2024 §3.5, Eq.3.14) :
        Si λ_S ≈ 0 (composant électromécanique — vannes, relais) :  SFF ≈ DC
        Un avertissement est émis si λ_S = 0 et DC > 0 pour signaler l'incohérence
        fréquente : fournir DC sans λ_SD/λ_SU revient à ignorer les défaillances
        sûres dans le calcul SFF.

    Table de correspondance HFT/SIL (IEC 61508-2 Table 2, composants Type B) :
        HFT=0 : SFF < 60% → SIL1 max | 60–90% → SIL2 | ≥90% → SIL3
        HFT=1 : SFF < 60% → SIL2 max | 60–90% → SIL3 | ≥90% → SIL4
        HFT=2 : SIL4 atteignable quelle que soit la SFF

    Correspondance architecture → HFT (IEC 61508-2 §B.3.3) :
        1oo1, 2oo2 → HFT=0  (pas de redondance)
        1oo2, 1oo2D, 2oo3 → HFT=1  (tolérance à 1 panne)
        1oo3 → HFT=2  (tolérance à 2 pannes)

    Note : Route 2H (données terrain) peut dépasser ces limites mais n'est
    pas implémentée ici.
    """
    lambda_D = p.lambda_DU + p.lambda_DD
    lambda_total = lambda_D + p.lambda_S   # λ_S = λ_SD + λ_SU via __post_init__
    sff = (p.lambda_S + p.lambda_DD) / lambda_total if lambda_total > 0 else 0.0

    # ── Diagnostic : cas électromécanique SFF ≈ DC ─────────────────────────
    # (Uberti 2024 §3.5, Eq.3.14 : λ_s ≈ 0 → SFF = λ_DD/λ_D = DC)
    warnings_sff = []
    if p.lambda_S == 0.0 and p.DC > 0.0:
        sff_dc = p.DC  # approximation Uberti Eq.3.14
        warnings_sff.append(
            f"AVERTISSEMENT SFF : lambda_S=0 mais DC={p.DC:.1%}. "
            f"Pour un composant électromécanique, SFF ≈ DC = {sff_dc:.1%} "
            f"(Uberti 2024 Eq.3.14). Vérifier si lambda_SD et/ou lambda_SU "
            f"devraient être renseignés. SFF calculé = {sff:.1%}."
        )
    if lambda_D == 0.0 and lambda_total > 0.0:
        warnings_sff.append(
            "AVERTISSEMENT SFF : lambda_DU = lambda_DD = 0 — "
            "composant sans défaillance dangereuse. SFF = 1.0 par convention."
        )
        sff = 1.0

    hft_map = {"1oo1": 0, "2oo2": 0, "1oo2": 1, "1oo2D": 1, "2oo3": 1, "1oo3": 2}
    hft = hft_map.get(arch, 0)
    if hft == 0:
        sil_max = 1 if sff < 0.60 else (2 if sff < 0.90 else 3)
    elif hft == 1:
        sil_max = 2 if sff < 0.60 else (3 if sff < 0.90 else 4)
    else:
        sil_max = 4
    return {
        "sff": sff,
        "hft": hft,
        "sil_max_arch": sil_max,
        "lambda_S_total": p.lambda_S,   # = λ_SD + λ_SU
        "lambda_SD": p.lambda_SD,
        "lambda_SU": p.lambda_SU,
        "warnings": warnings_sff,       # liste vide si aucun problème
    }


def pfh_koon_corrected(
    p: SubsystemParams,
    M: Optional[int] = None,
    N: Optional[int] = None,
) -> float:
    """
    PFH kooN généralisé corrigé — formule analytique Omeiri étendue (p=1)
    ou Markov Time-Domain exact (p≥2).

    Paramètres
    ──────────
    M, N : paramètres kooN (si None, utilise p.M et p.N)

    Logique de sélection selon p = N−M :
    ─────────────────────────────────────
    p = 0 (NooN) : un seul canal, PFH = λ_DU
        Source : IEC 61508-6 §B.3.3.2.1

    p = 1 (MooN avec N-M=1 : 1oo2, 2oo3, 3oo4, 4oo5...) :
        Formule analytique Omeiri étendue à tout N.
        PFH = N×(N−1) × λ_DU × [λ_D×tCE1 + (T1/2+MRT)×λ_DD] + β×λ_DU
        Valide pour λ×T1 < 0.102/N (Source B < 5%).
        Au-delà : compute_exact TD.

        DÉRIVATION (Sprint E — doc 09_SPRINT_E_PFH_KOON_GENERALIZED.md) :

        Coefficient N×(N-1) :
          = 2 × C(N,2) [identité combinatoire, N paires × 2 orderings]
          = C(N,2) × 2!  [Uberti (2024) Annexe E Eq.E.7, r=1]
          Vérifié avec IEC §B.3.3.2.2 (N=2→2) et §B.3.3.2.5 (N=3→6).
          Source : Uberti (2024) + IEC §B.3.3.2 — DANS LES SOURCES.

        Remplacement λDU²×T1 → λDU×λD×tCE (extension DC>0) :
          Justifié par IEC §B.3.3.2.2/5 pour N=2 et N=3.
          Extension à N≥4 : CONTRIBUTION ORIGINALE PRISM Sprint E.

        Terme manquant Omeiri N×(N-1)×λDU×(T1/2+MRT)×λDD :
          Omeiri (2021) Eq.17 pour N=2, Eq.22 pour N=3.
          Généralisation à N≥4 : CONTRIBUTION ORIGINALE PRISM Sprint E.

        Validation numérique : δ < 2% vs TD pour λ×T1 ≤ 0.01, tout DC, N=2..5.
        (cf. doc 09_SPRINT_E_PFH_KOON_GENERALIZED.md §2.6)

        Sources :
          IEC 61508-6 §B.3.3.2.2 et §B.3.3.2.5 (coefficient, tCE, N=2,3)
          Uberti (2024) Annexe E Eq.E.7 (coefficient DC=0, tout N)
          Omeiri et al. (2021) JESA 54(6) Eq.17/22 (termes manquants N=2,3)
          PRISM v0.5.0 Sprint E — extension N≥4 (contribution originale)

    p ≥ 2 (1oo3, 1oo4, 2oo4, 1oo5...) :
        Pas de formule analytique fermée précise.
        Toujours routé vers compute_exact (Markov Time-Domain).
        La loi 2^p/(p+1) quantifie l'erreur SS — jamais utilisée ici.
        Source : PRISM v0.5.0 Bug #11 — preuve analytique 2^p/(p+1)

    Seuil de validité formule analytique p=1 :
        Loi empirique (PRISM Sprint E, observation numérique sur grille TD) :
        λ×T1 < 0.102/N  [Source B < 5%, DC=0, β=0]
        Produit N×seuil = 0.1001 ± 0.0007 pour N=2..6 (< 1% variation).
        Cette loi N'EST PAS dérivée analytiquement — déclarée empirique.
        Pour DC intermédiaire : interpolation dans THRESHOLDS_OMEIRI_5PCT.

    Retourne
    ────────
    float : PFH [1/h]
    """
    _M = M if M is not None else p.M
    _N = N if N is not None else p.N
    _p = _N - _M  # ordre de redondance

    # Dispatch vers fonctions dédiées si disponibles (plus documentées)
    exact_funcs = {
        (1, 1): pfh_1oo1,
        (2, 2): pfh_2oo2,
        (1, 2): pfh_1oo2_corrected,
        (2, 3): pfh_2oo3_corrected,
        (1, 3): pfh_1oo3_corrected,
    }
    fn = exact_funcs.get((_M, _N))
    if fn:
        return fn(p)

    # p = 0 (NooN, N > 2) : redondance nulle
    if _p == 0:
        return p.lambda_DU  # IEC §B.3.3.2.1

    # p = 1 : formule Omeiri généralisée N×(N-1)
    # Valide analytiquement pour tout N ≥ 2 (démontrée Sprint E)
    if _p == 1:
        ldu = (1 - p.beta)   * p.lambda_DU
        ldd = (1 - p.beta_D) * p.lambda_DD
        lD  = ldu + ldd
        MRT = p.MTTR_DU  # Mean Repair Time DU — Omeiri 2021 §2.2
        if lD > 0:
            tCE1 = (ldu / lD) * (p.T1 / 2.0 + MRT) + (ldd / lD) * p.MTTR
        else:
            tCE1 = p.T1 / 2.0
        coeff    = _N * (_N - 1)   # = C(N,2)×2, identique pour IEC et Omeiri
        pfh_core = coeff * ldu * (lD * tCE1 + (p.T1 / 2.0 + MRT) * ldd)
        pfh_ccf  = p.beta * p.lambda_DU
        return pfh_core + pfh_ccf

    # p ≥ 2 : TD exact via compute_exact (Bug #11 — SS sous-estime de 2^p/(p+1))
    # On construit un SubsystemParams compatible avec l'architecture demandée
    from copy import copy as _copy
    from .markov import compute_exact
    p_arch = _copy(p)
    p_arch.M = _M
    p_arch.N = _N
    p_arch.architecture = f"{_M}oo{_N}"
    r = compute_exact(p_arch, mode="high_demand")
    return r["pfh"]


def pfh_moon(p: SubsystemParams, k: Optional[int] = None, n: Optional[int] = None) -> float:
    """
    PFH kooN généralisé — dispatch vers formule exacte si disponible,
    sinon approximation DC=0% (Uberti 2024 Annexe E, Eq.E.7).

    Paramètres :
        k : nombre de canaux requis pour succès (défaut : p.M)
        n : nombre total de canaux (défaut : p.N)

    Architectures avec formule exacte IEC 61508-6 (DC quelconque) :
        1oo1, 2oo2, 1oo2, 2oo3, 1oo3 → fonctions dédiées

    Architectures génériques (k,n) avec DC=0% uniquement :
        PFH = C(n, n-k+1) × λ_DU^(n-k+1) × T1^(n-k) + β×λ_DU
        Source : Uberti 2024 Annexe E Eq.E.7 ; NTNU Ch.8 slide 27.
        ⚠ VALIDE UNIQUEMENT POUR DC=0% (λ_DD=0).
        Pour DC>0% avec N>3 : utiliser compute_exact(mode='high_demand')
        (Markov CTMC exact — markov.py).

    Validation DC=0% : conforme NTNU Ch.8 slide 22 formule C(n,n-k+1)×λDU^(n-k+1)×τ^(n-k)
    """
    from math import comb
    _k = k if k is not None else p.M
    _n = n if n is not None else p.N

    # Dispatch vers formules exactes pour les architectures connues
    exact = {(1,1): pfh_1oo1, (2,2): pfh_2oo2,
             (1,2): pfh_1oo2, (2,3): pfh_2oo3, (1,3): pfh_1oo3}
    fn = exact.get((_k, _n))
    if fn:
        return fn(p)

    # Formule généralisée corrigée — pfh_koon_corrected couvre tout (M, N)
    # Pour p=1 : Omeiri étendu (< 2% vs TD pour λT1 ≤ 0.02)
    # Pour p≥2 : Markov TD exact
    # Source : PRISM v0.5.0 Sprint E — pfh_koon_corrected()
    return pfh_koon_corrected(p, M=_k, N=_n)
