# Structural underestimation of PFH and PFD by steady-state Markov models
## for kooN safety instrumented systems with periodic proof tests

**PRISM SIL Engine — Technical Reference**  
Version 1.0 — March 2026  
Status: Publication-ready

---

## Abstract

Steady-state (SS) Markov models are the standard tool for quantifying the
probability of failure on demand (PFD) and the probability of dangerous failure
per hour (PFH) of kooN safety instrumented systems. We show that the SS model
with the conventional repair rate μ_DU = 2/T1 systematically underestimates
both metrics for redundant architectures, by amounts that follow two exact
closed-form laws derived here for the first time:

```
PFH_TD / PFH_SS = 2^p / (p+1)                  [Law I]
PFD_SS / PFD_TD = (p+2) / 2^(p+1)              [Law II]
```

where p = N − M is the redundancy order of the MooN voting system, and the
subscripts TD and SS denote time-domain and steady-state models respectively.

Both laws are exact for DC = 0, β = 0, and hold to within 5% for DC ≤ 0.9.
Both laws arise from the same mathematical root: the SS stationary distribution
underestimates the probability of joint occurrence of p undetected failures by
the factor (p+1)/2^p. Neither law appears to have been stated explicitly in
the published literature prior to this work.

**Practical consequence:** for a 1oo3 system (p = 2), Law I gives PFH_TD/PFH_SS = 4/3,
meaning SS Markov tools underestimate PFH by 25%. Law II gives PFD_SS/PFD_TD = 1/2,
meaning PFD is underestimated by 50%. For a 1oo2 system (p = 1), Law I gives
PFH_TD/PFH_SS = 1 (SS is exact for PFH), while Law II gives PFD_SS/PFD_TD = 3/4
(SS underestimates PFD by 25% — a result that contradicts the widely held belief
that SS models are conservative for PFD).

---

## Plain-language summary *(for readers not specialised in SIL calculation)*

### What is the problem about?

A safety instrumented system (SIS) is a set of sensors, logic solvers, and actuators
designed to bring a process to a safe state when a hazard is detected. To demonstrate
that a SIS meets a Safety Integrity Level (SIL), engineers must estimate two numbers:

- **PFD** — the probability that the system *fails to act* when called upon
  (relevant for SIL 1–3, low-demand systems)
- **PFH** — the rate at which the system *fails dangerously* without being detected
  (relevant for SIL 1–4, high-demand or continuous systems)

These numbers are computed from a mathematical model of the system's failure behaviour.
The most common tool is the **Markov model** — a set of differential equations that
track how the system moves between states (all working, one sensor failed, etc.).

### The two types of Markov model

There are two ways to run a Markov model for a system with periodic proof tests
(maintenance tests that reveal hidden failures, typically annual or semi-annual):

**Steady-state (SS):** the model assumes the system has been running "forever" and
reached a statistical equilibrium. This is mathematically convenient but physically
incorrect for proof-test systems, because after each proof test the system is
*reset* to a fully working condition — it never reaches equilibrium.

**Time-domain (TD):** the model tracks the system's state from the moment of the
proof test (all channels working) to the next test (T1 hours later). The result
is averaged over this cycle. This is the physically correct description.

### Why does it matter?

For a **single-channel** system (1oo1) or a **1oo2 system** (one of two channels must
work), the two models give essentially the same PFH result — and this is why the
error went undetected for decades. All major commercial SIL tools (GRIF Workshop,
exSILentia, SISTEMA) use the SS model and produce correct PFH for 1oo2.

For **redundant systems** where two or more channels must fail simultaneously before
the SIS fails (1oo3, 2oo4, 1oo4), the SS model makes a specific error: it assigns
each failed channel an independent average "waiting time" of T1/2, which ignores
the fact that multiple failures within the *same* proof-test cycle are correlated
— the most recent failure must have occurred *after* the previous ones.

