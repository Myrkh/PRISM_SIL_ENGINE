# Analyse des Sources Primaires — PRISM SIL Engine
## NTNU Ch.8 (Rausand & Lundteigen) et Uberti 2024 (Politecnico Milano)

**Statut :** Intégration v0.3.5 → v0.4.0  
**Auteur :** Analyse réalisée session 2026-03-10  
**Démarche :** Scientifique et conservatrice — aucune modification sans justification vérifiable.

---

## 1. Documents analysés

| Source | Référence complète | Rôle dans le moteur |
|--------|-------------------|---------------------|
| **NTNU Ch.8** | Rausand M. & Lundteigen M.A., *«Calculation of PFH»*, RAMS Group, Dept. of Mechanical and Industrial Engineering, NTNU Trondheim, Version 0.1, 37 slides. | Référence académique primaire pour les formules PFH haute demande, dérivations alternatives, méthode Markov. |
| **Uberti 2024** | Uberti M., *«Functional Safety: a comparison between RBD and Markov models for the analysis of Safety Instrumented Systems»*, Tesi di Laurea Magistrale, Politecnico di Milano, Academic Year 2023-2024, 125 p. Advisor: Prof. L. Cristaldi. | Validation indépendante des formules IEC 61508, décomposition des taux de défaillance, étude comparative RBD vs Markov. |

---

## 2. Points de convergence — ce que les deux sources confirment

### 2.1 Décomposition des taux de défaillance

**Uberti 2024 §3.4, Eq.3.9 :**
```
λ_total = λ_Sd + λ_Su + λ_Dd + λ_Du + λ_NE
```

Cette décomposition en 5 composantes est la base de toute la fonctionnalité SIL.
Les défaillances sans effet (λ_NE) sont exclues des calculs de sécurité fonctionnelle.

**Implication pour le moteur :**
- `SubsystemParams` v0.3.5 utilisait `lambda_S` scalaire (= λ_Sd + λ_Su amalgamés)
- **Correction Sprint 1 :** ajout de `lambda_SD` et `lambda_SU` séparés avec `lambda_S = lambda_SD + lambda_SU`
- La distinction est nécessaire pour : calcul STR précis (λ_Su latente vs λ_Sd immédiate), générateur Markov futur

### 2.2 Formule SFF (Safe Failure Fraction)

**Uberti 2024 §3.5, Eq.3.13 :**
```
SFF = (λ_s + λ_Dd) / (λ_s + λ_D)
    = (λ_SD + λ_SU + λ_DD) / (λ_SD + λ_SU + λ_DD + λ_DU)
```

**Cas particulier (Uberti 2024 §3.5, Eq.3.14) :**
Pour composants électromécaniques en haute demande avec λ_s ≈ 0 :
```
SFF ≈ DC
```

**Statut dans le moteur :** ✅ CORRECT avant Sprint 1 — la formule `(lambda_S + lambda_DD) / (lambda_S + lambda_DD + lambda_DU)` était déjà conforme. La correction Sprint 1 documente explicitement la conformité et garantit `lambda_S = lambda_SD + lambda_SU`.

**Nota :** Le cas `SFF = DC` sera utile pour validation rapide (ROADMAP).

### 2.3 Formule t_CE (temps d'exposition équivalent du groupe)

**Uberti 2024 §6.1, Eq.6.3 :** (même relation que NTNU Ch.8 slide 31)
```
t_CE = (λ_DU/λ_D) × (T₁/2 + MRT) + (λ_DD/λ_D) × MTTR
```

**Distinction physique (NTNU slide 31, Uberti Eq.6.3) :**
- `MTTR` = Mean Time To Repair pour **λ_DD** : déclenchement immédiat par diagnostics, réparation planifiable dès la détection.
- `MRT` / `MTTR_DU` = Mean Repair Time pour **λ_DU** : défaillance latente, révélée au proof test seulement. La réparation commence après la découverte. Physiquement ≈ MTTR dans la plupart des systèmes, mais concept distinct.

**Correction Sprint 1 :** Remplacement du `getattr(p, 'MRT', p.MTTR)` fragile par `p.MTTR_DU` — champ explicite dans `SubsystemParams` avec `MTTR_DU = MTTR` par défaut (backward compatible).

