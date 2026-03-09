"""
ptc_engine — Proof Test Coverage Analyzer
==========================================
Package Python, miroir de ptc_analyzer.ts.

Usage :
    from ptc_engine import kb, ProcedureParser, PTCCalculator, generate_report

Modules :
    kb        — chargeur Knowledge Base
    parser    — ProcedureParser (classification des étapes)
    scorer    — PTCCalculator (calcul PTC + IC95%)
    reporter  — PTCReporter (rapport texte + impact PFDavg)
"""

from .kb import load as load_kb
from .parser import ProcedureParser, ProcedureStep, StepClassification
from .scorer import PTCCalculator, ComponentPTCResult
from .reporter import generate_report

__version__ = "2.0.0"
__all__ = [
    "load_kb",
    "ProcedureParser",
    "ProcedureStep",
    "StepClassification",
    "PTCCalculator",
    "ComponentPTCResult",
    "generate_report",
]
