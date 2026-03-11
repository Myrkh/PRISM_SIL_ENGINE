# Changelog

All notable changes to this project will be documented in this file.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) — Semantic Versioning.

---

## [0.5.0] — 2026-03-11

### 🔴 Bug Fix — Critical (Bug #11)

**PFH underestimation for architectures with N−M ≥ 2 (1oo3, 2oo4, 1oo4)**

The Markov steady-state solver (`compute_pfh`) used an effective repair rate
`μ_DU = 1/(T1/2 + MTTR_DU)` to model proof-test renewal of DU channels. This
approximation is exact for N−M ≤ 1 (1oo1, 1oo2, 2oo3) but systematically
underestimates PFH for N−M ≥ 2.

**Root cause — analytical proof:**

In a kooN system with p = N−M, the system fails when p DU channels have
accumulated simultaneously within the same proof-test interval [0, T1]. Their
ages are correlated by construction — they cannot exceed T1. The steady-state
model ignores this correlation by assigning each channel an independent mean
age of T1/2.

For DC = 0, β = 0:

```
PFH_TD = C(N, p+1) × λ^(p+1) × T1^p / (p+1)   [time-domain, exact]
PFH_SS = C(N, p+1) × λ^(p+1) × (T1/2)^p        [steady-state, approx]

PFH_TD / PFH_SS = 2^p / (p+1)
```

| Architecture | p = N−M | Correction factor | SS underestimates by |
|---|---|---|---|
| 1oo1, 2oo2   | 0 | 1.000 | 0%   |
| 1oo2, 2oo3   | 1 | 1.000 | 0%   |
| **1oo3, 2oo4** | **2** | **1.333** | **−25%** |
| **1oo4**       | **3** | **2.000** | **−50%** |

**Validation — 4 independent methods:**

1. Analytical proof (DC=0, β=0) — algebraic derivation, exact
2. Omeiri et al. (2021) Table 5 MPM simulation — TD matches to < 0.01%
3. PRISM Monte Carlo (λT1=0.1, 1M cycles) — MC/TD = 1.033 (within ±3.2% stat)
4. Generalised law — verified on 6 architectures, confirmed to < 2.3%

Note: the IEC 61508-6 §B.3.3 formulas themselves are derived in time-domain
(tCE × tGE factors), not steady-state. The bug was in the Markov numerical
solver, not in the IEC derivation.

**Fix — Moteur 2B Time-Domain CTMC:**

New method `MarkovSolver.compute_pfh_timedomain()` — DU states absorbing over
[0, T1], DD repair retained. PFH = (1/T1) × ∫₀^T1 flux_to_dangerous(t) dt.

`compute_exact(mode='high_demand')` now selects automatically:
- N−M ≤ 1 → steady-state (exact, ~0.2 ms)
- N−M ≥ 2 → time-domain (exact, ~35 ms)

New function `pfh_1oo3_corrected()` in `formulas.py` — routes to time-domain.
`pfh_arch_corrected` dispatch updated for `1oo3`.

**New tests (Groupe G, T20–T24):**

| Test | Description | Reference | Result |
|---|---|---|---|
| T20 | pfh_1oo3_corrected DC=0.6 | Omeiri Table 5 MPM=3.818e-10 | ✅ Δ<1% |
| T21 | pfh_1oo3_corrected DC=0.9 | Omeiri Table 5 MPM=2.508e-11 | ✅ Δ<1% |
| T22 | pfh_1oo3_corrected DC=0.99 | Omeiri Table 5 MPM=3.699e-13 | ✅ Δ<1% |
| T23 | pfh_1oo3 IEC unchanged | Non-regression | ✅ Pass |
| T24 | compute_exact uses TD for N−M≥2 | Loi 2^p/(p+1) | ✅ Pass |
| T_law | Ratio TD/SS = 2^p/(p+1) | 6 architectures | ✅ Δ<2.3% |

**Files changed:** `markov.py`, `formulas.py`, `tests/test_verification.py`

---

### ✨ New Feature — Error Surface Module (`error_surface.py`)

**Systematic quantification of IEC 61508-6 validity domains**

New module `sil_engine/error_surface.py` — computes the relative error between
IEC simplified formulas and the exact Markov TD reference, over the grid
(λ×T1, DC), for all standard architectures.

**Two error sources identified and separated for the first time:**

**Source A — Missing IEC terms (Omeiri 2021)**
Present even at very small λ×T1. Dominant at high DC.
Example: 1oo2 DC=0.9, λT1=0.01 → δ_IEC = −89.8% (corrected to −0.1% by Omeiri).

**Source B — Taylor non-linearity (λ×T1 ≫ 0)**
Present even at DC=0. Scales as (λ×T1)^(N−M).
Example: 2oo3 DC=0, λT1=0.1 → δ_IEC/Omeiri = +15.8%.

**Computed switchover thresholds (5% residual error criterion):**

After Omeiri analytical correction, Markov is required when:

