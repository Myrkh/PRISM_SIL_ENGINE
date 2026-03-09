# sil-engine

**Open-source IEC 61508 SIL calculation engine.**  
The first fully transparent, auditable, validated alternative to GRIF, exSILentia, and SILSafer.

[![License: LGPL v3](https://img.shields.io/badge/License-LGPL%20v3-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![Validated](https://img.shields.io/badge/IEC%2061508--6-79%20test%20cases-green.svg)](packages/sil-py/tests/)
[![CI](https://github.com/Myrkh/PRISM_SIL_ENGINE/actions/workflows/ci.yml/badge.svg)](https://github.com/Myrkh/PRISM_SIL_ENGINE/actions)

---

## Why this exists

Commercial SIL tools cost thousands per seat and are **black boxes** — you cannot audit the formulas, verify the assumptions, or reproduce the results independently.

This is a problem. IEC 61508 certifications rely on these calculations. Auditors and notified bodies (TÜV, Bureau Veritas, Exida) deserve to verify them.

**sil-engine** solves this:
- Every formula is traceable to its source (IEC clause, paper DOI, or public slides)
- Every result is reproducible with the test cases provided
- The code is readable, documented, and contribution-friendly

---

## What's included

Two complementary engines:

| Engine | Language | Method | When to use |
|--------|----------|--------|-------------|
| [`sil-py`](packages/sil-py/) | Python 3.10+ | IEC analytical + exact Markov CTMC | SIL 3/4, research, λ·T₁ ≥ 0.1 |
| [`sil-ts`](packages/sil-ts/) | TypeScript 5 | IEC 61508-6 Annex B analytical | Real-time UI, λ·T₁ < 0.1 |

Both engines cover the same IEC 61508-6 Annex B formulas and produce identical results for the standard architectures.

---

## Install in one command

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
    lambda_S     = 1e-9,          # safe failure rate
    k=1, n=2,
    component_type = "B",         # Type B: complex component
)
print(f"SFF = {verdict['arch_result'].sff * 100:.0f}%")
print(f"SIL final = SIL {verdict['sil_final']}")   # min(SIL_prob, SIL_arch)
print(f"Limited by: {verdict['limiting_factor']}")
```

### More examples

```python
# PFD(t) instantaneous sawtooth curve — how PFD evolves during the proof test interval
from sil_engine import pfd_instantaneous
curve = pfd_instantaneous(p, "1oo2", n_points=200)
print(f"PFD peak = {curve.pfd_max:.2e}  ({curve.pfd_max/curve.pfd_avg:.1f}× average)")
print(f"Time fraction at SIL 3 or better: {curve.frac_sil.get('SIL3', 0) + curve.frac_sil.get('SIL4', 0):.0%}")

# MGL CCF model (Multiple Greek Letters) — more precise than simple β
from sil_engine import pfd_mgl, MGLParams
mgl = MGLParams(beta=0.02, gamma=0.5, delta=0.5)
pfd_mgl_result = pfd_mgl(p, "1oo3", mgl)

# Demand duration model — for systems where demands last hours, not seconds
from sil_engine import pfd_demand_duration
result = pfd_demand_duration(
    lambda_DU       = p.lambda_DU,
    lambda_de       = 1 / 8760,   # 1 demand per year
    demand_duration = 8.0,        # each demand lasts 8 hours
    T1              = p.T1,
)

# Exact Markov solver — when λ·T1 > 0.1 (analytical formulas become inaccurate)
from sil_engine import route_compute
r = route_compute(p, "1oo2", mode="pfd")
print(f"Engine used: {r['engine_used']}")  # auto-switches to Markov when needed

# Full SIF (sensor + logic + final element)
sensor = SubsystemParams(lambda_DU=5e-9, lambda_DD=4.5e-8, DC=0.9, beta=0.02, T1=8760)
logic  = SubsystemParams(lambda_DU=1e-10, lambda_DD=9e-10, DC=0.99, beta=0.01, T1=8760)
fe     = SubsystemParams(lambda_DU=5e-8, lambda_DD=4.5e-7, DC=0.9, beta=0.02, T1=8760)
pfd_sif = pfd_arch(sensor, "1oo2") + pfd_arch(logic, "1oo1") + pfd_arch(fe, "1oo2")
from sil_engine import sil_from_pfd
print(f"SIF PFDavg = {pfd_sif:.2e}  SIL {sil_from_pfd(pfd_sif)}")
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
- **Exact Markov CTMC** — scipy matrix exponential, valid for any λ·T₁
- **Auto-routing** — switches automatically to Markov when λ·T₁ > 0.1
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
|-----------|-------|-----------|--------|
| IEC 61508-6 Tables B.2–B.4 (PFDavg) | 38 | ≤ 10% | ✅ 100% pass |
| IEC 61508-6 Tables B.10–B.13 (PFH)  | 18 | ≤ 10% | ✅ 100% pass |
| 61508.org Worked Example 2024        |  6 | ≤  2% | ✅ 100% pass |
| NTNU Ch8 Markov examples             |  3 | ≤  2% | ✅ 100% pass |

> IEC tables themselves are rounded to 1–2 significant figures, so 2–5% discrepancy is expected and normal.

Reproduction scripts: [`packages/sil-py/tests/test_verification.py`](packages/sil-py/tests/test_verification.py)

---

## Theory & sources

Full derivations in [`docs/theory/`](docs/theory/):

| Document | Content |
|----------|---------|
| [01 — IEC 61508-6 Formulas](docs/theory/01_IEC_FORMULAS.md) | Complete Annex B formulas with derivations |
| [02 — Markov Models](docs/theory/02_MARKOV_MODELS.md) | State spaces, generator matrices per architecture |
| [03 — Verification Tables](docs/theory/03_VERIFICATION_TABLES.md) | All IEC reference tables used for validation |
| [04 — Monte Carlo](docs/theory/04_MONTE_CARLO.md) | Stochastic simulation, uncertainty analysis |
| [05 — PST](docs/theory/05_PST.md) | Partial Stroke Test — exact multi-phase model |
| [06 — PDS / PTIF](docs/theory/06_PDS_PTIF.md) | PDS method, test-independent failures |
| [07 — Validation Protocol](docs/theory/07_VALIDATION.md) | How results are verified and tolerances justified |

Primary sources used:
- **IEC 61508-6:2010** Annex B — normative formulas
- **IEC 61508-2:2010** Table 2/3 — architectural constraints
- **NTNU RAMS Group** (Lundteigen & Rausand) — public lecture slides, ntnu.edu
- **Omeiri, Innal, Liu (2021)** JESA 54(6) — corrected PFH formulas DOI:10.21152/1750-9548.15.4.871
- **61508.org Worked Example** (2024) — independent validation reference

---

## REST API (optional)

The Python engine can run as a standalone REST API:

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
- Verified PFH 1oo2 corrected formula — Omeiri/Innal 2021 (paywall)
- PST with 3 distinct repair times — Innal/Lundteigen 2016 RESS (paywall)
- Benchmark results from GRIF or exSILentia (screenshots welcome)

---

## Relationship to PRISM

sil-engine is the open-source calculation core of **PRISM** — a commercial SIF lifecycle platform covering HAZOP/LOPA, proof test management, SIL calculations, audit trails, and report generation.

The engine is open. The platform is commercial.  
This is intentional: industry gets a free, auditable calculation engine; PRISM users get a full workflow tool built on top of it.

---

## License

[GNU Lesser General Public License v3.0](LICENSE)

**In plain terms:**  
✅ Use this in your commercial software — no restriction  
✅ Use this in research and academic work — cite the repo  
⚠️ If you modify the engine itself, you must open-source those modifications  
❌ You cannot re-license the engine under a more restrictive license
