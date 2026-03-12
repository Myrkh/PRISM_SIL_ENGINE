"""
Weibull λ(t) — PFD/PFH pour SIS avec taux de défaillance non-constant.

Sources primaires :
  - Rausand & Høyland (2004) §B.3 Eq.(B.5–B.8), §10.3–10.4
    Définitions R(t), h(t), MTTF, PFDavg exact.
  - Rogova, Lodewijks & Lundteigen (2017) J.Risk Reliab. 231(4):373-382
    DOI:10.1177/1748006X17694999 — PFDavg/PFH kooN Weibull, formules approx.
  - Wu, Zhang, Lundteigen, Liu, Zheng (2019) RESS 185
    DOI:10.1016/j.ress.2018.11.003 — Formules conditionnelles, vieillissement.
  - Chebila & Innal (2015) JLPPI 34:167-176
    DOI:10.1016/j.jlp.2015.02.002 — PFH_kooN = N·λ·R·PFD_{koo(N-1)}, Eq.(17).

Théorie complète : docs/theory/10_SPRINT_F_WEIBULL.md

NOTE : La référence "Lundteigen & Rausand 2009 RESS 94(7)" citée précédemment
comme source pour Weibull SIS est incorrecte après vérification (ce volume porte
sur les contraintes architecturales IEC, pas sur λ(t) variable).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from scipy import integrate as sci_integrate
from scipy import special as sci_special


# ─────────────────────────────────────────────────────────────────────────────
# Exceptions
# ─────────────────────────────────────────────────────────────────────────────

class WeibullParameterError(ValueError):
    """Paramètre Weibull hors plage physiquement raisonnable."""


class WeibullAgeError(ValueError):
    """Composant trop âgé : R(t_age) < seuil — calcul non fiable."""


# ─────────────────────────────────────────────────────────────────────────────
# Paramètres Weibull
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class WeibullParams:
    """
    Paramétrage Weibull 2-paramètres pour un sous-système SIS.

    Distribution : F(t) = 1 − exp(−(t/η)^β_w)
    Source : Rausand & Høyland (2004) §B.3 Eq.(B.6).

    Attributs
    ---------
    beta_w : float
        Paramètre de forme (shape parameter), sans dimension.
        - β_w < 1 : mortalité infantile (taux décroissant) — rare pour SIS
        - β_w = 1 : exponentielle (IEC 61508 standard)
        - β_w > 1 : usure / vieillissement — cas courant composants mécaniques
        Plage physique acceptable : [0.1, 10.0].
    eta : float
        Vie caractéristique (h). F(η) = 1 − e⁻¹ ≈ 63.2%.
        η > 0 obligatoire.
    mttf : float, optional
        Si fourni, η est calculé automatiquement depuis mttf via
        η = mttf / Γ(1 + 1/β_w). Incompatible avec eta explicite.
    T1 : float
        Intervalle de proof test (h). > 0 obligatoire.
    M : int
        Nombre minimal de canaux fonctionnels requis (vote M-parmi-N).
    N : int
        Nombre total de canaux redondants.
    t_age : float
        Âge du composant en début d'intervalle de proof test (h). ≥ 0.
        - t_age = 0 : composant neuf (AGAN après proof test parfait).
        - t_age > 0 : vieillissement cumulé (hypothèse minimal repair).
    DC : float
        Couverture diagnostique [0, 1). Sépare λ_DU = (1−DC)·h(t)
        et λ_DD = DC·h(t). Sprint F : DC = 0 (complet Sprint G).
    min_survival : float
        Seuil minimal sur R(t_age) en dessous duquel WeibullAgeError est levé.
        Défaut : 1e-4 (composant quasi-certain d'être défaillant).
    """
    beta_w : float          # Paramètre de forme
    T1     : float          # Intervalle proof test [h]
    eta    : float = 0.0    # Vie caractéristique [h] (0 = calculer depuis mttf)
    mttf   : float = 0.0    # MTTF cible [h] (0 = utiliser eta directement)
    M      : int   = 1      # Minimum canaux requis
    N      : int   = 1      # Total canaux
    t_age  : float = 0.0    # Âge courant [h]
    DC     : float = 0.0    # Diagnostic coverage
    min_survival : float = 1e-4  # Seuil R(t_age) minimal

    def __post_init__(self) -> None:
        # ── Validation des ranges ──────────────────────────────────────────
        if not (0.1 <= self.beta_w <= 10.0):
            raise WeibullParameterError(
                f"beta_w={self.beta_w} hors plage [0.1, 10.0]."
            )
        if self.T1 <= 0:
            raise WeibullParameterError(f"T1={self.T1} doit être > 0.")
        if self.t_age < 0:
            raise WeibullParameterError(f"t_age={self.t_age} doit être ≥ 0.")
        if not (0.0 <= self.DC < 1.0):
            raise WeibullParameterError(f"DC={self.DC} doit être dans [0, 1).")
        if self.DC > 0.0:
            raise NotImplementedError(
                f"DC={self.DC} > 0 non implémenté dans Sprint F (Weibull v0.6.0). "
                "La décomposition λ_DU=(1−DC)·h(t) / λ_DD=DC·h(t) avec taux "
                "variable est prévue Sprint G. "
                "Utiliser DC=0 et lambda_DU=(1−DC)·lambda_totale en entrée."
            )
        if self.M < 1 or self.N < 1 or self.M > self.N:
            raise WeibullParameterError(
                f"Architecture invalide : M={self.M}, N={self.N}. 1 ≤ M ≤ N requis."
            )

        # ── Calcul eta depuis mttf si nécessaire ──────────────────────────
        if self.mttf > 0.0 and self.eta <= 0.0:
            gamma_factor = sci_special.gamma(1.0 + 1.0 / self.beta_w)
            self.eta = self.mttf / gamma_factor
        elif self.eta <= 0.0:
            raise WeibullParameterError(
                "Fournir soit eta > 0, soit mttf > 0 (eta calculé automatiquement)."
            )

        if self.eta <= 0:
            raise WeibullParameterError(f"eta={self.eta} doit être > 0.")

    @property
    def p(self) -> int:
        """Nombre de défaillances DU simultanées nécessaires (p = N − M)."""
        return self.N - self.M

    @property
    def mttf_computed(self) -> float:
        """MTTF calculé depuis (beta_w, eta). Source: Rausand & Høyland 2004 Eq.(B.8)."""
        return self.eta * sci_special.gamma(1.0 + 1.0 / self.beta_w)


# ─────────────────────────────────────────────────────────────────────────────
# Fonctions de base Weibull
# ─────────────────────────────────────────────────────────────────────────────

def _weibull_R(t: float, beta_w: float, eta: float) -> float:
    """
    Fiabilité Weibull : R(t) = exp(−(t/η)^β_w).
    Source : Rausand & Høyland (2004) §B.3 Eq.(B.5).
    """
    if t <= 0.0:
        return 1.0
    return math.exp(-((t / eta) ** beta_w))


def _weibull_h(t: float, beta_w: float, eta: float) -> float:
    """
    Taux de défaillance Weibull : h(t) = (β_w/η)·(t/η)^(β_w−1).
    Source : Rausand & Høyland (2004) §B.3 Eq.(B.7).

    Note : h(0) = 0 pour β_w > 1, +∞ pour β_w < 1, λ pour β_w = 1.
    """
    if t <= 0.0:
        if beta_w < 1.0:
            return math.inf
        elif beta_w == 1.0:
            return 1.0 / eta
        else:
            return 0.0
    return (beta_w / eta) * ((t / eta) ** (beta_w - 1.0))


def _conditional_Q(t: float, t_age: float, beta_w: float, eta: float) -> float:
    """
    PFD conditionnelle du composant dans [t_age, t_age + t] :
    Q(t | t_age) = 1 − R(t_age + t) / R(t_age).

    Source : Wu et al. (2019) RESS 185, Eq.(6).
    """
    R_age = _weibull_R(t_age, beta_w, eta)
    if R_age < 1e-15:
        # Composant quasi-certain d'être défaillant — Q ≈ 1
        return 1.0
    R_next = _weibull_R(t_age + t, beta_w, eta)
    return 1.0 - R_next / R_age


# ─────────────────────────────────────────────────────────────────────────────
# PFH — formule analytique exacte
# ─────────────────────────────────────────────────────────────────────────────

def _pfh_1oo1_exact(wp: WeibullParams) -> float:
    """
    PFHavg 1oo1 : formule analytique EXACTE pour tout β_w.

    PFHavg = Q(T1 | t_age) / T1 = [1 − R(t_age + T1) / R(t_age)] / T1

    Preuve (doc §4.1) :
      PFH(t) = h(t_age+t) · R(t|t_age)
             = −(1/R_age) · d/dt[R(t_age+t)]
      ∫₀^T1 PFH(t) dt = [R(t_age) − R(t_age+T1)] / R(t_age) = Q(T1|t_age)
      → PFHavg = Q(T1|t_age) / T1   QED

    Source : dérivation first-principles, résultat implicite dans
    Rausand & Høyland (2004) §10.4 ; explicité dans Rogova et al. (2017) p.376.
    """
    return _conditional_Q(wp.T1, wp.t_age, wp.beta_w, wp.eta) / wp.T1


# ─────────────────────────────────────────────────────────────────────────────
# PFD — intégration numérique exacte
# ─────────────────────────────────────────────────────────────────────────────

def _pfd_component_avg(wp: WeibullParams, tol: float = 1e-10) -> float:
    """
    PFDavg composant 1oo1 exact : (1/T1) × ∫₀^T1 Q(t | t_age) dt.

    Source : Rausand & Høyland (2004) §10.3 définition PFDavg ;
             Rogova et al. (2017) Eq.(4).
    """
    R_age = _weibull_R(wp.t_age, wp.beta_w, wp.eta)
    if R_age < wp.min_survival:
        raise WeibullAgeError(
            f"R(t_age={wp.t_age:.0f}h) = {R_age:.2e} < {wp.min_survival:.0e}. "
            "Composant trop âgé — remplacer avant ce point."
        )

    def integrand(t: float) -> float:
        return _conditional_Q(t, wp.t_age, wp.beta_w, wp.eta)

    result, _err = sci_integrate.quad(
        integrand, 0.0, wp.T1,
        epsabs=tol, epsrel=tol, limit=200
    )
    return result / wp.T1


def _pfd_koon_avg(wp: WeibullParams, tol: float = 1e-10) -> float:
    """
    PFDavg kooN exact par intégration numérique.

    Formule :
      PFDavg_kooN = C(N, p+1) × (1/T1) × ∫₀^T1 [Q(t|t_age)]^(p+1) dt

    Valide pour Q(T1|t_age) ≪ 1 (approximation binomiale tronquée au premier terme).
    Source : Rogova et al. (2017) Eq.(15) ; Rausand & Høyland (2004) §9.4 Eq.(9.15).

    Pour p = 0 (1oo1) : route vers _pfd_component_avg (identique).
    """
    p = wp.p
    if p == 0:
        return _pfd_component_avg(wp, tol)

    R_age = _weibull_R(wp.t_age, wp.beta_w, wp.eta)
    if R_age < wp.min_survival:
        raise WeibullAgeError(
            f"R(t_age={wp.t_age:.0f}h) = {R_age:.2e} < {wp.min_survival:.0e}."
        )

    comb = math.comb(wp.N, p + 1)

    def integrand(t: float) -> float:
        q = _conditional_Q(t, wp.t_age, wp.beta_w, wp.eta)
        return q ** (p + 1)

    result, _err = sci_integrate.quad(
        integrand, 0.0, wp.T1,
        epsabs=tol, epsrel=tol, limit=200
    )
    return comb * result / wp.T1


# ─────────────────────────────────────────────────────────────────────────────
# PFH kooN — intégration numérique
# ─────────────────────────────────────────────────────────────────────────────

def _pfh_koon_avg(wp: WeibullParams, tol: float = 1e-10) -> float:
    """
    PFHavg kooN par intégration numérique.

    Identité utilisée :
      PFH_kooN(t) = N · h(t) · R(t|t_age) · C(N-1, p) · [Q(t|t_age)]^p

    Source : Chebila & Innal (2015) JLPPI 34:167-176, Eq.(17) ;
             Rogova et al. (2017) Eq.(20)-(22).

    Pour p = 0 (1oo1) : route vers _pfh_1oo1_exact (résultat analytique exact).
    """
    p = wp.p
    if p == 0:
        return _pfh_1oo1_exact(wp)

    R_age = _weibull_R(wp.t_age, wp.beta_w, wp.eta)
    if R_age < wp.min_survival:
        raise WeibullAgeError(
            f"R(t_age={wp.t_age:.0f}h) = {R_age:.2e} < {wp.min_survival:.0e}."
        )

    comb_nm1_p = math.comb(wp.N - 1, p)
    prefactor = wp.N * comb_nm1_p

    def integrand(t: float) -> float:
        t_abs = wp.t_age + t
        h = _weibull_h(t_abs, wp.beta_w, wp.eta)
        R = _weibull_R(t_abs, wp.beta_w, wp.eta) / R_age
        q = _conditional_Q(t, wp.t_age, wp.beta_w, wp.eta)
        return h * R * (q ** p)

    result, _err = sci_integrate.quad(
        integrand, 0.0, wp.T1,
        epsabs=tol, epsrel=tol, limit=200
    )
    return prefactor * result / wp.T1


# ─────────────────────────────────────────────────────────────────────────────
# API publique — résultats enrichis
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class WeibullResult:
    """
    Résultat complet d'un calcul Weibull PFD ou PFH.

    Attributs
    ---------
    pfd_avg : float
        PFDavg sur [t_age, t_age + T1] (basse demande).
    pfh_avg : float
        PFHavg sur [t_age, t_age + T1] (haute demande).
    pfd_component : float
        PFD du composant individuel Q(T1|t_age) sur l'intervalle.
    pfh_component : float
        PFH du composant individuel (analytique exact).
    lambda_eff : float
        Taux effectif apparent = Q(T1|t_age) / T1.
        Équivalent exponentiel «instantané» pour cet intervalle.
    ratio_pfd_vs_exp : float
        PFDavg_Weibull / PFDavg_exp(lambda_eff) pour ce même intervalle.
        Vaut 1.0 pour β_w = 1 et t_age = 0 (par construction).
    sil_pfd : int
        SIL correspondant à pfd_avg (−1 si hors limites).
    sil_pfh : int
        SIL correspondant à pfh_avg (−1 si hors limites).
    params : WeibullParams
        Paramètres d'entrée (trace complète).
    """
    pfd_avg           : float
    pfh_avg           : float
    pfd_component     : float
    pfh_component     : float
    lambda_eff        : float
    ratio_pfd_vs_exp  : float
    sil_pfd           : int
    sil_pfh           : int
    params            : WeibullParams


def _sil_from_pfd(pfd: float) -> int:
    """IEC 61508-1 Table 2 — SIL depuis PFDavg."""
    if pfd < 1e-4:
        return 4
    elif pfd < 1e-3:
        return 3
    elif pfd < 1e-2:
        return 2
    elif pfd < 1e-1:
        return 1
    return -1


def _sil_from_pfh(pfh: float) -> int:
    """IEC 61508-1 Table 2 — SIL depuis PFHavg."""
    if pfh < 1e-8:
        return 4
    elif pfh < 1e-7:
        return 3
    elif pfh < 1e-6:
        return 2
    elif pfh < 1e-5:
        return 1
    return -1


def compute_weibull(wp: WeibullParams, tol: float = 1e-10) -> WeibullResult:
    """
    Point d'entrée principal Sprint F.

    Calcule PFDavg et PFHavg pour une architecture MooN avec taux de
    défaillance Weibull, à l'âge t_age.

    Paramètres
    ----------
    wp : WeibullParams
        Paramètres Weibull (valide après __post_init__).
    tol : float
        Tolérance pour l'intégration numérique (défaut 1e-10).

    Retour
    ------
    WeibullResult
        Résultats complets avec métadonnées.

    Exemples
    --------
    >>> from sil_engine.weibull import WeibullParams, compute_weibull
    >>> wp = WeibullParams(beta_w=2.0, mttf=219000.0, T1=8760.0, M=1, N=1)
    >>> r = compute_weibull(wp)
    >>> print(f"PFDavg = {r.pfd_avg:.3e}")
    """
    # ── PFD et PFH kooN ───────────────────────────────────────────────────
    pfd_avg = _pfd_koon_avg(wp, tol)
    pfh_avg = _pfh_koon_avg(wp, tol)

    # ── Métriques composant individuel ────────────────────────────────────
    pfd_comp = _conditional_Q(wp.T1, wp.t_age, wp.beta_w, wp.eta)
    pfh_comp = _pfh_1oo1_exact(wp)

    # ── Taux effectif apparent (λ_eff = Q(T1|t_age)/T1) ──────────────────
    lambda_eff = pfd_comp / wp.T1

    # ── Ratio vs exponentielle à même lambda_eff ──────────────────────────
    # PFDavg_exp_exact = 1 − (1−exp(−λ_eff·T1))/(λ_eff·T1)  (pas l'approx. λT1/2)
    lT1 = lambda_eff * wp.T1
    if lT1 < 1e-12:
        # Composant quasi-parfait : les deux méthodes donnent ≈ 0
        ratio = 1.0
    else:
        if wp.p == 0:
            # 1oo1 : ratio PFDavg_Weibull / PFDavg_exp(λ_eff)
            pfd_exp_exact = 1.0 - (1.0 - math.exp(-lT1)) / lT1
            ratio = pfd_avg / pfd_exp_exact if pfd_exp_exact > 0 else 1.0
        else:
            # kooN : ratio Q_comp^(p+1) intégré vs [Q_comp_exp]^(p+1) intégré
            # Approximation : ratio ≈ (pfd_comp_W / pfd_comp_exp)^(p+1)
            pfd_comp_exp = 1.0 - math.exp(-lT1)
            comp_ratio = pfd_comp / pfd_comp_exp if pfd_comp_exp > 0 else 1.0
            ratio = comp_ratio ** (wp.p + 1)

    return WeibullResult(
        pfd_avg          = pfd_avg,
        pfh_avg          = pfh_avg,
        pfd_component    = pfd_comp,
        pfh_component    = pfh_comp,
        lambda_eff       = lambda_eff,
        ratio_pfd_vs_exp = ratio,
        sil_pfd          = _sil_from_pfd(pfd_avg),
        sil_pfh          = _sil_from_pfh(pfh_avg),
        params           = wp,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Profil de vieillissement
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class AgingIntervalResult:
    """Résultat pour un intervalle de proof test dans un profil de vieillissement."""
    interval_index : int    # Numéro d'intervalle (0-based)
    t_age_start    : float  # Âge en début d'intervalle [h]
    t_age_years    : float  # Âge en début d'intervalle [années]
    pfd_avg        : float
    pfh_avg        : float
    lambda_eff     : float
    ratio_vs_exp   : float  # vs exponentielle à même lambda_eff_initial
    sil_pfd        : int
    sil_pfh        : int
    survival       : float  # R(t_age_start)


def weibull_aging_profile(
    beta_w        : float,
    eta           : float   = 0.0,
    mttf          : float   = 0.0,
    T1            : float   = 8760.0,
    n_intervals   : int     = 25,
    M             : int     = 1,
    N             : int     = 1,
    min_survival  : float   = 1e-3,
    tol           : float   = 1e-10,
) -> list[AgingIntervalResult]:
    """
    Profil PFDavg / PFHavg sur n_intervals intervalles successifs.

    Hypothèse : maintenance minimale (minimal repair) — le proof test révèle
    et répare les défaillances, mais l'âge du composant continue à croître.
    L'intervalle s'arrête dès que R(t_age) < min_survival.

    Source hypothèse maintenance minimale : Wu et al. (2019) RESS 185, §2.2.

    Paramètres
    ----------
    beta_w, eta/mttf, T1, M, N : identiques à WeibullParams.
    n_intervals : nombre maximal d'intervalles.
    min_survival : seuil en dessous duquel l'intervalle est exclu.

    Retour
    ------
    list[AgingIntervalResult], trié par t_age croissant.
    """
    # Référence lambda_eff initiale (intervalle 0, composant neuf)
    wp0 = WeibullParams(
        beta_w=beta_w, eta=eta, mttf=mttf, T1=T1, M=M, N=N,
        t_age=0.0, min_survival=1e-15
    )
    lambda_eff_ref = _conditional_Q(T1, 0.0, beta_w, wp0.eta) / T1

    results: list[AgingIntervalResult] = []

    for i in range(n_intervals):
        t_age = i * T1
        R_age = _weibull_R(t_age, beta_w, wp0.eta)
        if R_age < min_survival:
            break

        wp = WeibullParams(
            beta_w=beta_w, eta=wp0.eta, T1=T1, M=M, N=N,
            t_age=t_age, min_survival=min_survival
        )
        try:
            r = compute_weibull(wp, tol)
        except WeibullAgeError:
            break

        # Ratio vs lambda_eff_ref (exponentielle à même λ initial)
        lT1_ref = lambda_eff_ref * T1
        if lT1_ref < 1e-12 or wp.p > 0:
            ratio_ref = r.ratio_pfd_vs_exp
        else:
            pfd_exp_ref_exact = 1.0 - (1.0 - math.exp(-lT1_ref)) / lT1_ref
            ratio_ref = r.pfd_avg / pfd_exp_ref_exact if pfd_exp_ref_exact > 0 else 1.0

        results.append(AgingIntervalResult(
            interval_index = i,
            t_age_start    = t_age,
            t_age_years    = t_age / 8760.0,
            pfd_avg        = r.pfd_avg,
            pfh_avg        = r.pfh_avg,
            lambda_eff     = r.lambda_eff,
            ratio_vs_exp   = ratio_ref,
            sil_pfd        = r.sil_pfd,
            sil_pfh        = r.sil_pfh,
            survival       = R_age,
        ))

    return results


# ─────────────────────────────────────────────────────────────────────────────
# Outil sensibilité : ratio Weibull vs IEC à même MTTF
# ─────────────────────────────────────────────────────────────────────────────

def ratio_weibull_vs_iec(
    beta_w  : float,
    mttf    : float,
    T1      : float,
    t_age   : float,
    M       : int = 1,
    N       : int = 1,
    tol     : float = 1e-10,
) -> float:
    """
    Ratio PFDavg_Weibull(β_w, MTTF, t_age) / PFDavg_IEC(λ=1/MTTF)
    à même MTTF.

    PFDavg_IEC exact = 1 − (1−exp(−λ·T1))/(λ·T1)  [exponentielle, kooN]

    Paramètres
    ----------
    beta_w : paramètre de forme Weibull
    mttf   : MTTF de référence [h] — η calculé automatiquement
    T1     : intervalle proof test [h]
    t_age  : âge du composant [h]
    M, N   : architecture

    Retour
    ------
    float : ratio > 1 → Weibull moins fiable qu'IEC (vieillissement)
            ratio < 1 → Weibull plus fiable qu'IEC (phase de jeunesse)
            ratio = 1 → cohérence (β_w = 1 ou t_age au point d'inflexion)
    """
    wp = WeibullParams(
        beta_w=beta_w, mttf=mttf, T1=T1, M=M, N=N, t_age=t_age
    )
    r = compute_weibull(wp, tol)

    # IEC exponentielle exacte (pas l'approximation λT1/2)
    lambda_iec = 1.0 / mttf
    lT1 = lambda_iec * T1
    p = N - M

    if p == 0:
        pfd_iec = 1.0 - (1.0 - math.exp(-lT1)) / lT1
    else:
        # kooN IEC : C(N,p+1) × ∫₀^T1 (1-exp(-λt))^(p+1) dt / T1
        comb = math.comb(N, p + 1)
        def integrand(t: float) -> float:
            return (1.0 - math.exp(-lambda_iec * t)) ** (p + 1)
        integral, _ = sci_integrate.quad(integrand, 0.0, T1, epsabs=1e-12, epsrel=1e-12)
        pfd_iec = comb * integral / T1

    return r.pfd_avg / pfd_iec if pfd_iec > 0 else float('inf')
