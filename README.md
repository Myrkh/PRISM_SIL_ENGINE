# PRISM SIL Engine

**Open-source IEC 61508 SIL calculation engine.**  
The first fully transparent, auditable, validated alternative to GRIF, exSILentia, and SILSafer.

[![License: LGPL v3](https://img.shields.io/badge/License-LGPL%20v3-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![Validated](https://img.shields.io/badge/IEC%2061508--6-79%20test%20cases-green.svg)](packages/sil-py/tests)
[![CI](https://github.com/Myrkh/PRISM_SIL_ENGINE/actions/workflows/ci.yml/badge.svg)](https://github.com/Myrkh/PRISM_SIL_ENGINE/actions)

---

## Why this exists

Commercial SIL tools cost thousands per seat and are **black boxes** — you cannot audit the formulas, verify the assumptions, or reproduce the results independently.

This is a problem. IEC 61508 certifications rely on these calculations. Auditors and notified bodies (TÜV, Bureau Veritas, Exida) deserve to verify them.

**PRISM SIL Engine** solves this:

- Every formula is traceable to its source (IEC clause, paper DOI, or public slides)
- Every result is reproducible with the test cases provided
- The code is readable, documented, and contribution-friendly

---

## What's included

Two complementary engines:

| Engine | Language | Method | When to use |
|---|---|---|---|
| [`sil-py`](packages/sil-py) | Python 3.10+ | IEC analytical + exact Markov CTMC | SIL 3/4, research, λ·T₁ ≥ 0.1 |
| [`sil-ts`](packages/sil-ts) | TypeScript 5 | IEC 61508-6 Annex B analytical | Real-time UI, λ·T₁ < 0.1 |

Both engines cover the same IEC 61508-6 Annex B formulas and produce identical results for the standard architectures.

---

## Install

### Python

```bash
pip install sil-engine
```

### TypeScript / Node.js

```bash
npm install @sil-engine/ts
```

---

## Quick start — Python

```python
from sil_engine import SubsystemParams, pfd_arch, pfh_moon, sil_achieved

# Define your subsystem
p = SubsystemParams(
    lambda_DU = 5e-8,    # dangerous undetected failure rate [1/h]
    lambda_DD = 4.5e-7,  # dangerous detected failure rate [1/h]
    DC   = 0.9,          # diagnostic coverage
    beta = 0.02,         # CCF beta-factor
    MTTR = 8.0,          # mean time to repair [h]
    T1   = 8760.0,       # proof test interval [h]  (1 year)
)

# PFDavg — low demand mode
pfd = pfd_arch(p, "1oo2")
print(f"PFDavg = {pfd:.2e}")     # → 4.48e-06  (SIL 4)

# PFH — high demand / continuous mode (any kooN, including 2oo4)
pfh = pfh_moon(p, k=2, n=4)
print(f"PFH 2oo4 = {pfh:.2e}")  # → 1.00e-10  (SIL 4)

# Full SIL verdict: probabilistic AND architectural constraints (IEC 61508-2 Route 1H)
verdict = sil_achieved(
    pfd_or_pfh   = pfd,
    lambda_DU    = p.lambda_DU,
    lambda_DD    = p.lambda_DD,
    lambda_S     = 1e-9,
    k=1, n=2,
    component_type = "B",
)
print(f"SIL final = SIL {verdict['sil_final']}")
```

---

## Features

### Both engines

- PFDavg: 1oo1, 1oo2, 2oo2, 2oo3, 1oo3, 1oo2D, kooN generic
- PFH: 1oo1, 1oo2, 2oo3, 1oo3, generalised kooN (1oo4, 2oo4, 3oo4, …)
- CCF: β-factor (IEC §B.2) + MGL Multiple Greek Letters (IEC Annex D)
- Imperfect proof test (PTC < 1, two-interval model)
- Spurious Trip Rate (STR) — analytical + Markov

### Python engine (extras)

- **Exact Markov CTMC** — two solvers, auto-selected:
  - Steady-state (N−M ≤ 1) — ~0.2 ms, exact
  - Time-domain (N−M ≥ 2) — ~35 ms, exact (see research note below)
- **Auto-routing** — switches automatically to Markov when λ·T₁ > 0.1
- **Error surface** — quantifies IEC validity domains over (λ·T₁, DC) grid
- **PFD(t) curve** — instantaneous PFD, peak value, time per SIL zone
- **Architectural constraints** — SFF, HFT, SIL verdict Route 1H/2H (IEC 61508-2)
- **Demand duration model** — non-instantaneous demands (NTNU Ch8)
- **PST** — Partial Stroke Test, multi-phase Markov
- **MTTFS** — Mean Time To Fail Spuriously via matrix solve
- **Monte Carlo** — uncertainty propagation on λ, DC, β

---

## Validation

Validated against IEC 61508-6 Annex B reference tables and public worked examples:

| Reference | Cases | Tolerance | Status |
|---|---|---|---|
| IEC 61508-6 Tables B.2–B.4 (PFDavg) | 38 | ≤ 10% | ✅ 100% pass |
| IEC 61508-6 Tables B.10–B.13 (PFH) | 18 | ≤ 10% | ✅ 100% pass |
| Omeiri et al. (2021) Table 5 — 1oo3 PFH | 3 | < 0.01% | ✅ exact match |
| 61508.org Worked Example 2024 | 6 | ≤ 2% | ✅ 100% pass |
| NTNU Ch8 Markov examples | 3 | ≤ 2% | ✅ 100% pass |

> IEC tables themselves are rounded to 1–2 significant figures, so 2–5% discrepancy is expected and normal.

Reproduction scripts: [`packages/sil-py/tests/test_verification.py`](packages/sil-py/tests/test_verification.py)

---

## Research notes — v0.5.0

### Bug #11 — Steady-state Markov underestimates PFH for 1oo3, 2oo4, 1oo4

All major SIL tools (GRIF, exSILentia, SISTEMA) use a steady-state Markov model
with an effective repair rate `μ_DU = 1/(T1/2 + MTTR_DU)` to model proof-test
renewal. This approximation is exact for N−M ≤ 1 (1oo1, 1oo2, 2oo3) but
systematically underestimates PFH for higher redundancy architectures.

**Analytical law (DC=0, β=0, exact proof):**

```
PFH_time-domain / PFH_steady-state = 2^p / (p+1)   where p = N−M
```

| Architecture | p | Underestimation |
|---|---|---|
| 1oo1, 1oo2, 2oo3 | 0 or 1 | **0%** (exact) |
| **1oo3, 2oo4** | **2** | **−25%** |
| **1oo4** | **3** | **−50%** |

The IEC 61508-6 §B.3.3 formulas are themselves derived in time-domain and are
not affected. The bug is in the Markov numerical solver only.

PRISM v0.5.0 corrects this with a Time-Domain CTMC solver (DU states absorbing,
DD repair retained) that reproduces Omeiri et al. (2021) Table 5 to < 0.01%.

Full derivation: [`docs/theory/08_BUG11_TD_VS_SS.md`](docs/theory/08_BUG11_TD_VS_SS.md)

---

### Sprint D — IEC 61508 validity domains

The IEC §B.1 recommendation `λ·T₁ < 0.1` for using simplified formulas is
the same threshold for all architectures. It has no published quantitative basis.

PRISM v0.5.0 computes the actual switchover thresholds using the TD Markov as
the exact reference, separating two error sources:

- **Source A** — missing terms for DC > 0 (corrected by Omeiri formulas)
- **Source B** — Taylor non-linearity (corrected only by Markov)

**Switchover thresholds (5% residual error, after Omeiri correction):**

| Architecture | DC = 0 | DC = 0.9 | IEC §B.1 |
|---|---|---|---|
| 1oo1 | λT₁ > 0.102 | λT₁ > 0.983 | λT₁ > 0.100 |
| 1oo2 | λT₁ > 0.051 | λT₁ > 0.496 | λT₁ > 0.100 |
| 2oo3 | λT₁ > 0.033 | λT₁ > 0.323 | λT₁ > 0.100 |

The single threshold 0.1 is **3× too permissive for 2oo3 at low DC** and
**10× too conservative for 1oo1 at high DC**.

API: [`sil_engine/error_surface.py`](packages/sil-py/sil_engine/error_surface.py)

---

## Theory & sources

Full derivations in [`docs/theory/`](docs/theory):

| Document | Content |
|---|---|
| [01 — IEC 61508-6 Formulas](docs/theory/01_IEC_FORMULAS.md) | Complete Annex B formulas with derivations |
| [02 — Markov Models](docs/theory/02_MARKOV_MODELS.md) | State spaces, generator matrices per architecture |
| [03 — Verification Tables](docs/theory/03_VERIFICATION_TABLES.md) | All IEC reference tables used for validation |
| [04 — Monte Carlo](docs/theory/04_MONTE_CARLO.md) | Stochastic simulation, uncertainty analysis |
| [05 — PST](docs/theory/05_PST.md) | Partial Stroke Test — exact multi-phase model |
| [06 — PDS / PTIF](docs/theory/06_PDS_PTIF.md) | PDS method, test-independent failures |
| [07 — Validation Protocol](docs/theory/07_VALIDATION.md) | How results are verified and tolerances justified |
| [**08 — Bug #11: TD vs SS**](docs/theory/08_BUG11_TD_VS_SS.md) | **PFH underestimation law 2^p/(p+1) — full proof** |

Primary sources:

- **IEC 61508-6:2010** Annex B — normative formulas
- **IEC 61508-2:2010** Table 2/3 — architectural constraints
- **NTNU RAMS Group** (Lundteigen & Rausand) — public lecture slides, ntnu.edu
- **Omeiri, Innal, Liu (2021)** JESA 54(6) — corrected PFH formulas. DOI:10.21152/1750-9548.15.4.871
- **Chebila & Innal (2015)** JLPPI 34:167-176 — validity domains (prior work)
- **61508.org Worked Example** (2024) — independent validation reference

---

## REST API (optional)

```bash
pip install "sil-engine[api]"
uvicorn sil_engine.api:app --host 0.0.0.0 --port 8001
```

Documentation auto-generated at `http://localhost:8001/docs` (Swagger UI).

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

Most wanted contributions:

- Weibull λ(t) for mechanical components — source: NTNU Ch5 (public)
- Benchmark results from GRIF or exSILentia (screenshots welcome)
- PST with 3 distinct repair times — Innal/Lundteigen 2016 RESS (paywall)
- Validation: 1oo3/2oo4/1oo4 results from any commercial tool (to quantify Bug #11 impact)

---

## Citing this work

If you use PRISM SIL Engine in research or academic work:

```bibtex
@software{prism_sil_engine,
  title  = {{PRISM SIL Engine} — Open-source IEC 61508 SIL calculation engine},
  author = {Myrkh},
  year   = {2026},
  url    = {https://github.com/Myrkh/PRISM_SIL_ENGINE},
  note   = {v0.5.0. Includes first published proof of PFH underestimation
            law 2^p/(p+1) for N−M ≥ 2 kooN architectures.}
}
```

---

## Relationship to PRISM

sil-engine is the open-source calculation core of **PRISM** — a commercial SIF lifecycle platform covering HAZOP/LOPA, proof test management, SIL calculations, audit trails, and report generation.

The engine is open. The platform is commercial.  
Industry gets a free, auditable calculation engine. PRISM users get a full workflow tool built on top of it.

---

## License

[GNU Lesser General Public License v3.0](LICENSE)

✅ Use in commercial software — no restriction  
✅ Use in research — cite the repository  
⚠️ Modifications to the engine must be open-sourced  
❌ Cannot re-license under a more restrictive license
