"""
Solveur Markov CTMC exact pour IEC 61508-6.

Sources :
  - IEC 61508-6:2010 Annexe B §B.5.2 (MD 12_MARKOV_MODELS_EXACT)
  - NTNU Ch.5 Markov, Ch.8 PFD, Ch.9 PFH (MD 24_MTTFS_PST_PFH_NTNU)
  - Omeiri/Innal 2021 Eq.6 — PFH = Σ P_i × λ_ij (MD 22_PFH_CORRECTED)
  - Corrections : MD 23_CODE_BUGFIXES (μ_DU, CCF DD, MTTFS)

Moteur 2 : Markov CTMC — résultats exacts, ~2-30s de calcul.
"""

import math
import numpy as np
from scipy.linalg import expm
from scipy.integrate import solve_ivp, quad
from typing import Optional
from .formulas import SubsystemParams, sil_from_pfd, sil_from_pfh


# ─────────────────────────────────────────────────────────────────────────────
# Solveur Markov générique (espace d'états complet)
# ─────────────────────────────────────────────────────────────────────────────

class MarkovSolver:
    """
    Solveur CTMC exact pour architectures MooN avec CCF.
    
    Construit dynamiquement l'espace d'états (n_W, n_DU, n_DD).
    CCF : β-factor model pour DU ET DD (MD 23 Bug 2 fix).
    """

    def __init__(self, p: SubsystemParams):
        self.p = p
        self.ldu = p.lambda_DU * (1 - p.beta)       # DU indépendant
        self.ldd = p.lambda_DD * (1 - p.beta_D)      # DD indépendant
        self.ldu_ccf = p.lambda_DU * p.beta           # DU CCF
        self.ldd_ccf = p.lambda_DD * p.beta_D         # DD CCF (MD23 Bug2)
        self.mu = 1.0 / p.MTTR if p.MTTR > 0 else 1.0 / 8.0
        self.T1 = p.T1
        self.M = p.M
        self.N = p.N
        self.PTC = p.PTC

    def _build_states(self) -> list:
        """États = (n_W, n_DU, n_DD) avec n_W + n_DU + n_DD = N."""
        N = self.N
        states = []
        for n_DU in range(N + 1):
            for n_DD in range(N - n_DU + 1):
                n_W = N - n_DU - n_DD
                states.append((n_W, n_DU, n_DD))
        return states

    def _is_failed(self, state: tuple) -> bool:
        """Système échoue si n_W < M (canaux fonctionnels insuffisants)."""
        n_W, n_DU, n_DD = state
        return n_W < self.M

    def _build_generator(self, states: list) -> np.ndarray:
        """
        Matrice Q pour PFDavg (temps-dépendant, DU absorbant entre essais).
        
        Transitions : W→DU, W→DD, DD→W, CCF_DU, CCF_DD.
        DU est absorbant (correct pour intégration sur [0,T1]).
        
        FIX MD23 Bug2 : ajout CCF DD.
        """
        n = len(states)
        idx = {s: i for i, s in enumerate(states)}
        Q = np.zeros((n, n))

        for i, (n_W, n_DU, n_DD) in enumerate(states):
            # W → DU (indépendant)
            if n_W > 0:
                tgt = (n_W - 1, n_DU + 1, n_DD)
                if tgt in idx:
                    rate = n_W * self.ldu
                    Q[i, idx[tgt]] += rate; Q[i, i] -= rate

            # W → DD (indépendant)
            if n_W > 0:
                tgt = (n_W - 1, n_DU, n_DD + 1)
                if tgt in idx:
                    rate = n_W * self.ldd
                    Q[i, idx[tgt]] += rate; Q[i, i] -= rate

            # DD → W (réparation)
            if n_DD > 0:
                tgt = (n_W + 1, n_DU, n_DD - 1)
                if tgt in idx:
                    rate = n_DD * self.mu
                    Q[i, idx[tgt]] += rate; Q[i, i] -= rate

            # CCF DU : tous les canaux W passent en DU simultanément
            if n_W > 0 and self.ldu_ccf > 0:
                tgt = (0, n_W + n_DU, n_DD)
                if tgt in idx and tgt != (n_W, n_DU, n_DD):
                    Q[i, idx[tgt]] += self.ldu_ccf; Q[i, i] -= self.ldu_ccf

            # CCF DD : tous les canaux W passent en DD simultanément (MD23 Bug2)
            if n_W > 0 and self.ldd_ccf > 0:
                tgt = (0, n_DU, n_W + n_DD)
                if tgt in idx and tgt != (n_W, n_DU, n_DD):
                    Q[i, idx[tgt]] += self.ldd_ccf; Q[i, i] -= self.ldd_ccf

        return Q

    def _build_generator_pfh(self, states: list) -> np.ndarray:
        """
        Matrice Q pour PFH (steady state) — INCLUT μ_DU.
        
        FIX MD23 Bug1 : sans μ_DU, les états DU sont absorbants
        → π converge vers 100% en états défaillants → PFH faux.
        
        Source : NTNU Ch.5 slide 38, Ch.9 slide 35.
        μ_DU = 1/(T1/2 + MRT) modélise la "réparation" DU au proof test.
        """
        n = len(states)
        idx = {s: i for i, s in enumerate(states)}
        Q = np.zeros((n, n))
        mu_du = 1.0 / (self.T1 / 2.0 + self.p.MTTR)

        for i, (n_W, n_DU, n_DD) in enumerate(states):
            if n_W > 0:
                tgt = (n_W - 1, n_DU + 1, n_DD)
                if tgt in idx:
                    rate = n_W * self.ldu
                    Q[i, idx[tgt]] += rate; Q[i, i] -= rate

            if n_W > 0:
                tgt = (n_W - 1, n_DU, n_DD + 1)
                if tgt in idx:
                    rate = n_W * self.ldd
                    Q[i, idx[tgt]] += rate; Q[i, i] -= rate

            if n_DD > 0:
                tgt = (n_W + 1, n_DU, n_DD - 1)
                if tgt in idx:
                    rate = n_DD * self.mu
                    Q[i, idx[tgt]] += rate; Q[i, i] -= rate

            # DU → W (proof test — MD23 Bug1 fix)
            if n_DU > 0:
                tgt = (n_W + 1, n_DU - 1, n_DD)
                if tgt in idx:
                    rate = n_DU * mu_du
                    Q[i, idx[tgt]] += rate; Q[i, i] -= rate

            if n_W > 0 and self.ldu_ccf > 0:
                tgt = (0, n_W + n_DU, n_DD)
                if tgt in idx and tgt != (n_W, n_DU, n_DD):
                    Q[i, idx[tgt]] += self.ldu_ccf; Q[i, i] -= self.ldu_ccf

            if n_W > 0 and self.ldd_ccf > 0:
                tgt = (0, n_DU, n_W + n_DD)
                if tgt in idx and tgt != (n_W, n_DU, n_DD):
                    Q[i, idx[tgt]] += self.ldd_ccf; Q[i, i] -= self.ldd_ccf

        return Q

    # ── PFDavg (mode basse demande) ──────────────────────────────────────

    def compute_pfdavg(self, method: str = "ode") -> float:
        """PFDavg exact par résolution CTMC sur [0, T1]. Source : MD12 §Résolution."""
        states = self._build_states()
        n = len(states)
        idx = {s: i for i, s in enumerate(states)}
        Q = self._build_generator(states)

        pi0 = np.zeros(n)
        start = (self.N, 0, 0)
        pi0[idx.get(start, 0)] = 1.0

        unavail_idx = [i for i, s in enumerate(states) if self._is_failed(s)]

        if method == "expm":
            return self._compute_expm(Q, pi0, unavail_idx)
        return self._compute_ode(Q, pi0, unavail_idx)

    def _compute_expm(self, Q, pi0, unavail_idx) -> float:
        """PFDavg via exponentielle de matrice (trapèze sur 100 points)."""
        T1 = self.T1
        M_pts = 100
        t_pts = np.linspace(0, T1, M_pts + 1)
        dt = T1 / M_pts
        integral = 0.0
        for k, t in enumerate(t_pts):
            pi_t = pi0 @ expm(Q * t)
            p_unavail = sum(pi_t[i] for i in unavail_idx)
            weight = 0.5 if (k == 0 or k == M_pts) else 1.0
            integral += weight * p_unavail * dt
        return integral / T1

    def _compute_ode(self, Q, pi0, unavail_idx) -> float:
        """PFDavg via intégration ODE (Radau)."""
        T1 = self.T1
        sol = solve_ivp(lambda t, pi: Q.T @ pi, [0, T1], pi0,
                        method='Radau', dense_output=True, rtol=1e-8, atol=1e-10)

        def p_unavail(t):
            pi_t = sol.sol(t)
            return sum(max(0.0, pi_t[i]) for i in unavail_idx)

        integral, _ = quad(p_unavail, 0, T1, limit=500)
        return integral / T1

    # ── PFH (mode haute demande) ─────────────────────────────────────────

    def compute_pfh(self) -> float:
        """
        PFH par Markov steady-state — EXPERIMENTAL.
        
        ATTENTION : Le modèle d'états générique (n_W, n_DU, n_DD) ne modélise pas
        correctement le "DD → shutdown automatique" requis pour PFH.
        Les formules analytiques corrigées (pfh_arch_corrected) sont recommandées.
        
        Ce solveur donne des résultats indicatifs mais pas de référence.
        Pour un Markov PFH exact, il faut des modèles dédiés par architecture
        (cf. Omeiri/Innal 2021, NTNU Ch.9 slides 35-37).
        """
        # Utiliser les formules analytiques corrigées comme fallback fiable
        from .formulas import pfh_arch_corrected
        return pfh_arch_corrected(self.p)

    # ── MTTFS (Mean Time To First System Failure) ────────────────────────

    def compute_mttfs(self) -> dict:
        """
        MTTFS via résolution Q_safe × m = -1.
        Source : NTNU Ch.5 slides 40-45 (MD 24_MTTFS_PST_PFH_NTNU).
        """
        states = self._build_states()
        n = len(states)
        Q = self._build_generator_pfh(states)

        failed = [i for i, s in enumerate(states) if self._is_failed(s)]
        safe = [i for i in range(n) if i not in failed]

        if not safe:
            return {"mttfs_hours": 0.0, "mttfs_years": 0.0}

        n_safe = len(safe)
        Q_safe = np.zeros((n_safe, n_safe))
        for ii, i in enumerate(safe):
            for jj, j in enumerate(safe):
                Q_safe[ii, jj] = Q[i, j]

        # MTTFS = -Q_safe^(-1) × 1 → résoudre Q_safe × m = -1
        ones = -np.ones(n_safe)
        try:
            m = np.linalg.solve(Q_safe, ones)
        except np.linalg.LinAlgError:
            m = np.linalg.lstsq(Q_safe, ones, rcond=None)[0]

        # MTTFS = m[idx_initial] (état initial = all OK)
        start_state = (self.N, 0, 0)
        start_idx_global = next((i for i, s in enumerate(states) if s == start_state), 0)
        start_idx_safe = safe.index(start_idx_global) if start_idx_global in safe else 0
        mttfs = max(0.0, m[start_idx_safe])

        return {
            "mttfs_hours": mttfs,
            "mttfs_years": mttfs / 8760.0,
            "n_safe_states": n_safe,
            "n_total_states": n,
        }


