"""
sil-engine — IEC 61508-6 SIL Calculation Engine
=================================================
Open-source. Auditable. Validated.

The first fully transparent IEC 61508-6 calculation engine.
Every formula is traceable to its source. Every result is reproducible.

Quick start
-----------
    from sil_engine import SubsystemParams, pfd_arch, pfh_moon, sil_achieved

    p = SubsystemParams(
        lambda_DU = 5e-8,   # dangerous undetected failure rate [1/h]
        lambda_DD = 4.5e-7, # dangerous detected failure rate [1/h]
        DC   = 0.9,         # diagnostic coverage
        beta = 0.02,        # CCF beta-factor
        MTTR = 8.0,         # mean time to repair [h]
        T1   = 8760.0,      # proof test interval [h]
    )

    pfd = pfd_arch(p, "1oo2")                          # PFDavg
    pfh = pfh_moon(p, k=2, n=4)                        # PFH 2oo4 (generalised)
    verdict = sil_achieved(pfd, p.lambda_DU,            # full SIL verdict
                           p.lambda_DD, lambda_S=1e-9,
                           k=1, n=2, component_type="B")
    print(f"SIL {verdict['sil_final']}")

Sources
-------
    IEC 61508-6:2010 Annex B (NF EN 61508-6:2011)
    NTNU RAMS Group — Lundteigen & Rausand (public slides, ntnu.edu)
    Omeiri, Innal, Liu (2021) JESA 54(6):871-879  DOI:10.21152/1750-9548.15.4.871
"""

__version__ = "0.3.3"
__license__ = "LGPL-3.0-or-later"

# ── Core model ────────────────────────────────────────────────────────────────
from .formulas import SubsystemParams

# ── PFD — low demand mode (IEC 61508-6 §B.3.2) ───────────────────────────────
from .formulas import (
    pfd_arch,            # dispatch by name:  pfd_arch(p, "1oo2")
    pfd_1oo1, pfd_1oo2, pfd_2oo2, pfd_2oo3, pfd_1oo3, pfd_1oo2d,
    pfd_moon,            # MooN generic via p.M / p.N fields
    pfd_imperfect_test,  # PTC < 1
)

# ── PFH — high demand / continuous mode (IEC 61508-6 §B.3.3) ─────────────────
from .formulas import (
    pfh_arch,            # standard architectures
    pfh_arch_corrected,  # Omeiri/Innal 2021 corrected terms
    pfh_1oo1, pfh_1oo2, pfh_1oo2_ntnu, pfh_2oo2, pfh_2oo3, pfh_1oo3,
)

# ── SIL lookup ────────────────────────────────────────────────────────────────
from .formulas import sil_from_pfd, sil_from_pfh

# ── Extensions V3.3 ──────────────────────────────────────────────────────────
from .extensions import (
    # Generalised kooN  (1oo4, 2oo4, 3oo4, any k-out-of-n)
    pfh_moon,            # pfh_moon(p, k, n)
    pfh_moon_arch,       # pfh_moon_arch(p, "2oo4")
    pfd_koon_generic,    # pfd_koon_generic(p, k, n)
    pfd_arch_extended,   # pfd_arch_extended(p, "1oo4")  — with fallback

    # PFD(t) instantaneous sawtooth curve
    pfd_instantaneous,   # returns PFDCurveResult
    PFDCurveResult,

    # CCF — Multiple Greek Letters (MGL)  IEC 61508-6 Annex D
    pfd_mgl, pfh_mgl,
    MGLParams,           # MGLParams(beta, gamma, delta)

    # Architectural constraints  IEC 61508-2 Table 2  Route 1H / 2H
    architectural_constraints,
    sil_achieved,        # min(SIL_probabilistic, SIL_architectural)
    ArchConstraintResult,

    # Demand duration model  (NTNU Ch8)
    pfd_demand_duration,

    # Auto-routing IEC ↔ Markov CTMC
    route_compute,
)

# ── Exact Markov solver ───────────────────────────────────────────────────────
from .markov import MarkovSolver, compute_exact

# ── PST — Partial Stroke Test ─────────────────────────────────────────────────
from .pst import PSTSolver, pst_analytical_koon

# ── STR — Spurious Trip Rate ──────────────────────────────────────────────────
from .str_solver import str_analytical, str_markov

# ── Monte Carlo uncertainty propagation ───────────────────────────────────────
from .montecarlo import SystemMonteCarlo

__all__ = [
    "SubsystemParams",
    # PFD
    "pfd_arch", "pfd_1oo1", "pfd_1oo2", "pfd_2oo2", "pfd_2oo3",
    "pfd_1oo3", "pfd_1oo2d", "pfd_moon", "pfd_imperfect_test",
    # PFH
    "pfh_arch", "pfh_arch_corrected",
    "pfh_1oo1", "pfh_1oo2", "pfh_1oo2_ntnu", "pfh_2oo2", "pfh_2oo3", "pfh_1oo3",
    # SIL
    "sil_from_pfd", "sil_from_pfh",
    # Extensions
    "pfh_moon", "pfh_moon_arch",
    "pfd_koon_generic", "pfd_arch_extended",
    "pfd_instantaneous", "PFDCurveResult",
    "pfd_mgl", "pfh_mgl", "MGLParams",
    "architectural_constraints", "sil_achieved", "ArchConstraintResult",
    "pfd_demand_duration", "route_compute",
    # Advanced
    "MarkovSolver", "compute_exact",
    "PSTSolver", "pst_analytical_koon",
    "str_analytical", "str_markov",
    "SystemMonteCarlo",
]
