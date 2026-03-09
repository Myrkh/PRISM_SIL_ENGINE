"""
Suite de vérification vs tableaux IEC 61508-6 Annexe B.
Source : Fichier 13 — Tableaux B.2 à B.13 + B.9.

14 cas de test prioritaires.
Tolérance : ±1% = VALIDÉ, ±5% = ACCEPTABLE, >5% = ERREUR.
"""

import math
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from solver.formulas import SubsystemParams, pfd_arch, pfh_arch


# ─────────────────────────────────────────────────────────────────────────────
# 14 cas de test prioritaires (Fichier 13)
# ─────────────────────────────────────────────────────────────────────────────

VERIFICATION_CASES = [
    # (id, description, params_dict, expected, mode, arch)
    {
        "id": "T01",
        "desc": "1oo1 DC=90% T1=1an",
        "arch": "1oo1",
        "mode": "pfd",
        "lambda_DU": 5e-7 * 0.1,    # DC=90% → λ_DU = λ×(1-DC)
        "lambda_DD": 5e-7 * 0.9,
        "DC": 0.9, "beta": 0, "beta_D": 0,
        "MTTR": 8, "T1": 8760,
        "expected": 2.2e-4,
    },
    {
        "id": "T02",
        "desc": "1oo1 DC=0% T1=1an",
        "arch": "1oo1",
        "mode": "pfd",
        "lambda_DU": 5e-7,
        "lambda_DD": 0,
        "DC": 0, "beta": 0, "beta_D": 0,
        "MTTR": 8, "T1": 8760,
        "expected": 2.2e-3,
    },
    {
        "id": "T03",
        "desc": "1oo2 DC=90% β=2% T1=1an",
        "arch": "1oo2",
        "mode": "pfd",
        "lambda_DU": 5e-7 * 0.1,
        "lambda_DD": 5e-7 * 0.9,
        "DC": 0.9, "beta": 0.02, "beta_D": 0.01,
        "MTTR": 8, "T1": 8760,
        "expected": 4.5e-6,
    },
    {
        "id": "T04",
        "desc": "1oo2 DC=90% β=10% T1=1an",
        "arch": "1oo2",
        "mode": "pfd",
        "lambda_DU": 5e-7 * 0.1,
        "lambda_DD": 5e-7 * 0.9,
        "DC": 0.9, "beta": 0.10, "beta_D": 0.05,
        "MTTR": 8, "T1": 8760,
        "expected": 2.2e-5,
    },
    {
        "id": "T05",
        "desc": "2oo3 DC=90% β=2% T1=1an",
        "arch": "2oo3",
        "mode": "pfd",
        "lambda_DU": 5e-7 * 0.1,
        "lambda_DD": 5e-7 * 0.9,
        "DC": 0.9, "beta": 0.02, "beta_D": 0.01,
        "MTTR": 8, "T1": 8760,
        "expected": 4.6e-6,
    },
    {
        "id": "T06",
        "desc": "2oo3 DC=90% β=2% λ=2.5E-6 T1=1an",
        "arch": "2oo3",
        "mode": "pfd",
        "lambda_DU": 2.5e-6 * 0.1,
        "lambda_DD": 2.5e-6 * 0.9,
        "DC": 0.9, "beta": 0.02, "beta_D": 0.01,
        "MTTR": 8, "T1": 8760,
        "expected": 2.7e-5,
    },
    {
        "id": "T07",
        "desc": "1oo2 DC=60% β=2% λ=5E-6 T1=1an",
        "arch": "1oo2",
        "mode": "pfd",
        "lambda_DU": 5e-6 * 0.4,
        "lambda_DD": 5e-6 * 0.6,
        "DC": 0.6, "beta": 0.02, "beta_D": 0.01,
        "MTTR": 8, "T1": 8760,
        "expected": 2.8e-4,
    },
    {
        "id": "T08",
        "desc": "1oo2 DC=0% β=2% λ=5E-6 T1=1an",
        "arch": "1oo2",
        "mode": "pfd",
        "lambda_DU": 5e-6,
        "lambda_DD": 0,
        "DC": 0, "beta": 0.02, "beta_D": 0.01,
        "MTTR": 8, "T1": 8760,
        "expected": 1.1e-3,
    },
    {
        "id": "T09",
        "desc": "1oo2 DC=0% β=10% λ=5E-6 PTC=90% T1=1an",
        "arch": "1oo2",
        "mode": "pfd",
        "lambda_DU": 5e-6,
        "lambda_DD": 0,
        "DC": 0, "beta": 0.10, "beta_D": 0.05,
        "MTTR": 8, "T1": 8760,
        "PTC": 0.9, "T2": 87600,
        "expected": 6.0e-3,
    },
    {
        "id": "T10",
        "desc": "1oo1 DC=99% λ=2.5E-5 T1=10ans",
        "arch": "1oo1",
        "mode": "pfd",
        "lambda_DU": 2.5e-5 * 0.01,
        "lambda_DD": 2.5e-5 * 0.99,
        "DC": 0.99, "beta": 0, "beta_D": 0,
        "MTTR": 8, "T1": 87600,
        "expected": 1.1e-2,
    },
    {
        "id": "T11",
        "desc": "2oo3 DC=90% β=2% λ=2.5E-5 T1=10ans (Markov requis)",
        "arch": "2oo3",
        "mode": "pfd",
        "lambda_DU": 2.5e-5 * 0.1,
        "lambda_DD": 2.5e-5 * 0.9,
        "DC": 0.9, "beta": 0.02, "beta_D": 0.01,
        "MTTR": 8, "T1": 87600,
        "expected": 6.3e-2,
        "markov_required": True,
    },
    {
        "id": "T12",
        "desc": "PFH 1oo1 DC=90% λ=5E-7",
        "arch": "1oo1",
        "mode": "pfh",
        "lambda_DU": 5e-7 * 0.1,
        "lambda_DD": 5e-7 * 0.9,
        "DC": 0.9, "beta": 0, "beta_D": 0,
        "MTTR": 8, "T1": 8760,
        "expected": 5e-8,
    },
    {
        "id": "T13",
        "desc": "PFH 1oo2 DC=90% β=2% λ=2.5E-7 T1=1an",
        "arch": "1oo2",
        "mode": "pfh",
        "lambda_DU": 2.5e-7 * 0.1,
        "lambda_DD": 2.5e-7 * 0.9,
        "DC": 0.9, "beta": 0.02, "beta_D": 0.01,
        "MTTR": 8, "T1": 8760,
        "expected": 5.1e-10,
    },
    {
        "id": "T14",
        "desc": "PFH 2oo3 DC=90% β=2% λ=2.5E-7 T1=1an",
        "arch": "2oo3",
        "mode": "pfh",
        "lambda_DU": 2.5e-7 * 0.1,
        "lambda_DD": 2.5e-7 * 0.9,
        "DC": 0.9, "beta": 0.02, "beta_D": 0.01,
        "MTTR": 8, "T1": 8760,
        "expected": 5.2e-10,
    },
]


