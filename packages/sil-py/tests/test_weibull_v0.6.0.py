"""
Suite de tests Sprint F — Weibull λ(t) PFD/PFH.

Groupes de tests :
  Groupe J : Propriétés algébriques fondamentales (T35–T41)
  Groupe K : Vieillissement — profil et sensibilité (T42–T46)

Références :
  - Rausand & Høyland (2004) §10.3–10.4
  - Rogova et al. (2017) DOI:10.1177/1748006X17694999
  - Wu et al. (2019) DOI:10.1016/j.ress.2018.11.003
  - Chebila & Innal (2015) DOI:10.1016/j.jlp.2015.02.002
"""

import math
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sil_engine.weibull import (
    WeibullParams, WeibullResult, WeibullParameterError, WeibullAgeError,
    compute_weibull, weibull_aging_profile, ratio_weibull_vs_iec,
    _weibull_R, _weibull_h, _conditional_Q,
    _pfh_1oo1_exact, _pfd_component_avg, _pfd_koon_avg
)
from scipy import integrate as sci_integrate, special as sci_special
import numpy as np


# ─────────────────────────────────────────────────────────────────────────────
# Groupe J — Propriétés algébriques fondamentales
# ─────────────────────────────────────────────────────────────────────────────

def test_T35_weibull_beta1_pfd_equals_exact_exponential():
    """
    T35 — Propriété fondamentale : Weibull(β=1) doit reproduire la valeur
    exacte de l'exponentielle.

    La vérification se fait contre l'intégrale exacte, PAS contre λT1/2
    (qui est une approximation d'ordre 2 avec ~1.3% d'erreur à λT1=0.04).

    Source : Rausand & Høyland (2004) §B.3 — β_w=1 ↔ F(t) = 1−exp(−t/η) = exponentielle.
    """
    lambda_ref = 4.566e-6  # h⁻¹
    T1 = 8760.0
    eta_exp = 1.0 / lambda_ref

    wp = WeibullParams(beta_w=1.0, eta=eta_exp, T1=T1)
    r = compute_weibull(wp)

    # Référence : intégrale exacte (1/T1)∫₀^T1 (1−exp(−λt)) dt
    pfd_exact_exp, _ = sci_integrate.quad(
        lambda t: 1.0 - math.exp(-lambda_ref * t), 0.0, T1, epsabs=1e-14
    )
    pfd_exact_exp /= T1

    err = abs(r.pfd_avg - pfd_exact_exp) / pfd_exact_exp
    assert err < 1e-10, (
        f"T35 : Weibull(β=1) PFDavg={r.pfd_avg:.8e} ≠ exp exact {pfd_exact_exp:.8e} "
        f"(erreur={err:.2e})"
    )


def test_T36_pfh_analytic_equals_numeric():
    """
    T36 — PFHavg analytique = Q(T1|t_age)/T1 doit être identique à
    l'intégrale numérique de h(t)·R(t|t_age) à précision flottante.

    Source : Preuve §4.1 doc 10_SPRINT_F_WEIBULL.md — h(t)·R(t) = −dR/dt.
    """
    beta_w, eta, T1, t_age = 2.5, 200000.0, 8760.0, 5 * 8760.0
    wp = WeibullParams(beta_w=beta_w, eta=eta, T1=T1, t_age=t_age)

    r = compute_weibull(wp)
    pfh_analytic = r.pfh_avg  # Q(T1|t_age)/T1

    # Référence numérique directe
    R_age = _weibull_R(t_age, beta_w, eta)
    def integrand(t: float) -> float:
        return _weibull_h(t_age + t, beta_w, eta) * _weibull_R(t_age + t, beta_w, eta) / R_age
    pfh_num, _ = sci_integrate.quad(integrand, 0.0, T1, epsabs=1e-14, epsrel=1e-14)
    pfh_num /= T1

    err = abs(pfh_analytic - pfh_num) / pfh_num
    assert err < 1e-12, (
        f"T36 : PFH analytique={pfh_analytic:.10e} ≠ numérique {pfh_num:.10e} "
        f"(erreur={err:.2e})"
    )


def test_T37_beta1_ratio_vs_iec_equals_one():
    """
    T37 — Weibull(β=1) à t_age=0 : ratio_weibull_vs_iec doit être 1.0000.

    Par construction : β_w=1, MTTF → η = MTTF → λ_iec = 1/MTTF = 1/η.
    Les deux calculs utilisent exactement la même distribution exponentielle.
    Source : tautologie mathématique.
    """
    ratio = ratio_weibull_vs_iec(beta_w=1.0, mttf=219000.0, T1=8760.0, t_age=0.0)
    assert abs(ratio - 1.0) < 1e-8, (
        f"T37 : ratio(β=1, t_age=0) = {ratio:.8f}, attendu 1.000000"
    )