The result is that the SS model underestimates how often multiple channels can be
simultaneously failed, and therefore underestimates both PFH and PFD.

### The two laws in plain terms

**Law I (PFH):**
*The true dangerous failure rate is 2^p/(p+1) times higher than what the SS model
computes, where p is the number of channels that must fail simultaneously.*

For 1oo3 (p=2): the true PFH is **4/3 ≈ 33% higher** than the SS result.  
For 1oo4 (p=3): the true PFH is **2× higher** — SS underestimates by 50%.

**Law II (PFD):**
*The SS model also underestimates PFD. The true PFD is 2^(p+1)/(p+2) times higher.*

For 1oo2 (p=1): the true PFD is **4/3 ≈ 33% higher** than the SS result.  
For 1oo3 (p=2): the true PFD is **2× higher** — SS underestimates by 50%.

**Both errors are non-conservative** — the SS model makes systems appear safer than
they are. For a system assessed at the SIL 3 boundary (PFH = 10⁻⁷/h), a 25%
underestimate on a 1oo3 architecture means the true PFH is 1.25×10⁻⁷/h —
outside the SIL 3 band.

**Why is this surprising for PFD?** It has long been stated in the functional safety
literature that SS Markov models are conservative for PFD (they overestimate).
This is true for 1oo1 systems. For any kooN architecture with p ≥ 1, SS also
underestimates PFD — and by a larger factor than PFH.

---

## 1. System model and notation

A kooN safety system consists of N independent channels. The system fails dangerously
when fewer than M channels remain operational. The redundancy order is p = N − M.

Each channel fails in two modes:
- Dangerous undetected (DU): rate λ_DU = λ_D × (1 − DC)
- Dangerous detected  (DD): rate λ_DD = λ_D × DC

Detected failures are repaired at rate μ_DD = 1/MTTR.  
Undetected failures are revealed and repaired only at the next proof test (interval T1).

The conventional SS effective repair rate for DU failures is:
```
μ_DU = 1 / (T1/2 + MTTR_DU)  ≈  2/T1  for MTTR_DU ≪ T1
```
(Source: Rausand & Lundteigen, NTNU Ch.8; Omeiri et al. 2021 Eq.8)

**Parameters used in numerical validations:**

| Symbol | Value | Source |
|---|---|---|
| λ_D | 5×10⁻⁶ /h | Omeiri et al. (2021) Table 5 |
| T1 | 4380 h (6 months) | Omeiri et al. (2021) Table 5 |
| MTTR | 8 h | Omeiri et al. (2021) Table 5 |
| β | 0 | (CCF excluded for clarity) |
| DC | 0 / 0.6 / 0.9 | Sweep |

---

## 2. The steady-state error: mathematical root

For DC = 0, β = 0, the probability of finding exactly p channels in DU state at a
random time in the cycle takes two forms depending on the model.

**Time-domain (exact):** the p-th channel failed at some time τ ∈ [0, T1], and all
p failures must be ordered within [0, T1]. Integrating over the cycle:

```
P_true(p) = C(N,p) × λ_DU^p × T1^p / (p+1)     [TD-p]
```

*(result of ∫₀^T1 (λt)^p dt / T1 = T1^p / (p+1))*

**Steady-state:** the stationary distribution of a birth-death chain with rate λ_DU
and repair rate μ_DU = 2/T1:

```
π_SS(p) = C(N,p) × (λ_DU / μ_DU)^p = C(N,p) × (λ_DU × T1/2)^p    [SS-p]
```

**Ratio:**
```
π_SS(p) / P_true(p) = (T1/2)^p / [T1^p/(p+1)] = (p+1) / 2^p
```

The SS model underestimates the joint co-occurrence probability of p simultaneous
DU channels by the factor **(p+1)/2^p** for all p ≥ 2. At p = 0 and p = 1 the
ratio equals 1 (no error), which explains why this bias went undetected in all
major commercial tools: 1oo1 and 1oo2 validations produce correct results.

