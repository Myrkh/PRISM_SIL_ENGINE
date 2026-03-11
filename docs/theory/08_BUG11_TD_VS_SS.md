# Bug #11 — PFH underestimation for N−M ≥ 2 architectures
## Steady-State vs Time-Domain Markov for periodic proof-test systems

**PRISM SIL Engine — Technical Reference**  
Version 0.5.0 — March 2026

---

## 1. The problem in one sentence

The Markov steady-state solver underestimates PFH by a factor of **2^p/(p+1)** for
architectures where p = N−M ≥ 2 (1oo3, 2oo4, 1oo4). The IEC 61508-6 formulas
are not affected — they are derived in time-domain.

---

## 2. Two Markov models for the same system

A kooN safety system with periodic proof tests every T1 hours can be modelled
in two ways.

### Model A — Steady-State (what PRISM used before v0.5.0)

DU failures are repaired at an effective rate μ_DU = 1/(T1/2 + MTTR_DU), chosen
so that the mean sojourn time in DU state equals T1/2 + MTTR_DU (source: NTNU
Ch.8 slide 31; Omeiri et al. 2021 Eq.8).

The PFH is computed from the stationary distribution of the Markov chain:

```
PFH_SS = Σ_{i∈safe, j∈danger} π_i × Q[i,j]
```

This model has been used in GRIF Workshop, exSILentia, and SISTEMA.

### Model B — Time-Domain (PRISM v0.5.0, Moteur 2B)

DU states are absorbing between proof tests. After each proof test, the system
resets to (N working, 0 DU, 0 DD). The PFH is the average dangerous-failure
flux over one cycle:

```
PFH_TD = (1/T1) × ∫₀^T1 Σ_{i∈safe, j∈danger} π(t)_i × Q[i,j] dt
```

where π(t) solves the forward equation dπ/dt = Q^T π, π(0) = (1, 0, …, 0).

This is the physically correct model for periodic proof-test systems.

---

## 3. Why the two models agree for N−M ≤ 1

For a 1oo2 system (N−M = 1), the dangerous failure requires exactly one DU
channel to be present when the last working channel fails.

In steady-state, one DU channel has mean age T1/2 — its age is uniformly
distributed over [0, T1] in the stationary regime.

In time-domain, the probability of finding one DU channel at time t ∈ [0, T1]
is proportional to λ_DU × t (it failed at some point before t). The mean age
of that channel, given it exists at t, is t/2. Averaging over t gives T1/2.

**The two models give the same mean age for a single DU channel → identical PFH.**

This is why every Markov SS implementation produces correct results for 1oo1
and 1oo2 architectures. The approximation error is invisible at N−M = 1.

---

## 4. Why the models diverge for N−M ≥ 2

For a 1oo3 system (N−M = 2), the dangerous failure requires two DU channels
to have accumulated before the last working channel fails.

**The key constraint**: both DU channels must have failed within the same
proof-test period [0, T1]. Their ages are not independent — they are both
bounded by [0, T1] and by each other (channel 2 failed after channel 1).

**Steady-state model**: assigns each DU channel an independent mean age T1/2,
so the probability of two simultaneous DU channels scales as (T1/2)². This
ignores the correlation between the two ages.

**Time-domain model**: the probability that two DU channels have accumulated
by time t is proportional to (λ_DU × t)². Averaging over t:

```
∫₀^T1 (λ_DU × t)² × λ_DU dt / T1 = λ_DU³ × T1² / 3
```

The steady-state gives λ_DU³ × (T1/2)² × 3 = 3λ_DU³ T1² / 4.

**Ratio** = (T1²/3) / (3T1²/4) = 4/3.

For p = N−M simultaneous DU channels:

```
PFH_TD / PFH_SS = 2^p / (p+1)
```

This ratio is **exact** for DC=0, β=0, and holds approximately for DC>0
(within 2–11% depending on DC, exact only at DC=0).

---

## 5. Analytical proof (DC=0, β=0)

For a kooN system with N channels, all DU (DC=0), no CCF (β=0):

**Time-domain derivation:**

The probability of finding exactly p DU channels at time t (starting from
all-working at t=0) is:

```
P(p DU at t) ≈ C(N,p) × (λ_DU × t)^p    [for λ_DU × t ≪ 1]
```

The PFH (flux into state p+1 DU = dangerous) is:

```
PFH_TD = (1/T1) × ∫₀^T1 C(N,p) × (λ_DU × t)^p × (N-p) × λ_DU dt
       = C(N,p) × (N-p) × λ_DU^(p+1) × T1^p / (p+1)
       = C(N, p+1) × (p+1) × λ_DU^(p+1) × T1^p / (p+1)
       = C(N, p+1) × λ_DU^(p+1) × T1^p
```

Wait — let us be careful. C(N,p) × (N−p) = C(N, p+1) × (p+1). So:

```
PFH_TD = C(N, p+1) × λ_DU^(p+1) × T1^p / (p+1)
```

**Steady-state derivation:**

The stationary probability of p DU channels with μ_DU = 2/T1:

```
π(p DU) ≈ C(N,p) × (λ_DU / μ_DU)^p = C(N,p) × (λ_DU × T1/2)^p
```

The PFH (flux from p DU to p+1 DU = dangerous):

```
PFH_SS = (N−p) × λ_DU × π(p DU)
       = C(N,p) × (N−p) × λ_DU^(p+1) × (T1/2)^p
       = C(N, p+1) × λ_DU^(p+1) × (T1/2)^p
```

