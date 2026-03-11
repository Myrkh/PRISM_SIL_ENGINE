"""
PRISM Engine — Extensions avancées
===================================
Fonctionnalités manquantes pour égaler / dépasser GRIF Workshop.

Sources :
  [1] NTNU Ch9 slides 22+34 (errata) — PFH koon généralisé
  [2] IEC 61508-6 Annexe B §B.3.2.2 — PFD(t) instantané
  [3] IEC 61508-6 Annexe D (via 11_IEC_FORMULAS_COMPLETE.md) — MGL CCF
  [4] NTNU Architectural Constraints slides Route 1H (lundteig.folk.ntnu.no)
  [5] NTNU Ch8 §"Including Demand Duration" — PFD demand mode
  [6] formulas.py markov_required() — routage auto
"""

from __future__ import annotations
import math
from typing import Optional
import numpy as np
from dataclasses import dataclass, field

from .formulas import SubsystemParams, pfd_arch, pfh_arch, sil_from_pfd, sil_from_pfh


# ─────────────────────────────────────────────────────────────────────────────
# 1. PFH koon GÉNÉRALISÉ
# Source : NTNU Ch9 slide 34 (errata formula 8.48)
#
# PFH_koon = [∏(i=1..n-k)(n-i+1)] × lD_eff^(n-k) × (1-β)λDU × [∏(i=2..n-k) tGEi] × tCE + β×λDU
#
# où tGEi = (λDU/λD)×(T1/(n-k+2-i) + MRT) + (λDD/λD)×MTTR
#     tCE  = (λDU/λD)×(T1/2 + MRT) + (λDD/λD)×MTTR
#     lD_eff = (1-β_D)×λDD + (1-β)×λDU
#
# Vérification :
#   koon=1oo2 → n-k=1 : ∏(2)×lD_eff×lDU×tCE = 2×lD_eff×lDU×tCE ✓
#   koon=2oo3 → n-k=1 : ∏(3)×lD_eff×lDU×tCE = 3×lD_eff×lDU×tCE  ← MAIS spec dit 6
#   NOTE : le facteur 2 vient du choix du DERNIER canal qui tombe — combinatoire C(n-k,1)=n-k+1... 
#   La formule exacte NTNU slide 34 est (après lecture attentive) :
#   PFH_koon = (n-k+1)! × C(n,1) × lD_eff^(n-k) × lDU × tCE × ∏ tGEi + β×λDU
#   Pour 2oo3 : (n-k+1)!=2!=2, C(3,1)×... → 6 total
#   Utilisons la vérification numérique directe de chaque cas.
# ─────────────────────────────────────────────────────────────────────────────

