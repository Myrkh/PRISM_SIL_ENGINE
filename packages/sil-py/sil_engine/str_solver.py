"""
STR — Spurious Trip Rate : analytique koon + Markov.

Sources :
  - Lundteigen & Rausand, NTNU Ch.12 (MD 21_STR_SPURIOUS_TRIP) — ACCÈS LIBRE
  - NTNU Ch.12 slides 22-31 : formules STR_IF, STR_DD, STR_FD, Markov STR

Aucun outil commercial (exSILentia, GRIF) n'expose le STR par Markov exact.
"""

import numpy as np
from math import comb
from .formulas import SubsystemParams


def str_analytical(p: SubsystemParams) -> dict:
    """
    STR analytique koon complet.
    Source : NTNU Ch.12 slides 22-28.
    
    STR_G = STR_IF + STR_DD + STR_FD
    
    STR_IF(koon) = n × C(n-1,k-1) × [(1-β_SO)λ_SO]^k × MTTR_SO^(k-1) + β_SO×λ_SO
    STR_DD(koon) = n × C(n-1,n-k) × [(1-β_D)λ_DD]^(n-k+1) × MTTR^(n-k) + β_D×λ_DD
    STR_FD       = λ_FD
    """
    k, n = p.M, p.N

    # ── STR_IF : Spurious Operation — NTNU Ch.12 slide 24
    if k == 1:
        str_if = n * p.lambda_SO
    elif p.lambda_SO > 0:
        lso_ind = (1 - p.beta_SO) * p.lambda_SO
        str_if = (n * comb(n - 1, k - 1) * lso_ind ** k
                  * p.MTTR_SO ** (k - 1)) + p.beta_SO * p.lambda_SO
    else:
        str_if = 0.0

    # ── STR_DD : DD → safe state transition — NTNU Ch.12 slide 27
    n_dd_trip = n - k + 1  # nb DD failures needed for trip
    if n == k:  # noon (série) : tout DD → trip
        str_dd = n * p.lambda_DD
    elif n_dd_trip <= 0:
        str_dd = 0.0
    elif p.lambda_DD > 0:
        ldd_ind = (1 - p.beta_D) * p.lambda_DD
        str_dd = (n * comb(n - 1, n_dd_trip - 1) * ldd_ind ** n_dd_trip
                  * p.MTTR ** (n_dd_trip - 1)) + p.beta_D * p.lambda_DD
    else:
        str_dd = 0.0

    # ── STR_FD : False Demands — NTNU Ch.12 slide 26
    str_fd = p.lambda_FD

    str_total = str_if + str_dd + str_fd
    mttfs = 1.0 / str_total if str_total > 0 else float('inf')

    return {
        "str_total": str_total,
        "str_if": str_if,
        "str_dd": str_dd,
        "str_fd": str_fd,
        "mttfs_hours": mttfs,
        "mttfs_years": mttfs / 8760.0,
        "trips_per_year": str_total * 8760.0,
        "method": "analytical_koon",
    }


def str_markov(p: SubsystemParams) -> dict:
    """
    STR par modèle Markov (état stationnaire).
    Source : NTNU Ch.12 slide 31.
    
    STR_tot = Σ_{j ∈ FST} P_i × λ_ij
    
    Construit un espace d'états avec transitions SO et DD vers trip.
    μ_DU inclus pour le steady-state (comme PFH).
    """
    k, n = p.M, p.N

    ldu_ind = p.lambda_DU * (1 - p.beta)
    ldd_ind = p.lambda_DD * (1 - p.beta_D)
    ldu_ccf = p.lambda_DU * p.beta
    ldd_ccf = p.lambda_DD * p.beta_D
    lso = p.lambda_SO
    lso_ccf = p.beta_SO * p.lambda_SO
    mu_dd = 1.0 / p.MTTR if p.MTTR > 0 else 1.0 / 8.0
    mu_du = 1.0 / (p.T1 / 2.0 + p.MTTR)

    # Build states: (n_W, n_DU, n_DD)
    states = []
    for n_DU in range(n + 1):
        for n_DD in range(n - n_DU + 1):
            n_W = n - n_DU - n_DD
            states.append((n_W, n_DU, n_DD))

    n_states = len(states)
    idx = {s: i for i, s in enumerate(states)}
    Q = np.zeros((n_states, n_states))

    for i, (nw, ndu, ndd) in enumerate(states):
        if nw > 0:
            tgt = (nw - 1, ndu + 1, ndd)
            if tgt in idx:
                r = nw * ldu_ind; Q[i, idx[tgt]] += r; Q[i, i] -= r
        if nw > 0:
            tgt = (nw - 1, ndu, ndd + 1)
            if tgt in idx:
                r = nw * ldd_ind; Q[i, idx[tgt]] += r; Q[i, i] -= r
        if ndd > 0:
            tgt = (nw + 1, ndu, ndd - 1)
            if tgt in idx:
                r = ndd * mu_dd; Q[i, idx[tgt]] += r; Q[i, i] -= r
        if ndu > 0:
            tgt = (nw + 1, ndu - 1, ndd)
            if tgt in idx:
                r = ndu * mu_du; Q[i, idx[tgt]] += r; Q[i, i] -= r
        if nw > 0 and ldu_ccf > 0:
            tgt = (0, nw + ndu, ndd)
            if tgt in idx and tgt != (nw, ndu, ndd):
                Q[i, idx[tgt]] += ldu_ccf; Q[i, i] -= ldu_ccf
        if nw > 0 and ldd_ccf > 0:
            tgt = (0, ndu, nw + ndd)
            if tgt in idx and tgt != (nw, ndu, ndd):
                Q[i, idx[tgt]] += ldd_ccf; Q[i, i] -= ldd_ccf

    # Steady state π Q = 0, Σ π = 1
    A = Q.T.copy()
    A[:, -1] = 1.0
    b = np.zeros(n_states); b[-1] = 1.0
    try:
        pi = np.linalg.solve(A, b)
    except np.linalg.LinAlgError:
        pi = np.linalg.lstsq(A, b, rcond=None)[0]

    # STR = Σ P_i × (SO rate towards trip from state i)
    # For koon safety, spurious trip = (n-k+1)oon for SO
    # For 1oon: any SO on any W channel → trip → rate = nw × λ_SO
    # For k≥2: only CCF SO causes instant trip; independent SO needs k simultaneous
    str_so = 0.0
    for i, (nw, ndu, ndd) in enumerate(states):
        if nw > 0 and lso > 0:
            if k == 1:
                str_so += pi[i] * nw * lso
            else:
                # CCF SO → instant trip
                str_so += pi[i] * lso_ccf

    # DD contribution: β_D×λ_DD = CCF DD → all channels fail → shutdown
    str_dd = 0.0
    for i, (nw, ndu, ndd) in enumerate(states):
        if nw > 0:
            str_dd += pi[i] * ldd_ccf

    str_total = str_so + str_dd + p.lambda_FD
    mttfs = 1.0 / str_total if str_total > 0 else float('inf')

    return {
        "str_total_markov": str_total,
        "str_so": str_so,
        "str_dd": str_dd,
        "str_fd": p.lambda_FD,
        "mttfs_hours": mttfs,
        "mttfs_years": mttfs / 8760.0,
        "trips_per_year": str_total * 8760.0,
        "n_states": n_states,
        "method": "markov_steady_state",
    }
