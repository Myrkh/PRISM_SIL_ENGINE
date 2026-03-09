"""
ptc_engine.scorer — PTCCalculator
====================================
Port Python exact de la classe PTCCalculator du ptc_analyzer.ts.

Formule centrale : PTC = Σ(c_i × λ_i) / Σ(λ_i)

Combinaison de couvertures multiples :
  c_combined = 1 - Π(1 - c_ij)   (analogie redondance fiabilité)

Incertitude sur λ : EF=3 lognormal → σ_log ≈ 0.55
Propagation analytique (dérivée partielle, miroir exact du TS).
"""

import math
from dataclasses import dataclass, field
from .parser import StepClassification


# ── Structures de résultat (miroir des interfaces TS) ─────────────────────────

@dataclass
class FailureModeResult:
    failure_mode_id: str
    display_fr: str
    lambda_fit: float
    lambda_source: str
    dangerous: bool
    coverage_achieved: float          # c_i ∈ [0,1]
    coverage_max_possible: float      # si toutes les étapes KB incluses
    detecting_steps: list[str]        # IDs étapes couvrant ce mode
    detecting_test_types: list[str]
    not_covered: bool
    coverage_gap: float               # = coverage_max_possible - coverage_achieved
    dc_online: float = 0.0


@dataclass
class RecommendedStep:
    test_type_id: str
    display_fr: str
    ptc_gain: float                   # gain PTC si étape ajoutée
    lambda_additional_covered: float
    failure_modes_covered: list[str]


@dataclass
class ComponentPTCResult:
    component_id: str
    component_type: str
    display_fr: str
    sif_function: str | None
    ptc: float
    ptc_lower_95: float
    ptc_upper_95: float
    ptc_max_achievable: float
    lambda_DU_total: float
    lambda_DU_covered: float
    lambda_DU_uncovered: float
    failure_modes: list[FailureModeResult]
    critical_gaps: list[FailureModeResult]
    recommended_steps: list[RecommendedStep]
    warnings: list[str]
    detected_test_types: list[str]    # liste complète des types détectés


