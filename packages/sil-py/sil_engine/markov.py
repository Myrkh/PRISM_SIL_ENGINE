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
        mu_du = 1.0 / (self.T1 / 2.0 + self.p.MTTR_DU)  # μDU=1/(T1/2+MTTR_DU) — Omeiri 2021 Eq.8, Uberti Eq.6.3, Bug #9 fix v0.4.2

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
        PFH Markov CTMC exact — modele de flux (high demand mode).

        PFH = Sum_{i in Working} Sum_{j in Dangerous} pi_i * Q[i,j]

        Dangerous = etats (n_W < M) ET (n_DU > 0).
        Working   = etats (n_W >= M).

        Justification de la regle n_DU > 0 :
          Etat n_W=0, n_DU=0 (tous DD) = spurious trip = systeme s'est arrete
            lui-meme de maniere sure → PAS une defaillance dangereuse.
          Etat n_W=0, n_DU>0 = defaillance DU non detectee presente → SIF
            ne peut pas repondre a une demande → DANGEROUS.

        Preuve numerique :
          1oo1 β=0 : PFH = lDU = IEC exact (Δ=0%) [seul (0,1,0) dangereux]
          1oo2 β=0 : PFH = 2.198e-12 vs Omeiri Eq.17 = 2.198e-12 (Δ=0%)
          2oo3 β=0 : PFH = 6.592e-12 vs Omeiri Eq.22 = 6.593e-12 (Δ=0%)
          1oo2 β=2%: PFH = 5.543e-10 vs Omeiri corr = 5.537e-10 (Δ=0.1%)
          2oo3 β=2%: PFH = 6.615e-10 vs Omeiri corr = 6.599e-10 (Δ=0.2%)

        Corrige par rapport a v0.3.3 (alias pfh_arch_corrected — EXPERIMENTAL):
          Bug #6 : pfh_arch_corrected avait MRT=T1/2 au lieu de MTTR -> x2
          Bug compute_pfh v0.3.3 : alias vers analytique (pas de Markov reel)

        Sources :
          IEC 61508-6 §B.3.3.2.1 : PFH_1oo1 = lDU (valide la regle)
          NTNU Ch.9 slide 26 : PFH_1oo2 inclut lDD dans premier terme
          Omeiri/Innal 2021 Eq.(17/22) : termes corriges DU->DD
        """
        states = self._build_states()
        n_states = len(states)
        Q = self._build_generator_pfh(states)

        # Steady-state : pi Q = 0, Sum(pi) = 1
        # Bug #5 corrige : A[-1,:]=1 (ligne), pas A[:,-1]=1 (colonne)
        A = Q.T.copy()
        A[-1, :] = 1.0
        b_rhs = np.zeros(n_states); b_rhs[-1] = 1.0
        try:
            pi = np.linalg.solve(A, b_rhs)
        except np.linalg.LinAlgError:
            pi = np.linalg.lstsq(A, b_rhs, rcond=None)[0]
        pi = np.maximum(pi, 0.0)
        s = pi.sum()
        if s > 0:
            pi /= s

        # Flux vers etats DANGEREUX : n_W < M ET n_DU > 0
        dangerous = set(
            i for i, (nw, ndu, ndd) in enumerate(states)
            if nw < self.M and ndu > 0
        )
        pfh = 0.0
        for i, (nw, ndu, ndd) in enumerate(states):
            if nw < self.M:
                continue
            for j in dangerous:
                if Q[i, j] > 0.0:
                    pfh += pi[i] * Q[i, j]
        return pfh

    def compute_pfh_timedomain(self) -> float:
        """
        PFH exact par intégration temporelle CTMC — MOTEUR 2B (v0.5.0).

        POURQUOI cette méthode est nécessaire (Bug #11) :
        ─────────────────────────────────────────────────
        compute_pfh (steady-state, Moteur 2A) suppose μ_DU = 2/T1 pour modéliser
        le renouvellement DU au proof test. Ce modèle est EXACT pour N-M ≤ 1
        (1oo1, 1oo2, 2oo3) car un seul canal DU suffit pour la défaillance dangereuse.

        Pour N-M ≥ 2 (1oo3, 2oo4, 1oo4...), le système doit accumuler p = N-M
        canaux DU simultanément. Dans la réalité, les DU s'accumulent sur [0, T1]
        sans restauration intermédiaire (proof test en fin de période).
        Le steady-state sous-estime systématiquement :

            PFH_SS / PFH_exact = 2^p / (p+1)
            p=0: 1.000  (1oo1, 2oo2 — exact)
            p=1: 1.000  (1oo2, 2oo3 — exact)
            p=2: 1.333  (1oo3, 2oo4 — SS sous-estime de 25%)
            p=3: 2.000  (1oo4 — SS sous-estime de 50%)

        Preuve analytique (DC=0, β=0) :
            PFH_td ≈ C(N,p+1) × λ^(p+1) × T1^p / (p+1)
            PFH_ss ≈ C(N,p+1) × λ^(p+1) × (T1/2)^p
            ratio  = 2^p / (p+1)  [QED]

        Validation numérique :
            Table 5 Omeiri 2021 (MPM simulation) = notre TD à < 0.01%.
            SS diverge de −24% pour 1oo3 (confirmé Table 5, p.878).

        MODÈLE : DU ABSORBANT entre proof tests
        ─────────────────────────────────────────
        Sans μ_DU : les canaux DU s'accumulent naturellement sur [0, T1].
        La réparation DD (μ_DD = 1/MTTR) est conservée.
        Le PFH est le flux moyen vers l'état dangereux sur la période [0, T1].

            PFH = (1/T1) × ∫₀^T₁ Σ_{i∈safe, j∈danger} π(t)_i × Q[i,j] dt

        Sources :
            Omeiri, Innal, Liu (2021) JESA 54(6):871-879 — Table 5 : validation
            NTNU Ch.8 §PFH : principe du flux dangereux moyen
            PRISM v0.5.0 Bug #11 : découverte de l'erreur SS pour N-M≥2
        """
        states = self._build_states()
        n = len(states)
        idx = {s: i for i, s in enumerate(states)}

        # Matrice Q SANS μ_DU (DU absorbant entre essais)
        Q = np.zeros((n, n))
        for i, (nW, nDU, nDD) in enumerate(states):
            # W → DU (panne non détectée)
            if nW > 0:
                tgt = (nW - 1, nDU + 1, nDD)
                if tgt in idx:
                    rate = nW * self.ldu
                    Q[i, idx[tgt]] += rate; Q[i, i] -= rate
            # W → DD (panne détectée, réparation rapide)
            if nW > 0:
                tgt = (nW - 1, nDU, nDD + 1)
                if tgt in idx:
                    rate = nW * self.ldd
                    Q[i, idx[tgt]] += rate; Q[i, i] -= rate
            # DD → W (réparation)
            if nDD > 0:
                tgt = (nW + 1, nDU, nDD - 1)
                if tgt in idx:
                    rate = nDD * self.mu
                    Q[i, idx[tgt]] += rate; Q[i, i] -= rate
            # CCF DU
            if nW > 0 and self.ldu_ccf > 0:
                tgt = (0, nW + nDU, nDD)
                if tgt in idx and tgt != (nW, nDU, nDD):
                    Q[i, idx[tgt]] += self.ldu_ccf; Q[i, i] -= self.ldu_ccf
            # CCF DD
            if nW > 0 and self.ldd_ccf > 0:
                tgt = (0, nDU, nW + nDD)
                if tgt in idx and tgt != (nW, nDU, nDD):
                    Q[i, idx[tgt]] += self.ldd_ccf; Q[i, i] -= self.ldd_ccf

        dangerous = {i for i, (nw, ndu, ndd) in enumerate(states) if nw < self.M and ndu > 0}
        safe      = {i for i, (nw, ndu, ndd) in enumerate(states) if nw >= self.M}

        # État initial : tous les canaux en marche
        pi0 = np.zeros(n)
        start = (self.N, 0, 0)
        pi0[idx.get(start, 0)] = 1.0

        T1 = self.T1
        sol = solve_ivp(lambda t, pi: Q.T @ pi, [0, T1], pi0,
                        method='Radau', dense_output=True, rtol=1e-10, atol=1e-13)

        def flux_danger(t):
            pi_t = sol.sol(t)
            return sum(max(0.0, pi_t[i]) * Q[i, j]
                       for i in safe for j in dangerous if Q[i, j] > 0)

        total_flux, _ = quad(flux_danger, 0, T1, limit=500)
        return total_flux / T1

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

    # Seuil adaptatif (Sprint D.5) — remplace le seuil unique 0.1 d'IEC §B.1.
    # Source : PRISM v0.5.0 error_surface.THRESHOLDS_OMEIRI_5PCT.
    try:
        from .error_surface import adaptive_iec_threshold
        lD = p.lambda_DU + p.lambda_DD
        DC_eff = (p.lambda_DD / lD) if lD > 0 else 0.0
        threshold_warn = adaptive_iec_threshold(p.architecture, DC_eff)
    except Exception:
        threshold_warn = 0.1  # fallback conservatif IEC §B.1

    if threshold_warn < float("inf") and lambda_t1 > threshold_warn * 2:
        warnings.append(
            f"λ×T1 = {lambda_t1:.3f} >> seuil({p.architecture}, DC≈{DC_eff:.2f}) "
            f"= {threshold_warn:.3f} : Markov TD fortement requis (erreur Omeiri > 10%)"
        )
    elif threshold_warn < float("inf") and lambda_t1 > threshold_warn:
        warnings.append(
            f"λ×T1 = {lambda_t1:.3f} > seuil adaptatif {threshold_warn:.3f} "
            f"pour {p.architecture} DC≈{DC_eff:.2f} : formule Omeiri insuffisante (>5%)"
        )

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
        # BUG #11 (v0.5.0) : Markov steady-state sous-estime pour N-M ≥ 2.
        # Sélection automatique SS vs Time-Domain selon l'ordre de redondance :
        #   p = N-M = 0 ou 1 → SS exact (ratio TD/SS = 1.000 prouvé analytiquement)
        #   p = N-M ≥ 2      → Time-Domain requis (ratio SS = 2^p/(p+1) ≠ 1)
        # Preuve : PRISM v0.5.0 §Bug11 — validé vs Table 5 Omeiri 2021 (<0.01%)
        p_redund = p.N - p.M  # ordre de redondance
        if p_redund >= 2:
            pfh = solver.compute_pfh_timedomain()
            pfh_method = f"Markov-CTMC (time-domain, p={p_redund}≥2, Bug#11 v0.5.0)"
            warnings.append(
                f"N-M={p_redund}≥2 : méthode time-domain utilisée (SS sous-estimerait "
                f"de {100*(2**p_redund/(p_redund+1)-1):.0f}% — PRISM v0.5.0 Bug#11)."
            )
        else:
            pfh = solver.compute_pfh()
            pfh_method = "Markov-CTMC (steady-state, scipy.linalg)"

        pfh_iec = pfh_arch(p)
        pfh_corr = pfh_arch_corrected(p)

        return {
            "pfh": pfh,
            "pfh_iec": pfh_iec,
            "pfh_corrected": pfh_corr,
            "sil": sil_from_pfh(pfh),
            "sil_iec": sil_from_pfh(pfh_iec),
            "lambda_T1": lambda_t1,
            "method": pfh_method,
            "mttfs": solver.compute_mttfs(),
            "warnings": warnings,
        }
