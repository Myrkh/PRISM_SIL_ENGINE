"""
PRISM SIL Engine — Module d'analyse des domaines de validité IEC 61508
Fichier : error_surface.py
Version : PRISM v0.5.0 (Sprint D)

OBJECTIF
─────────
Quantifier systématiquement l'erreur entre les formules IEC 61508-6 simplifiées
et la référence exacte (Markov CTMC Time-Domain) sur la grille (λ×T1, DC).

CONTRIBUTION ORIGINALE
───────────────────────
Ce module constitue la première carte d'erreur utilisant le Markov Time-Domain
(DU absorbant) comme référence exacte. Les analyses précédentes (Chebila &
Innal 2015, JLPPI 34:167-176) utilisaient leurs propres formules analytiques
comme référence, qui sous-estimaient elles-mêmes pour N-M≥2 (Bug #11, v0.5.0).

DEUX SOURCES D'ERREUR IDENTIFIÉES ET SÉPARÉES
───────────────────────────────────────────────
Source A — Termes manquants IEC (Omeiri 2021) :
    Visible même pour λ×T1 petit. Dépend fortement de DC.
    Exemple : 1oo2 DC=0.9 λT1=0.01 → δ_IEC = −30%
    Correction : formules Omeiri (pfh_1oo2_corrected, pfh_2oo3_corrected)

Source B — Non-linéarité Taylor (λ×T1 >> 0) :
    Visible même pour DC=0. Dépend de l'architecture.
    Erreur ∝ (λ×T1)^(N-M)
    Exemple : 1oo3 DC=0 λT1=0.5 → δ_IEC = +106%
    Correction : seul le Markov TD est exact pour tout λ×T1

LOIS ASYMPTOTIQUES (DC=0, β=0) :
    δ_IEC_1oo1 ≈ +λT1/2      (ordre 1)
    δ_IEC_1oo2 ≈ +(λT1)²/2   (ordre 2)
    δ_IEC_2oo3 ≈ +(λT1)²/2   (ordre 2)
    δ_IEC_1oo3 ≈ +(λT1)³/6   (ordre 3, PLUS la correction Bug#11 4/3)

SEUILS DE BASCULE IEC → MARKOV
────────────────────────────────
Seuil PRISM actuel (empirique) : λ×T1 > 0.1 (identique pour toutes architectures)
Seuils calculés ici (fondés) par architecture ET niveau d'erreur acceptable :
    Erreur acceptable 1%  : λT1 seuil varie de 0.02 (1oo3) à 0.14 (1oo1)
    Erreur acceptable 5%  : λT1 seuil varie de 0.05 (1oo3) à 0.32 (1oo1)
    Erreur acceptable 10% : λT1 seuil varie de 0.07 (1oo3) à 0.45 (1oo1)

SOURCES
────────
IEC 61508-6:2010 Annexe B §B.3.3 — formules PFH architectures kooN
Omeiri, Innal, Liu (2021) JESA 54(6):871-879 — corrections termes manquants
Chebila & Innal (2015) JLPPI 34:167-176 — analyse domaines de validité (référence antérieure)
PRISM v0.5.0 Bug #11 — loi 2^p/(p+1) TD vs SS, TD comme référence exacte
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass, field
from typing import Optional

from .formulas import (
    SubsystemParams, sil_from_pfh,
    pfh_1oo1, pfh_1oo2, pfh_2oo3, pfh_1oo3,
    pfh_1oo2_corrected, pfh_2oo3_corrected, pfh_1oo3_corrected,
)
from .markov import compute_exact


# ─────────────────────────────────────────────────────────────────────────────
# 1. STRUCTURES DE DONNÉES
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class GridPoint:
    """Un point de la grille d'erreur."""
    lambda_T1: float          # λ_D × T1 (produit adimensionnel)
    DC: float                 # Couverture diagnostique [0, 1)
    architecture: str         # "1oo1", "1oo2", "2oo3", "1oo3"
    pfh_iec: float            # PFH formule IEC standard
    pfh_omeiri: float         # PFH formule Omeiri corrigée
    pfh_td: float             # PFH Markov Time-Domain (référence exacte)
    error_iec_pct: float      # (pfh_iec / pfh_td - 1) × 100  [%]
    error_omeiri_pct: float   # (pfh_omeiri / pfh_td - 1) × 100  [%]


