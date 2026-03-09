"""
Moteur Monte Carlo pour PRISM — Moteur 3.
Source : IEC 61508-6 §B.5.3 et B.6.

Usage :
    mc = SystemMonteCarlo(request)
    result = mc.run(n_simulations=10000)
"""

import numpy as np
from scipy import stats
from typing import Optional, Callable
from .formulas import SubsystemParams, pfd_arch, sil_from_pfd


class UncertaintyModel:
    """
    Distribution d'incertitude sur un taux de défaillance λ.
    IEC 61508-6 §B.6 : recommande la loi log-normale.
    """

    def __init__(self, lambda_mean: float,
                 error_factor: float = 3.0,
                 dist_type: str = "lognormal"):
        self.lambda_mean = lambda_mean
        self.ef = error_factor
        self.dist_type = dist_type
        # Paramètres log-normale : σ_ln = ln(ef) / 1.645 (IC 90%)
        self.sigma_ln = np.log(error_factor) / 1.645
        self.mu_ln = np.log(lambda_mean)

    def sample(self, n: int, rng: np.random.Generator) -> np.ndarray:
        if self.dist_type == "lognormal":
            return rng.lognormal(self.mu_ln, self.sigma_ln, n)
        elif self.dist_type == "uniform":
            lo, hi = self.lambda_mean / self.ef, self.lambda_mean * self.ef
            return rng.uniform(lo, hi, n)
        elif self.dist_type == "triangular":
            lo, hi = self.lambda_mean / self.ef, self.lambda_mean * self.ef
            return rng.triangular(lo, self.lambda_mean, hi, n)
        return rng.lognormal(self.mu_ln, self.sigma_ln, n)

    def ci_90(self) -> tuple:
        lo = stats.lognorm.ppf(0.05, s=self.sigma_ln, scale=np.exp(self.mu_ln))
        hi = stats.lognorm.ppf(0.95, s=self.sigma_ln, scale=np.exp(self.mu_ln))
        return lo, hi

    @staticmethod
    def from_observations(n_failures: int, T_obs: float,
                          alpha: float = 0.05) -> "UncertaintyModel":
        """Construit depuis données d'observation (Chi-2, IEC B.6)."""
        lambda_hat = n_failures / T_obs if T_obs > 0 else 1e-6
        if n_failures > 0:
            lambda_inf = stats.chi2.ppf(1 - alpha, 2 * n_failures) / (2 * T_obs)
            lambda_sup = stats.chi2.ppf(alpha, 2 * (n_failures + 1)) / (2 * T_obs)
            ef = np.sqrt(lambda_sup / lambda_inf) if lambda_inf > 0 else 3.0
        else:
            ef = 3.0
        return UncertaintyModel(lambda_hat, ef)


class SystemMonteCarlo:
    """
    Monte Carlo pour propagation d'incertitudes sur PFDavg.
    Implémente Figure B.38 de l'IEC 61508-6.
    """

    def __init__(self, seed: int = 42):
        self.rng = np.random.default_rng(seed)

    def run(self,
            subsystems: list,
            n_simulations: int = 10000,
            progress_callback: Optional[Callable] = None) -> dict:
        """
        Propage les incertitudes sur λ vers l'incertitude sur PFDavg global.
        
        Args:
            subsystems : liste de dict {
                'params': SubsystemParams,
                'uncertainty': UncertaintyModel (optionnel),
                'architecture': str,
                'weight': float (contribution en série, par défaut 1.0)
            }
            n_simulations : nombre d'itérations Monte Carlo
        
        Returns:
            dict avec statistiques complètes
        """
        pfd_samples = np.zeros(n_simulations)
        report_every = max(1, n_simulations // 10)

        for i in range(n_simulations):
            pfd_total = 0.0

            for sub in subsystems:
                p = sub["params"]

                # Tirer λ selon incertitude si disponible
                if "uncertainty" in sub and sub["uncertainty"] is not None:
                    unc: UncertaintyModel = sub["uncertainty"]
                    lambda_D = unc.sample(1, self.rng)[0]
                    DC = p.DC
                    p_sampled = SubsystemParams(
                        lambda_DU=lambda_D * (1 - DC),
                        lambda_DD=lambda_D * DC,
                        DC=DC,
                        beta=p.beta,
                        beta_D=p.beta_D,
                        MTTR=p.MTTR,
                        T1=p.T1,
                        PTC=p.PTC,
                        architecture=p.architecture,
                        M=p.M,
                        N=p.N,
                    )
                else:
                    p_sampled = p

                arch = sub.get("architecture", p.architecture)
                pfd_sub = pfd_arch(p_sampled, arch)
                pfd_total += pfd_sub

            pfd_samples[i] = pfd_total

            if progress_callback and (i + 1) % report_every == 0:
                progress_callback(int((i + 1) / n_simulations * 100))

        return self._statistics(pfd_samples, n_simulations)

    def _statistics(self, samples: np.ndarray, n: int) -> dict:
        valid = samples[samples > 0]
        if len(valid) == 0:
            return {"error": "No valid samples"}

        mean = float(np.mean(valid))
        std = float(np.std(valid))
        ci_half = 1.645 * std / np.sqrt(n)

        return {
            "n_simulations": n,
            "mean": mean,
            "median": float(np.median(valid)),
            "std": std,
            "p5": float(np.percentile(valid, 5)),
            "p10": float(np.percentile(valid, 10)),
            "p50": float(np.percentile(valid, 50)),
            "p90": float(np.percentile(valid, 90)),
            "p95": float(np.percentile(valid, 95)),
            "ci_90_lower": float(mean - ci_half),
            "ci_90_upper": float(mean + ci_half),
            "rrf_mean": float(1.0 / mean) if mean > 0 else float("inf"),
            "sil_p50": sil_from_pfd(float(np.percentile(valid, 50))),
            "sil_p95": sil_from_pfd(float(np.percentile(valid, 95))),
            "histogram_log10": [float(x) for x in np.log10(valid)],
        }