# ─────────────────────────────────────────────────────────────────────────────
# API publique — point d'entrée unifié
# ─────────────────────────────────────────────────────────────────────────────

def compute_exact(p: SubsystemParams, mode: str = "low_demand") -> dict:
    """
    Calcul Markov exact pour un sous-système.
    
    Args:
        p    : paramètres du sous-système
        mode : 'low_demand' (PFDavg) ou 'high_demand' (PFH)
    """
    from .formulas import lambda_T1_product, pfd_arch, pfh_arch, pfh_arch_corrected

    warnings = []
    lambda_t1 = lambda_T1_product(p)
    if lambda_t1 > 0.3:
        warnings.append(f"λ×T1 = {lambda_t1:.3f} > 0.3 : Markov exact requis")
    elif lambda_t1 > 0.1:
        warnings.append(f"λ×T1 = {lambda_t1:.3f} > 0.1 : Markov exact recommandé")

    solver = MarkovSolver(p)

    if mode == "low_demand":
        n_states = len(solver._build_states())
        method = "ode" if n_states <= 20 else "expm"
        pfdavg = solver.compute_pfdavg(method=method)

        pfd_iec = pfd_arch(p)
        ecart = (pfd_iec - pfdavg) / pfdavg * 100 if pfdavg > 0 else 0.0
        if abs(ecart) > 10:
            warnings.append(f"Écart IEC vs Markov : {ecart:.1f}% (IEC={pfd_iec:.3e}, Markov={pfdavg:.3e})")

        mttfs = solver.compute_mttfs()

        return {
            "pfdavg": pfdavg,
            "rrf": 1.0 / pfdavg if pfdavg > 0 else float("inf"),
            "sil": sil_from_pfd(pfdavg),
            "pfd_iec_approx": pfd_iec,
            "ecart_pct": ecart,
            "lambda_T1": lambda_t1,
            "method": f"Markov-CTMC ({method})",
            "n_states": n_states,
            "mttfs": mttfs,
            "warnings": warnings,
        }

    else:  # high_demand
        pfh = solver.compute_pfh()
        pfh_iec = pfh_arch(p)
        pfh_corr = pfh_arch_corrected(p)

        return {
            "pfh": pfh,
            "pfh_iec": pfh_iec,
            "pfh_corrected": pfh_corr,
            "sil": sil_from_pfh(pfh),
            "sil_iec": sil_from_pfh(pfh_iec),
            "lambda_T1": lambda_t1,
            "method": "analytique-corrigée (Omeiri/Innal 2021)",
            "mttfs": solver.compute_mttfs(),
            "warnings": warnings,
        }
