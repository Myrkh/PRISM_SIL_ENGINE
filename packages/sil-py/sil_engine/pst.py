"""
PST — Partial Stroke Test : Markov multi-phases + analytique koon.

Sources :
  - IEC 61508-6 §B.3.4 (MD 15_PST_EXACT_FORMULAS)
  - NTNU Ch.11 slides 20-31 (MD 24_MTTFS_PST_PFH_NTNU)
  - Bug fix linking matrix (MD 23_CODE_BUGFIXES Bug 4)

CRITIQUE : Les formules PST de l'IEC sont incorrectes.
Ce module implémente le calcul exact par CTMC multi-phases.
"""

import numpy as np
from scipy.integrate import solve_ivp, quad
from .formulas import SubsystemParams, sil_from_pfd


class PSTSolver:
    """
    Solveur Markov multi-phases pour systèmes avec PST.
    
    États : 0=W, 1=DU_cov (couvert par PST), 2=DU_unc (non couvert), 3=DD
    
    Linking matrices (NTNU Ch.11 slides 20-31) :
      PST : DU_cov → W (réparé), DU_unc → DU_unc (reste)
      FT  : tout → W si PTC=1, sinon DU_unc reste avec prob (1-PTC)
    """

    def __init__(self, p: SubsystemParams,
                 T_PST: float = 720.0,
                 c_PST: float = 0.70,
                 d_PST: float = 2.0):
        self.p = p
        self.T_PST = T_PST
        self.c_PST = c_PST
        self.d_PST = d_PST
        self.mu = 1.0 / p.MTTR if p.MTTR > 0 else 1.0 / 8.0
        self.ldu_cov = p.lambda_DU * c_PST
        self.ldu_unc = p.lambda_DU * (1 - c_PST)
        self.ldd = p.lambda_DD
        self.n_pst = max(1, int(p.T1 / T_PST))
        self.T1 = p.T1

    def compute_pfdavg(self) -> dict:
        """PFDavg avec PST par CTMC multi-phases."""
        pfd_with_pst = self._integrate_multiphase()
        pfd_without_pst = self._pfd_no_pst()
        pfd_iec_pst = self._pfd_iec_formula()

        improvement = pfd_without_pst / pfd_with_pst if pfd_with_pst > 0 else 1.0
        iec_error = (pfd_iec_pst - pfd_with_pst) / pfd_with_pst * 100 if pfd_with_pst > 0 else 0.0

        warnings = []
        if abs(iec_error) > 5:
            warnings.append(
                f"Formule IEC PST donne {pfd_iec_pst:.3e} vs Markov exact {pfd_with_pst:.3e} "
                f"(écart {iec_error:+.1f}%). Utiliser le résultat Markov."
            )

        return {
            "pfdavg_with_pst": pfd_with_pst,
            "pfdavg_without_pst": pfd_without_pst,
            "pfdavg_iec_formula": pfd_iec_pst,
            "improvement_factor": improvement,
            "iec_error_pct": iec_error,
            "n_pst_per_T1": self.n_pst,
            "T_PST": self.T_PST,
            "c_PST": self.c_PST,
            "sil_with_pst": sil_from_pfd(pfd_with_pst),
            "sil_without_pst": sil_from_pfd(pfd_without_pst),
            "warnings": warnings,
        }

    def _build_q_pst(self) -> np.ndarray:
        """Matrice Q : états W, DU_cov, DU_unc, DD."""
        Q = np.zeros((4, 4))
        Q[0, 1] = self.ldu_cov;  Q[0, 0] -= self.ldu_cov
        Q[0, 2] = self.ldu_unc;  Q[0, 0] -= self.ldu_unc
        Q[0, 3] = self.ldd;      Q[0, 0] -= self.ldd
        Q[3, 0] = self.mu;       Q[3, 3] = -self.mu
        return Q

    def _apply_pst_reset(self, pi: np.ndarray) -> np.ndarray:
        """
        Linking matrix PST (NTNU Ch.11 slide 31) :
          W       → W       (1.0)
          DU_cov  → W       (1.0)  [détecté par PST, réparé]
          DU_unc  → DU_unc  (1.0)  [non détecté, reste]
          DD      → DD      (1.0)  [inchangé par PST]
        """
        return np.array([
            pi[0] + pi[1],   # W + DU_cov réparé
            0.0,              # DU_cov → 0
            pi[2],            # DU_unc reste
            pi[3],            # DD inchangé
        ])

    def _apply_ft_reset(self, pi: np.ndarray) -> np.ndarray:
        """
        Linking matrix FT (proof test complet) — NTNU Ch.11 slide 31.
        FIX MD23 Bug 4 : respecte PTC (proof test coverage).
        
          W       → W       (1.0)
          DU_cov  → W       (1.0)
          DU_unc  → W       (PTC)
          DU_unc  → DU_unc  (1-PTC)  [reste si non couvert]
          DD      → W       (1.0)    [réparé]
        """
        PTC = self.p.PTC
        return np.array([
            pi[0] + pi[1] + pi[2] * PTC + pi[3],  # W
            0.0,
            pi[2] * (1.0 - PTC),                    # DU_unc non couvert
            0.0,
        ])

    def _integrate_multiphase(self) -> float:
        """Intégration multi-phases : N PSTs + 1 FT par période T1."""
        Q = self._build_q_pst()
        dt_phase = self.T_PST
        pi_current = np.array([1.0, 0.0, 0.0, 0.0])
        total_integral = 0.0
        unavail_idx = [1, 2, 3]
        t_current = 0.0

        for phase in range(self.n_pst):
            t_end = min(t_current + dt_phase, self.T1)
            dt = t_end - t_current

            sol = solve_ivp(lambda t, pi: Q.T @ pi, [0, dt], pi_current,
                            method='Radau', dense_output=True, rtol=1e-8, atol=1e-10)

            integral, _ = quad(
                lambda t: sum(max(0.0, sol.sol(t)[i]) for i in unavail_idx),
                0, dt, limit=200)
            total_integral += integral

            pi_end = sol.sol(dt)

            if phase < self.n_pst - 1:
                pi_current = self._apply_pst_reset(pi_end)
            else:
                pi_current = self._apply_ft_reset(pi_end)

            t_current = t_end

        return total_integral / self.T1

    def _pfd_no_pst(self) -> float:
        """PFD sans PST (proof test seul à T1)."""
        Q = self._build_q_pst()
        pi0 = np.array([1.0, 0.0, 0.0, 0.0])
        sol = solve_ivp(lambda t, pi: Q.T @ pi, [0, self.T1], pi0,
                        method='Radau', dense_output=True, rtol=1e-8, atol=1e-10)
        integral, _ = quad(
            lambda t: sum(max(0.0, sol.sol(t)[i]) for i in [1, 2, 3]),
            0, self.T1, limit=200)
        return integral / self.T1

    def _pfd_iec_formula(self) -> float:
        """Formule IEC PST (incorrecte — pour comparaison). MD15."""
        return (self.ldu_cov * self.T_PST / 2.0
                + self.ldu_unc * self.T1 / 2.0
                + self.ldd * self.p.MTTR)