| Architecture | DC=0.0 | DC=0.6 | DC=0.9 | IEC §B.1 current |
|---|---|---|---|---|
| 1oo1 | λT1 > 0.102 | λT1 > 0.250 | λT1 > 0.983 | λT1 > 0.100 |
| 1oo2 | λT1 > 0.051 | λT1 > 0.126 | λT1 > 0.496 | λT1 > 0.100 |
| 2oo3 | λT1 > 0.033 | λT1 > 0.082 | λT1 > 0.323 | λT1 > 0.100 |

Key finding: the IEC §B.1 threshold (λT1 > 0.1, identical for all architectures)
is 3× too permissive for 2oo3 at low DC, and 10× too conservative for 1oo1/1oo2
at high DC. Architecture-adaptive thresholds are more rigorous.

Previous work (Chebila & Innal 2015) used analytical formulas as reference;
those formulas themselves underestimated for N−M ≥ 2 (Bug #11). This is the
first error surface computed against the exact TD Markov reference.

**API:**

```python
from sil_engine.error_surface import (
    compute_grid_point,        # single (λT1, DC) point
    compute_error_surface,     # full 30×20 grid for one architecture
    compare_architectures,     # multi-arch comparison at fixed DC
    find_crossover_thresholds, # switchover thresholds by (arch, DC)
    print_error_report,        # structured text report
)
```

**Files added:** `sil_engine/error_surface.py`

---

### 🔍 Research Notes

Both findings above represent, to the authors' knowledge, results not
previously published in the open literature:

1. The law `PFH_TD/PFH_SS = 2^p/(p+1)` — quantitative characterisation of
   the steady-state approximation error for high-redundancy kooN architectures.

2. The separation of IEC error into Source A (Omeiri terms) and Source B
   (Taylor non-linearity), with architecture/DC-adaptive switchover thresholds
   computed against a TD-exact reference.

If you use these results in academic work, please cite the repository:

```
PRISM SIL Engine, v0.5.0 (2026).
https://github.com/Myrkh/PRISM_SIL_ENGINE
```

---

## [0.4.2] — 2026-03-10

### Bug Fixes (Bugs #7–10)

**#7a `formulas.py` ~363 — `pfh_1oo2_corrected` MRT**
`MRT = p.MTTR` → `p.MTTR_DU`
Omeiri Eq.(17) uses MRT = Mean Repair Time for DU failures, distinct from MTTR
(which applies to DD). Source: Omeiri et al. (2021) §2.2.

**#7b `formulas.py` ~387 — `pfh_2oo3_corrected` MRT**
Same fix: `MRT = p.MTTR` → `p.MTTR_DU`

**#8a `extensions.py` ~79 — `pfh_moon`**
`getattr(p,'MRT',p.MTTR)` → `p.MTTR_DU`

**#8b `extensions.py` ~265 — `pfd_mgl`**
Same fix.

**#8c `extensions.py` ~615 — `pfd_koon_generic`**
Same fix.

**#9 `markov.py` ~122 — `_build_generator_pfh`**
`mu_du` now uses `self.p.MTTR_DU` instead of `self.p.MTTR`.

**#10 `markov.py` ~375 — method label**
Corrected label in `compute_exact` output.

### Research — Omeiri Table 4 Typo (Pending external validation)
DC=0.9 row, Eq.(22) and MPM columns: published 1.538e-7, computed 1.538e-8
(factor 10×). Three independent proofs: physical monotonicity, cross-validation,
IEC column consistency. Email sent to Olivier (INERIS). Formula unchanged
pending response.

---

## [0.4.1] — 2026-03-09

### Bug Fixes (Bugs #1–6)

**#1 `test_verification.py`** — import path `solver.*` → `sil_engine.*`

**#2 `extensions.py`** — `MarkovSolver` TypeError: `p_arch.architecture = arch`
must be set before instantiation.

**#3 `test_verification.py`** — T11 expected value corrected to Markov result
(λ×T1 = 2.19, Markov required).

**#4 `formulas.py` — PFD tCE calculation**
`T1/2` → `T1/2 + MTTR_DU` (missing restoration time term).

**#5 `str_solver.py`** — `A[:,-1]=1` → `A[-1,:]=1` (normalization row/column swap).

**#6 `formulas.py` — pfh_corrected MRT**
`MRT = T1/2` → `p.MTTR` (wrong fallback value).

---

## [0.4.0] — 2026-03-08

Initial structured release. Dual-engine architecture established:
- Motor 1: IEC 61508-6 Annex B analytical formulas
- Motor 2: Markov CTMC exact solver (scipy)
- Auto-routing: λ×T1 < 0.1 → Motor 1, else Motor 2
- Extensions: kooN generic, PFD(t), MGL CCF, PST, STR, Monte Carlo
- Validation: IEC Tables B.2–B.13, 14 cases (10 validated ≤1%, 4 acceptable ≤5%)