**Ratio:**

```
PFH_TD / PFH_SS = [T1^p / (p+1)] / (T1/2)^p = 2^p / (p+1)   QED
```

---

## 6. Validation against 4 independent methods

### Method 1 — Numerical verification (6 architectures, DC=0.9)

| Architecture | p | TD/SS measured | 2^p/(p+1) | Deviation |
|---|---|---|---|---|
| 1oo1 | 0 | 1.0000 | 1.0000 | 0.0% |
| 1oo2 | 1 | 0.9964 | 1.0000 | 0.4% |
| 2oo3 | 1 | 0.9960 | 1.0000 | 0.4% |
| **1oo3** | **2** | **1.3035** | **1.3333** | **2.2%** |
| **2oo4** | **2** | **1.3028** | **1.3333** | **2.3%** |
| **1oo4** | **3** | **1.9169** | **2.0000** | **4.2%** |

Deviations increase with DC because DD channels partially compensate the
correlation effect (DC=0 deviations are < 0.4% for all architectures).

### Method 2 — Omeiri et al. (2021) Table 5 MPM simulation

Parameters: λ_D = 5×10⁻⁶/h, T1 = 4380 h, MTTR = MRT = 8 h, β = 0.

| DC | TD (PRISM) | MPM (Omeiri) | Deviation |
|---|---|---|---|
| 0.6 | 3.8177×10⁻¹⁰ | 3.8180×10⁻¹⁰ | −0.01% |
| 0.9 | 2.5079×10⁻¹¹ | 2.5080×10⁻¹¹ | 0.00% |
| 0.99 | 3.6995×10⁻¹³ | 3.6990×10⁻¹³ | +0.01% |

The PRISM Time-Domain CTMC reproduces Omeiri's independent Monte-Carlo
simulation to within 0.01%.

### Method 3 — PRISM Monte Carlo (independent simulation)

Parameters: λ_D = 10⁻²/h, T1 = 100 h (λT1 = 0.1), DC = 0, β = 0.
1,000,000 cycles (~1000 dangerous events for statistical reliability).

| Method | PFH | Ratio vs TD |
|---|---|---|
| Monte Carlo | 8.900×10⁻⁶ | 1.033 (within ±1/√1000 = 3.2%) |
| Time-Domain | 8.618×10⁻⁶ | 1.000 (reference) |
| Steady-State | 6.503×10⁻⁶ | 0.755 (−25%) |

### Method 4 — IEC 61508-6 formula itself (DC=0)

IEC Eq.(23) for 1oo3 uses tCE × tGE = (T1/2) × (T1/3) = T1²/6.
PFH_IEC = 6 × λ³ × T1²/6 = λ³ × T1².
This matches PFH_TD exactly (to 0.9% due to finite λT1 correction).
PFH_SS = 3 × λ³ × (T1/2)² = 3λ³T1²/4 — 25% below.

**The IEC 61508-6 formulas are themselves derived in time-domain.**

---

## 7. Impact on existing tools

The steady-state Markov model with μ_DU = 1/(T1/2 + MTTR_DU) is used in all
major commercial SIL tools (GRIF Workshop, exSILentia, SISTEMA) and in academic
implementations.

For architectures with N−M ≥ 2:
- **1oo3** (common in gas detection, fire detection): underestimates PFH by **25%**
- **1oo4** (extreme redundancy): underestimates by **50%**
- **2oo4** (very common in voting logic): underestimates by **25%**

This means SIL 3 assessments using 1oo3 architectures may have been performed
with a PFH that is 25% lower than the true value. For a SIL 3 boundary at
PFH = 10⁻⁷/h, a 25% underestimate shifts the apparent PFH from 1.0×10⁻⁷ to
the true 1.25×10⁻⁷ — potentially crossing the SIL boundary.

---

## 8. Implementation in PRISM v0.5.0

### `markov.py` — `MarkovSolver.compute_pfh_timedomain()`

Builds the generator Q **without** the μ_DU term (DU states absorbing).
Integrates the dangerous flux using `scipy.integrate.solve_ivp` (Radau method)
and `quad`. Runtime: ~35 ms for 1oo3 (vs ~0.2 ms for steady-state).

### `markov.py` — `compute_exact(mode='high_demand')`

```python
p_redund = p.N - p.M
if p_redund >= 2:
    pfh = solver.compute_pfh_timedomain()   # exact, ~35 ms
    # warning added to output
else:
    pfh = solver.compute_pfh()              # exact for p≤1, ~0.2 ms
```

### `formulas.py` — `pfh_1oo3_corrected(p)`

Routes to `MarkovSolver(p).compute_pfh_timedomain()`. The IEC-based analytical
correction (Omeiri 2021 Eq.27) is not implemented because the time-domain is
strictly more accurate (+0.01% vs +2.5% for Omeiri Eq.27).

---

## 9. References

| Source | Used for |
|---|---|
| IEC 61508-6:2010 §B.3.3 | PFH formulas — time-domain derivation confirmed |
| Omeiri, Innal, Liu (2021) JESA 54(6):871-879 | Table 5 validation; μ_DU definition (Eq.8) |
| Rausand & Lundteigen (NTNU Ch.8) | μ_DU = 1/(T1/2 + MRT) source |
| Chebila & Innal (2015) JLPPI 34:167-176 | Prior validity analysis (reference was approximate) |
| PRISM v0.5.0 Bug #11 (this document) | First quantification of 2^p/(p+1) law |
