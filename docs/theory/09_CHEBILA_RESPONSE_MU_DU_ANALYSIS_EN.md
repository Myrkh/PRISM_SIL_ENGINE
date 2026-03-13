# Response to Chebila — Analysis of the proposal μ_DU = 1/(T1/(N+1) + MTTR_DU)

**PRISM SIL Engine — Technical Note**  
Version 0.5.1 — March 2026  
In response to: Dr. M. Chebila, personal communication, March 2026

---

## 1. The proposal

Following our March 2026 email presenting the 2^p/(p+1) law, Dr. Chebila proposes to
correct the Steady-State Markov bias by modifying the repair rate μ_DU:

> "For 1oo1 and series architectures: μ_DU = 1/(T1/2 + MTTR_DU).  
> For 1oo2: μ_DU = 1/(T1/**3** + MTTR_DU).  
> For 1oo3: μ_DU = 1/(T1/**4** + MTTR_DU)."

The implicit pattern is **μ_DU = (N+1)/T1**, corresponding to a mean sojourn time
of T1/(N+1) for a 1ooN system.

---

## 2. Numerical results (DC=0, β=0)

Parameters: λ_DU = 1.0×10⁻⁶/h, T1 = 8760 h  
(drawn from Chebila & Innal 2015, Table 1 — our established validation reference).

| Architecture | p | PFH_TD (reference) | PFH_SS standard | Std error | PFH_SS Chebila | Chebila error |
|---|---|---|---|---|---|---|
| 1oo2 | 1 | 8.760×10⁻⁹ | 8.760×10⁻⁹ | **0.0%** | 5.840×10⁻⁹ | **−33.3%** |
| 1oo3 | 2 | 7.674×10⁻¹¹ | 5.755×10⁻¹¹ | −25.0% | 1.439×10⁻¹¹ | **−81.2%** |
| 1oo4 | 3 | 6.722×10⁻¹³ | 3.361×10⁻¹³ | −50.0% | 2.151×10⁻¹⁴ | **−96.8%** |
| 2oo3 | 1 | 2.628×10⁻⁸ | 2.628×10⁻⁸ | **0.0%** | 1.314×10⁻⁸ | **−50.0%** |
| 2oo4 | 2 | 3.070×10⁻¹⁰ | 2.302×10⁻¹⁰ | −25.0% | 3.683×10⁻¹¹ | **−88.0%** |

The proposal worsens the bias systematically in every case tested.

The most informative result concerns **1oo2 and 2oo3** (p=1): the standard SS model
is exact at these architectures (0.0% error). The proposed modification introduces
errors of −33% and −50% respectively where there were none.

---

## 3. Physical argument: the DU sojourn time T1/2 is architecture-independent

**The proposal implies** that the mean sojourn time of a DU channel depends on N
(T1/2 for N=1, T1/3 for N=2, T1/4 for N=3).

**This is not physically supported.** The sojourn time of a DU channel is determined
solely by the channel's own proof-test cycle, not by the architecture of the voting system.

**Derivation:**

A channel fails DU at a time t_fail drawn uniformly from [0, T1] (DC=0, independent
failures). It remains in DU state until the next proof test. Its sojourn time is:

```
τ = T1 − t_fail,    t_fail ~ Uniform[0, T1]
E[τ] = T1/2        (independent of N)
```

**Monte Carlo validation** (10⁶ cycles, DC=0, β=0):

| N | Measured mean sojourn | Ratio T1/sojourn | Theoretical value |
|---|---|---|---|
| 1 | 4379.77 h | T1/2.0001 | T1/2 |
| 2 | 4381.56 h | T1/1.9993 | T1/2 |
| 3 | 4378.93 h | T1/2.0005 | T1/2 |
| 4 | 4381.84 h | T1/1.9992 | T1/2 |

E[τ] = T1/2 = 4380 h for all N, to within 0.02%. The rate μ_DU = 2/T1 is therefore
**correct and architecture-independent.**

The value T1/(N+1) does appear naturally in the statistics of the system — but in a
different context. As discussed in §5, it is the conditional mean age of the most
recently failed channel *given that all N channels are simultaneously in DU state*.
This is an order-statistic quantity for the fully failed system, not the sojourn time
of an individual channel.

---

## 4. True source of the bias: the stationary distribution π(p)

The bias does not originate in μ_DU. It originates in the **stationary distribution**
π(p) itself.

### 4.1 Time-domain average vs. stationary probability

For p simultaneous DU channels, averaging over the proof-test cycle [0, T1]:

**Time-domain (exact):**
```
P_true(p) = C(N,p) × λ_DU^p × T1^p / (p+1)
```
*(from ∫₀^T1 (λt)^p dt / T1 = T1^p/(p+1))*

**Steady-state stationary distribution:**
```
π_SS(p) ≈ C(N,p) × (λ_DU × T1/2)^p = C(N,p) × λ_DU^p × (T1/2)^p
```

**Ratio:**
```
π_SS(p) / P_true(p) = (T1/2)^p / [T1^p/(p+1)] = (p+1) / 2^p
```

| p | Architecture | Ratio (p+1)/2^p | Consequence |
|---|---|---|---|
| 0 | 1oo1 | 1.000 | SS exact ✓ |
| 1 | 1oo2 | 1.000 | SS exact ✓ |
| 2 | 1oo3 | **0.750** | SS underestimates by 25% |
| 3 | 1oo4 | **0.500** | SS underestimates by 50% |

The SS model underestimates the co-occurrence probability of p simultaneous DU
channels for p ≥ 2. This propagates directly into PFH:

```
PFH_SS = (N−p) × λ_DU × π_SS(p) = C(N,p+1) × (p+1) × λ^(p+1) × (T1/2)^p
PFH_TD = (N−p) × λ_DU × P_true(p) = C(N,p+1) × λ^(p+1) × T1^p

Ratio PFH_TD / PFH_SS = 2^p/(p+1)   QED
```

### 4.2 Why modifying μ_DU cannot remedy this

Modifying μ_DU changes π_SS(p) = C(N,p) × (λ/μ)^p. Setting π_SS = P_true requires:

```
(λ/μ)^p = λ^p × T1^p / (p+1)
1/μ = T1 / (p+1)^(1/p)
μ_correct = (p+1)^(1/p) / T1
```

**Numerical values:**

| p | μ_correct × T1 = (p+1)^(1/p) | Rational? | Proposal |
|---|---|---|---|
| 1 | 2.000000 | Yes (= 2) | 3 — off by 50% |
| 2 | **1.732051** (= √3) | **No** | 4 |
| 3 | **1.587401** (= ∛4) | **No** | 5 |
| 4 | **1.495349** (= ⁴√5) | **No** | 6 |

There are three fundamental difficulties with the μ_DU correction approach:

1. **Irrational values:** the exact correction for PFH requires μ_correct × T1 = (p+1)^(1/p),
   which is irrational for all p ≥ 2. The integer denominators proposed (T1/3, T1/4…) do
   not correspond to any exact value.

2. **No physical motivation:** (p+1)^(1/p) has no natural interpretation as the sojourn
   time of an individual DU channel.

3. **PFH and PFD cannot be corrected simultaneously:** even if a fictitious μ were found
   that corrects PFH, the same μ would not correct PFD — which follows the companion law
   (p+2)/2^(p+1). A single μ_DU parameter cannot resolve both simultaneously.

---

## 5. Physical interpretation of T1/(N+1)

The proposed sojourn T1/(N+1) for a 1ooN system does have a natural origin, which is
worth identifying precisely.

Consider the state in which all N channels have simultaneously failed DU. The N failure
times, ordered as t₁ < t₂ < … < t_N within [0, T1], form a set of order statistics of
Uniform[0, T1] variates. The expected value of the maximum (the most recently failed
channel, t_N) is N·T1/(N+1), and the expected age of that channel at the end of the cycle
is T1 − N·T1/(N+1) = T1/(N+1).

This is therefore the conditional mean remaining sojourn of the *last channel to fail*,
given that all N channels are already in DU state. It characterises the fully failed system
state — not the dynamics leading to it.

In the Markov model, the dangerous flux is computed from the transition *into* the fully
failed state (i.e., from the state with N−1 DU channels). The relevant sojourn time for
this transition is that of the individual channel being in state N−1 DU, which is T1/2.
Using the conditional sojourn of the fully failed state to parameterise the transition
*into* it conflates two different levels of the Markov state space.

---

## 6. Summary

| Proposition | Assessment | Evidence |
|---|---|---|
| μ_DU must depend on N | Does not hold | Monte Carlo (10⁶ cycles, §3) |
| T1/3 for 1oo2 improves the bias | Does not hold — introduces −33% where error = 0 | §2 |
| T1/4 for 1oo3 improves the bias | Does not hold — worsens from −25% to −81% | §2 |
| A μ_DU modification can correct the SS bias | Not feasible in general | μ_correct is irrational; PFH and PFD require different corrections (§4.2) |

The source of the SS bias is the underestimation of the co-occurrence probability π(p)
for p ≥ 2 — an intrinsic property of the stationary distribution that a change of μ_DU
cannot resolve.

The time-domain model (absorbing DU states, numerical integration), as implemented in
PRISM v0.5.0, handles both PFH and PFD exactly for all architectures.

---

## 7. Note on the 2^p/(p+1) law

Dr. Chebila confirms not having seen this ratio stated explicitly in the literature.
The present response does not challenge the 2^p/(p+1) law — it proposes an alternative
correction route that, upon testing, does not improve accuracy. The law remains supported
by five independent methods (see 08_BUG11_TD_VS_SS §6).

---

## 8. References

| Source | Role |
|---|---|
| NTNU Ch.8 slide 31; Omeiri et al. 2021 Eq.(8) | Original definition μ_DU = 1/(T1/2 + MTTR_DU) |
| Chebila & Innal (2015) JLPPI 34:167-176 | Validation parameters (Table 1) |
| Chebila, personal communication, March 2026 | Proposal μ_DU = 1/(T1/(N+1) + MTTR) |
| PRISM v0.5.0 — 08_BUG11_TD_VS_SS §6 | 2^p/(p+1) law — five independent validations |
| This document §3 | Monte Carlo proof: sojourn T1/2 is architecture-independent |
| This document §4 | Analytical derivation: μ_correct = (p+1)^(1/p)/T1 is irrational |
