# Contributing to sil-engine

Thank you. A verified, open-source IEC 61508 engine benefits the entire safety engineering community — students, researchers, independent engineers, and companies that cannot afford commercial tools.

---

## Ground rules

1. **Every formula needs a source.** A standard clause, a paper DOI, or a URL to public slides. No source = no merge.
2. **Every formula change needs a test case.** With a reference value from that same source.
3. **All existing tests must still pass.** `pytest packages/sil-py/tests/` must be green.

---

## How to contribute

### Setup

```bash
git clone https://github.com/your-org/sil-engine
cd sil-engine/packages/sil-py

pip install -e ".[dev]"   # installs in editable mode + dev tools

pytest tests/ -v          # run the test suite — should be 100% green
python examples/quickstart.py  # should complete without error
```

### Types of contributions

**Always welcome — no prior discussion needed:**
- New test cases with public reference values
- Bug reports with a reproducible number
- Documentation improvements, typo fixes
- Translations of theory documents

**Formula additions or changes — open an issue first:**

| Priority | Feature | Source | Status |
|----------|---------|--------|--------|
| 🔴 High | Weibull λ(t) for mechanical actuators | NTNU Ch5 (public) | Open |
| 🔴 High | PFH 1oo2 corrected (Omeiri/Innal 2021) | DOI:10.21152/1750-9548.15.4.871 | Needs paper |
| 🔴 High | PST with 3 distinct repair times | Innal/Lundteigen RESS 2016 DOI:10.1016/j.ress.2016.01.022 | Needs paper |
| 🟡 Med | PFH 2oo3 corrected | Jin/Lundteigen/Rausand 2013 IJRQSE | Needs paper |
| 🟡 Med | CMooN PDS factors | PDS Handbook 2013, SINTEF | Needs handbook |
| 🟢 Low | GRIF / exSILentia benchmark comparison | Screenshots from tool | Open |

**Out of scope:**
- Proprietary formulas without public source
- UI / frontend code (that belongs to the commercial platform)
- Changes that break the IEC 61508-6 Annex B validation tables

---

## Writing a test case

```python
def test_1oo2_dc90_b3():
    """
    Source: IEC 61508-6:2010 Table B.3, row 1oo2, DC=90%, β=2%, λ_D=5e-8/h, T1=8760h
    Reference value: PFDavg ≈ 4.5e-6
    Tolerance: ≤ 10% (IEC tables are rounded to 1-2 significant figures)
    """
    p = SubsystemParams(
        lambda_DU = 5e-9,   # λ_D × (1-DC) = 5e-8 × 0.1
        lambda_DD = 4.5e-8, # λ_D × DC     = 5e-8 × 0.9
        DC = 0.9, beta = 0.02, MTTR = 8.0, T1 = 8760.0,
    )
    result = pfd_arch(p, "1oo2")
    ref    = 4.5e-6
    assert abs(result - ref) / ref < 0.10, f"Got {result:.3e}, expected ≈ {ref:.2e}"
```

---

## Validation tolerance policy

| Error vs reference | Classification |
|--------------------|----------------|
| < 2% | ✅ PASS — excellent |
| 2 – 10% | ⚠️ WARN — acceptable (IEC table rounding) |
| > 10% | ❌ FAIL — must be investigated and fixed |

Note: IEC 61508-6 reference tables are printed with 1–2 significant figures. A 5% discrepancy between your implementation and the table is completely normal and expected.

---

## Docstring format for formula functions

```python
def pfh_1oo2(p: SubsystemParams) -> float:
    """
    PFH for 1oo2 architecture — high demand / continuous mode.

    Source: IEC 61508-6:2010 §B.3.3.2.2
      PFH_G(1oo2) = 2 × [(1-β_D)λ_DD + (1-β)λ_DU] × (1-β)λ_DU × t_CE + β × λ_DU

    where t_CE = (λ_DU/λ_D) × (T1/2 + MRT) + (λ_DD/λ_D) × MTTR

    Note: IEC §B.3.3.2.2 slide 29 excludes the DU→DD transition (considered safe-state).
    For the conservative formulation including DU→DD, see pfh_1oo2_ntnu().
    Reference: NTNU Ch9 slide 26 (Lundteigen & Rausand).
    """
```

---

## Pull request checklist

- [ ] Formula docstring includes source citation (clause, DOI, or URL)
- [ ] New test case added with reference value and source
- [ ] All existing tests pass (`pytest tests/ -v`)
- [ ] Quickstart example still runs (`python examples/quickstart.py`)
- [ ] No new dependencies without discussion

---

## License

By contributing, you agree your contributions are licensed under LGPL-3.0-or-later.