@dataclass
class ErrorSurfaceResult:
    """
    Résultat complet d'une analyse de surface d'erreur.

    Contient la grille complète + les seuils de bascule calculés.
    """
    architecture: str
    N: int
    M: int
    beta: float
    MTTR: float
    T1_ref: float                    # T1 utilisé pour la normalisation

    grid: list[GridPoint] = field(default_factory=list)

    # Seuils de bascule (λ×T1 à partir duquel |δ_IEC| > seuil)
    # Calculés pour DC=0 (source B uniquement, borne inférieure)
    threshold_1pct_dc0: float = float('inf')
    threshold_5pct_dc0: float = float('inf')
    threshold_10pct_dc0: float = float('inf')

    # Seuils worst-case (sur tout DC)
    threshold_1pct_worst: float = float('inf')
    threshold_5pct_worst: float = float('inf')
    threshold_10pct_worst: float = float('inf')

    # Recommandation finale
    recommended_threshold: float = 0.1   # seuil recommandé pour bascule IEC→Markov
    recommended_basis: str = ""           # justification du seuil


# ─────────────────────────────────────────────────────────────────────────────
# 2. FONCTIONS DE CALCUL D'UN POINT
# ─────────────────────────────────────────────────────────────────────────────

def _pfh_iec_dispatch(arch: str):
    """Retourne la fonction PFH IEC standard pour l'architecture donnée."""
    return {"1oo1": pfh_1oo1, "1oo2": pfh_1oo2,
            "2oo3": pfh_2oo3, "1oo3": pfh_1oo3}[arch]


def _pfh_omeiri_dispatch(arch: str):
    """Retourne la fonction PFH Omeiri corrigée pour l'architecture donnée."""
    return {"1oo1": pfh_1oo1,              # 1oo1 n'a pas de correction Omeiri
            "1oo2": pfh_1oo2_corrected,
            "2oo3": pfh_2oo3_corrected,
            "1oo3": pfh_1oo3_corrected}[arch]


