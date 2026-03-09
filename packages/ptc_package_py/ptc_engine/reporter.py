"""
ptc_engine.reporter — PTCReporter
====================================
Génère le rapport texte structuré à partir des résultats du scorer.
C'est l'équivalent Python du PTCReporter (non encore implémenté dans TS).

Contient aussi le calcul d'impact PFDavg (IEC 61508-6 Annexe B simplifié).
"""

import math
from .parser import StepClassification
from .scorer import ComponentPTCResult


def pct(v: float) -> str:
    return f"{v * 100:.1f}%"


def pfd_impact(result: ComponentPTCResult, T1_hours: float = 8760) -> dict:
    """
    Calcule l'impact du PTC sur le PFDavg.
    Formule IEC 61508-6 Annexe B simplifiée :
      PFDavg = λDU × T1 × (1 - PTC/2)

    Retourne dict avec PFDavg(PTC=1.0), PFDavg(réel), facteur.
    """
    lambda_du = result.lambda_DU_total * 1e-9   # FIT → /h
    ptc_real = result.ptc

    pfd_perfect = lambda_du * T1_hours * (1 - 1.0 / 2)
    pfd_real = lambda_du * T1_hours * (1 - ptc_real / 2)
    factor = pfd_real / pfd_perfect if pfd_perfect > 0 else 1.0

    return {
        "lambda_DU_per_h": lambda_du,
        "T1_hours": T1_hours,
        "pfd_ptc_1": pfd_perfect,
        "pfd_real": pfd_real,
        "factor": factor,
    }


