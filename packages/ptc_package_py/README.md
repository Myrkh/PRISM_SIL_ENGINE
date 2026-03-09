# ptc_engine — Proof Test Coverage Analyzer v2.0

Port Python du `ptc_analyzer.ts`, algorithme identique, 100% traçable.

## Structure

```
ptc_engine/
  __init__.py     — exports publics
  kb.py           — chargeur Knowledge Base + enrichissements taxonomie FR
  parser.py       — ProcedureParser  (miroir ProcedureParser.ts)
  scorer.py       — PTCCalculator    (miroir PTCCalculator.ts)
  reporter.py     — PTCReporter      (+ calcul impact PFDavg)

knowledge_base_v2.json   — KB OREDA2015/SINTEF A27482 (43 composants, 302 FM)
generate_kb_v2.py        — générateur KB (source de vérité)
ptc_run_lts1127.py       — exemple : LTS1127 TotalEnergies BCUC
```

## Usage minimal

```python
from ptc_engine import load_kb, ProcedureParser, ProcedureStep, PTCCalculator, generate_report

kb = load_kb("knowledge_base_v2.json")

steps = [
    ProcedureStep("P01", "Poser une inhibition", location="SdC", section="§1"),
    ProcedureStep("P02", "Forcer simulation 0%", location="LT", section="§2"),
    # ...
]

parser = ProcedureParser(kb)
classifications = parser.classify_procedure(steps)

calculator = PTCCalculator(kb)
result = calculator.compute_component_ptc(
    component_id="level_transmitter_radar",
    component=kb["components"]["level_transmitter_radar"],
    classifications=classifications,
    sif_function="LAHH",
)

print(generate_report("MON-ID", "Ma procédure", classifications, result))
```

## Algorithme

```
PTC = Σ(c_i × λ_i) / Σ(λ_i)

Couverture combinée  : c_combined = 1 - Π(1 - c_j)
Incertitude IC 95%   : propagation analytique, EF=3 → σ_log = 0.55
Impact PFDavg        : PFDavg = λDU × T1 × (1 - PTC/2)   [IEC 61508-6 Annexe B]
```

## Composants disponibles (43)

level_transmitter_radar, level_transmitter_gwr, pressure_transmitter_4_20ma_hart,
shutdown_valve_pneumatic_src, fire_detector_uv_ir_flame, gas_detector_infrared, ...
(voir knowledge_base_v2.json → components)

## Résultats validés

| Procédure | Composant | Fonction | PTC |
|---|---|---|---|
| AIChE CEP 2015 Emerson (comprehensive) | PT 4-20mA HART | PAHH | 85.4% |
| FAS-82803 TotalEnergies (UV/IR flame) | fire_detector_uv_ir_flame | NO_FLAME | 66.9% |
| NOR-MET-SEI-INST-PM-00042_002 (LTS1127) | level_transmitter_radar | LAHH | 68.9% |