def pfh_moon(p: SubsystemParams, k: int, n: int) -> float:
    """
    PFH pour architecture koon (k-out-of-n) généralisé.

    Source : IEC 61508-6 §B.3.3.2 + NTNU Ch9 (formule unifiée vérifiée) :

      PFH_koon = coeff × lD_eff^r × lDU × ∏(tGE_i, i=1..r) + β×λDU

      coeff = n! / (k-1)!                        [coefficient combinatoire]
      r     = n - k                               [ordre de redondance]
      tGE_i = (λDU/λD)×(T1/(i+1) + MRT) + (λDD/λD)×MTTR   [diviseurs : 2, 3, ..., r+1]
      lD_eff = (1-β_D)×λDD + (1-β)×λDU
      lDU    = (1-β)×λDU

    Vérifications IEC (DC=0, β→0) :
      1oo1 : coeff=1, r=0 → λDU ✓
      1oo2 : coeff=2, r=1, divs=[2] → 2×lD_eff×lDU×t(2) ✓
      2oo3 : coeff=6, r=1, divs=[2] → 6×lD_eff×lDU×t(2) ✓
      1oo3 : coeff=6, r=2, divs=[2,3] → 6×lD_eff²×lDU×t(2)×t(3) ✓

    Architectures nouvelles (non IEC, calculées par extension) :
      1oo4 : coeff=24, r=3, divs=[2,3,4]
      2oo4 : coeff=24, r=2, divs=[2,3]
      3oo4 : coeff=12, r=1, divs=[2]
    """
    import math as _math

    if k < 1 or k > n or n < 1:
        raise ValueError(f"Architecture invalide : {k}oo{n}")
    if k == 1 and n == 1:
        return p.lambda_DU

    lDU   = p.lambda_DU
    lDD   = p.lambda_DD
    lD    = lDU + lDD
    MRT   = p.MTTR_DU  # Mean Repair Time DU (Omeiri 2021 §2.2, Bug #8a fix v0.4.2)
    beta  = p.beta
    betaD = p.beta_D

    ldu    = (1.0 - beta)  * lDU
    ldd    = (1.0 - betaD) * lDD
    lD_eff = ldd + ldu

    r = n - k   # ordre de redondance (0 = série, ≥1 = redondant)

    # Cas série : k == n → tout composant défaillant = système défaillant
    if r == 0:
        # PFH_serie = sum(λDU_i) = n×λDU pour composants identiques
        return n * lDU

    if lD <= 0:
        return beta * lDU

    # Coefficient combinatoire : n! / (k-1)!
    coeff = _math.factorial(n) // _math.factorial(k - 1)

    # Facteurs de temps : tGE_i = (λDU/λD)×(T1/(i+1)+MRT) + (λDD/λD)×MTTR
    # pour i = 1, 2, ..., r  →  diviseurs = 2, 3, ..., r+1
    def tge(divisor: int) -> float:
        return (lDU / lD) * (p.T1 / divisor + MRT) + (lDD / lD) * p.MTTR

    t_product = 1.0
    for i in range(1, r + 1):          # diviseurs 2..r+1
        t_product *= tge(i + 1)

    pfh_indep = coeff * (lD_eff ** r) * ldu * t_product
    pfh_ccf   = beta * lDU
    return pfh_indep + pfh_ccf


def pfh_moon_arch(p: SubsystemParams, arch: str) -> float:
    """
    Dispatch PFH par nom d'architecture (1oo1, 1oo2, 2oo3, 2oo4, 1oo3, 1oo4, ...).
    """
    table = {
        "1oo1": (1, 1), "1oo2": (1, 2), "2oo2": (2, 2),
        "1oo3": (1, 3), "2oo3": (2, 3), "3oo3": (3, 3),
        "1oo4": (1, 4), "2oo4": (2, 4), "3oo4": (3, 4), "4oo4": (4, 4),
    }
    if arch not in table:
        raise ValueError(f"Architecture inconnue: {arch}")
    k, n = table[arch]
    return pfh_moon(p, k, n)


# ─────────────────────────────────────────────────────────────────────────────
# 2. PFD(t) INSTANTANÉ — courbe en dents de scie
# Source : IEC 61508-6 §B.3.2.2 + NTNU Ch8 slides
#
# Pour 1oo1 :
#   PFD(t) = λDU×t + λDD×MTTR              (montée linéaire)
#   Remise à zéro à t=T1 (essai périodique)
#
# Pour MooN : approximation analytique à partir de PFDavg(T1_effective)
#   En utilisant l'expression exacte IEC avec T1 remplacé par 2t
#   (car t_CE = T1/2 → à l'instant t, la "dent" monte avec t/2 comme temps effectif)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class PFDCurveResult:
    """Résultat de la courbe PFD(t) sur une période."""
    t:          np.ndarray   # vecteur temps [h]
    pfd_t:      np.ndarray   # PFD instantané
    pfd_avg:    float        # moyenne sur T1
    pfd_max:    float        # maximum (fin de période)
    sil_avg:    int          # SIL correspondant à pfd_avg
    sil_min:    int          # SIL au moment le plus défavorable (pfd_max)
    frac_sil:   dict         # fraction du temps dans chaque zone SIL
    n_points:   int = 200