**Quantification de l'impact :** Pour λ_DU = 5×10⁻⁹/h, λ_DD = 45×10⁻⁹/h (DC=90%), T1=8760h, MTTR=8h : 
- `MTTR_DU = 8h` → PFH = 1.002161×10⁻¹⁰/h
- `MTTR_DU = 200h` → PFH = 1.002254×10⁻¹⁰/h  
Δ = +0.01% → impact numérique faible, mais distinction théorique nécessaire pour rigueur normative.

---

## 3. Formules PFH — analyse comparative NTNU vs IEC

### 3.1 Hypothèse fondamentale IEC (NTNU Ch.8 slides 29-30)

> *«A group failure (DGF) occurs if a D (DU or DD) failure occurs first (independent failure), and then a DU failure. If a DD failure occurs as the last failure (independent or CCF), it results in a transition to the safe state.»*

Cette hypothèse est **discutable** (NTNU slide 29 le note explicitement : *«questionable since it is impossible to know WHEN the DD failure is the last»*), mais est celle retenue par IEC 61508-6 Annexe B pour simplification.

**Conséquence dans le moteur :**
- `pfh_1oo2()` et `pfh_2oo3()` : hypothèse IEC — DD-dernier omis → **borne inférieure**
- `pfh_1oo2_ntnu()` : inclut le terme DU→DD → **borne supérieure conservatrice**
- `pfh_1oo2_corrected()` et `pfh_2oo3_corrected()` : correction Omeiri 2021 — terme DU→DD ajouté → **valeur intermédiaire recommandée**

### 3.2 PFH 1oo2 — Synthèse des formules disponibles

| Fonction | Formule | Source | Hypothèse | Biais |
|----------|---------|--------|-----------|-------|
| `pfh_1oo2()` | `2×λ_D^(i)×ldu×t_CE + β×λDU` | IEC §B.3.3.2.2 | DD-dernier → safe | Sous-estimation ~8.7% |
| `pfh_1oo2_ntnu()` | `ldu²×T1 + ldu×ldd×T1 + 2×ldu×ldd×MTTR + β×λDU` | NTNU Ch.8 slides 24-26 | Tous DGF inclus | Sur-estimation conservative |
| `pfh_1oo2_corrected()` | `pfh_IEC + 2×ldu×(T1/2+MRT)×λDD` | Omeiri et al. 2021 Eq.17 | Terme DU→DD ajouté | Recommandée SIL3/4 |

**Note sur `pfh_1oo2_ntnu` :** La formule NTNU développée (slide 26) avec approximation Maple :
```
Pr(DGF in (0,τ)) ≈ (λDU×τ)² + λDU×λDD×τ² + 2×λDU×λDD×MTTR
```
Soit : `PFH = λDU²×τ + λDU×λDD×τ + 2×λDU×λDD×MTTR + β×λDU`

Le terme `λDU×λDD×τ` est l'option (a) NTNU slide 24 : *«DU fails first, then DD occurs during exposure window»*. IEC l'omet car DD-dernier → safe (slide 29). Omeiri le réintègre dans sa correction.

### 3.3 CCF — terme βD×λDD omis (NTNU Ch.8 slide 28)

> *«β_D×λ_DD was omitted. The main reason is that a double DD failure is assumed to result in a commanded transition to the safe state.»*

**Confirmation de notre implémentation :** `pfh_ccf = beta * lambda_DU` ✅

Cela signifie que la CCF de défaillances DD (qui provoquerait un trip commun) résulte en un état sûr, pas en DGF.

### 3.4 kooN généralisé (NTNU Ch.8 slides 22, 34)

**Formule kooN générale (slide 34) :**
```
PFH_G = (∏_{i=1}^{n-k+1}(n-i+1)) × (λ_D^(i))^{n-k} × (1-β)λ_DU × (∏_{i=2}^{n-k} t_GEi) × t_CE + β×λDU
```

**Note slide 34 :** *«There is an error in formula (9.59) in the SIS book, so the one above has been developed for the purpose of the slides. It is in line with the new version of section 8.4, formula 8.48, found under errata for the textbook.»*

