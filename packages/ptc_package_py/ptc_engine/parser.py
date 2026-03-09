"""
ptc_engine.parser — ProcedureParser
=====================================
Port Python exact de la classe ProcedureParser du ptc_analyzer.ts.
Algorithme déterministe : règles explicites, pas de ML.
Traçable : chaque classification peut être auditée via matched_keywords.
"""

import re
import unicodedata
from dataclasses import dataclass, field


@dataclass
class ProcedureStep:
    id: str
    text: str
    location: str = ""
    expected_result: str = ""
    section: str = ""


@dataclass
class DetectedTestType:
    test_type_id: str
    confidence: float       # 0-1
    matched_keywords: list[str] = field(default_factory=list)


@dataclass
class StepClassification:
    step: ProcedureStep
    detected_test_types: list[DetectedTestType] = field(default_factory=list)
    unclassified: bool = True


class ProcedureParser:
    """
    Miroir exact de ProcedureParser (ptc_analyzer.ts).
    """

    def __init__(self, kb: dict):
        self._taxonomy: dict = kb["test_taxonomy"]

    # ── normalize ─────────────────────────────────────────────────────────────
    def _normalize(self, text: str) -> str:
        """
        Normalise une chaîne pour le matching.
        Miroir exact de normalize() TS :
          - lowercase
          - supprime accents (NFD decompose + strip combining chars)
          - normalise nombres+unités ("4ma" → "4 ma")
          - normalise espaces
        """
        t = text.lower()
        # Supprime accents
        t = unicodedata.normalize("NFD", t)
        t = "".join(c for c in t if unicodedata.category(c) != "Mn")
        # Normalise nombre+unité
        t = re.sub(r"(\d+)\s*(ma|vdc|vac|bar|psi|ms|hz|db)", r"\1 \2", t, flags=re.IGNORECASE)
        # Normalise espaces
        t = re.sub(r"\s+", " ", t).strip()
        return t

    # ── matchScore ────────────────────────────────────────────────────────────
    def _match_score(self, text: str, keyword: str) -> float:
        """
        Calcule un score de matching entre un texte et un keyword.
        Miroir exact de matchScore() TS.

        Retourne 0 (pas de match) ou score ∈ (0, 1].

        Règle 1 : substring exact → 1.0
        Règle 2 : token overlap ≥ 80% des tokens du keyword → ratio × 0.9
        Règle 3 : tokens courts (≤2 chars) ignorés pour éviter faux positifs
        """
        norm_text = self._normalize(text)
        norm_kw = self._normalize(keyword)

        # Match exact sous-chaîne → score maximal
        if norm_kw in norm_text:
            return 1.0

        # Token overlap
        kw_tokens = [t for t in norm_kw.split(" ") if len(t) > 2]
        # Minimum 2 tokens significatifs pour le path token-overlap
        # (évite les faux positifs sur tokens communs comme "test", "niveau")
        if len(kw_tokens) < 2:
            return 0.0

        text_tokens = set(norm_text.split(" "))
        matched = [t for t in kw_tokens if t in text_tokens]
        ratio = len(matched) / len(kw_tokens)

        # Seuil : au moins 80% des tokens du keyword trouvés
        return ratio * 0.9 if ratio >= 0.8 else 0.0

    # ── classifyStep ─────────────────────────────────────────────────────────
    def classify_step(self, step: ProcedureStep) -> StepClassification:
        """
        Classifie une étape de procédure en types de test.
        Miroir exact de classifyStep() TS.
        """
        all_text = " ".join([
            step.text,
            step.expected_result,
            step.location,
        ])

        detected: list[DetectedTestType] = []

        for test_type_id, entry in self._taxonomy.items():
            all_keywords = entry["keywords_fr"] + entry["keywords_en"]
            best_score = 0.0
            matched_keywords: list[str] = []

            for kw in all_keywords:
                score = self._match_score(all_text, kw)
                if score > 0:
                    matched_keywords.append(kw)
                    best_score = max(best_score, score)

            # Seuil minimal de confiance : 0.7 (identique au TS)
            if best_score >= 0.7:
                detected.append(DetectedTestType(
                    test_type_id=test_type_id,
                    confidence=best_score,
                    matched_keywords=matched_keywords,
                ))

        # Trier par confiance décroissante
        detected.sort(key=lambda d: -d.confidence)

        return StepClassification(
            step=step,
            detected_test_types=detected,
            unclassified=len(detected) == 0,
        )

    def classify_procedure(self, steps: list[ProcedureStep]) -> list[StepClassification]:
        """Classifie toute une liste d'étapes."""
        return [self.classify_step(s) for s in steps]