def pfd_instantaneous(p: SubsystemParams, arch: str = "1oo1",
                      n_points: int = 200) -> PFDCurveResult:
    """
    Calcule PFD(t) instantané sur une période T1 (dent de scie).

    Méthode : à l'instant t dans [0, T1], on considère que les canaux
    ont eu un intervalle de test effectif de 2t (pour 1oo1) ou applique
    la formule IEC avec T1_eff = 2t.

    Source : IEC 61508-6 §B.3.2.2 — PFDavg = λD×T1/2 → PFD(t) = λD×t
    Pour architectures redondantes, la forme est plus complexe ; on utilise
    l'approximation : PFD(t) ≈ PFDavg_formula(T1_eff=2t) qui donne exactement
    PFDavg quand intégré de 0 à T1.

    Returns: PFDCurveResult
    """
    T1 = p.T1
    t_arr = np.linspace(0, T1, n_points)
    pfd_arr = np.zeros(n_points)

    for i, t in enumerate(t_arr):
        if t <= 0:
            pfd_arr[i] = 0.0
            continue
        # Créer un sous-système avec T1_eff = 2t (intervalle effectif à l'instant t)
        p_eff = SubsystemParams(
            lambda_DU=p.lambda_DU,
            lambda_DD=p.lambda_DD,
            DC=p.DC,
            beta=p.beta,
            beta_D=p.beta_D,
            MTTR=p.MTTR,
            T1=2.0 * t,   # T1_effectif = 2t → PFDavg avec ce T1 = PFD(t)
        )
        pfd_arr[i] = pfd_arch(p_eff, arch)

    pfd_avg = float(np.trapezoid(pfd_arr, t_arr) / T1)
    pfd_max = float(np.max(pfd_arr))

    # Zones SIL (basse demande)
    sil_bounds = [(1e-5, 1e-4), (1e-4, 1e-3), (1e-3, 1e-2), (1e-2, 1e-1)]
    frac_sil = {}
    for sil_level, (lo, hi) in zip([4, 3, 2, 1], sil_bounds):
        mask = (pfd_arr >= lo) & (pfd_arr < hi)
        frac_sil[f"SIL{sil_level}"] = float(np.sum(mask) / n_points)
    below = pfd_arr < 1e-5
    frac_sil["above_SIL4"] = float(np.sum(below) / n_points)
    above = pfd_arr >= 1e-1
    frac_sil["below_SIL1"] = float(np.sum(above) / n_points)

    return PFDCurveResult(
        t=t_arr, pfd_t=pfd_arr,
        pfd_avg=pfd_avg, pfd_max=pfd_max,
        sil_avg=sil_from_pfd(pfd_avg),
        sil_min=sil_from_pfd(pfd_max),
        frac_sil=frac_sil,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 3. MGL — Multiple Greek Letters CCF Model
# Source : IEC 61508-6 Annexe D (extrait de nos specs 11_IEC_FORMULAS_COMPLETE.md)
#
# Modèle β : tous les CCF = β×λ (ordre 2 seulement)
# Modèle MGL : distingue paires (β), triplets (γ), quadruplets (δ)
#
# Pour un système nooN avec N canaux :
#   λ_CCF_pair    = β × λDU                          (2 canaux simultanés)
#   λ_CCF_triple  = β × γ × λDU                      (3 canaux simultanés)
#   λ_CCF_quad    = β × γ × δ × λDU                  (4 canaux simultanés)
#
# Le PFD corrigé MGL pour 1oo2 :
#   PFD_1oo2_MGL = PFD_indep + β×λDU×(T1/2+MRT)
#   (même formule que β, car paires = β)
#
# Pour 1oo3 et plus, le terme CCF change :
#   PFD_1oo3_MGL ≈ PFD_indep + β×γ×λDU×(T1/2+MRT)  [triplet requis]
#   PFD_2oo3_MGL ≈ PFD_indep + β×λDU×(T1/2+MRT)    [paire suffit]
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class MGLParams:
    """
    Paramètres du modèle MGL (Multiple Greek Letters).
    Source : IEC 61508-6 Annexe D.

    beta  : fraction CCF pour paires  (ordre 2)
    gamma : fraction CCF pour triplets (ordre 3)  — gamma × beta ≤ beta
    delta : fraction CCF pour quad.   (ordre 4)  — delta × gamma × beta ≤ gamma × beta
    """
    beta:  float = 0.02
    gamma: float = 0.5    # γ = P(3 canaux | CCF) / P(2 canaux | CCF)
    delta: float = 0.5    # δ = P(4 canaux | CCF) / P(3 canaux | CCF)

    def ccf_pair(self,   lDU: float) -> float: return self.beta * lDU
    def ccf_triple(self, lDU: float) -> float: return self.beta * self.gamma * lDU
    def ccf_quad(self,   lDU: float) -> float: return self.beta * self.gamma * self.delta * lDU


def pfd_mgl(p: SubsystemParams, arch: str, mgl: MGLParams) -> float:
    """
    PFD avec modèle MGL au lieu du simple β.
    Source : IEC 61508-6 Annexe D + extension logique.

    Pour la plupart des architectures, seul le terme CCF dans la formule IEC change.
    On remplace β×λDU×(T1/2+MRT) par le terme CCF approprié à l'architecture.
    """
    lDU = p.lambda_DU
    lDD = p.lambda_DD
    lD  = lDU + lDD
    MRT  = p.MTTR_DU  # Mean Repair Time DU (Omeiri 2021 §2.2, Bug #8b fix v0.4.2)
    T1   = p.T1
    MTTR = p.MTTR

    # Temps CCF moyen pondéré (même t_CE pour CCF)
    t_ccf = (lDU / lD) * (T1 / 2 + MRT) + (lDD / lD) * MTTR if lD > 0 else T1 / 2

    # Terme indépendant : on utilise β_eff=0 pour isoler
    p_no_ccf = SubsystemParams(
        lambda_DU=lDU, lambda_DD=lDD, DC=p.DC,
        beta=0.0, beta_D=0.0, MTTR=MTTR, T1=T1
    )
    pfd_indep = pfd_arch_extended(p_no_ccf, arch)

    # Terme CCF selon architecture
    arch_to_min_ccf_order = {
        "1oo1": 1, "2oo2": 1,           # 1 seul canal → pas de CCF
        "1oo2": 2, "2oo3": 2,           # paire suffit
        "1oo3": 3, "2oo4": 2, "3oo4": 2,# triplet pour 1oo3
        "1oo4": 4,                        # quadruplet pour 1oo4
    }
    order = arch_to_min_ccf_order.get(arch, 2)

    if order == 1:
        pfd_ccf = 0.0
    elif order == 2:
        pfd_ccf = mgl.ccf_pair(lDU) * t_ccf
    elif order == 3:
        pfd_ccf = mgl.ccf_triple(lDU) * t_ccf
    else:
        pfd_ccf = mgl.ccf_quad(lDU) * t_ccf

    return pfd_indep + pfd_ccf


def pfh_mgl(p: SubsystemParams, k: int, n: int, mgl: MGLParams) -> float:
    """PFH avec MGL — même logique que pfd_mgl."""
    lDU = p.lambda_DU
    p_no_ccf = SubsystemParams(
        lambda_DU=p.lambda_DU, lambda_DD=p.lambda_DD, DC=p.DC,
        beta=0.0, beta_D=0.0, MTTR=p.MTTR, T1=p.T1
    )
    pfh_indep = pfh_moon(p_no_ccf, k, n)

    ccf_order = n - k + 1  # nombre de canaux en CCF pour défaillance groupe
    if ccf_order <= 1:
        pfh_ccf = lDU  # 1oo1 = λDU direct
    elif ccf_order == 2:
        pfh_ccf = mgl.ccf_pair(lDU)
    elif ccf_order == 3:
        pfh_ccf = mgl.ccf_triple(lDU)
    else:
        pfh_ccf = mgl.ccf_quad(lDU)

    return pfh_indep + pfh_ccf


# ─────────────────────────────────────────────────────────────────────────────
# 4. SFF + HFT — Contraintes Architecturales Route 1H
# Source : NTNU Architectural Constraints slides (lundteig.folk.ntnu.no)
#          IEC 61508-2 Table 2 (Route 1H)
#
# SFF = (λS + λDD) / (λS + λDD + λDU)
# HFT = n - k  pour architecture koon
#
# Table Route 1H (SIL max par HFT et SFF) :
#           Type A             Type B
# SFF       HFT=0 HFT=1 HFT=2  HFT=0 HFT=1 HFT=2
# <60%       SIL1  SIL2  SIL3    —    SIL1  SIL2
# 60-90%     SIL2  SIL3  SIL4   SIL1  SIL2  SIL3
# 90-99%     SIL3  SIL4  SIL4   SIL2  SIL3  SIL4
# ≥99%       SIL3  SIL4  SIL4   SIL3  SIL4  SIL4
#
# Route 2H (sans SFF — données terrain disponibles) :
#   HFT=0 → SIL2, HFT=1 → SIL3, HFT=2 → SIL4
# ─────────────────────────────────────────────────────────────────────────────

# Table Route 1H : [SFF_band][type][HFT] → max SIL
_ROUTE_1H = {
    #  SFF band    Type A (HFT=0,1,2)   Type B (HFT=0,1,2)
    "<60":   {"A": [1, 2, 3], "B": [0, 1, 2]},
    "60-90": {"A": [2, 3, 4], "B": [1, 2, 3]},
    "90-99": {"A": [3, 4, 4], "B": [2, 3, 4]},
    ">=99":  {"A": [3, 4, 4], "B": [3, 4, 4]},
}

# Route 2H : HFT → max SIL (sans distinction SFF/type)
_ROUTE_2H = [2, 3, 4]   # index = HFT (0, 1, 2)


@dataclass
class ArchConstraintResult:
    sff:          float    # Safe Failure Fraction
    hft:          int      # Hardware Fault Tolerance (n-k)
    sil_max_1H_A: int      # SIL max Route 1H Type A
    sil_max_1H_B: int      # SIL max Route 1H Type B
    sil_max_2H:   int      # SIL max Route 2H (si données terrain)
    sff_band:     str      # Bande SFF
    warning:      Optional[str] = None


def architectural_constraints(
    lambda_DU: float,
    lambda_DD: float,
    lambda_S:  float,        # taux de défaillance sûre
    k: int, n: int,          # architecture koon
) -> ArchConstraintResult:
    """
    Calcule SFF, HFT et les contraintes architecturales Route 1H et 2H.
    Source : IEC 61508-2 Table 2 (Route 1H) + NTNU Architectural Constraints slides.

    SFF = (λS + λDD) / (λS + λDD + λDU)
    HFT = n - k
    """
    total = lambda_S + lambda_DD + lambda_DU
    sff   = (lambda_S + lambda_DD) / total if total > 0 else 0.0
    hft   = n - k

    # Bande SFF
    if sff < 0.60:
        band = "<60"
    elif sff < 0.90:
        band = "60-90"
    elif sff < 0.99:
        band = "90-99"
    else:
        band = ">=99"

    hft_idx = min(hft, 2)   # table définie jusqu'à HFT=2

    sil_A = _ROUTE_1H[band]["A"][hft_idx]
    sil_B = _ROUTE_1H[band]["B"][hft_idx]
    sil_2H = _ROUTE_2H[hft_idx]

    warn = None
    if hft > 2:
        warn = f"HFT={hft} > 2 : la table Route 1H est définie jusqu'à HFT=2 seulement"

    return ArchConstraintResult(
        sff=sff, hft=hft,
        sil_max_1H_A=sil_A,
        sil_max_1H_B=sil_B,
        sil_max_2H=sil_2H,
        sff_band=band,
        warning=warn,
    )


def sil_achieved(
    pfd_or_pfh: float,
    lambda_DU: float, lambda_DD: float, lambda_S: float,
    k: int, n: int,
    mode: str = "low_demand",  # "low_demand" ou "high_demand"
    component_type: str = "B",  # "A" ou "B"
) -> dict:
    """
    Verdict SIL complet : min(SIL_probabiliste, SIL_architectural).
    Source : NTNU Architectural Constraints slides, principe du maillon faible.

    Retourne un dictionnaire avec :
      - sil_prob      : SIL déduit de PFD/PFH
      - sil_arch_1H   : SIL max selon contrainte architecturale Route 1H
      - sil_arch_2H   : SIL max selon Route 2H
      - sil_final     : min des deux (maillon faible)
      - arch_result   : ArchConstraintResult détaillé
    """
    if mode == "low_demand":
        sil_prob = sil_from_pfd(pfd_or_pfh)
    else:
        sil_prob = sil_from_pfh(pfd_or_pfh)

    arch = architectural_constraints(lambda_DU, lambda_DD, lambda_S, k, n)

    sil_arch = arch.sil_max_1H_A if component_type == "A" else arch.sil_max_1H_B

    return {
        "sil_prob":    sil_prob,
        "sil_arch_1H": sil_arch,
        "sil_arch_2H": arch.sil_max_2H,
        "sil_final":   min(sil_prob, sil_arch) if sil_arch > 0 else 0,
        "arch_result": arch,
        "limiting_factor": "probabilistic" if sil_prob <= sil_arch else "architectural",
    }


# ─────────────────────────────────────────────────────────────────────────────
# 5. DEMAND DURATION — PFD en mode demande avec durée
# Source : NTNU Ch8 slides §"Including Demand Duration" (slide 28)
#
# Modèle : système 1oo1 avec λDU, taux de demande λde, durée demande µde=1/d_dur
#
# Formules approchées (hypothèse λDU << µDU, µde) :
#
#   PFD1 ≈ λDU×µde / [(λde+µde)×(λde+µDU)]   (haute fiabilité, courte durée)
#   PFD2 ≈ λDU / (λde+µDU)                    (si λde << µde)
#
# µDU = 1/(T1/2 + MRT) — taux de "réparation" DU (découverte à l'essai)
# ─────────────────────────────────────────────────────────────────────────────

def pfd_demand_duration(
    lambda_DU: float,
    lambda_de: float,   # taux de demande [h^-1] (ex: 1/8760 = 1 demande/an)
    demand_duration: float,  # durée de la demande [h]
    T1: float,          # intervalle essai [h]
    MRT: float = 8.0,   # mean repair time [h]
) -> dict:
    """
    PFD avec modèle demand duration.
    Source : NTNU Ch8 slides §"Including Demand Duration" (slide 28).

    µde  = 1/demand_duration  (taux de restauration après demande)
    µDU  = 1/(T1/2 + MRT)     (taux de "découverte" DU via essai périodique)

    Deux approximations :
      PFD1 ≈ λDU×µde / [(λde+µde)×(λde+µDU)]   [NTNU slide 28, éq. haute fiabilité]
      PFD2 ≈ λDU / (λde+µDU)                    [si λde << µde, simplifiée]

    La PFD2 (simplifiée) est recommandée si λde << µde.
    """
    mu_de = 1.0 / demand_duration if demand_duration > 0 else 1e10
    mu_DU = 1.0 / (T1 / 2.0 + MRT)

    pfd1 = lambda_DU * mu_de / ((lambda_de + mu_de) * (lambda_de + mu_DU))
    pfd2 = lambda_DU / (lambda_de + mu_DU)

    # Ratio pour savoir quelle formule est pertinente
    ratio = lambda_de / mu_de if mu_de > 0 else 0.0
    recommended = "PFD1" if ratio > 0.1 else "PFD2"

    return {
        "pfd1": pfd1,
        "pfd2": pfd2,
        "pfd_recommended": pfd1 if recommended == "PFD1" else pfd2,
        "formula_used": recommended,
        "mu_de": mu_de,
        "mu_DU": mu_DU,
        "lambda_de_over_mu_de": ratio,
        "note": "PFD1 si λde/µde>0.1, PFD2 si λde<<µde (NTNU Ch8 slide 28)"
    }


# ─────────────────────────────────────────────────────────────────────────────
# 6. ROUTAGE AUTOMATIQUE IEC → Markov
# Source : formulas.markov_required() + logique de routage
# ─────────────────────────────────────────────────────────────────────────────

def route_compute(
    p: SubsystemParams,
    arch: str,
    mode: str = "pfd",   # "pfd" ou "pfh"
    force_markov: bool = False,
) -> dict:
    """
    Routage automatique : formule Omeiri corrigée ou Markov TD exact.

    CORRECTION v0.5.0 Sprint D.5 — trois bugs corrigés :

    Bug A (formule IEC brute) :
        Avant : mode pfh utilisait pfh_arch() = IEC standard.
        Pour DC=0.9, λT1=0.07 : erreur Source A = −89.8%.
        Après : utilise pfh_arch_corrected() = Omeiri corrigé.
        Erreur résiduelle : +0.7% (Source B uniquement).
        Source : Omeiri, Innal, Liu (2021) JESA 54(6) — corrections Source A.

    Bug B (Bug #11 hérité) :
        Avant : chemin Markov appelait solver.compute_pfh() = SS.
        Pour 1oo3 : sous-estimation −25% (loi 2^p/(p+1), p=2).
        Après : appelle compute_exact() qui sélectionne TD pour N-M≥2.
        Source : PRISM v0.5.0 Bug #11 — loi TD/SS = 2^p/(p+1).

    Bug C (seuil empirique λT1 > 0.1 unique) :
        Avant : seuil 0.1 identique pour toutes architectures et DC.
        Trop permissif pour 2oo3 DC=0 (Source B = 7.7% dès λT1=0.05).
        Trop conservatif pour 1oo1 DC=0.9 (erreur 2.5% à λT1=0.5).
        Après : adaptive_iec_threshold(arch, DC) interpolé par morceaux.
        Source : PRISM v0.5.0 Sprint D — table THRESHOLDS_OMEIRI_5PCT.

    Logique de routage (mode pfh) :
        λT1 ≤ seuil(arch, DC) → Omeiri corrigé [rapide, ~0.01 ms]
        λT1 > seuil(arch, DC) → Markov TD exact [précis, ~35 ms pour 1oo3]
        1oo3 → toujours Omeiri/TD (pfh_1oo3_corrected = TD, seuil = ∞)

    Logique de routage (mode pfd) :
        Inchangée — formules PFD n'ont pas de correction Omeiri spécifique.

    Retourne :
        result          : valeur PFD ou PFH
        engine_used     : "IEC_Omeiri_corrected" | "Markov_CTMC_TD" | fallback
        lambda_T1       : produit λD × T1
        threshold_used  : seuil adaptatif utilisé pour la décision
        markov_triggered: True si Markov déclenché
        warning         : message si bascule forcée ou anomalie
    """
    from .formulas import lambda_T1_product, pfh_arch_corrected
    from .error_surface import adaptive_iec_threshold
    from .markov import compute_exact

    lD   = p.lambda_DU + p.lambda_DD
    lT1  = lD * p.T1
    DC_eff = (p.lambda_DD / lD) if lD > 0 else 0.0

    # FIX Bug #2 (conservé) : construire p_arch avec architecture/M/N corrects
    from copy import copy as _copy
    p_arch = _copy(p)
    p_arch.architecture = arch
    if arch and len(arch) >= 3:
        try:
            p_arch.M = int(arch[0])
            p_arch.N = int(arch[-1])
        except (ValueError, IndexError):
            pass

    # Seuil adaptatif (Bug C fix)
    try:
        threshold = adaptive_iec_threshold(arch, DC_eff)
    except Exception:
        threshold = 0.1  # fallback conservatif

    # FIX Bug A : critère de bascule sur le seuil Omeiri vs TD (Source B)
    use_markov = force_markov or (lT1 > threshold and threshold < float("inf"))

    warning = None
    if use_markov and not force_markov:
        warning = (
            f"λD×T1 = {lT1:.3f} > seuil({arch}, DC={DC_eff:.2f}) = {threshold:.4f} "
            f"→ erreur résiduelle Omeiri > 5%. Basculement vers Markov TD."
        )
    elif force_markov:
        warning = f"Markov forcé par l'appelant (force_markov=True)."

    if use_markov:
        try:
            if mode == "pfd":
                # PFD : Markov CTMC exact (SS, exact pour PFD)
                from .markov import MarkovSolver
                solver = MarkovSolver(p_arch)
                result = solver.compute_pfdavg()
                engine = "Markov_CTMC_SS"
            else:
                # FIX Bug B : compute_exact sélectionne TD pour N-M≥2
                r = compute_exact(p_arch, mode="high_demand")
                result = r["pfh"]
                engine = f"Markov_CTMC_TD" if "time-domain" in r.get("method", "") else "Markov_CTMC_SS"
        except Exception as e:
            # Fallback IEC corrigé en cas d'erreur Markov
            warning = (warning or "") + f" [Markov error: {e}] Fallback Omeiri."
            result = pfd_arch(p, arch) if mode == "pfd" else pfh_arch_corrected(p_arch)
            engine = "IEC_Omeiri_corrected_fallback"
    else:
        # FIX Bug A : Omeiri corrigé au lieu de IEC brut
        if mode == "pfd":
            result = pfd_arch(p, arch)
            engine = "IEC_simplified"
        else:
            result = pfh_arch_corrected(p_arch)
            engine = "IEC_Omeiri_corrected"

    return {
        "result":          result,
        "engine_used":     engine,
        "lambda_T1":       lT1,
        "threshold_used":  threshold,
        "markov_triggered": use_markov,
        "warning":         warning,
    }


# ─────────────────────────────────────────────────────────────────────────────
# BONUS : PFD koon GÉNÉRALISÉ (pendant de pfh_moon pour le PFD)
# Source : IEC 61508-6 §B.3.2.2 — extension logique
#
# PFD_koon = coeff × lD_eff^(r+1) × ∏(tGE_i, i=1..r+1) + β×λDU×t_CCF
#
# tGE_i = (λDU/λD)×(T1/(i+1)+MRT) + (λDD/λD)×MTTR  pour i=1..r+1
#   → diviseurs : 2, 3, ..., r+2
# coeff = n! / (k-1)!  (même coefficient que PFH)
#
# Vérifications :
#   1oo1 : coeff=1, r=0, t_CE(div=2) → λD×t_CE ✓
#   1oo2 : coeff=2, r=1, t_CE×t_GE   → 2×lD²×t_CE×t_GE ✓
#   2oo3 : coeff=6, r=1               → 6×lD²×t_CE×t_GE ✓
#   1oo3 : coeff=6, r=2, 3 temps      → 6×lD³×t_CE×t_GE×t_G2E ✓
# ─────────────────────────────────────────────────────────────────────────────

def pfd_koon_generic(p: SubsystemParams, k: int, n: int) -> float:
    """
    PFD pour architecture koon généralisé.
    Source : IEC 61508-6 §B.3.2.2 — extension aux architectures non tabulées.

    PFD_koon = coeff × lD_eff^(r+1) × ∏(tGEi, i=1..r+1) + β×λDU×t_CE
    coeff = n! / (k-1)!,  r = n-k,  diviseurs = [2, 3, ..., r+2]
    """
    import math as _math

    if k < 1 or k > n or n < 1:
        raise ValueError(f"Architecture invalide : {k}oo{n}")

    lDU   = p.lambda_DU
    lDD   = p.lambda_DD
    lD    = lDU + lDD
    MRT   = p.MTTR_DU  # Mean Repair Time DU (Omeiri 2021 §2.2, Bug #8c fix v0.4.2)
    beta  = p.beta
    betaD = p.beta_D

    ldu    = (1.0 - beta)  * lDU
    ldd    = (1.0 - betaD) * lDD
    lD_eff = ldd + ldu

    if lD <= 0:
        return 0.0

    r = n - k

    # Coefficient combinatoire
    coeff = _math.factorial(n) // _math.factorial(k - 1)

    # Facteurs de temps : r+1 termes, diviseurs 2..r+2
    def tge(divisor: int) -> float:
        return (lDU / lD) * (p.T1 / divisor + MRT) + (lDD / lD) * p.MTTR

    t_product = 1.0
    for i in range(1, r + 2):       # i=1..r+1, diviseurs=2..r+2
        t_product *= tge(i + 1)

    # Terme CCF : β×λDU × t_CE (durée moyenne d'exposition CCF)
    t_ccf = tge(2)
    pfd_ccf = beta * lDU * t_ccf

    return coeff * (lD_eff ** (r + 1)) * t_product + pfd_ccf


def pfd_arch_extended(p: SubsystemParams, arch: str) -> float:
    """
    Dispatch PFD étendu : utilise formulas.pfd_arch pour les archs IEC standard,
    pfd_koon_generic pour les nouvelles (1oo4, 2oo4, 3oo4, ...).
    """
    try:
        return pfd_arch(p, arch)
    except ValueError:
        pass
    # Parse arch : "2oo4" → k=2, n=4
    import re
    m = re.match(r'^(\d+)oo(\d+)$', arch)
    if not m:
        raise ValueError(f"Architecture non reconnue : {arch}")
    k, n = int(m.group(1)), int(m.group(2))
    return pfd_koon_generic(p, k, n)