# ─────────────────────────────────────────────────────────────────────────────
# PST Analytique koon — NTNU Ch.11 slides 28-30
# Source : MD 24_MTTFS_PST_PFH_NTNU §2
# ─────────────────────────────────────────────────────────────────────────────

def pst_analytical_koon(p: SubsystemParams,
                        T_PST: float,
                        c_PST: float) -> float:
    """
    PFDavg avec PST — formule analytique koon.
    Source : NTNU Ch.11 slides 28-30 (MD24).
    
    1oo1 : PFDavg = Θ×λ_DU×τ_PST/2 + (1-Θ)×λ_DU×τ/2 + λ_DD×MTTR
    1oo2 : PFDavg = 2×[...]²×tCE(PST)×tGE(PST) + CCF terms
    """
    k, n = p.M, p.N
    theta = c_PST
    tau = p.T1
    tau_pst = T_PST
    ldu = p.lambda_DU
    ldd = p.lambda_DD
    ld = ldu + ldd
    mttr = p.MTTR
    mrt = tau / 2.0

    if k == 1 and n == 1:
        return (theta * ldu * tau_pst / 2.0
                + (1 - theta) * ldu * tau / 2.0
                + ldd * mttr)

    # tCE et tGE modifiés pour PST (NTNU Ch.11 slide 29)
    if ld > 0:
        t_CE = (theta * (ldu / ld) * (tau_pst / 2.0 + mrt)
                + (1 - theta) * (ldu / ld) * (tau / 2.0 + mrt)
                + (ldd / ld) * mttr)
        t_GE = (theta * (ldu / ld) * (tau_pst / 3.0 + mrt)
                + (1 - theta) * (ldu / ld) * (tau / 3.0 + mrt)
                + (ldd / ld) * mttr)
    else:
        t_CE = tau / 2.0
        t_GE = tau / 3.0

    ldu_ind = (1 - p.beta) * ldu
    ldd_ind = (1 - p.beta_D) * ldd

    if k == 1 and n == 2:
        pfd_ind = 2.0 * (ldu_ind + ldd_ind) ** 2 * t_CE * t_GE
        pfd_ccf = (theta * p.beta * ldu * (tau_pst / 2.0 + mrt)
                   + (1 - theta) * p.beta * ldu * (tau / 2.0 + mrt)
                   + p.beta_D * ldd * mttr)
        return pfd_ind + pfd_ccf

    if k == 2 and n == 3:
        pfd_ind = 3.0 * (ldu_ind + ldd_ind) ** 2 * t_CE * t_GE
        pfd_ccf = (theta * p.beta * ldu * (tau_pst / 2.0 + mrt)
                   + (1 - theta) * p.beta * ldu * (tau / 2.0 + mrt)
                   + p.beta_D * ldd * mttr)
        return pfd_ind + pfd_ccf

    # Fallback
    from .formulas import pfd_arch
    return pfd_arch(p)
