"""
sil-engine quick start
======================
Reproduces IEC 61508-6 Annex B Table B.3 reference values and demonstrates
the main features of the Python engine.

Run from the packages/sil-py directory:
    python examples/quickstart.py
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sil_engine import (
    SubsystemParams, pfd_arch, pfh_moon,
    pfd_instantaneous, architectural_constraints, sil_achieved,
    pfd_demand_duration, route_compute,
    sil_from_pfd, sil_from_pfh,
)


def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# ── 1. PFDavg ─────────────────────────────────────────────────────────────────
section("1. PFDavg — IEC 61508-6 Table B.3 (T1=1 year, MTTR=8h)")

# λ_D = 5e-8/h, DC=90%  →  λ_DU = 5e-9, λ_DD = 4.5e-8
p = SubsystemParams(
    lambda_DU=5e-9, lambda_DD=4.5e-8,
    DC=0.9, beta=0.02, beta_D=0.01,
    MTTR=8.0, T1=8760.0,
)

for arch in ["1oo1", "1oo2", "2oo3", "1oo3"]:
    pfd = pfd_arch(p, arch)
    print(f"  {arch:6s}  PFDavg = {pfd:.3e}  → SIL {sil_from_pfd(pfd)}")


# ── 2. PFH — generalised kooN ─────────────────────────────────────────────────
section("2. PFH — generalised kooN (IEC + extensions)")

for k, n in [(1,2), (2,3), (1,3), (1,4), (2,4), (3,4)]:
    pfh = pfh_moon(p, k, n)
    tag = "IEC Annex B" if n <= 3 else "extension"
    print(f"  {k}oo{n}   PFH = {pfh:.3e}  → SIL {sil_from_pfh(pfh)}  [{tag}]")


# ── 3. PFD(t) instantaneous curve ─────────────────────────────────────────────
section("3. PFD(t) — instantaneous sawtooth curve")

curve = pfd_instantaneous(p, "1oo2", n_points=200)
print(f"  PFDavg   = {curve.pfd_avg:.3e}  (SIL {curve.sil_avg})")
print(f"  PFD_max  = {curve.pfd_max:.3e}  ({curve.pfd_max/curve.pfd_avg:.1f}× avg — at end of T1)")
print(f"  SIL at PFD_max = SIL {curve.sil_min}")
fracs = {k: f"{v*100:.0f}%" for k, v in curve.frac_sil.items() if v > 0.01}
print(f"  Time per SIL zone: {fracs}")


# ── 4. Full SIL verdict — probabilistic + architectural ───────────────────────
section("4. Full SIL verdict (IEC 61508-2 Route 1H)")

pfd = pfd_arch(p, "1oo2")
verdict = sil_achieved(
    pfd_or_pfh=pfd,
    lambda_DU=p.lambda_DU, lambda_DD=p.lambda_DD, lambda_S=1e-9,
    k=1, n=2,
    mode="low_demand",
    component_type="B",
)
ac = verdict["arch_result"]
print(f"  SFF = {ac.sff*100:.1f}%  (band: {ac.sff_band}%)")
print(f"  HFT = {ac.hft}  (1oo2: n-k = 1)")
print(f"  SIL probabilistic  = SIL {verdict['sil_prob']}")
print(f"  SIL architectural  = SIL {verdict['sil_arch_1H']}  (Route 1H, Type B)")
print(f"  SIL FINAL          = SIL {verdict['sil_final']}  ← {verdict['limiting_factor']} is limiting")


# ── 5. Demand duration ────────────────────────────────────────────────────────
section("5. Demand duration — for fire pumps, ESD, etc.")

dd = pfd_demand_duration(
    lambda_DU=p.lambda_DU,
    lambda_de=1 / 8760,   # 1 demand per year
    demand_duration=8.0,  # demand lasts 8 hours
    T1=8760.0, MRT=8.0,
)
print(f"  λ_demand = 1/year,  duration = 8h")
print(f"  PFD ({dd['formula_used']}) = {dd['pfd_recommended']:.3e}  → SIL {sil_from_pfd(dd['pfd_recommended'])}")


# ── 6. Auto-routing ───────────────────────────────────────────────────────────
section("6. Auto-routing: IEC analytical ↔ Markov CTMC")

p_low  = SubsystemParams(lambda_DU=1e-9, lambda_DD=0, DC=0, beta=0.02, T1=730)
p_high = SubsystemParams(lambda_DU=5e-5, lambda_DD=0, DC=0, beta=0.02, T1=8760)

for p_, label in [(p_low, "low"), (p_high, "high")]:
    r = route_compute(p_, "1oo2", "pfd")
    flag = " ⚠ auto-switched" if "Markov" in r["engine_used"] else ""
    print(f"  λ·T1={r['lambda_T1']:.3f}  engine={r['engine_used']}{flag}")


# ── 7. Full SIF ───────────────────────────────────────────────────────────────
section("7. Full SIF — sensor + logic + final element")

sensor = SubsystemParams(lambda_DU=5e-9,  lambda_DD=4.5e-8,  DC=0.9,  beta=0.02, T1=8760)
logic  = SubsystemParams(lambda_DU=1e-10, lambda_DD=9e-10,   DC=0.99, beta=0.01, T1=8760)
fe     = SubsystemParams(lambda_DU=5e-8,  lambda_DD=4.5e-7,  DC=0.9,  beta=0.02, T1=8760)

pfd_s = pfd_arch(sensor, "1oo2")
pfd_l = pfd_arch(logic,  "1oo1")
pfd_f = pfd_arch(fe,     "1oo2")
total = pfd_s + pfd_l + pfd_f

print(f"  Sensor (1oo2)     PFDavg = {pfd_s:.3e}")
print(f"  Logic  (1oo1)     PFDavg = {pfd_l:.3e}")
print(f"  Final elem (1oo2) PFDavg = {pfd_f:.3e}")
print(f"  {'─'*38}")
print(f"  SIF total         PFDavg = {total:.3e}  → SIL {sil_from_pfd(total)}")

print("\n✓ All examples completed successfully.\n")