def run_single_case(case: dict) -> dict:
    """Exécute un cas de test et retourne le résultat."""
    p = SubsystemParams(
        lambda_DU=case["lambda_DU"],
        lambda_DD=case.get("lambda_DD", 0),
        DC=case.get("DC", 0),
        beta=case.get("beta", 0),
        beta_D=case.get("beta_D", 0),
        MTTR=case.get("MTTR", 8),
        T1=case.get("T1", 8760),
        PTC=case.get("PTC", 1.0),
        T2=case.get("T2", 87600),
        architecture=case["arch"],
    )

    mode = case["mode"]
    if mode == "pfd":
        arch = case["arch"]
        if case.get("PTC", 1.0) < 1.0:
            from solver.formulas import pfd_imperfect_test
            computed = pfd_imperfect_test(p, arch)
        else:
            computed = pfd_arch(p, arch)
    else:
        computed = pfh_arch(p, case["arch"])

    expected = case["expected"]
    if expected > 0:
        error_pct = abs(computed - expected) / expected * 100
    else:
        error_pct = 0.0

    if error_pct < 1.0:
        status = "VALIDÉ"
    elif error_pct < 5.0:
        status = "ACCEPTABLE"
    else:
        status = "ERREUR"

    return {
        "id": case["id"],
        "desc": case["desc"],
        "arch": case["arch"],
        "mode": mode,
        "computed": computed,
        "expected": expected,
        "error_pct": error_pct,
        "status": status,
        "markov_required": case.get("markov_required", False),
    }


def run_all_verification_cases() -> dict:
    """Lance tous les cas de vérification IEC."""
    results = []
    n_ok = n_acceptable = n_error = 0

    for case in VERIFICATION_CASES:
        r = run_single_case(case)
        results.append(r)
        if r["status"] == "VALIDÉ":
            n_ok += 1
        elif r["status"] == "ACCEPTABLE":
            n_acceptable += 1
        else:
            n_error += 1

    return {
        "total": len(results),
        "valide": n_ok,
        "acceptable": n_acceptable,
        "erreur": n_error,
        "pass_rate": (n_ok + n_acceptable) / len(results) * 100,
        "results": results,
    }


if __name__ == "__main__":
    print("=" * 70)
    print("VÉRIFICATION MOTEUR IEC — Tableaux Annexe B")
    print("=" * 70)

    report = run_all_verification_cases()

    for r in report["results"]:
        marker = "✓" if r["status"] == "VALIDÉ" else ("~" if r["status"] == "ACCEPTABLE" else "✗")
        print(f"{marker} {r['id']} {r['desc']}")
        print(f"   Calculé: {r['computed']:.3e}  Attendu: {r['expected']:.3e}  "
              f"Écart: {r['error_pct']:.1f}%  → {r['status']}")

    print()
    print(f"RÉSULTAT : {report['valide']}/{report['total']} validés, "
          f"{report['acceptable']} acceptables, "
          f"{report['erreur']} erreurs")
    print(f"Taux de réussite : {report['pass_rate']:.1f}%")