def compute_grid_point(
    lambda_T1: float,
    DC: float,
    arch: str,
    N: int,
    M: int,
    T1: float = 8760.0,
    beta: float = 0.0,
    MTTR: float = 8.0,
    MTTR_DU: float = 8.0,
) -> GridPoint:
    """
    Calcule un point (λ×T1, DC) de la surface d'erreur.

    Paramètres
    ──────────
    lambda_T1 : produit λ_D × T1 (adimensionnel, axe X de la carte)
    DC        : couverture diagnostique [0, 1) (axe Y de la carte)
    arch      : "1oo1", "1oo2", "2oo3", "1oo3"
    N, M      : paramètres kooN (N canaux, M requis)
    T1        : période de proof test [h] (uniquement pour MTTR/T1 ratio)
    beta      : facteur CCF
    MTTR      : temps de réparation DD [h]
    MTTR_DU   : temps de réparation DU [h]

    Retourne
    ────────
    GridPoint avec IEC, Omeiri, TD et erreurs relatives.

    Notes
    ─────
    λ_D × T1 est le seul paramètre qui gouverne la non-linéarité (Source B).
    DC gouverne les termes manquants (Source A).
    Les deux sont indépendants → la grille 2D capture l'espace complet.
    """
    lD = lambda_T1 / T1
    ldu = (1 - DC) * lD
    ldd = DC * lD

    p = SubsystemParams(
        lambda_DU=ldu, lambda_DD=ldd,
        MTTR=MTTR, MTTR_DU=MTTR_DU,
        T1=T1, beta=beta, beta_D=beta,
        architecture=arch, M=M, N=N,
    )

    fn_iec    = _pfh_iec_dispatch(arch)
    fn_omeiri = _pfh_omeiri_dispatch(arch)

    pfh_iec    = fn_iec(p)
    pfh_omeiri = fn_omeiri(p)

    # Référence exacte : Markov TD (sélection automatique SS vs TD selon N-M)
    r = compute_exact(p, mode="high_demand")
    pfh_td = r["pfh"]

    # Erreurs relatives (signe : + = IEC surestime, - = IEC sous-estime)
    err_iec    = (pfh_iec    / pfh_td - 1.0) * 100.0 if pfh_td > 0 else 0.0
    err_omeiri = (pfh_omeiri / pfh_td - 1.0) * 100.0 if pfh_td > 0 else 0.0

    return GridPoint(
        lambda_T1=lambda_T1, DC=DC, architecture=arch,
        pfh_iec=pfh_iec, pfh_omeiri=pfh_omeiri, pfh_td=pfh_td,
        error_iec_pct=err_iec, error_omeiri_pct=err_omeiri,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 3. CALCUL DE LA SURFACE COMPLÈTE
# ─────────────────────────────────────────────────────────────────────────────

def compute_error_surface(
    arch: str,
    N: int,
    M: int,
    lambda_T1_range: Optional[np.ndarray] = None,
    DC_range: Optional[np.ndarray] = None,
    T1: float = 8760.0,
    beta: float = 0.0,
    MTTR: float = 8.0,
    MTTR_DU: float = 8.0,
    progress: bool = True,
) -> ErrorSurfaceResult:
    """
    Calcule la surface d'erreur IEC vs Markov TD sur la grille (λ×T1, DC).

    La grille par défaut couvre :
        λ×T1 ∈ [0.001, 5.0]  — 30 points log-espacés
        DC   ∈ [0.0, 0.99]   — 20 points linéaires

    Chaque point calcule :
        δ_IEC(λT1, DC) = (PFH_IEC / PFH_TD - 1) × 100  [%]
        δ_Omeiri(λT1, DC) = (PFH_Omeiri / PFH_TD - 1) × 100  [%]

    Sources
    ───────
    IEC 61508-6:2010 Annexe B §B.3.3 : formules PFH simplifiées
    Omeiri et al. (2021) JESA 54(6) : corrections analytiques
    PRISM v0.5.0 Bug#11 : TD comme référence exacte
    Chebila & Innal (2015) JLPPI 34:167-176 : domaines validité (précédent partiel)
    """
    if lambda_T1_range is None:
        lambda_T1_range = np.logspace(-3, np.log10(5.0), 30)
    if DC_range is None:
        DC_range = np.linspace(0.0, 0.99, 20)

    result = ErrorSurfaceResult(
        architecture=arch, N=N, M=M,
        beta=beta, MTTR=MTTR, T1_ref=T1,
    )

    total = len(lambda_T1_range) * len(DC_range)
    done = 0

    for lT1 in lambda_T1_range:
        for DC in DC_range:
            pt = compute_grid_point(
                lambda_T1=lT1, DC=DC, arch=arch, N=N, M=M,
                T1=T1, beta=beta, MTTR=MTTR, MTTR_DU=MTTR_DU,
            )
            result.grid.append(pt)
            done += 1
            if progress and done % 50 == 0:
                pct = done / total * 100
                print(f"  {arch} : {done}/{total} points ({pct:.0f}%)", flush=True)

    # Calcul des seuils de bascule
    _compute_thresholds(result, lambda_T1_range, DC_range)
    return result


def _compute_thresholds(
    result: ErrorSurfaceResult,
    lambda_T1_range: np.ndarray,
    DC_range: np.ndarray,
) -> None:
    """
    Extrait les seuils λ×T1 à partir desquels |δ_IEC| dépasse 1%, 5%, 10%.

    Deux seuils calculés :
    - DC=0 (source B uniquement, borne basse)
    - worst-case sur tout DC (borne haute)

    Source : définition PRISM Sprint D — première quantification sur grille TD.
    """
    # Filtrer points DC=0 (premier DC de la grille)
    dc0 = DC_range[0]
    pts_dc0  = [p for p in result.grid if abs(p.DC - dc0) < 1e-6]
    pts_all  = result.grid

    for threshold_pct, attr_dc0, attr_worst in [
        (1.0,  "threshold_1pct_dc0",  "threshold_1pct_worst"),
        (5.0,  "threshold_5pct_dc0",  "threshold_5pct_worst"),
        (10.0, "threshold_10pct_dc0", "threshold_10pct_worst"),
    ]:
        # DC=0 : premier λT1 où |δ_IEC| > threshold
        for pt in sorted(pts_dc0, key=lambda x: x.lambda_T1):
            if abs(pt.error_iec_pct) > threshold_pct:
                setattr(result, attr_dc0, pt.lambda_T1)
                break

        # Worst-case : minimum des λT1 où |δ_IEC| > threshold, sur tout DC
        lT1_worst = float('inf')
        for lT1 in sorted(set(p.lambda_T1 for p in pts_all)):
            pts_lT1 = [p for p in pts_all if abs(p.lambda_T1 - lT1) < 1e-12]
            if any(abs(p.error_iec_pct) > threshold_pct for p in pts_lT1):
                lT1_worst = min(lT1_worst, lT1)
                break
        setattr(result, attr_worst, lT1_worst)

    # Seuil recommandé = worst-case 5% (compromis précision/performance)
    result.recommended_threshold = result.threshold_5pct_worst
    result.recommended_basis = (
        f"λ×T1 au-delà duquel |δ_IEC| > 5% pour au moins un DC "
        f"(pire cas sur DC ∈ [0, 0.99]). "
        f"Source : PRISM v0.5.0 Sprint D — carte d'erreur IEC vs Markov TD."
    )


# ─────────────────────────────────────────────────────────────────────────────
# 4. RAPPORT TEXTUEL
# ─────────────────────────────────────────────────────────────────────────────

def print_error_report(result: ErrorSurfaceResult) -> None:
    """
    Affiche un rapport structuré de la surface d'erreur.

    Format conçu pour être directement transférable dans un document
    de justification IEC ou un article académique.
    """
    arch = result.architecture
    p = result.N - result.M  # ordre de redondance

    print("=" * 70)
    print(f"RAPPORT D'ERREUR — Architecture {arch} (N={result.N}, M={result.M})")
    print(f"β={result.beta:.1%}, MTTR={result.MTTR}h, T1_ref={result.T1_ref}h")
    print("=" * 70)

    print()
    print("SOURCE B — Non-linéarité Taylor (DC=0, erreur IEC pure)")
    print("─" * 50)
    print("Loi asymptotique : δ_IEC ≈ (λT1)^p × C_arch")
    print(f"  p = N-M = {p}  →  erreur croît comme (λT1)^{p}")
    print()

    # Tableau DC=0
    dc0 = min(set(pt.DC for pt in result.grid))
    pts_dc0 = sorted([pt for pt in result.grid if abs(pt.DC - dc0) < 1e-6],
                     key=lambda x: x.lambda_T1)
    print(f"{'λ×T1':>8}  {'δ_IEC':>8}  {'δ_Omeiri':>10}  Statut")
    for pt in pts_dc0:
        stat = "✓ OK" if abs(pt.error_iec_pct) < 1 else (
               "~ ACCEPTABLE" if abs(pt.error_iec_pct) < 5 else
               "⚠ DÉPASSÉ" if abs(pt.error_iec_pct) < 10 else "✗ INVALIDE")
        print(f"{pt.lambda_T1:>8.4f}  {pt.error_iec_pct:>+7.1f}%  "
              f"{pt.error_omeiri_pct:>+9.1f}%  {stat}")

    print()
    print("SOURCE A — Termes manquants Omeiri (DC variable, λT1=0.01 fixé)")
    print("─" * 50)
    lT1_ref = 0.01
    pts_lT1 = sorted([pt for pt in result.grid
                      if abs(pt.lambda_T1 - min(result.grid,
                             key=lambda x: abs(x.lambda_T1 - lT1_ref)).lambda_T1) < 1e-10],
                     key=lambda x: x.DC)
    print(f"{'DC':>6}  {'δ_IEC':>8}  {'δ_Omeiri':>10}  Source A")
    for pt in pts_lT1:
        source_a = pt.error_iec_pct - pts_lT1[0].error_iec_pct
        print(f"{pt.DC:>6.2f}  {pt.error_iec_pct:>+7.1f}%  "
              f"{pt.error_omeiri_pct:>+9.1f}%  {source_a:+.1f}%")

    print()
    print("SEUILS DE BASCULE IEC → MARKOV")
    print("─" * 50)
    print(f"{'Erreur max':>12}  {'DC=0 (source B)':>18}  {'Worst-case (tout DC)':>22}")
    for thr, dc0_attr, worst_attr in [
        ("1%",  "threshold_1pct_dc0",  "threshold_1pct_worst"),
        ("5%",  "threshold_5pct_dc0",  "threshold_5pct_worst"),
        ("10%", "threshold_10pct_dc0", "threshold_10pct_worst"),
    ]:
        dc0_val   = getattr(result, dc0_attr)
        worst_val = getattr(result, worst_attr)
        dc0_str   = f"λT1 > {dc0_val:.4f}" if dc0_val < float('inf') else "jamais"
        worst_str = f"λT1 > {worst_val:.4f}" if worst_val < float('inf') else "jamais"
        print(f"{thr:>12}  {dc0_str:>18}  {worst_str:>22}")

    print()
    print(f"Seuil PRISM actuel : λT1 > 0.1 (empirique, toutes architectures)")
    print(f"Seuil PRISM v0.5.0 recommandé pour {arch} : λT1 > {result.recommended_threshold:.4f}")
    print(f"Justification : {result.recommended_basis}")

    print()
    print("SOURCES")
    print("─" * 50)
    print("IEC 61508-6:2010 §B.3.3 — formules PFH architectures kooN")
    print("Omeiri, Innal, Liu (2021) JESA 54(6):871-879 — corrections analytiques")
    print("Chebila & Innal (2015) JLPPI 34:167-176 — domaines de validité précédents")
    print("PRISM v0.5.0 Bug #11 — référence TD exacte, loi 2^p/(p+1)")
    print("=" * 70)


# ─────────────────────────────────────────────────────────────────────────────
# 5. COMPARAISON MULTI-ARCHITECTURES
# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
# TABLE DES SEUILS PRÉCOMPILÉS + INTERPOLATION
# ─────────────────────────────────────────────────────────────────────────────

# Seuils de bascule (Omeiri corrigé → Markov TD) précompilés.
# Critère : erreur résiduelle |δ_Omeiri| > 5% (Source B uniquement).
# Conditions de calcul : β=0, MTTR=8h, T1=8760h, grille 300 pts log-espacés.
# Pour β>0, les seuils restent conservatifs (Source B indépendante de β en 1er ordre).
#
# Sources :
#   PRISM v0.5.0 Sprint D — calcul numérique sur grille TD exacte
#   PRISM v0.5.0 Sprint D.5 — correction critère error_omeiri_pct
#   IEC 61508-6 §B.1 — seuil de référence (0.1, unique pour toutes archs)
#
# Lecture :
#   1oo1 DC=0   : seuil 0.101 ≈ seuil IEC §B.1 (cohérent)
#   1oo1 DC=0.9 : seuil 0.986 — 10× plus permissif (IEC §B.1 trop conservatif)
#   2oo3 DC=0   : seuil 0.033 — 3× plus restrictif (IEC §B.1 trop permissif)
#   1oo3        : ∞ — pfh_1oo3_corrected = TD exact, jamais de bascule nécessaire
THRESHOLDS_OMEIRI_5PCT: dict[str, dict[float, float]] = {
    # {arch: {DC_anchor: lambda_T1_seuil}}
    "1oo1": {0.00: 0.1010, 0.60: 0.2512, 0.90: 0.9859, 0.99: float("inf")},
    "1oo2": {0.00: 0.0495, 0.60: 0.1232, 0.90: 0.4976, 0.99: 4.2145},
    "2oo3": {0.00: 0.0332, 0.60: 0.0827, 0.90: 0.3246, 0.99: 2.8284},
    "1oo3": {0.00: float("inf"), 0.60: float("inf"), 0.90: float("inf"), 0.99: float("inf")},
}


def adaptive_iec_threshold(
    arch: str,
    DC: float,
    criterion_pct: float = 5.0,
) -> float:
    """
    Seuil λ×T1 adaptatif (architecture + DC) au-delà duquel le Markov TD est requis.

    Interpole linéairement dans la table THRESHOLDS_OMEIRI_5PCT pour les DC
    intermédiaires. Les valeurs sont conservatrices (β=0 worst-case pour Source B).

    Pour criterion_pct = 5.0 (défaut) : utilise la table précompilée directement.
    Pour criterion_pct ≠ 5.0 : recalcul numérique à la demande (coûteux, ~2 min).

    Paramètres
    ──────────
    arch         : "1oo1", "1oo2", "2oo3", "1oo3"
    DC           : couverture diagnostique [0, 1)
    criterion_pct: erreur résiduelle Omeiri max acceptable [%] (défaut 5%)

    Retourne
    ────────
    float : λ×T1 seuil. Au-delà, utiliser Markov TD.
            float('inf') si la formule corrigée est toujours exacte (1oo3).

    Sources
    ───────
    Table THRESHOLDS_OMEIRI_5PCT — PRISM v0.5.0 Sprint D (calcul numérique TD)
    Interpolation linéaire par morceaux en DC — approximation conservative
    IEC 61508-6 §B.1 — seuil historique (0.1) superseded par cette fonction
    Chebila & Innal (2015) JLPPI 34:167-176 — concept de domaine de validité
    """
    if criterion_pct != 5.0:
        # Recalcul exact à la demande (rare, pour research uniquement)
        import numpy as np
        thr = find_crossover_thresholds(
            error_limit_pct=criterion_pct,
            DC_values=[0.0, 0.6, 0.9, 0.99],
        )
        anchors = thr.get(arch, {})
    else:
        anchors = THRESHOLDS_OMEIRI_5PCT.get(arch, {})

    if not anchors:
        # Architecture inconnue → seuil conservatif IEC §B.1
        return 0.1

    # Interpolation linéaire par morceaux sur DC
    dc_keys = sorted(anchors.keys())
    vals = [anchors[k] for k in dc_keys]

    # Extrapolation basse (DC < dc_keys[0]) → valeur la plus conservatrice
    if DC <= dc_keys[0]:
        return vals[0]
    # Extrapolation haute (DC >= dc_keys[-1]) → valeur la plus permissive
    if DC >= dc_keys[-1]:
        return vals[-1]

    # Interpolation linéaire entre les deux points encadrants
    for i in range(len(dc_keys) - 1):
        if dc_keys[i] <= DC < dc_keys[i + 1]:
            dc_lo, dc_hi = dc_keys[i], dc_keys[i + 1]
            v_lo, v_hi = vals[i], vals[i + 1]
            # Gérer inf (DC=0.99 pour 1oo1)
            if v_hi == float("inf"):
                return float("inf")
            t = (DC - dc_lo) / (dc_hi - dc_lo)
            return v_lo + t * (v_hi - v_lo)

    return vals[-1]



def compare_architectures(
    lambda_T1_range: Optional[np.ndarray] = None,
    DC: float = 0.0,
    beta: float = 0.0,
    T1: float = 8760.0,
    MTTR: float = 8.0,
) -> dict:
    """
    Calcule et compare les erreurs IEC pour toutes les architectures standard
    sur un axe λ×T1, à DC fixé.

    Utilisé pour générer les courbes iso-architecture (Figure 1 de la publication).

    Retourne
    ────────
    dict {arch: {'lambda_T1': [...], 'error_iec': [...], 'error_omeiri': [...]}}

    Source : PRISM v0.5.0 Sprint D — première comparaison multi-architecture
             avec TD comme référence unique.
    """
    if lambda_T1_range is None:
        lambda_T1_range = np.logspace(-3, np.log10(5.0), 50)

    architectures = [
        ("1oo1", 1, 1),
        ("1oo2", 2, 1),
        ("2oo3", 3, 2),
        ("1oo3", 3, 1),
    ]

    results = {}
    for arch, N, M in architectures:
        errs_iec    = []
        errs_omeiri = []
        for lT1 in lambda_T1_range:
            pt = compute_grid_point(
                lambda_T1=lT1, DC=DC, arch=arch, N=N, M=M,
                T1=T1, beta=beta, MTTR=MTTR,
            )
            errs_iec.append(pt.error_iec_pct)
            errs_omeiri.append(pt.error_omeiri_pct)

        results[arch] = {
            "lambda_T1":    lambda_T1_range.tolist(),
            "error_iec":    errs_iec,
            "error_omeiri": errs_omeiri,
            "N": N, "M": M,
            "p": N - M,
        }

    return results


def find_crossover_thresholds(
    error_limit_pct: float = 5.0,
    DC_values: Optional[list] = None,
    lambda_T1_range: Optional[np.ndarray] = None,
    beta: float = 0.0,
    T1: float = 8760.0,
    MTTR: float = 8.0,
) -> dict:
    """
    Calcule les seuils de bascule IEC→Markov pour chaque architecture
    et chaque valeur de DC.

    Résultat : une table {arch: {DC: lambda_T1_seuil}} prête à être
    intégrée dans compute_exact() comme critère de bascule adaptatif.

    Justification du seuil adaptatif (vs seuil unique 0.1) :
        Le seuil unique 0.1 est trop conservatif pour 1oo1 (seuil réel ≈ 0.45)
        et trop permissif pour 1oo3 (seuil réel ≈ 0.05 à DC=0.9).
        Un seuil adaptatif par architecture améliore la performance sans perte
        de précision.

    Sources :
        PRISM v0.5.0 Sprint D — calcul numérique sur grille TD
        Chebila & Innal (2015) — concept de domaine de validité (adapté)
        IEC 61508-6 §B.1 — recommandation générale λ×T1 < 0.1
    """
    if DC_values is None:
        DC_values = [0.0, 0.6, 0.9, 0.99]
    if lambda_T1_range is None:
        lambda_T1_range = np.logspace(-3, np.log10(5.0), 100)

    architectures = [
        ("1oo1", 1, 1),
        ("1oo2", 2, 1),
        ("2oo3", 3, 2),
        ("1oo3", 3, 1),
    ]

    thresholds = {}
    for arch, N, M in architectures:
        thresholds[arch] = {}
        for DC in DC_values:
            seuil = float('inf')
            for lT1 in lambda_T1_range:
                pt = compute_grid_point(
                    lambda_T1=lT1, DC=DC, arch=arch, N=N, M=M,
                    T1=T1, beta=beta, MTTR=MTTR,
                )
                # CRITÈRE SOURCE B : erreur résiduelle Omeiri vs TD (pas IEC brut)
                if abs(pt.error_omeiri_pct) > error_limit_pct:
                    seuil = lT1
                    break
            thresholds[arch][DC] = seuil

    return thresholds
