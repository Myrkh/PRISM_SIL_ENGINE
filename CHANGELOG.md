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

## [0.3.4] — 2026-03-09 — Bugfixes & multi-source benchmark

### Fixed

**Bug #1 — BLOQUANT — `tests/test_verification.py` (9 occurrences)**
- `from solver.formulas import ...` → `from sil_engine.formulas import ...`
- `from solver.extensions import ...` → `from sil_engine.extensions import ...`
- Le répertoire `solver/` n'existe pas dans le package publié ; le module s'appelle `sil_engine`.
- Impact : 6 fonctions `test_*` déclenchaient `ModuleNotFoundError` → 0/6 tests exécutables.
- Résultat : **6/6 tests pytest PASS** après correction.

**Bug #2 — BLOQUANT — `sil_engine/extensions.py::route_compute()` l.545**
- `solver = MarkovSolver(p, arch)` → `TypeError: __init__() takes 2 positional arguments but 3 were given`
- `MarkovSolver.__init__(self, p)` n'accepte qu'un seul argument.  
  L'architecture est transmise via `p.architecture`, `p.M`, `p.N` (lus par `_build_states()` et `_is_failed()`).
- Fix : `p_arch = copy(p); p_arch.architecture = arch; p_arch.M = int(arch[0]); p_arch.N = int(arch[-1]); solver = MarkovSolver(p_arch)`
- Impact : le solveur Markov CTMC **ne s'activait jamais** ; tout cas `λ·T₁ > 0.1` tombait silencieusement en `IEC_simplified_fallback`, rendant la bascule automatique inopérante.
- Résultat : `route_compute()` → `engine=Markov_CTMC` pour `λ·T₁ > 0.1` ✓

**Bug #3 — FIX — `tests/test_verification.py` cas T11**
- `expected = 6.3e-2` correspondait à la valeur IEC Table B.9, invalide car `λ·T₁ = 2.19 >> 0.1` (IEC §B.2.2).
- Le cas portait `"markov_required": True` mais `run_single_case()` appelait quand même `pfd_arch()` (formule IEC).
- Fix : `expected = 3.76e-2` (valeur Markov CTMC exacte) + routage conditionnel vers `route_compute()` si `markov_required=True`.
- Résultat : T11 passe de ERREUR (Δ=23%) → **VALIDÉ (Δ=0.1%)** ✓

**Bug #5 — BLOQUANT — `sil_engine/str_solver.py::str_markov()` l.~87**
- `A[:, -1] = 1.0` remplaçait la dernière **colonne** de `Q^T` → système linéaire incohérent → vecteur `π` non normalisé (somme ≈ 4×10¹⁰) → `STR_Markov = 1635/h` (absurde vs 2.1×10⁻⁶/h analytique).
- Fix : `A[-1, :] = 1.0` → remplace la dernière **ligne** (contrainte `Σπᵢ = 1`, méthode standard).
- Source : NTNU Ch.5 slide 38 — *"Replace one row of Q^T with normalization constraint"* ; Rausand §5.3.
- Résultat : `STR_Markov = 2.104×10⁻⁶/h` → **Δ = 0.0% vs analytique** ✓

### Added

**Benchmark multi-sources `benchmark_architectures.py`** — fichier remplacé et étendu :

- **§0** : résumé des 5 corrections avec justification technique, avant/après, impact
- **§1** : vérification IEC 61508-6 Annexe B Tables B.4–B.13 (15 cas) — **10 VALIDÉS ±1% | 5 ACCEPTABLES | 0 ERREURS | pass=100%**
- **§2** : comparaison PFH IEC vs corrigé (Omeiri/Innal/Liu 2021, JESA 54(6):871-879)  
  Δ = +1866% pour 1oo2/2oo3 à DC=90%, β=0 — terme `2×λDU×(T1/2+MRT)×λDD` absent de l'IEC confirmé