class PTCCalculator:
    """
    Miroir exact de PTCCalculator (ptc_analyzer.ts).
    """

    def __init__(self, kb: dict):
        self._kb = kb

    # ── combineCoverage ───────────────────────────────────────────────────────
    @staticmethod
    def _combine_coverage(coverages: list[float]) -> float:
        """
        Couverture combinée de plusieurs tests sur un même mode.
        c_combined = 1 - Π(1 - c_j)
        Miroir exact de combineCoverage() TS.
        """
        result = 1.0
        for c in coverages:
            result *= (1.0 - c)
        return 1.0 - result

    # ── computeUncertainty ────────────────────────────────────────────────────
    @staticmethod
    def _compute_uncertainty(
        ptc: float,
        failure_modes: list[dict],
        coverages: list[float],
    ) -> tuple[float, float]:
        """
        Intervalle de confiance PTC à 95%.
        Propagation analytique, EF=3 lognormal → σ_log = 0.55.
        Miroir exact de computeUncertainty() TS.
        """
        sigma_log = 0.55
        lambda_total = sum(fm["lambda_fit"] for fm in failure_modes)
        variance = 0.0
        for i, fm in enumerate(failure_modes):
            li = fm["lambda_fit"]
            ci = coverages[i]
            # dPTC/dλ_i
            d_ptc_d_li = (ci * lambda_total - ptc * lambda_total) / (lambda_total ** 2)
            var_li = (li * sigma_log) ** 2
            variance += d_ptc_d_li ** 2 * var_li

        sigma = math.sqrt(variance)
        lower = max(0.0, ptc - 1.96 * sigma)
        upper = min(1.0, ptc + 1.96 * sigma)
        return lower, upper

    # ── computeRecommendations ────────────────────────────────────────────────
    def _compute_recommendations(
        self,
        fm_results: list[FailureModeResult],
        lambda_total: float,
        lambda_covered: float,
        detected_test_types: set[str],
    ) -> list[RecommendedStep]:
        """
        Calcule les étapes recommandées pour maximiser le PTC.
        Pour chaque type de test non encore inclus, calcule le gain PTC potentiel.
        Miroir exact de computeRecommendations() TS.
        """
        # Collecter tous les testTypeIds mentionnés dans les failure modes
        all_types_in_kb: set[str] = set()
        for fm_r in fm_results:
            # Retrouver les coverage entries dans la KB brute
            pass

        # Approche : pour chaque type de test dans la taxonomie,
        # calculer le gain si on l'ajoutait
        taxonomy = self._kb["test_taxonomy"]
        recommendations: list[RecommendedStep] = []

        for test_type_id, entry in taxonomy.items():
            if test_type_id in detected_test_types:
                continue  # déjà présent

            # Calculer le λ additionnel qui serait couvert
            additional_covered = 0.0
            modes_covered: list[str] = []

            for fm_r in fm_results:
                # On cherche le FM dans la KB pour accéder à sa coverage
                comp_fms = []
                for comp in self._kb["components"].values():
                    for fm in comp["failure_modes"]:
                        if fm["id"] == fm_r.failure_mode_id:
                            comp_fms.append(fm)

                for fm_kb in comp_fms:
                    c_new = fm_kb.get("coverage", {}).get(test_type_id, 0.0)
                    if c_new > 0:
                        # Couverture combinée actuelle + nouveau test
                        current_c = fm_r.coverage_achieved
                        new_c = 1.0 - (1.0 - current_c) * (1.0 - c_new)
                        delta = (new_c - current_c) * fm_r.lambda_fit
                        if delta > 0:
                            additional_covered += delta
                            if fm_r.failure_mode_id not in modes_covered:
                                modes_covered.append(fm_r.failure_mode_id)

            if additional_covered > 0:
                ptc_gain = additional_covered / lambda_total
                recommendations.append(RecommendedStep(
                    test_type_id=test_type_id,
                    display_fr=entry["display_fr"],
                    ptc_gain=ptc_gain,
                    lambda_additional_covered=additional_covered,
                    failure_modes_covered=modes_covered,
                ))

        # Trier par gain décroissant
        recommendations.sort(key=lambda r: -r.ptc_gain)
        return recommendations[:5]  # Top 5

    # ── computeComponentPTC ───────────────────────────────────────────────────
    def compute_component_ptc(
        self,
        component_id: str,
        component: dict,
        classifications: list[StepClassification],
        sif_function: str | None = None,
    ) -> ComponentPTCResult:
        """
        Calcule le PTC pour un composant donné avec les étapes classifiées.
        Miroir exact de computeComponentPTC() TS.
        """
        # Collecter tous les types de test détectés
        detected_test_types: set[str] = set()
        for cls in classifications:
            for dt in cls.detected_test_types:
                detected_test_types.add(dt.test_type_id)

        # Map testTypeId → liste des stepIds
        test_to_steps: dict[str, list[str]] = {}
        for cls in classifications:
            for dt in cls.detected_test_types:
                if dt.test_type_id not in test_to_steps:
                    test_to_steps[dt.test_type_id] = []
                test_to_steps[dt.test_type_id].append(cls.step.id)

        # Filtrer les failure modes dangereux pour la fonction SIF
        all_fms = component["failure_modes"]
        if sif_function:
            dangerous_modes = [
                fm for fm in all_fms
                if sif_function in fm.get("dangerous_for_function", [])
                or "ALL" in fm.get("dangerous_for_function", [])
            ]
        else:
            dangerous_modes = all_fms

        if not dangerous_modes:
            return self._empty_result(component_id, component)

        lambda_total = sum(fm["lambda_fit"] for fm in dangerous_modes)
        fm_results: list[FailureModeResult] = []
        achieved_coverages: list[float] = []

        for fm in dangerous_modes:
            applicable_coverages: list[float] = []
            detecting_test_types: list[str] = []
            detecting_steps: list[str] = []

            for test_type_id, c_i in fm.get("coverage", {}).items():
                if test_type_id in detected_test_types and c_i > 0:
                    applicable_coverages.append(c_i)
                    detecting_test_types.append(test_type_id)
                    detecting_steps.extend(test_to_steps.get(test_type_id, []))

            # Couverture combinée : 1 - Π(1 - c_j)
            c_achieved = (
                self._combine_coverage(applicable_coverages)
                if applicable_coverages else 0.0
            )

            # Couverture max possible (toutes étapes KB)
            all_pos = [v for v in fm.get("coverage", {}).values() if v > 0]
            c_max = self._combine_coverage(all_pos) if all_pos else 0.0

            achieved_coverages.append(c_achieved)

            fm_results.append(FailureModeResult(
                failure_mode_id=fm["id"],
                display_fr=fm["display_fr"],
                lambda_fit=fm["lambda_fit"],
                lambda_source=fm.get("lambda_source", "OREDA2015"),
                dangerous=True,
                coverage_achieved=c_achieved,
                coverage_max_possible=c_max,
                detecting_steps=list(set(detecting_steps)),
                detecting_test_types=detecting_test_types,
                not_covered=(c_achieved == 0.0),
                coverage_gap=c_max - c_achieved,
                dc_online=fm.get("dc_online", 0.0),
            ))

        # PTC = Σ(c_i × λ_i) / Σ(λ_i)
        lambda_covered = sum(
            r.coverage_achieved * r.lambda_fit for r in fm_results
        )
        ptc = lambda_covered / lambda_total if lambda_total > 0 else 0.0

        # PTC max achievable
        lambda_max = sum(r.coverage_max_possible * r.lambda_fit for r in fm_results)
        ptc_max = lambda_max / lambda_total if lambda_total > 0 else 0.0

        # Intervalle de confiance 95%
        lower, upper = self._compute_uncertainty(ptc, dangerous_modes, achieved_coverages)

        # Gaps critiques : non couverts + λ > 5% du total
        critical_gaps = sorted(
            [r for r in fm_results if r.not_covered and r.lambda_fit > lambda_total * 0.05],
            key=lambda r: -r.lambda_fit,
        )

        # Recommandations
        recommended = self._compute_recommendations(
            fm_results, lambda_total, lambda_covered, detected_test_types
        )

        # Warnings (miroir exact TS)
        warnings: list[str] = []
        ptc_pct = ptc * 100
        if ptc < 0.6:
            warnings.append(
                f"⚠️ PTC = {ptc_pct:.0f}% — très insuffisant (< 60%). SIL cible compromise."
            )
        elif ptc < 0.8:
            warnings.append(
                f"⚠️ PTC = {ptc_pct:.0f}% — en-dessous de la valeur typique minimale (80%)."
            )
        if critical_gaps:
            ids = ", ".join(g.failure_mode_id for g in critical_gaps)
            warnings.append(f"⚠️ {len(critical_gaps)} mode(s) dangereux non couverts : {ids}")

        return ComponentPTCResult(
            component_id=component_id,
            component_type=component.get("category", ""),
            display_fr=component["display_fr"],
            sif_function=sif_function,
            ptc=ptc,
            ptc_lower_95=lower,
            ptc_upper_95=upper,
            ptc_max_achievable=ptc_max,
            lambda_DU_total=lambda_total,
            lambda_DU_covered=lambda_covered,
            lambda_DU_uncovered=lambda_total - lambda_covered,
            failure_modes=fm_results,
            critical_gaps=critical_gaps,
            recommended_steps=recommended,
            warnings=warnings,
            detected_test_types=sorted(detected_test_types),
        )

    @staticmethod
    def _empty_result(component_id: str, component: dict) -> "ComponentPTCResult":
        return ComponentPTCResult(
            component_id=component_id,
            component_type=component.get("category", ""),
            display_fr=component["display_fr"],
            sif_function=None,
            ptc=0.0, ptc_lower_95=0.0, ptc_upper_95=0.0, ptc_max_achievable=0.0,
            lambda_DU_total=0.0, lambda_DU_covered=0.0, lambda_DU_uncovered=0.0,
            failure_modes=[], critical_gaps=[], recommended_steps=[], warnings=[],
            detected_test_types=[],
        )
