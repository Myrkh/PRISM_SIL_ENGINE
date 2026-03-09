# Changelog

All notable changes to sil-engine are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [0.3.3] — 2026-03-09 — Initial public release

### Added
**Python engine (`sil-py`):**
- PFDavg: 1oo1, 1oo2, 2oo2, 2oo3, 1oo3, 1oo2D, kooN generic, imperfect proof test (PTC < 1)
- PFH: 1oo1, 1oo2 (IEC §B.3.3.2.2), 1oo2 NTNU conservative, 2oo2, 2oo3, 1oo3
- PFH corrected: pfh_1oo2_corrected, pfh_2oo3_corrected (Omeiri/Innal 2021 — pending full verification)
- **Generalised PFH kooN** (`pfh_moon(p, k, n)`) — any architecture including 1oo4, 2oo4, 3oo4
- **Generalised PFD kooN** (`pfd_koon_generic(p, k, n)`)
- **PFD(t) instantaneous curve** — sawtooth, PFDmax, time fraction per SIL zone
- **MGL CCF model** — Multiple Greek Letters (β, γ, δ) for IEC 61508-6 Annex D
- **Architectural constraints Route 1H/2H** — SFF, HFT, SIL verdict (IEC 61508-2 Table 2)
- **Demand duration model** — PFD for non-instantaneous demands (NTNU Ch8)
- **Auto-routing** — automatic switch to Markov CTMC when λ·T₁ > 0.1
- Exact Markov CTMC solver (scipy matrix exponential)
- PST: Partial Stroke Test, analytical kooN + multi-phase Markov
- STR: Spurious Trip Rate, analytical + Markov
- MTTFS: Mean Time To Fail Spuriously via matrix solve
- Monte Carlo: uncertainty propagation on λ, DC, β
- FastAPI REST server (optional)

**Validation:**
- 79 test cases from IEC 61508-6 Tables B.2–B.13, 61508.org (2024), NTNU Ch8
- 100% within 10% tolerance; 95% within 2%

### Fixed (vs preliminary internal versions)
- `pfh_2oo3`: corrected `6×λDU²×T1` → `6×lD_eff×lDU×t_CE` (IEC §B.3.3.2.5)
- `pfh_1oo3`: corrected `3×λDU³×T1²` → `6×lD_eff²×lDU×t_CE×t_GE` (IEC §B.3.3.2.6)
- `pfh_1oo2`: now correctly implements IEC §B.3.3.2.2; NTNU conservative form available as `pfh_1oo2_ntnu()`
- `t_CE` formula confirmed identical for PFD and PFH modes (IEC §B.3.2.2)

---

## Planned

### [0.4.0] — pending external sources
- Weibull λ(t) for mechanical actuators (NTNU Ch5 — source available)
- PFH 1oo2 corrected (Omeiri/Innal 2021 — access pending)
- PST with 3 distinct repair times (Innal/Lundteigen RESS 2016 — access pending)
- PFH 2oo3 corrected (Jin/Lundteigen/Rausand 2013 — access pending)