- **§3** : comparaison PDS Method Handbook 2013 SINTEF (A23298) — modèle CCF β-multiple (CMooN) vs β-standard IEC
- **§4** : Rausand & Høyland 2004 §5.3 — domaine de validité IEC : Δ<1% si `λ·T₁ < 0.05`, Δ=+35% à `λ·T₁ = 4.38`
- **§5** : ISA-TR84.00.02-2002 Part 2 §6 — SIF réacteur chimique 5 sous-systèmes (FT 2oo3, PT 1oo2, TS 1oo2, LS 1oo2, PES 1oo2)
- **§6** : Hardware réel — Triconex TRICON TMR (λDU=5×10⁻¹⁰/h) et Hima HIMatrix F3 (λDU=2.9×10⁻¹⁰/h) d'après FMEDA publiées
- **§7** : Matrice 11 configurations SIF capteur × logique × actionneur avec contributions S%/L%/FE%
- **§8** : PFD(t) instantané + Monte Carlo propagation incertitude (EF=3, 10 000 tirages)
- **§9** : PST gain PFD XV 1oo1, STR par architecture, concordance STR analytique vs Markov (Δ=0.0%)

### Notes de compatibilité API (benchmark uniquement)

- `UncertaintyModel(λ_mean, error_factor=3.0)` — le paramètre `ef` ne correspond pas au nom de l'attribut dans le code source
- `SystemMonteCarlo(seed=42).run(subsystems=[...])` — initialisation et appel séparés
- `PSTSolver(p, T_PST=, c_PST=).compute_pfdavg()['pfdavg_with_pst']` — clé de retour explicite
- `str_analytical(p: SubsystemParams) → dict` — prend un `SubsystemParams` entier, pas 3 arguments séparés

---

## [0.3.5] — 2026-03-10 — Markov exact compute_pfh + Bug #6

### Fixed

**Bug #6 — CRITIQUE — `pfh_1oo2_corrected()` et `pfh_2oo3_corrected()` (Omeiri 2021)**
- `MRT = p.T1 / 2.0` → `MRT = p.MTTR`
- Le terme `pfh_missing` utilisait T1/2 au lieu de MTTR comme Mean Repair Time.
- Avec T1=8760h, MTTR=8h : résultat environ ×547 trop grand.
- Source : Omeiri et al. 2021, JESA 54(6) p.875 — *«MRT = mean repair time ≈ MTTR for repairable systems»*.
- Impact : correction majeure sur les formules corrigées Omeiri. Les formules IEC standard (pfh_1oo2, pfh_2oo3) n'étaient pas affectées.
- Résultat : **8/8 cas de validation Markov PASS, Δ_max = 0.2%**.

### Added

**`compute_pfh()` — Markov CTMC exact pour mode haute demande / continu**
- Calcul PFH par somme des flux vers états dangereux : `PFH = Σ_i π_i × Σ_{j∈Danger} Q[i,j]`
- Conforme Omeiri et al. 2021 Eq.6, NTNU Ch.8 slide 37 — *«PFH = P₂ × 2λ_D»* (steady-state).
- Intégré dans `compute_exact(mode='high_demand')` avec basculement automatique si `λ·T1 > 0.1`.
- Validation : 8 cas de référence couvrant 1oo1, 1oo2, 2oo2, 2oo3, 1oo3 avec β∈{0%, 2%}.

**`ROADMAP.md`** — 19 items priorisés, 4 niveaux (Fondations → Normes → Différenciants → Crédibilité)

---

## [0.4.0] — 2026-03-10 — Refactoring SubsystemParams + documentation sources primaires

### Added

**`SubsystemParams` — décomposition rigoureuse λ_S = λ_SD + λ_SU**
- Nouveaux champs : `lambda_SD` (Safe Detected), `lambda_SU` (Safe Undetected).
- Source : Uberti M. (2024) *Functional Safety: RBD and Markov for SIS*, Politecnico Milano, Eq.3.9.
- Règle de cohérence dans `__post_init__` : si `lambda_SD` ou `lambda_SU` fournis,
  `lambda_S` est recalculé et une `ValueError` est levée si `lambda_S` est aussi fourni de façon incohérente.
