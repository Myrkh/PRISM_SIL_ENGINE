"""
IEC 61508-6 Annexe B — Formules analytiques + Corrections académiques.

Sources :
  - IEC 61508-6:2010 Annexe B (MD 11_IEC_FORMULAS_COMPLETE)
  - Omeiri, Innal, Liu (2021) JESA 54(6):871-879 — PFH corrigé (MD 22_PFH_CORRECTED)
  - Rausand & Lundteigen NTNU Ch.9 — PFH exact avec DD (MD 24_MTTFS_PST_PFH_NTNU)
  - Rausand & Lundteigen NTNU Ch.12 — STR (MD 21_STR_SPURIOUS_TRIP)

Moteur 1 : IEC simplifié — valide pour λ×T1 << 1 (erreur < 1% si λ×T1 < 0.05).
"""

import math
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SubsystemParams:
    """Paramètres d'un sous-système SIF."""
    lambda_DU: float       # Taux défaillance dangereuse non détectée [1/h]
    lambda_DD: float       # Taux défaillance dangereuse détectée [1/h]
    lambda_S: float = 0.0  # Taux défaillance sécurité [1/h]
    DC: float = 0.0        # Couverture diagnostique (0-1)
    beta: float = 0.02     # Facteur CCF DU
    beta_D: float = 0.01   # Facteur CCF DD
    MTTR: float = 8.0      # Temps moyen réparation DD [h]
    T1: float = 8760.0     # Intervalle essai périodique [h]
    PTC: float = 1.0       # Couverture essai périodique (proof test coverage)
    T2: float = 87600.0    # Intervalle essai complet si PTC < 1 [h]
    architecture: str = "1oo1"
    M: int = 1             # M dans MooN
    N: int = 1             # N dans MooN
    # STR parameters (MD 21_STR_SPURIOUS_TRIP — NTNU Ch.12)
    lambda_SO: float = 0.0   # Taux spurious operation [1/h]
    beta_SO: float = 0.02    # Facteur CCF pour SO
    MTTR_SO: float = 8.0     # Temps réparation SO [h]
    lambda_FD: float = 0.0   # Taux fausses demandes [1/h]


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
    IEC 61508-6 §B.3.3.2.2 — PFH 1oo2.

    Source : 11_IEC_FORMULAS_COMPLETE.md §B.3.3.2.2 + NTNU Ch9 slide 31 :
      PFH_G(1oo2) = 2 × λD_indep × (1-β)λDU × t_CE + β×λDU

    t_CE = (λDU/λD)×(T1/2+MRT) + (λDD/λD)×MTTR   ← même t_CE que PFD

    Développé :  PFH = λDU²×T1 + 2×λDU²×MRT + 2×λDU×λDD×MTTR
    Exclut intentionnellement le terme DU→DD (λDU×λDD×T1) :
    IEC assume que n-k+1 DD failures → transition vers état sûr.
    (Source : NTNU Ch9 slide 29 — "DD failure as last = safe state, disregarded")

    Note : NTNU slide 26 propose une formule alternative plus conservatrice
    qui inclut le terme DU→DD. Voir pfh_1oo2_ntnu() si besoin.
    """
    ldu = p.lambda_DU * (1 - p.beta)
    ldd = p.lambda_DD * (1 - p.beta_D)
    lD = p.lambda_DU + p.lambda_DD
    MRT = getattr(p, 'MRT', p.MTTR)
    if lD > 0:
        tce = (p.lambda_DU / lD) * (p.T1 / 2.0 + MRT) + (p.lambda_DD / lD) * p.MTTR
    else:
        tce = 0.0
    pfh_indep = 2.0 * (ldd + ldu) * ldu * tce
    pfh_ccf = p.beta * p.lambda_DU
    return pfh_indep + pfh_ccf


def pfh_1oo2_ntnu(p: SubsystemParams) -> float:
    """
    PFH 1oo2 — Dérivation NTNU Ch9 slides 24-26 (alternative, plus conservatrice).

    PFH = λDU²×τ + λDU×λDD×τ + 2×λDU×λDD×MTTR + β×λDU

    Compte TOUS les scénarios DGF (y compris DU→DD), contrairement à IEC.
    À utiliser si on veut une borne supérieure conservatrice.
    Source : Rausand & Lundteigen, NTNU RAMS Group Ch9 slides 24-26.
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
    IEC 61508-6 §B.3.3.2.5 — PFH 2oo3.

    Source : 11_IEC_FORMULAS_COMPLETE.md §B.3.3.2.5 :
      PFH_G(2oo3) = 6 × [(1-β_D)λ_DD + (1-β)λ_DU] × (1-β)λ_DU × t_CE + β×λ_DU

    t_CE = (λ_DU/λ_D)×(T1/2+MRT) + (λ_DD/λ_D)×MTTR  (§B.3.2.2)

    CORRECTION : version précédente utilisait 6×ldu²×T1 (≈ t_CE pour DC=0% seulement).
    Erreur constatée : +99% à DC=0%, +38% à DC=90%/β=2% (isolé sur cas β=0%).
    v3.1 : t_CE utilise (T1/2+MRT) conformément à IEC §B.3.2.2.
    """
    ldu = p.lambda_DU * (1 - p.beta)
    ldd = p.lambda_DD * (1 - p.beta_D)
    lD = p.lambda_DU + p.lambda_DD
    MRT = getattr(p, 'MRT', p.MTTR)
    if lD > 0:
        tce = (p.lambda_DU / lD) * (p.T1 / 2.0 + MRT) + (p.lambda_DD / lD) * p.MTTR
    else:
        tce = 0.0
    pfh_indep = 6.0 * (ldd + ldu) * ldu * tce
    pfh_ccf = p.beta * p.lambda_DU
    return pfh_indep + pfh_ccf


def pfh_1oo3(p: SubsystemParams) -> float:
    """
    IEC 61508-6 §B.3.3.2.6 — PFH 1oo3.

    Source : 11_IEC_FORMULAS_COMPLETE.md §B.3.3.2.6 :
      PFH_G(1oo3) = 6 × [(1-β_D)λ_DD + (1-β)λ_DU]² × (1-β)λ_DU × t_CE × t_GE + β×λ_DU

    t_CE = (λ_DU/λ_D)×(T1/2+MRT) + (λ_DD/λ_D)×MTTR  (§B.3.2.2)
    t_GE = (λ_DU/λ_D)×(T1/3+MRT) + (λ_DD/λ_D)×MTTR  (§B.3.2.2.2)

    CORRECTION : version précédente utilisait 3×ldu³×T1².
    Impact pratique masqué par β×λ_DU dès β≥2%, mais formule structurellement fausse.
    v3.1 : t_CE=(λDU/λD)×(T1/2+MRT)+..., t_GE=(λDU/λD)×(T1/3+MRT)+... (IEC §B.3.2.2)
    """
    ldu = p.lambda_DU * (1 - p.beta)
    ldd = p.lambda_DD * (1 - p.beta_D)
    lD = p.lambda_DU + p.lambda_DD
    MRT = getattr(p, 'MRT', p.MTTR)
    if lD > 0:
        tce = (p.lambda_DU / lD) * (p.T1 / 2.0 + MRT) + (p.lambda_DD / lD) * p.MTTR
        tge = (p.lambda_DU / lD) * (p.T1 / 3.0 + MRT) + (p.lambda_DD / lD) * p.MTTR
    else:
        tce = tge = 0.0
    pfh_indep = 6.0 * (ldd + ldu) ** 2 * ldu * tce * tge
    pfh_ccf = p.beta * p.lambda_DU
    return pfh_indep + pfh_ccf


# ── PFH CORRIGÉ (Omeiri/Innal 2021) — MD 22_PFH_CORRECTED ──────────────

def pfh_1oo2_corrected(p: SubsystemParams) -> float:
    """
    PFH 1oo2 corrigé — Omeiri, Innal, Liu (2021) Eq.17.
    Source : JESA Vol.54 No.6 pp.871-879 (open access iieta.org).
    
    Contient le terme DU→DD manquant dans l'IEC 61508.
    Δ = 2×(1-β)×λ_DU × (T1/2 + MRT) × λ_DD
    """
    ldu = (1 - p.beta) * p.lambda_DU
    ldd = (1 - p.beta_D) * p.lambda_DD
    ld_ind = ldu + ldd
    MRT = p.T1 / 2.0

    # t_CE1 avec taux indépendants (Omeiri Eq.18)
    if ld_ind > 0:
        t_CE1 = (ldu / ld_ind) * (p.T1 / 2.0 + MRT) + (ldd / ld_ind) * p.MTTR
    else:
        t_CE1 = p.T1 / 2.0

    pfh_main = 2.0 * (ldd + ldu) * t_CE1 * ldu
    pfh_ccf = p.beta * p.lambda_DU
    # TERME MANQUANT IEC (Omeiri Eq.17, 3ème terme)
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
    MRT = p.T1 / 2.0

    if ld_ind > 0:
        t_CE1 = (ldu / ld_ind) * (p.T1 / 2.0 + MRT) + (ldd / ld_ind) * p.MTTR
    else:
        t_CE1 = p.T1 / 2.0

    pfh_main = 6.0 * (ldd + ldu) * t_CE1 * ldu
    pfh_ccf = p.beta * p.lambda_DU
    # TERME MANQUANT #1 (Omeiri Eq.22 — critique)
    pfh_missing_1 = 6.0 * ldu * (p.T1 / 2.0 + MRT) * ldd
    # TERME MANQUANT #2 (négligeable mais inclus pour exactitude)
    pfh_missing_2 = 3.0 * (ldd * p.MTTR + ldu * (p.T1 / 2.0 + MRT)) * p.beta * p.lambda_DU
    return pfh_main + pfh_ccf + pfh_missing_1 + pfh_missing_2


def pfh_arch(p: SubsystemParams, arch: Optional[str] = None) -> float:
    """Dispatch PFH (IEC standard)."""
    a = arch or p.architecture
    dispatch = {"1oo1": pfh_1oo1, "1oo2": pfh_1oo2, "2oo2": pfh_2oo2,
                "2oo3": pfh_2oo3, "1oo3": pfh_1oo3}
    fn = dispatch.get(a, pfh_1oo1)
    return fn(p)


def pfh_arch_corrected(p: SubsystemParams, arch: Optional[str] = None) -> float:
    """Dispatch PFH corrigé (Omeiri/Innal 2021 + NTNU Ch.9)."""
    a = arch or p.architecture
    dispatch = {"1oo1": pfh_1oo1, "1oo2": pfh_1oo2_corrected,
                "2oo2": pfh_2oo2, "2oo3": pfh_2oo3_corrected, "1oo3": pfh_1oo3}
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


def markov_required(p: SubsystemParams, threshold: float = 0.1) -> bool:
    """True si Markov exact recommandé (λ×T1 > threshold)."""
    return lambda_T1_product(p) > threshold


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
    """Contrainte architecturale Route 1H (IEC 61508-2 §7.4.3.1)."""
    lambda_D = p.lambda_DU + p.lambda_DD
    lambda_total = lambda_D + p.lambda_S
    sff = (p.lambda_S + p.lambda_DD) / lambda_total if lambda_total > 0 else 0.0
    hft_map = {"1oo1": 0, "2oo2": 0, "1oo2": 1, "1oo2D": 1, "2oo3": 1, "1oo3": 2}
    hft = hft_map.get(arch, 0)
    if hft == 0:
        sil_max = 1 if sff < 0.60 else (2 if sff < 0.90 else 3)
    elif hft == 1:
        sil_max = 2 if sff < 0.60 else (3 if sff < 0.90 else 4)
    else:
        sil_max = 4
    return {"sff": sff, "hft": hft, "sil_max_arch": sil_max}