def generate_report(
    procedure_id: str,
    procedure_title: str,
    classifications: list[StepClassification],
    result: ComponentPTCResult,
    T1_hours: float = 8760,
) -> str:
    """
    Génère le rapport complet sous forme de texte.
    Identique en structure à ce que produirait PTCReporter TS.
    """
    lines: list[str] = []
    add = lines.append

    W = 72

    def header(title: str):
        add("╔" + "═" * (W - 2) + "╗")
        add("║  " + title.ljust(W - 4) + "║")
        add("╚" + "═" * (W - 2) + "╝")

    def section(title: str):
        add(f"\n  ── {title} {'─' * max(1, W - 6 - len(title))}")

    add("=" * W)
    add(f"  RAPPORT PTC — {procedure_id}")
    add(f"  {procedure_title}")
    add(f"  Composant : {result.component_id}  |  Fonction SIF : {result.sif_function}")
    add(f"  Moteur    : PTC Analyzer v2.0 (ptc_engine Python)")
    add(f"  KB source : knowledge_base_v2.json — OREDA2015 / SINTEF A27482")
    add("=" * W)

    # ── CLASSIFICATION DES ÉTAPES ────────────────────────────────────────────
    add("")
    header("CLASSIFICATION DES ÉTAPES")

    current_section = ""
    n_classified = 0
    n_total = len(classifications)

    for cls in classifications:
        if cls.step.section != current_section:
            current_section = cls.step.section
            section(current_section)

        types = [dt.test_type_id for dt in cls.detected_test_types]
        icon = "✅" if types else "❓"
        n_classified += 0 if cls.unclassified else 1
        add(f"  {icon} {cls.step.id:<5} {cls.step.text[:60]}")
        for dt in cls.detected_test_types[:2]:
            add(f"         → {dt.test_type_id:<40} ({pct(dt.confidence)} conf.)")

    unclassified = [c for c in classifications if c.unclassified]
    add(f"\n  ✅ Classifiées  : {n_classified}/{n_total}")
    if unclassified:
        add(f"  ❓ Non classifiées ({len(unclassified)}) :")
        for c in unclassified:
            add(f"     • {c.step.id}: {c.step.text[:65]}")

    # ── TYPES DE TEST DÉTECTÉS ───────────────────────────────────────────────
    add("")
    header("TYPES DE TEST DÉTECTÉS")
    for tt in result.detected_test_types:
        add(f"  ✔  {tt}")

    # ── RÉSULTAT PTC ─────────────────────────────────────────────────────────
    add("")
    header("RÉSULTAT PTC")
    add(f"  Composant KB       : {result.component_id}")
    add(f"  Désignation        : {result.display_fr}")
    add(f"  Fonction SIF       : {result.sif_function}")
    add(f"  λ DU total         : {result.lambda_DU_total:.0f} FIT")
    add(f"  λ DU couvert       : {result.lambda_DU_covered:.1f} FIT")
    add(f"  λ DU non couvert   : {result.lambda_DU_uncovered:.1f} FIT")
    add(f"  PTC max achievable : {pct(result.ptc_max_achievable)}")
    add("")
    add(f"  ┌──────────────────────────────────────────────────────────────┐")
    add(f"  │  PTC = {pct(result.ptc):<8}  IC 95% [{pct(result.ptc_lower_95)} — {pct(result.ptc_upper_95)}]")
    add(f"  └──────────────────────────────────────────────────────────────┘")

    if result.warnings:
        add("")
        for w in result.warnings:
            add(f"  {w}")

    # ── ANALYSE PAR MODE DE DÉFAILLANCE ──────────────────────────────────────
    add("")
    header("ANALYSE PAR MODE DE DÉFAILLANCE")
    add(f"\n  {'Mode de défaillance':<42} {'λ':>5}  {'DC':>5}  {'c_test':>6}  {'c_max':>5}  Tests couvrants")
    add(f"  {'─'*42} {'─'*5}  {'─'*5}  {'─'*6}  {'─'*5}  {'─'*20}")

    for fm in result.failure_modes:
        if fm.coverage_achieved >= 0.85:
            icon = "✅"
        elif fm.coverage_achieved > 0.3:
            icon = "⚠️ "
        else:
            icon = "❌"
        tests = ", ".join(fm.detecting_test_types) if fm.detecting_test_types else "—"
        add(
            f"  {icon} {fm.failure_mode_id:<40} {fm.lambda_fit:>5.0f}  "
            f"{pct(fm.dc_online):>5}  {pct(fm.coverage_achieved):>6}  "
            f"{pct(fm.coverage_max_possible):>5}  {tests[:30]}"
        )

    # ── RECOMMANDATIONS ──────────────────────────────────────────────────────
    if result.recommended_steps:
        add("")
        header("ÉTAPES MANQUANTES — GAIN PTC POTENTIEL")
        for rec in result.recommended_steps:
            add(f"\n  + {rec.test_type_id}")
            add(f"    {rec.display_fr}")
            add(f"    Gain PTC estimé  : +{pct(rec.ptc_gain)}")
            add(f"    λ additionnel    : +{rec.lambda_additional_covered:.1f} FIT")
            add(f"    Modes couverts   : {', '.join(rec.failure_modes_covered)}")

    # ── IMPACT PFDavg ─────────────────────────────────────────────────────────
    add("")
    header("IMPACT SUR PFDavg (IEC 61508-6 Annexe B)")
    pfd = pfd_impact(result, T1_hours)
    add(f"\n  T1 = {T1_hours:.0f} h    λDU = {result.lambda_DU_total:.0f} FIT = {pfd['lambda_DU_per_h']:.3e} /h")
    add(f"\n  PFDavg (PTC = 1.00)   = {pfd['pfd_ptc_1']:.4f}   ← hypothèse test parfait")
    add(f"  PFDavg (PTC = {pct(result.ptc):<6}) = {pfd['pfd_real']:.4f}   ← réalité procédure")
    add(f"\n  Facteur de sous-estimation si PTC = 1.0 supposé : ×{pfd['factor']:.2f}")
    if pfd["factor"] > 1.05:
        add(f"  → Utiliser PTC=1.0 sous-estime le risque de {(pfd['factor']-1)*100:.0f}%")
    else:
        add(f"  → Impact PFDavg négligeable (facteur < 1.05)")

    add("\n" + "═" * W)
    add("  FIN DU RAPPORT")
    add("═" * W)

    return "\n".join(lines)