→ Cette formule corrigée n'est pas encore implémentée pour N>3 (kooN générique ROADMAP).

**Uberti 2024 Annexe E, Eq.E.4-E.8 :** Dérivation exacte via binomiale pour DU seulement :
```
PFH_{kooN} = (n choose n-k+1) × λ_DU^{n-k+1} × T1^{n-k}
```
Appliqué à 1oo2 : `PFH = λ_DU² × T1` (Eq.E.8) — conforme NTNU slide 27, valide DC=0%.

---

## 4. Méthode Markov — confirmation de notre implémentation

### 4.1 Procédure NTNU (slide 35)

1. Définir les états du système
2. Tracer le diagramme de transitions
3. **Calculer les probabilités en régime stationnaire** (ou transitoires)
4. **PFH = somme des «sauts» vers les états dangereux**

**Formule slide 37 (2oo4, non repairable, λD = λDU + λDD) :**
```
PFH_G = P₂ × 2λ_D
```
où P₂ est la probabilité stationnaire d'être dans l'état «critique» (2 canaux en panne).

**Notre `compute_pfh()` (markov.py) :**
```python
PFH = Σ_{i∈Working} Σ_{j∈Dangerous} π_i × Q[i,j]
```
C'est exactement la formule NTNU : probabilité stationnaire × taux de transition vers état dangereux.

**Validation 8/8 PASS, Δ_max = 0.2%** ✅

### 4.2 Footnote importante (NTNU slide 35)

> *«Alternatively, if time dependent probabilities have been calculated: Integrate and average the «jumps» into the dangerous states during a defined time interval.»*

→ Notre moteur utilise les probabilités stationnaires (steady-state), ce qui est l'approximation valide pour λ×T1 << 1. Pour les cas où λ×T1 > 0.1, les probabilités transitoires (intégration matricielle) seraient plus précises. C'est la raison de notre critère de basculement Markov/IEC.

### 4.3 Comparaison RBD vs Markov (Uberti 2024 §7.1.3)

Uberti compare l'approche RBD (IEC DTS 63394) vs Markov (IEC 62061) pour architecture 1oo1D :

| Paramètre varié | Conclusion |
|----------------|-----------|
| λ_D (10⁻⁸ à 10⁻⁶) | Compatible ; RBD légèrement conservative (safe side) |
| λ_D élevé (10⁻⁶ à 10⁻⁴) | Divergence significative ; RBD perd son sens conservatif |
| λ_react variable | Les deux modèles suivent le même trend ; écart constant |
| DC variable (0–100%) | RBD plus conservative avec DC croissant |
| β variable (0–10%) | RBD plus sensible au β que Markov |

**Conclusion Uberti :** RBD (formules IEC simplifiées) est valide et conservatif pour les plages industrielles typiques (λ_D ∈ [10⁻⁸, 10⁻⁶]/h). Au-delà, Markov est requis.

**Cette conclusion valide notre stratégie dual-engine :**
- Moteur IEC (RBD) pour λ×T1 < 0.1
- Moteur Markov exact pour λ×T1 ≥ 0.1 ou SIL3/4

---

## 5. Ce que les sources n'apportent pas (lacunes connues)

| Sujet | Statut | Source manquante |
|-------|--------|-----------------|
| λSU/λSD impact sur STR précis | ROADMAP | NTNU Ch.12 (non fourni encore) |
| kooN N>3 avec correction NTNU errata | ROADMAP | Rausand & Lundteigen SIS book §8.4 errata |
| Architecture 1oo1D diagnostic externe | Non implémenté | IEC 62061:2021, IEC DTS 63394 |
| PFH par intégration transitoire (λ×T1 > 0.5) | Non implémenté | Méthode Markov transitoire (ODE) |
| Maintenance imparfaite / Weibull λ(t) | ROADMAP | PDS Method Handbook (SINTEF) |

---

## 6. Corrections effectuées Sprint 1 — récapitulatif sourcé