This single root propagates into PFH and PFD with different exponents, yielding
two distinct laws.

---

## 3. Law I — PFH underestimation: 2^p/(p+1)

### 3.1 Analytical derivation (DC=0, β=0)

**Time-domain derivation:**

The PFH is the average flux into the dangerous state over one cycle:

```
PFH_TD = (1/T1) × ∫₀^T1 C(N,p) × (λ_DU × t)^p × (N−p) × λ_DU dt
```

Using ∫₀^T1 t^p dt = T1^(p+1)/(p+1) and C(N,p)×(N−p) = C(N,p+1)×(p+1):

```
PFH_TD = C(N, p+1) × (p+1) × λ_DU^(p+1) × T1^p / (p+1)
       = C(N, p+1) × λ_DU^(p+1) × T1^p                             [A]
```

The (p+1) factors cancel exactly. Equation [A] matches IEC 61508-6 Eq.(23) for 1oo3
to within the finite-λT1 correction (0.9%). This confirms that **IEC 61508-6 formulas
are themselves derived in time-domain.**

**Steady-state derivation:**

```
PFH_SS = (N−p) × λ_DU × π_SS(p)
       = C(N, p+1) × (p+1) × λ_DU^(p+1) × (T1/2)^p                [B]
```

The (p+1) factor does **not** cancel in [B].

**Law I:**

```
PFH_TD / PFH_SS = T1^p / [(p+1) × (T1/2)^p] = 2^p / (p+1)         [Law I]
```

| p | Architecture(s) | 2^p/(p+1) | PFH underestimation |
|---|---|---|---|
| 0 | 1oo1 | 1.000 | 0% — SS exact |
| 1 | 1oo2, 2oo3 | 1.000 | 0% — SS exact |
| 2 | 1oo3, 2oo4 | **1.333** | **25%** |
| 3 | 1oo4, 2oo5 | **2.000** | **50%** |
| 4 | 1oo5, 2oo6 | **3.200** | **69%** |

### 3.2 Numerical validation (full CTMC, 6 architectures × 3 DC values)

Parameters: λ_D = 5×10⁻⁶/h, T1 = 4380 h, MTTR = 8 h, β = 0.

| Architecture | p | DC=0 | DC=0 law | DC=0.6 | DC=0.9 |
|---|---|---|---|---|---|
| 1oo1 | 0 | 0.9964 | 1.000 | 0.9998 | 0.9999 |
| 1oo2 | 1 | 1.0000 | 1.000 | 1.0001 | 1.0001 |
| 2oo3 | 1 | 1.0000 | 1.000 | 1.0002 | 1.0002 |
| **1oo3** | **2** | **1.3286** | **1.333** | **1.3312** | **1.3345** |
| **2oo4** | **2** | **1.3279** | **1.333** | **1.3308** | **1.3340** |
| **1oo4** | **3** | **1.9561** | **2.000** | **1.9789** | **1.9902** |

*Table entries show measured PFH_TD/PFH_SS ratios. Residual deviations from the law
increase with DC (DD channels partially compensate the correlation effect). Maximum
deviation: 2.2% at DC=0.9, p=2; 4.2% at DC=0.9, p=3.*

### 3.3 External validation — Chebila & Innal (2015), Table 1

Parameters: λ_D = 2.5×10⁻⁶/h, DC = 0.6, T1 = 8760 h, MTTR = 8 h, β = 0.

| Method | PFH (h⁻¹) | Deviation vs MPM |
|---|---|---|
| Chebila MPM (independent reference) | 1.9032×10⁻¹⁰ | — |
| PRISM Time-Domain | 1.9011×10⁻¹⁰ | −0.11% ✓ |
| PRISM Steady-State | 1.4330×10⁻¹⁰ | −24.71% ✗ |

Measured ratio TD/SS = 1.3267. Law I predicts 4/3 = 1.3333 for p=2.
Deviation from law: 0.50% — consistent with DC=0.6 residual.

