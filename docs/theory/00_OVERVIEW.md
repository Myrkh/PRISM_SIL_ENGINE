# Theory Documentation — sil-engine

This folder contains the complete mathematical foundation for the sil-engine calculations.
Every formula in the code has a corresponding section here with its source reference.

## Document index

| # | File | Content | Primary source |
|---|------|---------|----------------|
| 01 | [IEC Formulas](01_IEC_FORMULAS.md) | Complete IEC 61508-6 Annex B formulas — PFD, PFH, all architectures | IEC 61508-6:2010 §B.3 |
| 02 | [Markov Models](02_MARKOV_MODELS.md) | Exact CTMC state spaces, generator matrices, multi-phase algorithm | IEC 61508-6:2010 §B.5.2 |
| 03 | [Verification Tables](03_VERIFICATION_TABLES.md) | IEC 61508-6 reference tables B.2–B.13, full reproduction | IEC 61508-6:2010 Annex B |
| 04 | [Monte Carlo](04_MONTE_CARLO.md) | Stochastic simulation, uncertainty analysis, parameter distributions | IEC 61508-6:2010 §B.5.3 |
| 05 | [PST](05_PST.md) | Partial Stroke Test — analytical kooN + exact multi-phase Markov | NTNU Ch11 (Lundteigen & Rausand) |
| 06 | [PDS / PTIF](06_PDS_PTIF.md) | PDS method, test-independent failures, CSU | IEC 61508-6 Annex D |
| 07 | [Validation Protocol](07_VALIDATION.md) | How results are verified, tolerance policy, benchmark methodology | — |
| 08 | [REST API](08_REST_API.md) | FastAPI server architecture, all endpoints | — |

## Key formulas at a glance

### PFD — low demand mode

```
PFD_1oo1  = λ_DU × T1/2 + λ_DD × MTTR

PFD_1oo2  = 2 × [(1-β_D)λ_DD + (1-β)λ_DU]² × t_CE × t_GE
           + β_D × λ_DD × MTTR + β × λ_DU × (T1/2 + MRT)

PFD_2oo3  = 6 × [(1-β_D)λ_DD + (1-β)λ_DU]² × t_CE × t_GE
           + β × λ_DU × (T1/2 + MRT)

PFD_1oo3  = 6 × [(1-β_D)λ_DD + (1-β)λ_DU]³ × t_CE × t_GE × t_G2E
           + β × λ_DU × (T1/2 + MRT)

where:
  t_CE  = (λ_DU/λ_D) × (T1/2 + MRT) + (λ_DD/λ_D) × MTTR
  t_GE  = (λ_DU/λ_D) × (T1/3 + MRT) + (λ_DD/λ_D) × MTTR
  t_G2E = (λ_DU/λ_D) × (T1/4 + MRT) + (λ_DD/λ_D) × MTTR
```
Source: IEC 61508-6:2010 §B.3.2.2

### PFH — high demand / continuous mode (generalised kooN)

```
PFH_koon = [n! / (k-1)!] × lD_eff^r × lDU × ∏(t_GE_i, i=1..r) + β × λ_DU

where:
  r       = n - k                          (redundancy order)
  lD_eff  = (1-β_D)λ_DD + (1-β)λ_DU
  lDU     = (1-β)λ_DU
  t_GE_i  = (λ_DU/λ_D) × (T1/(i+1) + MRT) + (λ_DD/λ_D) × MTTR

Verified: 1oo2 → 2×lD_eff×lDU×t(2) ✓
          2oo3 → 6×lD_eff×lDU×t(2) ✓
          1oo3 → 6×lD_eff²×lDU×t(2)×t(3) ✓
```
Source: IEC 61508-6:2010 §B.3.3.2 + NTNU Ch9 (Lundteigen & Rausand)

### SFF + HFT — architectural constraints (Route 1H)

```
SFF = (λ_S + λ_DD) / (λ_S + λ_DD + λ_DU)
HFT = n - k

SIL_final = min(SIL_probabilistic, SIL_architectural)
```
Source: IEC 61508-2:2010 Table 2 + NTNU Architectural Constraints slides

## Notation

| Symbol | Meaning | Unit |
|--------|---------|------|
| λ_DU | Dangerous Undetected failure rate | 1/h |
| λ_DD | Dangerous Detected failure rate | 1/h |
| λ_S | Safe failure rate | 1/h |
| λ_D | Total dangerous failure rate = λ_DU + λ_DD | 1/h |
| DC | Diagnostic Coverage = λ_DD / λ_D | — |
| β | CCF factor (Dangerous Undetected) | — |
| β_D | CCF factor (Dangerous Detected) | — |
| T1 | Proof test interval | h |
| MTTR | Mean Time To Repair (for DD failures) | h |
| MRT | Mean Repair Time (after proof test, for DU) | h |
| PFDavg | Average Probability of Failure on Demand | — |
| PFH | Probability of dangerous Failure per Hour | 1/h |
| SFF | Safe Failure Fraction | — |
| HFT | Hardware Fault Tolerance | — |

## SIL ranges

| SIL | Low demand (PFDavg) | High demand (PFH) |
|-----|---------------------|-------------------|
| 1 | 10⁻² – 10⁻¹ | 10⁻⁶ – 10⁻⁵ |
| 2 | 10⁻³ – 10⁻² | 10⁻⁷ – 10⁻⁶ |
| 3 | 10⁻⁴ – 10⁻³ | 10⁻⁸ – 10⁻⁷ |
| 4 | 10⁻⁵ – 10⁻⁴ | 10⁻⁹ – 10⁻⁸ |

Source: IEC 61508-1:2010 Table 2 and Table 3