# ─────────────────────────────────────────────────────────────────────────────
# GROUPE F — Extensions V3.3
# ─────────────────────────────────────────────────────────────────────────────

def test_pfh_moon_generalized():
    """PFH koon généralisé — cohérence et vérification IEC."""
    from solver.extensions import pfh_moon
    def P(lDU, lDD=0, DC=0, beta=0.02, betaD=0.01, T1=730):
        return SubsystemParams(lambda_DU=lDU, lambda_DD=lDD, DC=DC,
                               beta=beta, beta_D=betaD, T1=T1)
    p = P(5e-9, 4.5e-8, DC=0.9)
    assert abs(pfh_moon(p,1,1) - 5e-9) / 5e-9 < 0.01, "1oo1 doit = λDU"
    assert abs(pfh_moon(p,1,2) - 1e-10) / 1e-10 < 0.03, "1oo2 IEC Tableau B.10"
    assert abs(pfh_moon(p,2,3) - 1e-10) / 1e-10 < 0.03, "2oo3 IEC Tableau B.10"
    # Cohérence redondance
    p0 = P(5e-7, beta=0.0, betaD=0.0)
    v = [pfh_moon(p0,1,n) for n in [2,3,4]]
    assert v[0] > v[1] > v[2], f"1oo2>{v[0]:.2e} > 1oo3>{v[1]:.2e} > 1oo4>{v[2]:.2e}"


def test_pfd_curve():
    """PFD(t) : intégrale doit ≈ PFDavg IEC."""
    from solver.extensions import pfd_instantaneous
    from solver.formulas import pfd_arch
    p = SubsystemParams(lambda_DU=5e-8, lambda_DD=4.5e-7, DC=0.9,
                        beta=0.02, beta_D=0.01, T1=8760)
    res = pfd_instantaneous(p, "1oo2", n_points=200)
    ref = pfd_arch(p, "1oo2")
    assert abs(res.pfd_avg - ref) / ref < 0.03, f"avg={res.pfd_avg:.3e} vs IEC={ref:.3e}"
    assert res.pfd_max >= res.pfd_avg, "PFD max doit ≥ PFD avg"
    assert res.sil_avg >= 1


def test_mgl_ccf():
    """MGL : 1oo2 ratio≈1, 1oo3 MGL < β-simple."""
    from solver.extensions import pfd_mgl, MGLParams, pfd_arch_extended
    mgl = MGLParams(beta=0.02, gamma=0.5, delta=0.5)
    p = SubsystemParams(lambda_DU=5e-7, lambda_DD=0, DC=0.0,
                        beta=0.02, beta_D=0.0, T1=8760)
    r1oo2 = pfd_mgl(p, "1oo2", mgl) / pfd_arch_extended(p, "1oo2")
    assert abs(r1oo2 - 1.0) < 0.05, f"1oo2 MGL ratio={r1oo2:.3f} doit ≈1"
    assert pfd_mgl(p, "1oo3", mgl) < pfd_arch_extended(p, "1oo3"), "1oo3 MGL < β-simple"


def test_sff_hft():
    """SFF+HFT : NTNU slide 17 — SFF=85% TypeB HFT=1 → SIL2."""
    from solver.extensions import architectural_constraints
    ac = architectural_constraints(1e-7, 3e-7, 2.67e-7, k=1, n=2)
    assert abs(ac.sff - 0.85) < 0.01, f"SFF={ac.sff*100:.1f}%"
    assert ac.hft == 1
    assert ac.sil_max_1H_B == 2, f"TypeB SIL={ac.sil_max_1H_B}"
    assert ac.sil_max_1H_A == 3, f"TypeA SIL={ac.sil_max_1H_A}"


def test_demand_duration():
    """Demand duration : valeurs physiques cohérentes."""
    from solver.extensions import pfd_demand_duration
    dd = pfd_demand_duration(5e-7, 1/8760, 8, 8760, 8)
    assert 0 < dd['pfd_recommended'] < 1, "PFD doit être entre 0 et 1"
    # Demande plus courte → PFD1 plus grand (plus d'exposition relative)
    dd_long = pfd_demand_duration(5e-7, 1/8760, 48, 8760, 8)
    assert dd['pfd1'] > dd_long['pfd1'], "Demande courte → PFD1 plus grand"


def test_route_auto():
    """Routage auto : IEC si λT1<0.1, Markov tenté si λT1>0.1."""
    from solver.extensions import route_compute
    p_lo = SubsystemParams(lambda_DU=1e-9, lambda_DD=0, DC=0, beta=0.02, T1=730)
    p_hi = SubsystemParams(lambda_DU=5e-5, lambda_DD=0, DC=0, beta=0.02, T1=8760)
    r_lo = route_compute(p_lo, "1oo2", "pfd")
    r_hi = route_compute(p_hi, "1oo2", "pfd")
    assert r_lo['engine_used'] == "IEC_simplified"
    assert r_hi['lambda_T1'] > 0.1  # bascule tentée
    assert r_hi['result'] > 0       # résultat valide (fallback ou Markov)