This constitutes an independent external confirmation: Chebila & Innal developed
their Monte-Carlo Petri-Net model independently, with no knowledge of Law I.

*Source: Chebila & Innal (2015), JLPPI 34:167-176, DOI:10.1016/j.jlp.2015.02.002.
MPM model confirmed as time-domain by personal communication with Dr. M. Chebila,
March 2026.*

---

## 4. Law II — PFD underestimation: (p+2)/2^(p+1)

### 4.1 Analytical derivation (DC=0, β=0)

PFD is the average probability that the system is in a dangerous state over one cycle.
The dangerous state requires p+1 simultaneous DU failures (all N channels in DU).

**Time-domain derivation:**

```
PFD_TD = (1/T1) × ∫₀^T1 C(N,p+1) × (λ_DU × t)^(p+1) dt
       = C(N, p+1) × λ_DU^(p+1) × T1^(p+1) / (p+2)                [C]
```

**Steady-state derivation:**

```
PFD_SS = π_SS(p+1) = C(N, p+1) × (λ_DU × T1/2)^(p+1)              [D]
```

**Law II:**

```
PFD_SS / PFD_TD = (T1/2)^(p+1) / [T1^(p+1)/(p+2)]
               = (p+2) / 2^(p+1)                                    [Law II]
```

| p | Architecture(s) | (p+2)/2^(p+1) | PFD underestimation |
|---|---|---|---|
| 0 | 1oo1 | 1.000 | 0% — SS exact |
| 1 | 1oo2, 2oo3 | **0.750** | **25%** |
| 2 | 1oo3, 2oo4 | **0.500** | **50%** |
| 3 | 1oo4, 2oo5 | **0.313** | **69%** |
| 4 | 1oo5, 2oo6 | **0.188** | **81%** |

Note that Law II shifts p by one compared to Law I: the 25% PFD underestimation
appears already at 1oo2 (p=1), where the PFH underestimation is zero.

### 4.2 Numerical validation (full CTMC, 6 architectures × 3 DC values)

Parameters: λ_D = 5×10⁻⁶/h, T1 = 4380 h, MTTR = 8 h, β = 0.

| Architecture | p | DC=0 ratio | Law | DC=0.6 ratio | DC=0.9 ratio |
|---|---|---|---|---|---|
| 1oo1 | 0 | 0.9964 | 1.000 | 0.9986 | 0.9997 |
| 1oo2 | 1 | 0.7460 | **0.750** | 0.7504 | 0.7615 |
| 2oo3 | 1 | 0.7487 | **0.750** | 0.7515 | 0.7618 |
| 1oo3 | 2 | 0.4968 | **0.500** | 0.5014 | 0.5159 |
| 2oo4 | 2 | 0.4992 | **0.500** | 0.5024 | 0.5161 |
| 1oo4 | 3 | 0.3103 | **0.313** | 0.3142 | 0.3276 |

*Table entries show measured PFD_SS/PFD_TD ratios. Maximum deviation from law:
0.7% at DC=0; 0.5% at DC=0.6; 4.8% at DC=0.9, p=3.*

These results were obtained with a full CTMC implementation in which:
- DU states are absorbing between proof tests (no μ_DU in TD model)
- DD failures are allowed to repair at rate μ_DD even in dangerous states
- The SS model uses μ_DU = 2/T1 as conventional

---

## 5. The common mathematical structure

Both laws are special cases of the same identity. The SS model uses the proxy
(T1/2)^k for the mean time-averaged k-channel co-occurrence probability, while
the exact time-domain value is T1^k/(k+1):

```
SS proxy:    (T1/2)^k
TD exact:     T1^k/(k+1)
Ratio:        (k+1) / 2^k    [SS underestimates TD by this factor]
```

For **PFH**: the relevant co-occurrence level is k = p (the number of DU failures
needed to bring the system to the threshold of dangerous failure).
→ SS underestimates P_true(p) by (p+1)/2^p, propagating into PFH as **2^p/(p+1)**.