| Correction | Motivation | Source | Impact |
|------------|-----------|--------|--------|
| Ajout `lambda_SD` + `lambda_SU` dans `SubsystemParams` | Décomposition complète λ_S | Uberti 2024 Eq.3.9, IEC 61508-2 §3.6 | STR futur, Markov futur, SFF explicitement justifiée |
| Règle cohérence `lambda_S = lambda_SD + lambda_SU` en `__post_init__` | Intégrité des données | Uberti 2024 §3.5 | Détection d'erreurs utilisateur à la création |
| Ajout champ `MTTR_DU` (Mean Repair Time DU) | Distinction MTTR_DD vs MTTR_DU | NTNU Ch.8 slide 31, Uberti 2024 Eq.6.3 | +0.01% à +2% PFH selon ratio MTTR_DU/T1 |
| Remplacement `getattr(p,'MRT',p.MTTR)` par `p.MTTR_DU` | Fragilité API | Principe d'API explicite | Robustesse, maintenabilité |
| Mise à jour docstrings (toutes fonctions PFH + SFF) | Traçabilité scientifique | Sources primaires | Auditabilité IEC 61511 §11 |
| Enrichissement résultat `route1h_constraint` | Transparence lambda_SD, lambda_SU | IEC 61508-2 Table 2 | Rapport détaillé possible |

---

## 7. Recommandations pour v0.4.0 — issues priorisées

### Issue #1 — Haute priorité : kooN N>3 généralisé

**Base :** NTNU Ch.8 slide 34 formule corrigée (≠ SIS book §9.59).  
**Ce qu'il faut faire :** Implémenter la formule générale avec `t_GEi` cascadé.  
**Test de validation :** Comparer vs Markov exact pour 2oo4, 1oo4, 3oo4.

### Issue #2 — Haute priorité : SFF cas électromécanique (DC-only)

**Base :** Uberti 2024 Eq.3.14 : `SFF = DC` quand λ_s ≈ 0.  
**Ce qu'il faut faire :** Ajouter un flag ou une validation dans `route1h_constraint` qui alerte si λ_S = 0 et DC > 0 (incohérence fréquente dans les entrées).

### Issue #3 — Moyenne priorité : λSU/λSD dans générateur Markov

**Base :** Uberti 2024 §3.4 — λ_Su est latente (pattern ≈ λ_DU), λ_Sd est immédiate.  
**Ce qu'il faut faire :** Dans `MarkovGenerator`, distinguer les transitions :
- λ_SD → transition immédiate vers état safe detected (réparation MTTR)
- λ_SU → défaillance latente découverte au proof test (réparation après T1/2 + MTTR_SU)

### Issue #4 — Basse priorité : PFH via intégration transitoire

**Base :** NTNU Ch.8 slide 35 footnote 2 — valide pour λ×T1 proche de 1.  
**Ce qu'il faut faire :** Alternative dans `compute_exact()` mode `transient` utilisant scipy.linalg.expm ou intégration numérique des probabilités P(t).

---

## 8. Cohérence vérifiée — ce qui NE change PAS

Les points suivants ont été vérifiés comme **corrects avant Sprint 1** et restent inchangés :

| Point | Formule | Vérification |
|-------|---------|-------------|
| PFH = ROCOF dangereux | Slide 15 NTNU | Conforme — compute_pfh() = Σ π_i × Q[i→j_danger] |
| CCF 1oo2 : β×λDU seulement | NTNU slide 28 | `pfh_ccf = p.beta * p.lambda_DU` ✅ |
| DD-dernier → safe → omis IEC | NTNU slide 29 | `pfh_1oo2()` : terme λDU×λDD×T1 absent ✅ |
| t_CE = pfh_avg / t_GE | NTNU slide 33 | Vérifiable analytiquement ✅ |
| PFH_SIF = Σ PFH_sous-systèmes | NTNU slide 18 | Additivité des sous-systèmes ✅ |
| Markov : steady-state valide si λ×T1 << 1 | NTNU slide 35 fn.1 | Critère `lambda_T1 > 0.1` → Markov requis ✅ |

---

*Document rédigé pour PRISM SIL Engine v0.3.5 → v0.4.0*  
*Sources : Rausand & Lundteigen NTNU RAMS Group (v0.1) ; Uberti M. (2024) Politecnico Milano*
