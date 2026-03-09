"""
Extension PDS : PTIF et CSU.
Sources : PDS Method (SINTEF), NTNU Ch.8 PDS (MD 16_PDS_PTIF_CSU).
"""

from .formulas import SubsystemParams, pfd_arch, sil_from_pfd


class PDSSolver:
    """Calcul PDS : PFD + PTIF = CSU."""

    def __init__(self, p: SubsystemParams,
                 ptif_fraction: float = 0.05,
                 cPT: float = 1.0,
                 additional_ptif: float = 0.0):
        self.p = p
        self.ptif_fraction = ptif_fraction
        self.cPT = cPT
        self.additional_ptif = additional_ptif

    def compute(self) -> dict:
        """
        PFD + PTIF = CSU selon méthode PDS.
        PTIF = λ_DU_uncov × T1/2 + additional_ptif
        CSU = PFD + PTIF
        """
        p = self.p
        pfd = pfd_arch(p)
        ldu_uncov = p.lambda_DU * self.ptif_fraction * (1.0 - self.cPT)
        ptif = ldu_uncov * p.T1 / 2.0 + self.additional_ptif
        csu = pfd + ptif
        sil_pfd = sil_from_pfd(pfd)
        sil_csu = sil_from_pfd(csu)

        warnings = []
        if sil_csu < sil_pfd:
            warnings.append(f"SIL CSU ({sil_csu}) < SIL PFD ({sil_pfd}). Utiliser CSU pour classement PDS.")
        if self.ptif_fraction > 0.1:
            warnings.append(f"ptif_fraction = {self.ptif_fraction:.0%} élevé.")

        return {
            "pfd": pfd, "ptif": ptif, "csu": csu,
            "sil_from_pfd": sil_pfd, "sil_from_csu": sil_csu,
            "ldu_uncov": ldu_uncov, "ptif_fraction": self.ptif_fraction, "cPT": self.cPT,
            "rrf_pfd": 1.0 / pfd if pfd > 0 else float("inf"),
            "rrf_csu": 1.0 / csu if csu > 0 else float("inf"),
            "warnings": warnings,
        }

    def sensitivity_cPT(self, cPT_range=None) -> list:
        """Analyse de sensibilité : impact de cPT sur CSU."""
        if cPT_range is None:
            import numpy as np
            cPT_range = np.arange(0.5, 1.01, 0.05)
        results = []
        for cPT in cPT_range:
            r = PDSSolver(self.p, self.ptif_fraction, cPT, self.additional_ptif).compute()
            results.append({"cPT": cPT, "pfd": r["pfd"], "ptif": r["ptif"], "csu": r["csu"], "sil": r["sil_from_csu"]})
        return results
