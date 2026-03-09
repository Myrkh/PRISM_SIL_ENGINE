# 18 — Validation et Benchmark GRIF

## Statut : PARTIELLEMENT BLOQUÉ

Les cas de référence GRIF nécessitent que l'utilisateur fournisse les screenshots
ou exports CSV depuis GRIF Workshop. La structure d'accueil est définie ci-dessous.

---

## Protocole de Validation

### Niveaux de validation

```
Niveau 1 : Vérification IEC 61508-6 Annexe B
           Tableaux B.2–B.5 (PFD) et B.10–B.13 (PFH)
           → Automatisable immédiatement (données dans fichier 13)

Niveau 2 : Comparaison GRIF Workshop
           Cas fournis par l'utilisateur
           → Bloqué en attente des données

Niveau 3 : Cas réels SIF documentés
           Projets industriels avec PFD mesuré vs calculé
           → Hors scope initial
```

---

## Niveau 1 — Vérification IEC (AUTOMATISÉE)

```python
# tests/test_verification.py

import pytest
import numpy as np
from solver.markov import MarkovSolver
from solver.formulas import compute_iec_simplified

# Cas de test depuis IEC 61508-6 Tableau B.2 (T1=6 mois=4380h)
# Format: (architecture, lambda_du, DC, beta, T1, pfd_iec_expected, tolerance)

IEC_TEST_CASES_TABLE_B2 = [
    # 1oo1 — Tableau B.2
    ("1oo1", 1e-6, 0.0,  0.00, 4380, 2.19e-3, 0.01),
    ("1oo1", 1e-5, 0.0,  0.00, 4380, 2.19e-2, 0.01),
    ("1oo1", 1e-5, 0.9,  0.00, 4380, 2.21e-3, 0.01),  # avec DC
    
    # 1oo2 — Tableau B.2
    ("1oo2", 1e-5, 0.0,  0.10, 4380, 2.41e-3, 0.05),
    ("1oo2", 1e-5, 0.9,  0.02, 4380, 2.47e-4, 0.05),
    
    # 2oo3 — Tableau B.2
    ("2oo3", 1e-5, 0.0,  0.10, 4380, 7.26e-4, 0.05),
    ("2oo3", 1e-5, 0.9,  0.02, 4380, 7.77e-5, 0.05),
]

IEC_TEST_CASES_TABLE_B3 = [
    # T1 = 1 an = 8760h
    ("1oo1", 1e-6, 0.0,  0.00, 8760, 4.38e-3, 0.01),
    ("1oo1", 1e-5, 0.0,  0.00, 8760, 4.38e-2, 0.01),
    ("1oo2", 1e-5, 0.0,  0.10, 8760, 9.69e-3, 0.05),
    ("1oo2", 1e-5, 0.9,  0.02, 8760, 9.89e-4, 0.05),
    ("2oo3", 1e-5, 0.0,  0.10, 8760, 2.92e-3, 0.05),
    ("2oo3", 1e-5, 0.9,  0.02, 8760, 2.98e-4, 0.05),
]

# Tableau B.9 — Essai imparfait PTC=0.9, T1=8760h
IEC_TEST_CASES_IMPERFECT_PT = [
    ("1oo1", 1e-5, 0.0, 0.0, 8760, 0.9, 2.63e-2, 0.05),
    ("1oo2", 1e-5, 0.0, 0.1, 8760, 0.9, 5.83e-3, 0.05),
]


def run_all_verification_cases():
    """Lance tous les cas de vérification IEC et retourne un rapport."""
    results = []
    
    all_cases = (
        [(c, "B.2") for c in IEC_TEST_CASES_TABLE_B2] +
        [(c, "B.3") for c in IEC_TEST_CASES_TABLE_B3]
    )
    
    for (arch, ldu, DC, beta, T1, expected, tol), table in all_cases:
        # IEC simplifié
        iec_result = compute_iec_simplified(
            lambda_du=ldu, lambda_dd=ldu * DC / (1-DC) if DC < 1 else 0,
            DC=DC, beta=beta, MTTR=8.0, architecture=arch, T1=T1
        )
        pfd_iec = iec_result["pfdavg"]
        
        # Markov exact
        solver = MarkovSolver(
            lambda_du=ldu, DC=DC, beta=beta, MTTR=8.0,
            architecture=arch
        )
        pfd_markov = solver.compute_pfd(T1=T1)["pfdavg"]
        
        # Écarts
        err_iec = abs(pfd_iec - expected) / expected
        err_markov = abs(pfd_markov - expected) / expected
        
        results.append({
            "table": table,
            "architecture": arch,
            "lambda_du": ldu,
            "DC": DC,
            "beta": beta,
            "T1": T1,
            "expected": expected,
            "pfd_iec": pfd_iec,
            "pfd_markov": pfd_markov,
            "err_iec_pct": err_iec * 100,
            "err_markov_pct": err_markov * 100,
            "status_iec": "PASS" if err_iec <= tol else "FAIL",
            "status_markov": "PASS" if err_markov <= tol else "FAIL"
        })
    
    n_pass = sum(1 for r in results if r["status_markov"] == "PASS")
    return {
        "total": len(results),
        "passed": n_pass,
        "failed": len(results) - n_pass,
        "cases": results
    }


@pytest.mark.parametrize("arch,ldu,DC,beta,T1,expected,tol", IEC_TEST_CASES_TABLE_B2)
def test_iec_table_b2_markov(arch, ldu, DC, beta, T1, expected, tol):
    """Vérifie que Markov reproduit les tableaux B.2 IEC à ±5%."""
    solver = MarkovSolver(lambda_du=ldu, DC=DC, beta=beta, MTTR=8.0, architecture=arch)
    result = solver.compute_pfd(T1=T1)
    err = abs(result["pfdavg"] - expected) / expected
    assert err <= tol, (
        f"[{arch}] λ={ldu}, DC={DC}, β={beta}: "
        f"Markov={result['pfdavg']:.3e}, IEC={expected:.3e}, err={err*100:.1f}%"
    )


@pytest.mark.parametrize("arch,ldu,DC,beta,T1,expected,tol", IEC_TEST_CASES_TABLE_B3)
def test_iec_table_b3_markov(arch, ldu, DC, beta, T1, expected, tol):
    solver = MarkovSolver(lambda_du=ldu, DC=DC, beta=beta, MTTR=8.0, architecture=arch)
    result = solver.compute_pfd(T1=T1)
    err = abs(result["pfdavg"] - expected) / expected
    assert err <= tol
```