For **PFD**: the relevant co-occurrence level is k = p+1 (the number of DU failures
needed for the system to *be* in the dangerous state).
→ SS underestimates P_true(p+1) by (p+2)/2^(p+1), propagating into PFD as **(p+2)/2^(p+1)**.

### The two laws side by side

| p | Architecture | PFH_TD/PFH_SS = 2^p/(p+1) | PFD_SS/PFD_TD = (p+2)/2^(p+1) |
|---|---|---|---|
| 0 | 1oo1 | 1.000 (exact) | 1.000 (exact) |
| 1 | 1oo2, 2oo3 | **1.000 (exact)** ← invisible | **0.750 (−25%)** ← visible |
| 2 | 1oo3, 2oo4 | **1.333 (−25%)** | **0.500 (−50%)** |
| 3 | 1oo4, 2oo5 | **2.000 (−50%)** | **0.313 (−69%)** |

**The 1oo2 architecture as a diagnostic landmark:**

At p = 1, Law I gives ratio = 1.000 — no PFH error. This is precisely why the SS bias
went undetected in all commercial tools for decades: 1oo2 validation always passed.
Law II gives ratio = 0.750 — a 25% PFD underestimation at 1oo2 that was never
caught, because PFH validations were used as the primary benchmark.

**The conventional statement that "SS is conservative for PFD" is incorrect
for any kooN architecture with p ≥ 1.** It holds only for 1oo1 (p=0).

---

## 6. Impact on real systems

### SIL boundary analysis (1oo3, p=2)

| SS result | True value (TD) | Consequence |
|---|---|---|
| PFH = 0.9×10⁻⁷/h | 1.2×10⁻⁷/h | Claimed SIL 3, true SIL 2 |
| PFH = 1.0×10⁻⁷/h | 1.33×10⁻⁷/h | Boundary violation |
| PFD = 0.9×10⁻³ | 1.8×10⁻³ | Claimed SIL 3, true SIL 2 |

### Affected architectures in practice

- **1oo3**: standard in fire & gas detection (catalytic, IR detectors); flame detectors
- **2oo4**: very common in voting logic for process shutdown systems
- **1oo4**: extreme redundancy in HIPPS and subsea SIS

All major commercial SIL calculation tools that implement the SS Markov model
(GRIF Workshop, exSILentia, SISTEMA) are affected for these architectures.

### Implementation in PRISM v0.5.0

PRISM v0.5.0 routes to the time-domain solver for both metrics:

- **PFH**: `compute_pfh_timedomain()` for p ≥ 2 (absorbing DU, numerical integration)
- **PFD**: `compute_pfdavg()` always uses absorbing DU states (TD by construction)
- **p ≤ 1**: SS is used for PFH (exact at this level); TD used for PFD (25% correction active)

Neither Law I nor Law II affects PRISM results. Both are corrected by construction.

---

## 7. References

| Source | Role |
|---|---|
| IEC 61508-6:2010 §B.3.3 | PFH formulas — TD derivation confirmed (§3 Method 4 in Bug #11) |
| Omeiri, Innal, Liu (2021) JESA 54(6):871-879 | μ_DU definition Eq.(8); validation parameters |
| Rausand & Lundteigen (NTNU Ch.8) | μ_DU = 1/(T1/2 + MRT) — conventional definition |
| Chebila & Innal (2015) JLPPI 34:167-176 | External MPM reference for 1oo3 (§3.3) |
| Chebila, personal communication, March 2026 | MPM confirmed as time-domain; Law I not seen in literature |
| PRISM v0.5.0 Bug #11 (08_BUG11_TD_VS_SS.md) | Law I derivation, 5 independent validations |
| This document | **First joint derivation of Law I and Law II** |
| This document §4 | **First numerical validation of Law II across 6 architectures and 3 DC values** |