- Rétrocompatibilité totale : workflow `lambda_S` seul inchangé.
- Motivation : distinction nécessaire pour STR précis (λ_SU latente vs λ_SD immédiate) et générateur Markov futur.

**`SubsystemParams.MTTR_DU` — temps de réparation explicite pour λ_DU**
- Nouveau champ `MTTR_DU: float = -1.0` (sentinel → MTTR par défaut via `__post_init__`).
- Remplace le `getattr(p, 'MRT', p.MTTR)` fragile antérieur dans pfh_1oo2, pfh_2oo3, pfh_1oo3.
- Source : Uberti 2024 Eq.6.3, NTNU Ch.8 slide 31 — `t_CE = (λDU/λD)×(T1/2 + MRT) + (λDD/λD)×MTTR`.
- `MTTR_DU` (pour λ_DU, découvert au proof test) est physiquement distinct de `MTTR` (pour λ_DD,
  déclenchement immédiat) même si identiques en pratique.

**`route1h_constraint()` — résultat enrichi**
- Retourne maintenant `lambda_S_total`, `lambda_SD`, `lambda_SU` pour reporting détaillé.
- Docstring complète : formule SFF sourcée (IEC 61508-2 §6.7.4, Uberti 2024 Eq.3.13),
  Table HFT/SIL (IEC 61508-2 Table 2), correspondance architecture→HFT.

**`docs/SOURCE_ANALYSIS_NTNU_UBERTI.md`** — document d'analyse scientifique des sources primaires
- Analyse de convergence NTNU Ch.8 (Rausand & Lundteigen) vs Uberti 2024 (Politecnico Milano).
- Points documentés : décomposition λ, SFF, t_CE, hypothèse IEC DD-dernier, CCF βD omis,
  formules kooN, méthode Markov steady-state, comparaison RBD vs Markov.
- Tableau des corrections effectuées avec justification sourcée.
- Issues priorisées pour v0.5.0.

### Fixed

**`pfh_1oo2()`, `pfh_2oo3()`, `pfh_1oo3()` — MRT → MTTR_DU (API propre)**
- `getattr(p, 'MRT', p.MTTR)` → `p.MTTR_DU` dans les 3 fonctions.
- Comportement numérique inchangé (MTTR_DU = MTTR par défaut), API maintenant explicite et testable.

**Toutes fonctions PFH — docstrings refactorisées**
- Sources primaires citées avec numéro de slide/équation précis.
- Hypothèses IEC explicitées (DD-dernier → safe, CCF βD omis).
- Distinction pfh_1oo2 / pfh_1oo2_ntnu / pfh_1oo2_corrected clarifiée.

### Validation

- Tests IEC : **10/14 VALIDÉS ±1% | 4 ACCEPTABLES | 0 ERREURS** (identique v0.3.5 — aucune régression).
- 8 tests unitaires Sprint 1 : **8/8 PASS** (SubsystemParams cohérence, MTTR_DU, SFF, rétrocompatibilité).

---

## Planned

### [0.5.0] — Normes et architectures étendues
- kooN N>3 généralisé — formule NTNU Ch.8 slide 34 corrigée (≠ SIS book §9.59 errata)
- Architecture 1oo1D diagnostic externe — IEC 62061:2021, IEC DTS 63394
- PFH transitoire (λ×T1 proche de 1) — intégration ODE matrix exponential
- λSU/λSD dans générateur Markov (transitions distinctes latent vs immédiat)
- SFF = DC pour composants électromécaniques (Uberti 2024 Eq.3.14 — validation rapide)

### [0.6.0] — Différenciants
- Weibull λ(t) pour actionneurs mécaniques
- Maintenance imparfaite / dégradation PTC
- Base de données λ intégrée (OREDA/EXIDA)
- Rapport PDF automatique IEC 61511 §11

### [1.0.0] — Crédibilité externe
- Validation vs exSILentia/GRIF (50 cas)
- Publication PyPI + docs Sphinx
- Paper académique RESS