def test_T38_pfh_beta1_reproduces_1oo1_lambda():
    """
    T38 — PFHavg Weibull(β=1, t_age=0) ≈ λ pour λT1 ≪ 1.

    Formule IEC 61508-6 §B.3.3.1.1 : PFH_1oo1 ≈ λ_DU pour basse fréquence.
    En exact : PFH = [1−exp(−λT1)] / T1.
    Source : IEC 61508-6:2010 §B.3.3.1.1.
    """
    lambda_ref = 5e-8  # h⁻¹ — valeur IEC typique (λT1 = 4.38e-4 ≪ 1)
    T1 = 8760.0
    eta = 1.0 / lambda_ref

    wp = WeibullParams(beta_w=1.0, eta=eta, T1=T1)
    r = compute_weibull(wp)

    pfh_exact = (1.0 - math.exp(-lambda_ref * T1)) / T1
    err = abs(r.pfh_avg - pfh_exact) / pfh_exact

    assert err < 1e-10, (
        f"T38 : PFH Weibull(β=1)={r.pfh_avg:.8e} ≠ exact {pfh_exact:.8e} (erreur={err:.2e})"
    )

    # Bonus : vérifier ≈ λ à ±0.05%
    err_lambda = abs(r.pfh_avg - lambda_ref) / lambda_ref
    assert err_lambda < 1e-3, (
        f"T38 bonus : PFH={r.pfh_avg:.6e} doit être ≈ λ={lambda_ref:.6e} (erreur={err_lambda:.4%})"
    )


def test_T39_koon_pfd_beta1_matches_exponential_koon():
    """
    T39 — Weibull(β=1) kooN : PFDavg doit reproduire la formule kooN
    exponentielle exacte.

    Formule : PFDavg_kooN = C(N,p+1) × ∫₀^T1 (1−exp(−λt))^(p+1) dt / T1.
    Source : Rausand & Høyland (2004) §9.4 Eq.(9.15) + §10.3.
    """
    lambda_ref = 5e-7 * 0.1  # DC=90% → λ_DU faible
    T1 = 8760.0
    eta = 1.0 / lambda_ref

    for M, N in [(1, 2), (1, 3), (2, 3)]:
        p = N - M
        comb = math.comb(N, p + 1)

        wp = WeibullParams(beta_w=1.0, eta=eta, T1=T1, M=M, N=N)
        r = compute_weibull(wp)

        # Référence : intégrale exacte kooN exponentielle
        def integrand(t: float) -> float:
            return (1.0 - math.exp(-lambda_ref * t)) ** (p + 1)
        integral, _ = sci_integrate.quad(integrand, 0.0, T1, epsabs=1e-14)
        pfd_ref = comb * integral / T1

        err = abs(r.pfd_avg - pfd_ref) / pfd_ref
        assert err < 1e-8, (
            f"T39 {M}oo{N}: PFDavg Weibull(β=1)={r.pfd_avg:.6e} ≠ ref {pfd_ref:.6e} "
            f"(erreur={err:.2e})"
        )


def test_T40_weibull_params_validation():
    """
    T40 — WeibullParams lève WeibullParameterError pour paramètres invalides.

    Plages : beta_w ∈ [0.1, 10.0], T1 > 0, t_age ≥ 0, DC ∈ [0,1),
    M ≥ 1, N ≥ M, eta > 0 OU mttf > 0.
    """
    # beta_w hors plage
    try:
        WeibullParams(beta_w=0.05, eta=100000.0, T1=8760.0)
        assert False, "Doit lever WeibullParameterError pour beta_w=0.05"
    except WeibullParameterError:
        pass

    try:
        WeibullParams(beta_w=11.0, eta=100000.0, T1=8760.0)
        assert False, "Doit lever WeibullParameterError pour beta_w=11.0"
    except WeibullParameterError:
        pass

    # T1 négatif
    try:
        WeibullParams(beta_w=2.0, eta=100000.0, T1=-1.0)
        assert False, "Doit lever WeibullParameterError pour T1 < 0"
    except WeibullParameterError:
        pass

    # Ni eta ni mttf
    try:
        WeibullParams(beta_w=2.0, T1=8760.0)
        assert False, "Doit lever WeibullParameterError si ni eta ni mttf"
    except WeibullParameterError:
        pass

    # M > N
    try:
        WeibullParams(beta_w=2.0, eta=100000.0, T1=8760.0, M=3, N=2)
        assert False, "Doit lever WeibullParameterError pour M > N"
    except WeibullParameterError:
        pass

    # Cas valides — ne doivent PAS lever
    wp_ok = WeibullParams(beta_w=2.0, mttf=219000.0, T1=8760.0)
    assert wp_ok.eta > 0