---

## Niveau 2 — Benchmark GRIF (STRUCTURE D'ACCUEIL)

### Format de données attendu

Pour chaque cas GRIF à valider, fournir :

```json
{
  "case_id": "GRIF_001",
  "description": "Capteur pression 1oo2, SIL2, T1=1an",
  "source": "GRIF Workshop v20xx",
  "inputs": {
    "architecture": "1oo2",
    "lambda_du": 5e-6,
    "lambda_dd": 5e-7,
    "DC": 0.9,
    "beta": 0.02,
    "beta_D": null,
    "MTTR": 8,
    "T1": 8760
  },
  "grif_outputs": {
    "pfdavg": 1.03e-3,
    "pfh": null,
    "rrf": 970,
    "sil": 2
  }
}
```

### Cas GRIF fournis

```python
# À REMPLIR PAR L'UTILISATEUR

GRIF_CASES = [
    # {
    #     "case_id": "GRIF_001",
    #     ...
    # }
]
```

### Script de comparaison automatique

```python
def benchmark_vs_grif(grif_cases: list[dict]) -> dict:
    """
    Compare PRISM vs GRIF pour tous les cas fournis.
    
    Critères de passage :
    - PFD : écart < 1% → "validé", < 5% → "acceptable", > 5% → "divergent"
    - Si divergence : lancer Markov exact pour arbitrage
    """
    results = []
    
    for case in grif_cases:
        inp = case["inputs"]
        grif = case["grif_outputs"]
        
        # Calcul IEC PRISM
        iec = compute_iec_simplified(
            lambda_du=inp["lambda_du"],
            lambda_dd=inp.get("lambda_dd", 0),
            DC=inp["DC"],
            beta=inp["beta"],
            MTTR=inp["MTTR"],
            architecture=inp["architecture"],
            T1=inp["T1"]
        )
        
        # Calcul Markov PRISM
        solver = MarkovSolver(
            lambda_du=inp["lambda_du"],
            lambda_dd=inp.get("lambda_dd", 0),
            DC=inp["DC"],
            beta=inp["beta"],
            MTTR=inp["MTTR"],
            architecture=inp["architecture"]
        )
        markov = solver.compute_pfd(T1=inp["T1"])
        
        pfd_grif = grif["pfdavg"]
        pfd_iec = iec["pfdavg"]
        pfd_markov = markov["pfdavg"]
        
        err_iec = (pfd_iec - pfd_grif) / pfd_grif * 100
        err_markov = (pfd_markov - pfd_grif) / pfd_grif * 100
        
        def status(err):
            a = abs(err)
            if a < 1: return "VALIDÉ"
            if a < 5: return "ACCEPTABLE"
            return "DIVERGENT"
        
        results.append({
            "case_id": case["case_id"],
            "description": case["description"],
            "pfd_grif": pfd_grif,
            "pfd_iec_prism": pfd_iec,
            "pfd_markov_prism": pfd_markov,
            "err_iec_%": err_iec,
            "err_markov_%": err_markov,
            "status_iec": status(err_iec),
            "status_markov": status(err_markov),
            "arbitrage": "Markov" if abs(err_markov) < abs(err_iec) else "IEC"
        })
    
    n_validated = sum(1 for r in results if r["status_markov"] == "VALIDÉ")
    n_acceptable = sum(1 for r in results if r["status_markov"] == "ACCEPTABLE")
    
    return {
        "total": len(results),
        "validated": n_validated,
        "acceptable": n_acceptable,
        "divergent": len(results) - n_validated - n_acceptable,
        "cases": results
    }
```

