# PRISM SIL Engine — Analyse Sprint A : Bugs #7 à #10
## Propagation incomplète de `MTTR_DU` + label trompeur

**Date :** 2026-03-10  
**Version analysée :** v0.4.1  
**Fichiers concernés :** `formulas.py`, `extensions.py`, `markov.py`  
**Statut :** Markdown d'analyse — AVANT toute modification de code  
**Règle appliquée :** Vérifier et sourcer AVANT de modifier.

---

## 0. Contexte et cause racine commune

Le Sprint 1 (v0.4.0) a introduit `MTTR_DU` comme champ explicite dans `SubsystemParams`,
remplaçant le pattern `getattr(p, 'MRT', p.MTTR)` fragile. Ce champ modélise le
**Mean Repair Time pour les défaillances DU** — physiquement distinct de `MTTR`
(qui s'applique aux DD).

**La correction Sprint 1 a été appliquée aux fonctions IEC non-corrigées (`pfh_1oo2`,
`pfh_2oo3`, `pfh_1oo3`) mais n'a PAS été propagée à :**

1. `pfh_1oo2_corrected` et `pfh_2oo3_corrected` (formulas.py)
2. `pfh_moon` et `pfd_koon_generic` et `pfd_mgl` (extensions.py)
3. `_build_generator_pfh` (markov.py)

**De plus**, un mauvais commentaire ajouté lors du fix Bug #6 (« MRT = mean repair time = MTTR »)
perpétue une **mauvaise lecture de Omeiri 2021** en la présentant comme équivalence
conceptuelle alors qu'il s'agit de valeurs numériques égales dans les simulations de la
section 4 seulement.

---

## 1. Source primaire — Omeiri, Innal, Liu (2021), JESA 54(6):871-879

### 1.1 Nomenclature officielle (§2.2, p.872)

Le papier définit **explicitement et distinctement** :

| Symbole | Nom complet | Défaillances concernées |
|---------|-------------|------------------------|
| `MTTR`  | Mean Time To **Restoration** | DD (Dangerous Detected) |
| `MRT`   | Mean **Repair** Time | DU (Dangerous Undetected) |

**Citation §2.2 :** *«MTTR is the Mean Time To Restoration for dangerous detected failures (DD). MRT is the Mean Repair Time for dangerous undetected failures (DU).»*

**Équivalence dans PRISM :** `MRT` (Omeiri) ≡ `MTTR_DU` (SubsystemParams.MTTR_DU)

### 1.2 Paramètres numériques de la section 4 (p.877)

Omeiri utilise `MTTR = MRT = 8 h` uniquement comme hypothèse numérique pour
les tableaux de comparaison. Cette égalité numérique **n'est pas une définition** —
elle cache la distinction conceptuelle. Le commentaire `# MRT = mean repair time = MTTR`
ajouté lors du Bug #6 est donc erroné en tant que déclaration générale.

### 1.3 Formule tCE1 (Omeiri 2021, Eq.18)

```
tCE1 = (λDU_ind / λD_ind) × [T1/2 + MRT] + (λDD_ind / λD_ind) × MTTR
```

où `MRT` = Mean Repair Time pour DU = `MTTR_DU`.

**Différence avec IEC tCE (Eq.13) :**
- IEC tCE : utilise les taux totaux (λDU/λD, λDD/λD)
- Omeiri tCE1 : utilise les taux indépendants (λDU_ind/λD_ind, λDD_ind/λD_ind)
  avec λDU_ind = (1-β)λDU, λDD_ind = (1-βD)λDD

### 1.4 Terme manquant 1oo2 (Omeiri 2021, Eq.17)

```
PFH_1oo2_corrected = 2[(1-βD)λDD + (1-β)λDU] · tCE1 · (1-β)λDU
                   + β·λDU
                   + 2·(1-β)·λDU·[T1/2 + MRT]·λDD          ← terme manquant
```

**Note :** Dans ce terme, λDD est le **taux total** (non CCF-ajusté).

### 1.5 Formule complète 2oo3 (Omeiri 2021, Eq.22)

```
PFH_2oo3_corrected = 6[(1-βD)λDD + (1-β)λDU] · tCE1 · (1-β)λDU
                   + β·λDU
                   + 6·(1-β)·λDU·[T1/2 + MRT]·(1-βD)·λDD   ← terme manquant #1
                   + 3·((1-βD)λDD·MTTR + (1-β)λDU·[T1/2+MRT])·β·λDU  ← terme manquant #2
```

**Note :** Omeiri p.876 précise que le terme manquant #2 *«could be neglected against
the second one (βλDU)»* mais l'inclut pour exactitude.

---

## 2. Source secondaire — Uberti 2024, Eq.6.3

```
t_CE = (λ_DU/λ_D) × (T1/2 + MRT) + (λ_DD/λ_D) × MTTR
```

Uberti définit (§6.1) : *«MRT = Mean Repair Time pour les défaillances λ_DU (latentes,
révélées au proof test). MTTR = Mean Time To Repair pour λ_DD (déclenchement immédiat).»*

**Équivalence :** `MRT` (Uberti) ≡ `MTTR_DU` (SubsystemParams.MTTR_DU). ✓

---

## 3. Source tertiaire — NTNU Ch.8, slide 31 (Rausand & Lundteigen)

```
t_CE = (λDU/λD)(T1/2 + MRT) + (λDD/λD)·MTTR
μDU = 1/(T1/2 + MRT)
```

MRT dans NTNU = Mean Repair Time pour DU = `MTTR_DU`. ✓

---

## 4. Bug #7 — `pfh_1oo2_corrected` et `pfh_2oo3_corrected` : MRT régression

### 4.1 Localisation

```
formulas.py, ligne 363 (pfh_1oo2_corrected) :
    MRT = p.MTTR   # FIX Bug #6 : MTTR, pas T1/2   ← INCORRECT

formulas.py, ligne 387 (pfh_2oo3_corrected) :
    MRT = p.MTTR   # FIX Bug #6 : MTTR, pas T1/2   ← INCORRECT
```

### 4.2 Diagnostic

Le Bug #6 a corrigé `MRT = T1/2` → `MRT = MTTR`. C'était mieux que `T1/2` (qui donnait
×547 d'erreur), mais reste incorrect car `MRT` (Omeiri) = `MTTR_DU` ≠ `MTTR` en général.

Le commentaire `# Source : Omeiri 2021 p.875 note : MRT = mean repair time = MTTR` est
une **mauvaise interprétation** : Omeiri utilise `MTTR = MRT = 8h` en section 4 uniquement
comme paramètre numérique, pas comme définition conceptuelle.

### 4.3 Impact numérique

- **Cas par défaut** (`MTTR_DU = MTTR = 8h`) : **Δ = 0%** — les tests passent donc.
- **Cas MTTR=8h, MTTR_DU=48h** (maintenance après proof test programmé) :
  - `T1/2 + MTTR_DU` = 4380 + 48 = 4428h
  - `T1/2 + MTTR` = 4380 + 8 = 4388h
  - Erreur = (4428 - 4388) / 4428 = **+0.9%** sur tCE1

- **Cas extrême MTTR=8h, MTTR_DU=168h** (réparation semaine entière) :
  - Erreur sur tCE1 ≈ **3.5%** → répercuté sur tout le PFH
  - Potentiellement visible dans la classification SIL

### 4.4 Correction

```python
# AVANT (incorrect)
MRT = p.MTTR   # FIX Bug #6 : MTTR, pas T1/2

# APRÈS (correct — conforme Omeiri 2021 §2.2, Uberti 2024 Eq.6.3, NTNU Ch.8 slide 31)
MRT = p.MTTR_DU   # Mean Repair Time DU (Omeiri 2021 §2.2) ≡ MTTR_DU ≠ MTTR en général
```

**Applicabler à :** `pfh_1oo2_corrected` ligne 363 ET `pfh_2oo3_corrected` ligne 387.

---

## 5. Bug #8 — `extensions.py` : trois occurrences de `getattr` résiduelles

### 5.1 Localisation

```
extensions.py, ligne 79  (pfh_moon)         : MRT = getattr(p, 'MRT', p.MTTR)
extensions.py, ligne 265 (pfd_mgl)          : MRT = getattr(p, 'MRT', p.MTTR)
extensions.py, ligne 615 (pfd_koon_generic) : MRT = getattr(p, 'MRT', p.MTTR)
```

### 5.2 Diagnostic

Ce pattern était l'ancienne façon de lire `MRT` avant Sprint 1. Depuis Sprint 1,
`SubsystemParams` n'a pas d'attribut `MRT` — il n'existe que `MTTR_DU`.
Donc `getattr(p, 'MRT', p.MTTR)` retourne **toujours** `p.MTTR` (la valeur par défaut).

**Résultat :** Ces trois fonctions utilisent silencieusement `MTTR` pour le terme DU,
ignorant complètement `MTTR_DU`. C'est exactement le bug que Sprint 1 a résolu pour
les fonctions dans `formulas.py`, mais qui a survécu dans `extensions.py`.

### 5.3 Fonctions affectées et impact

| Fonction | Impact |
|----------|--------|
| `pfh_moon(p, k, n)` | PFH kooN N>3 (2oo4, 1oo4, 3oo4) — fonctions nouvelles non-IEC |
| `pfd_mgl(p, arch)` | PFD avec modèle MGL (β, γ, δ) — terme CCF `β×λDU×(T1/2+MRT)` |
| `pfd_koon_generic(p, k, n)` | PFD kooN généralisé — tous les tGEi |

### 5.4 Correction

```python
# AVANT (incorrect — getattr résiduel pré-Sprint1)
MRT = getattr(p, 'MRT', p.MTTR)

# APRÈS (correct — conforme Sprint1, Omeiri §2.2, Uberti Eq.6.3)
MRT = p.MTTR_DU   # Mean Repair Time DU ≡ MTTR_DU (SubsystemParams, Sprint 1)
```

---

## 6. Bug #9 — `markov.py/_build_generator_pfh` : `mu_du` utilise `MTTR` au lieu de `MTTR_DU`

### 6.1 Localisation

```
markov.py, ligne 122 (_build_generator_pfh) :
    mu_du = 1.0 / (self.T1 / 2.0 + self.p.MTTR)   ← INCORRECT
```

### 6.2 Diagnostic

`mu_du` modélise le taux de "découverte et réparation" des canaux DU lors du proof test.

**Source (NTNU Ch.8 slide 31, Uberti 2024 Eq.6.3, Omeiri 2021 §3.1.2, Eq.8) :**
```
μDU = 1 / (T1/2 + MRT)
```
où `MRT` = Mean Repair Time pour DU = `MTTR_DU`.

Le commentaire du code le dit lui-même ligne 117 :
```
μ_DU = 1/(T1/2 + MRT) modélise la "réparation" DU au proof test.
```
... mais utilise `self.p.MTTR` (pour DD) au lieu de `self.p.MTTR_DU` (pour DU).

**Note :** `self.mu = 1.0 / p.MTTR` (pour μDD dans `__init__`) est **correct** car il
s'applique aux DD. Seul `mu_du` est incorrect.

### 6.3 Impact — Le plus critique des 4 bugs

Ce bug affecte le **Moteur 2 (Markov exact)**, censé être la référence absolue.
Avec `MTTR_DU > MTTR` :
- `mu_du` bugué est **trop grand** → simulation retire les DU trop vite du système
- **PFH sous-estimé** — le moteur exact donne des résultats NON-conservatifs

**Exemple chiffré :**
- `T1 = 8760h, MTTR = 8h, MTTR_DU = 48h`
- `mu_du_correct = 1/(4380+48) = 1/4428 = 2.258e-4/h`
- `mu_du_bugué = 1/(4380+8) = 1/4388 = 2.279e-4/h`
- Erreur sur mu_du = +0.92% → PFH légèrement sous-estimé

Avec `MTTR_DU = 168h` (1 semaine) :
- `mu_du_correct = 1/(4380+168) = 2.200e-4/h`
- `mu_du_bugué = 1/(4380+8) = 2.279e-4/h`
- Erreur = +3.6% → **potentiellement visible sur classification SIL**

### 6.4 Correction

```python
# AVANT (incorrect)
mu_du = 1.0 / (self.T1 / 2.0 + self.p.MTTR)

# APRÈS (correct — conforme NTNU Ch.8 slide 31, Omeiri 2021 Eq.8, Uberti 2024 Eq.6.3)
mu_du = 1.0 / (self.T1 / 2.0 + self.p.MTTR_DU)   # μDU = 1/(T1/2 + MTTR_DU)
```

---

## 7. Bug #10 — Label trompeur dans `compute_exact(mode='high_demand')`

### 7.1 Localisation

```
markov.py, ligne 375 :
    "method": "analytique-corrigée (Omeiri/Innal 2021)",
```

### 7.2 Diagnostic

Dans `compute_exact(mode='high_demand')`, la valeur de retour `pfh` est calculée par
`solver.compute_pfh()` — c'est le **résultat Markov CTMC**. La clé `pfh_corrected`
contient la valeur Omeiri analytique (pour comparaison), pas la clé `pfh`.

Le label `"analytique-corrigée (Omeiri/Innal 2021)"` décrit donc la **mauvaise valeur**.
Un ingénieur safety qui cite ce label dans son dossier SIL attribue un résultat Markov
à la méthode analytique Omeiri — erreur de traçabilité dans un document normatif.

### 7.3 Correction

```python
# AVANT (trompeur)
"method": "analytique-corrigée (Omeiri/Innal 2021)",

# APRÈS (exact)
"method": "Markov-CTMC (steady-state, scipy.linalg)",
```

La clé `pfh_corrected` garde déjà sa propre attribution implicite via son nom.

---

## 8. Bilan des modifications planifiées

| # | Fichier | Ligne | Avant | Après | Source |
|---|---------|-------|-------|-------|--------|
| 7a | formulas.py | 363 | `MRT = p.MTTR` | `MRT = p.MTTR_DU` | Omeiri §2.2, Eq.17-18 |
| 7b | formulas.py | 387 | `MRT = p.MTTR` | `MRT = p.MTTR_DU` | Omeiri §2.2, Eq.22 |
| 8a | extensions.py | 79 | `getattr(p,'MRT',p.MTTR)` | `p.MTTR_DU` | Uberti Eq.6.3, NTNU slide 31 |
| 8b | extensions.py | 265 | `getattr(p,'MRT',p.MTTR)` | `p.MTTR_DU` | Uberti Eq.6.3 |
| 8c | extensions.py | 615 | `getattr(p,'MRT',p.MTTR)` | `p.MTTR_DU` | Uberti Eq.6.3 |
| 9  | markov.py | 122 | `self.p.MTTR` | `self.p.MTTR_DU` | NTNU Ch.8 slide 31, Omeiri Eq.8 |
| 10 | markov.py | 375 | `"analytique-corrigée (Omeiri/Innal 2021)"` | `"Markov-CTMC (steady-state, scipy.linalg)"` | Rigueur traçabilité |

**Règle de non-régression :** Les tests existants (MTTR_DU = MTTR par défaut) doivent
rester 100% PASS car la correction ne change pas le comportement à MTTR_DU=MTTR=8h.

---

## 9. Cas de test additionnels pour valider les corrections

### Test #T15 — Sensibilité MTTR_DU ≠ MTTR (pfh_corrected)

```python
p_base = SubsystemParams(lambda_DU=5e-7*0.1, lambda_DD=5e-7*0.9, 
                         MTTR=8, MTTR_DU=8, T1=8760, 
                         beta=0.02, beta_D=0.01)
p_asym = SubsystemParams(lambda_DU=5e-7*0.1, lambda_DD=5e-7*0.9, 
                         MTTR=8, MTTR_DU=48, T1=8760, 
                         beta=0.02, beta_D=0.01)

# Avec MTTR_DU > MTTR :
# pfh_1oo2_corrected(p_asym) > pfh_1oo2_corrected(p_base)  (tCE1 plus grand)
# pfh_1oo2(p_asym) > pfh_1oo2(p_base)                      (même direction)
# Les deux doivent répondre de façon cohérente
```

### Test #T16 — Markov exact cohérent avec analytique pour MTTR_DU ≠ MTTR

```python
# La différence Markov exact vs IEC doit augmenter avec MTTR_DU
# (car mu_du diminue → DU restent plus longtemps → PFH plus élevé)
result_8h = compute_exact(p_base, 'high_demand')
result_48h = compute_exact(p_asym, 'high_demand')
assert result_48h['pfh'] > result_8h['pfh']
```

---

## 10. Vérification structurelle de pfh_2oo3_corrected vs Omeiri Eq.22

Avant correction, vérifier que la structure est correcte (seul MRT est faux) :

**Omeiri Eq.22 :**
```
PFH_2oo3 = 6[(1-βD)λDD+(1-β)λDU]·tCE1·(1-β)λDU   [pfh_main]
          + βλDU                                      [pfh_ccf]
          + 6(1-β)λDU·[T1/2+MRT]·(1-βD)λDD          [pfh_missing_1]
          + 3((1-βD)λDD·MTTR+(1-β)λDU·[T1/2+MRT])·βλDU  [pfh_missing_2]
```

**Code actuel (avant correction) :**
```python
pfh_main      = 6*(ldd+ldu)*t_CE1*ldu       # ldu=(1-β)λDU, ldd=(1-βD)λDD ✓
pfh_ccf       = p.beta * p.lambda_DU        # βλDU ✓
pfh_missing_1 = 6*ldu*(T1/2+MRT)*ldd       # (1-βD)λDD via ldd ✓, MRT faux ✗
pfh_missing_2 = 3*(ldd*p.MTTR+ldu*(T1/2+MRT))*p.beta*p.lambda_DU  # structure ✓, MRT faux ✗
```

**Structure ✓** — seul `MRT = p.MTTR` → `MRT = p.MTTR_DU` à corriger.

---

## 11. Note sur la mauvaise lecture dans le commentaire Bug #6

```python
# Source : Omeiri 2021 p.875 note : MRT = mean repair time = MTTR.  ← INCORRECT
```

Omeiri §4 (p.877) utilise `λD = 5E-6/h; MTTR = MRT = 8h` comme paramètres numériques
égaux pour simplifier la comparaison. Ce n'est pas une définition. Le commentaire
doit être corrigé en même temps que le code.

---

*Analyse rédigée AVANT toute modification de code — PRISM SIL Engine Sprint A*  
*Sources : Omeiri/Innal/Liu (2021) JESA §2.2 Eq.8,13,17,18,22 ; Uberti 2024 Eq.6.3 ; NTNU Ch.8 slide 31*