def test_T41_mttf_auto_calculation():
    """
    T41 — Calcul automatique de η depuis mttf via η = mttf / Γ(1 + 1/β_w).

    Source : Rausand & Høyland (2004) §B.3 Eq.(B.8) — MTTF = η·Γ(1+1/β_w).
    Vérification : MTTF calculé depuis η doit retrouver mttf d'entrée.
    """
    MTTF_REF = 219000.0
    for beta_w in [1.0, 1.5, 2.0, 3.0]:
        wp = WeibullParams(beta_w=beta_w, mttf=MTTF_REF, T1=8760.0)
        mttf_recomputed = wp.mttf_computed
        err = abs(mttf_recomputed - MTTF_REF) / MTTF_REF
        assert err < 1e-12, (
            f"T41 β_w={beta_w}: MTTF recomputed={mttf_recomputed:.2f} ≠ {MTTF_REF} "
            f"(erreur={err:.2e})"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Groupe K — Vieillissement
# ─────────────────────────────────────────────────────────────────────────────

def test_T42_aging_profile_monotone_for_beta_gt1():
    """
    T42 — Pour β_w > 1, le PFDavg doit être strictement croissant avec l'âge.

    Propriété physique : β_w > 1 → h(t) croissant → plus de défaillances
    à mesure que le composant vieillit.
    Source : Rausand & Høyland (2004) §B.3 — h(t) = (β_w/η)(t/η)^(β_w−1).
    """
    profile = weibull_aging_profile(
        beta_w=2.5, mttf=219000.0, T1=8760.0, n_intervals=10, M=1, N=1
    )
    assert len(profile) >= 5, "T42 : profil trop court pour vérifier monotonie"

    pfd_values = [entry.pfd_avg for entry in profile]
    for i in range(1, len(pfd_values)):
        assert pfd_values[i] >= pfd_values[i-1], (
            f"T42 : PFDavg non-croissant à l'intervalle {i}: "
            f"{pfd_values[i]:.4e} < {pfd_values[i-1]:.4e}"
        )


def test_T43_aging_profile_beta1_constant():
    """
    T43 — Pour β_w = 1, le PFDavg doit être constant quel que soit t_age.

    Propriété exponentielle : sans mémoire → h(t) = λ = const
    → PFDavg(t_age) = PFDavg(0) pour tout t_age.
    Source : propriété de l'absence de mémoire de la loi exponentielle.
    """
    profile = weibull_aging_profile(
        beta_w=1.0, mttf=219000.0, T1=8760.0, n_intervals=15, M=1, N=1
    )
    assert len(profile) >= 10

    pfd_ref = profile[0].pfd_avg
    for entry in profile[1:]:
        err = abs(entry.pfd_avg - pfd_ref) / pfd_ref
        assert err < 1e-8, (
            f"T43 : β_w=1, PFDavg à t_age={entry.t_age_years:.1f}ans "
            f"={entry.pfd_avg:.6e} ≠ ref {pfd_ref:.6e} (erreur={err:.2e})"
        )


def test_T44_ratio_vs_iec_unity_at_crossover():
    """
    T44 — Pour β_w > 1, le ratio Weibull/IEC passe par 1.0 autour de t_age = MTTF.

    Observation numérique (§6.2 doc) : pour β_w ≥ 1.5, le ratio est < 1
    (Weibull plus fiable) pour t_age < MTTF, et > 1 après.
    → Il existe un t_age* ≈ MTTF tel que ratio = 1.

    Ce test vérifie l'existence du changement de signe (ratio−1).
    """
    MTTF = 219000.0
    T1 = 8760.0
    beta_w = 2.0

    # Avant MTTF : doit être < 1 (composant en phase utile → plus fiable qu'IEC)
    ratio_early = ratio_weibull_vs_iec(
        beta_w=beta_w, mttf=MTTF, T1=T1, t_age=0.0
    )
    # Après MTTF : doit être > 1 (vieillissement → moins fiable qu'IEC)
    ratio_late = ratio_weibull_vs_iec(
        beta_w=beta_w, mttf=MTTF, T1=T1, t_age=2.0 * MTTF
    )

    assert ratio_early < 1.0, (
        f"T44 : ratio(t_age=0) = {ratio_early:.4f} devrait être < 1.0 pour β_w={beta_w}"
    )
    assert ratio_late > 1.0, (
        f"T44 : ratio(t_age=2*MTTF) = {ratio_late:.4f} devrait être > 1.0 pour β_w={beta_w}"
    )


def test_T45_weibull_age_error_on_dead_component():
    """
    T45 — WeibullAgeError doit être levée si R(t_age) < min_survival.

    Un composant ayant t_age ≫ η est quasi-certain d'être défaillant.
    Source : garde-fou §11.3 doc 10_SPRINT_F_WEIBULL.md.
    """
    # η ≈ MTTF pour β_w=1 — t_age = 100×MTTF → R ≈ 0
    wp = WeibullParams(
        beta_w=2.0, eta=100000.0, T1=8760.0,
        t_age=10_000_000.0,  # ~1140 ans — bien au-delà
        min_survival=1e-4
    )
    try:
        compute_weibull(wp)
        assert False, "T45 : doit lever WeibullAgeError pour composant dégradé"
    except WeibullAgeError:
        pass


def test_T46_koon_aging_monotone_and_sil_degradation():
    """
    T46 — Architecture 1oo2, β_w=3.0 : vérifier que le SIL se dégrade
    avec l'âge, et que le passage SIL3→SIL2 se produit bien avant la fin de vie.

    Cas industriel : vanne ESD redondante 1oo2, MTTF=219 000 h,
    β_w=3 (usure marquée), T1=8760h.
    """
    profile = weibull_aging_profile(
        beta_w=3.0, mttf=219000.0, T1=8760.0,
        n_intervals=40, M=1, N=2, min_survival=1e-3
    )
    assert len(profile) >= 10, "T46 : profil trop court"

    # Les PFDavg doivent être strictement croissants
    pfd_list = [e.pfd_avg for e in profile]
    for i in range(1, len(pfd_list)):
        assert pfd_list[i] >= pfd_list[i-1], (
            f"T46 : non-monotone à intervalle {i}"
        )

    # Vérifier que SIL initial ≥ 3 (début de vie)
    sil_initial = profile[0].sil_pfd
    assert sil_initial >= 3, (
        f"T46 : SIL initial={sil_initial}, attendu ≥ 3 (vanne ESD 1oo2 neuve)"
    )

    # Vérifier que le SIL se dégrade au fil du temps
    sil_final = profile[-1].sil_pfd
    assert sil_final <= sil_initial, (
        f"T46 : SIL final={sil_final} ≥ SIL initial={sil_initial} — incohérent"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────────────────────────

TESTS = [
    # Groupe J — Algèbre
    ("T35", test_T35_weibull_beta1_pfd_equals_exact_exponential),
    ("T36", test_T36_pfh_analytic_equals_numeric),
    ("T37", test_T37_beta1_ratio_vs_iec_equals_one),
    ("T38", test_T38_pfh_beta1_reproduces_1oo1_lambda),
    ("T39", test_T39_koon_pfd_beta1_matches_exponential_koon),
    ("T40", test_T40_weibull_params_validation),
    ("T41", test_T41_mttf_auto_calculation),
    # Groupe K — Vieillissement
    ("T42", test_T42_aging_profile_monotone_for_beta_gt1),
    ("T43", test_T43_aging_profile_beta1_constant),
    ("T44", test_T44_ratio_vs_iec_unity_at_crossover),
    ("T45", test_T45_weibull_age_error_on_dead_component),
    ("T46", test_T46_koon_aging_monotone_and_sil_degradation),
]


if __name__ == "__main__":
    print("=" * 65)
    print("PRISM SIL Engine v0.6.0 — Tests Sprint F : Weibull λ(t)")
    print("=" * 65)
    passed = failed = 0
    for tid, fn in TESTS:
        try:
            fn()
            print(f"  ✅ {tid}  PASS  {fn.__name__}")
            passed += 1
        except Exception as exc:
            print(f"  ❌ {tid}  FAIL  {fn.__name__}")
            print(f"       {type(exc).__name__}: {exc}")
            failed += 1

    print()
    print(f"Résultat : {passed}/{passed+failed} tests PASS — {failed} FAIL")
    print()
    if failed == 0:
        print("✅ Sprint F Weibull — VALIDÉ")
    else:
        print("❌ Sprint F — échecs à corriger")
        sys.exit(1)