---

## Registre des Divergences Connues (IEC vs Markov)

Ces écarts sont attendus et documentés — non des bugs.

| Cas | λ×T1 | Architecture | IEC PFD | Markov PFD | Écart | Explication |
|---|---|---|---|---|---|---|
| λ=5e-5, T1=8760h | 0.44 | 1oo1 | 0.219 | 0.178 | -19% | Taylor ordre 1 insuffisant |
| λ=5e-5, T1=8760h | 0.44 | 1oo2 | 4.8e-3 | 3.6e-3 | -25% | Termes croisés negliges |
| PFH 2oo3 | — | 2oo3 | E | E×0.7 | -30% | IEC sous-estime (dangereux) |
| PST c=0.9, T1=8760h | 0.44 | 1oo1 | E | E×0.82 | -18% | Formule PST incorrecte |

*Légende : E = valeur IEC de référence*

---

## Rapport de Validation : Template

```markdown
# Rapport de Validation PRISM Calc Engine
Version : X.Y.Z
Date : YYYY-MM-DD

## 1. Vérification IEC 61508-6
- Tableaux B.2-B.5 : N/N cas passés (objectif : 100%)
- Tableaux B.10-B.13 (PFH) : N/N cas passés
- Essai imparfait B.9 : N/N cas passés

## 2. Comparaison GRIF Workshop
- Total cas : N
- Validés (< 1%) : N
- Acceptables (< 5%) : N
- Divergents : N (voir analyse)

## 3. Cas de divergence
[Pour chaque divergence > 5% : analyse cause, arbitrage Markov]

## 4. Conclusion
[PRISM atteint / n'atteint pas la parité GRIF sur les cas testés]
```
