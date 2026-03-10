# Vérification de la Table 4 — Omeiri, Innal, Liu (2021)
## Configuration 2oo3 sans CCF — Calculs pas à pas

**Document :** Omeiri H., Innal F., Liu Y., *"Consistency Checking of the IEC 61508 PFH
Formulas and New Formulas Proposal Based on the Markovian Approach"*,
Journal Européen des Systèmes Automatisés, Vol. 54, No. 6, pp. 871–879, December 2021.
DOI : https://doi.org/10.18280/jesa.540609

**Objectif :** Reproduire les calculs de la Table 4 (p. 878) étape par étape,
à partir des équations du papier, puis comparer avec les résultats d'un solveur
indépendant (PRISM SIL Engine). Aucune conclusion n'est tirée sans calcul explicite.

---

## 1. Paramètres d'entrée

Le papier définit les paramètres de la section 4 (p. 877) :

> *"The used parameters are: λD = 5E-6 h⁻¹ ; MTTR = MRT = 8 h ; T₁ = 4380 h ;
> β = 2β_D = 0.1 ; MTTR_sd = 24 h. Different values for DC are used."*

La section 4.2 (p. 877) précise pour les Tables 3, 4, 5 :

> *"In order to carry out an effective comparison between the different approaches,
> we only consider the contribution of independent failures: β = 2β_D = 0."*

**Paramètres retenus pour la Table 4 (2oo3 sans CCF) :**

| Symbole | Valeur | Source |
|---------|--------|--------|
| λ_D     | 5×10⁻⁶ h⁻¹ | §4, p.877 |
| MTTR    | 8 h | §4, p.877 |
| MRT     | 8 h | §4, p.877 |
| T₁      | 4380 h | §4, p.877 |
| β       | 0 | §4.2, p.877 |
| β_D     | 0 | §4.2, p.877 |

**Décomposition de λ_D selon DC** (définitions §2.2, p. 872) :

> *"λ_DD = DC · λ_D"*
> *"λ_DU = (1 − DC) · λ_D"*

| DC   | λ_DU = (1−DC)·λ_D | λ_DD = DC·λ_D |
|------|-------------------|----------------|
| 0.6  | 0.4 × 5×10⁻⁶ = **2.000×10⁻⁶ h⁻¹** | 0.6 × 5×10⁻⁶ = **3.000×10⁻⁶ h⁻¹** |
| 0.9  | 0.1 × 5×10⁻⁶ = **5.000×10⁻⁷ h⁻¹** | 0.9 × 5×10⁻⁶ = **4.500×10⁻⁶ h⁻¹** |
| 0.99 | 0.01 × 5×10⁻⁶ = **5.000×10⁻⁸ h⁻¹** | 0.99 × 5×10⁻⁶ = **4.950×10⁻⁶ h⁻¹** |

---

## 2. Équations utilisées

### 2.1 t_CE — Eq. (13), p. 874

$$t_{CE} = \frac{\lambda_{DU}}{\lambda_D}\left[\frac{T_1}{2} + MRT\right] + \frac{\lambda_{DD}}{\lambda_D} \cdot MTTR$$

> *"where: t_CE = (λ_DU / λ_D)[T₁/2 + MRT] + (λ_DD / λ_D) MTTR"*
> — Omeiri 2021, Eq. (13), p. 874

### 2.2 t_CE1 — Eq. (18), p. 875

$$t_{CE1} = \frac{\lambda_{DU}^{ind}}{\lambda_D^{ind}}\left[\frac{T_1}{2} + MRT\right] + \frac{\lambda_{DD}^{ind}}{\lambda_D^{ind}} \cdot MTTR$$

avec λ_DU^ind = (1−β)·λ_DU, λ_DD^ind = (1−β_D)·λ_DD.

**Note :** Quand β = β_D = 0 (cas Table 4), t_CE1 = t_CE.

### 2.3 IEC PFH 2oo3 — Eq. (19), p. 875

$$PFH_{2oo3}^{IEC} = 6\left[(1-\beta_D)\lambda_{DD} + (1-\beta)\lambda_{DU}\right] \cdot t_{CE} \cdot (1-\beta)\lambda_{DU} + \beta\lambda_{DU}$$

**Quand β = β_D = 0 :** PFH = 6(λ_DD + λ_DU) · t_CE · λ_DU

### 2.4 PFH 2oo3 corrigé — Eq. (22), p. 876

$$PFH_{2oo3} \approx 6\left[(1-\beta_D)\lambda_{DD} + (1-\beta)\lambda_{DU}\right] \cdot t_{CE1} \cdot (1-\beta)\lambda_{DU} + \beta\lambda_{DU}$$ 
$$+ 6\,(1-\beta)\lambda_{DU}\left[\frac{T_1}{2} + MRT\right](1-\beta_D)\lambda_{DD}$$
$$+ 3\left((1-\beta_D)\lambda_{DD} \cdot MTTR + (1-\beta)\lambda_{DU}\left[\frac{T_1}{2}+MRT\right]\right)\beta\lambda_{DU}$$

**Quand β = β_D = 0 :** les termes en β s'annulent, ce qui donne :

$$PFH_{2oo3}^{Eq.22} = \underbrace{6(\lambda_{DD}+\lambda_{DU}) \cdot t_{CE} \cdot \lambda_{DU}}_{\text{Terme 1 = IEC}} + \underbrace{6\,\lambda_{DU}\left[\frac{T_1}{2}+MRT\right]\lambda_{DD}}_{\text{Terme 2 = manquant IEC}}$$

---

## 3. Calculs pas à pas

### 3.1 Grandeurs communes (indépendantes de DC)

```
T₁/2 + MRT = 4380/2 + 8 = 2190 + 8 = 2198 h
```

### 3.2 DC = 0.6

**Taux de défaillance :**
```
λ_DU = 2.000×10⁻⁶ h⁻¹
λ_DD = 3.000×10⁻⁶ h⁻¹
λ_D  = 5.000×10⁻⁶ h⁻¹
```

**t_CE [Eq. 13] :**
```
t_CE = (2.000×10⁻⁶ / 5.000×10⁻⁶) × 2198 + (3.000×10⁻⁶ / 5.000×10⁻⁶) × 8
     = 0.4000 × 2198 + 0.6000 × 8
     = 879.2 + 4.8
     = 884.0 h
```

**IEC Eq. (19) :**
```
Terme unique = 6 × 5.000×10⁻⁶ × 884.0 × 2.000×10⁻⁶
             = 6 × 5.000×10⁻⁶ × 1.768×10⁻³
             = 5.304×10⁻⁸ h⁻¹

PFH_IEC = 5.304×10⁻⁸ h⁻¹
```

**Eq. (22) :**
```
Terme 1 = 6 × 5.000×10⁻⁶ × 884.0 × 2.000×10⁻⁶  =  5.304×10⁻⁸
Terme 2 = 6 × 2.000×10⁻⁶ × 2198.0 × 3.000×10⁻⁶  =  7.913×10⁻⁸
Terme 3 = 0  (β=0)

PFH_Eq22 = 5.304×10⁻⁸ + 7.913×10⁻⁸ = 1.322×10⁻⁷ h⁻¹
```

### 3.3 DC = 0.9

**Taux de défaillance :**
```
λ_DU = 5.000×10⁻⁷ h⁻¹
λ_DD = 4.500×10⁻⁶ h⁻¹
λ_D  = 5.000×10⁻⁶ h⁻¹
```

**t_CE [Eq. 13] :**
```
t_CE = (5.000×10⁻⁷ / 5.000×10⁻⁶) × 2198 + (4.500×10⁻⁶ / 5.000×10⁻⁶) × 8
     = 0.1000 × 2198 + 0.9000 × 8
     = 219.8 + 7.2
     = 227.0 h
```

**IEC Eq. (19) :**
```
Terme unique = 6 × 5.000×10⁻⁶ × 227.0 × 5.000×10⁻⁷
             = 6 × 5.000×10⁻⁶ × 1.135×10⁻⁴
             = 3.405×10⁻⁹ h⁻¹

PFH_IEC = 3.405×10⁻⁹ h⁻¹
```

**Eq. (22) :**
```
Terme 1 = 6 × 5.000×10⁻⁶ × 227.0 × 5.000×10⁻⁷  =  3.405×10⁻⁹
Terme 2 = 6 × 5.000×10⁻⁷ × 2198.0 × 4.500×10⁻⁶  =  2.967×10⁻⁸
Terme 3 = 0  (β=0)

PFH_Eq22 = 3.405×10⁻⁹ + 2.967×10⁻⁸ = 3.308×10⁻⁸ h⁻¹
```

### 3.4 DC = 0.99

**Taux de défaillance :**
```
λ_DU = 5.000×10⁻⁸ h⁻¹
λ_DD = 4.950×10⁻⁶ h⁻¹
λ_D  = 5.000×10⁻⁶ h⁻¹
```

**t_CE [Eq. 13] :**
```
t_CE = (5.000×10⁻⁸ / 5.000×10⁻⁶) × 2198 + (4.950×10⁻⁶ / 5.000×10⁻⁶) × 8
     = 0.0100 × 2198 + 0.9900 × 8
     = 21.98 + 7.92
     = 29.90 h
```

**IEC Eq. (19) :**
```
Terme unique = 6 × 5.000×10⁻⁶ × 29.90 × 5.000×10⁻⁸
             = 6 × 5.000×10⁻⁶ × 1.495×10⁻⁶
             = 4.485×10⁻¹¹ h⁻¹

PFH_IEC = 4.485×10⁻¹¹ h⁻¹
```

**Eq. (22) :**
```
Terme 1 = 6 × 5.000×10⁻⁶ × 29.90 × 5.000×10⁻⁸  =  4.485×10⁻¹¹
Terme 2 = 6 × 5.000×10⁻⁸ × 2198.0 × 4.950×10⁻⁶  =  3.264×10⁻⁹
Terme 3 = 0  (β=0)

PFH_Eq22 = 4.485×10⁻¹¹ + 3.264×10⁻⁹ = 3.309×10⁻⁹ h⁻¹
```

---

## 4. Résultats du solveur PRISM SIL Engine (indépendant)

Le solveur utilise trois méthodes indépendantes :

- **`pfh_2oo3(p)`** : implémentation de l'IEC Eq. (19)
- **`pfh_2oo3_corrected(p)`** : implémentation de l'Eq. (22) d'Omeiri 2021
- **`compute_exact(p, 'high_demand')`** : solveur Markov CTMC (scipy), aucune formule analytique, résolution en régime permanent de la matrice génératrice Q

| DC   | `pfh_2oo3` (IEC Eq.19) | `pfh_2oo3_corrected` (Omeiri Eq.22) | Markov CTMC |
|------|------------------------|--------------------------------------|-------------|
| 0.6  | 5.3040×10⁻⁸            | 1.3217×10⁻⁷                          | 1.3043×10⁻⁷ |
| 0.9  | 3.4050×10⁻⁹            | 3.3078×10⁻⁸                          | 3.2966×10⁻⁸ |
| 0.99 | 4.4850×10⁻¹¹           | 3.3089×10⁻⁹                          | 3.3074×10⁻⁹ |

**Vérification de cohérence interne :** calcul manuel (§3) versus solveur :

| DC   | Méthode | Manuel | Solveur | Écart |
|------|---------|--------|---------|-------|
| 0.6  | IEC Eq.19 | 5.304×10⁻⁸ | 5.3040×10⁻⁸ | **0.000 %** |
| 0.6  | Omeiri Eq.22 | 1.322×10⁻⁷ | 1.3217×10⁻⁷ | **0.002 %** |
| 0.9  | IEC Eq.19 | 3.405×10⁻⁹ | 3.4050×10⁻⁹ | **0.000 %** |
| 0.9  | Omeiri Eq.22 | 3.308×10⁻⁸ | 3.3078×10⁻⁸ | **0.006 %** |
| 0.99 | IEC Eq.19 | 4.485×10⁻¹¹ | 4.4850×10⁻¹¹ | **0.000 %** |
| 0.99 | Omeiri Eq.22 | 3.309×10⁻⁹ | 3.3089×10⁻⁹ | **0.003 %** |

→ Le solveur et le calcul manuel sont identiques à moins de 0.01 %.

---

## 5. Comparaison avec la Table 4 publiée

### Table 4 telle que publiée dans Omeiri 2021 (p. 878)

> *"Table 4. PFH Results for 2oo3 configuration without CCF"*

| DC   | IEC: Eq. (19) | MPM      | AM       | Eq. (22) |
|------|---------------|----------|----------|----------|
| 0.6  | 5.304E-8      | 1.299E-7 | 1.293E-7 | 1.322E-7 |
| 0.9  | 3.405E-9      | 3.285E-7 | 3.289E-7 | 3.308E-7 |
| 0.99 | 4.485E-11     | 3.295E-9 | 3.307E-9 | 3.309E-9 |

### Comparaison ligne par ligne

**DC = 0.6 :**

| Colonne | Publié | Notre calcul | Écart |
|---------|--------|--------------|-------|
| IEC Eq.(19) | 5.304E-8 | 5.304×10⁻⁸ | **0.00 %** ✓ |
| Eq.(22) | 1.322E-7 | 1.322×10⁻⁷ | **0.02 %** ✓ |
| Markov (MPM) | 1.299E-7 | 1.304×10⁻⁷ | **0.39 %** ✓ |

**DC = 0.99 :**

| Colonne | Publié | Notre calcul | Écart |
|---------|--------|--------------|-------|
| IEC Eq.(19) | 4.485E-11 | 4.485×10⁻¹¹ | **0.00 %** ✓ |
| Eq.(22) | 3.309E-9 | 3.309×10⁻⁹ | **0.003 %** ✓ |
| Markov (MPM) | 3.295E-9 | 3.307×10⁻⁹ | **0.37 %** ✓ |

**DC = 0.9 :**

| Colonne | Publié | Notre calcul | Écart |
|---------|--------|--------------|-------|
| IEC Eq.(19) | 3.405E-9 | 3.405×10⁻⁹ | **0.00 %** ✓ |
| Eq.(22) | **3.308E-7** | **3.308×10⁻⁸** | **900 %** ← |
| Markov (MPM) | **3.285E-7** | **3.297×10⁻⁸** | **896 %** ← |

---

## 6. Analyse de la discordance à DC = 0.9

### 6.1 Observation factuelle

Pour DC = 0.9, **les colonnes IEC Eq.(19) sont identiques** entre nos calculs et le papier
(écart 0.00 %). Les colonnes Eq.(22) et Markov présentent un écart d'un facteur ≈ 10.

Nos calculs donnent : **3.308×10⁻⁸**. Le papier publie : **3.308E-7**.
La mantisse `3.308` est identique. Seul l'exposant diffère : `E-8` vs `E-7`.

### 6.2 Contrainte physique de monotonicité

Par définition (§2.2 du papier) :

```
λ_DU = (1 − DC) × λ_D
```

Donc λ_DU est une **fonction strictement décroissante** de DC.

Le PFH d'un 2oo3 est, au premier ordre, proportionnel à λ_DU² (terme dominant
quand λ_DU << λ_DD). Il doit donc **décroître strictement** quand DC augmente.

Vérification avec les valeurs publiées :

```
DC = 0.6  → Eq.(22) = 1.322E-7
DC = 0.9  → Eq.(22) = 3.308E-7   (publiée)
DC = 0.99 → Eq.(22) = 3.309E-9
```

La valeur publiée à DC = 0.9 est **supérieure** à celle de DC = 0.6.
Cela impliquerait qu'augmenter la couverture diagnostic de 60 % à 90 %
**dégrade** la fiabilité du système — ce qui contredit la définition même du DC.

Avec nos valeurs :

```
DC = 0.6  → 1.322×10⁻⁷   (ratio 1)
DC = 0.9  → 3.308×10⁻⁸   (ratio 0.250 ≈ (0.1/0.4)² = 0.0625... au second ordre)
DC = 0.99 → 3.309×10⁻⁹   (ratio 0.025)
```

La décroissance est stricte et cohérente avec la physique. ✓

### 6.3 Cohérence entre colonnes à DC = 0.9

Dans le papier, à DC = 0.9 :

- **IEC Eq.(19)** = 3.405E-9 (notre calcul : 3.405×10⁻⁹, **Δ = 0 %**)
- **Eq.(22)** publiée = 3.308E-7

L'Eq.(22) est l'IEC augmentée d'un terme positif. Elle doit donc être
**supérieure** à l'IEC, mais du même ordre de grandeur.

À DC = 0.6 : Eq.(22) / IEC = 1.322E-7 / 5.304E-8 = **2.49** (facteur ~2.5) ✓
À DC = 0.9 : Eq.(22) / IEC = 3.308E-7 / 3.405E-9 = **97.1** si publiée correcte
À DC = 0.9 : Eq.(22) / IEC = 3.308E-8 / 3.405E-9 = **9.7** avec notre valeur

À DC = 0.99 : Eq.(22) / IEC = 3.309E-9 / 4.485E-11 = **73.8** ✓

La tendance Eq.(22)/IEC croît quand DC augmente (le terme manquant pèse de plus en plus,
car λ_DD domine). Notre valeur à DC = 0.9 s'insère dans cette tendance croissante
(2.49 → 9.7 → 73.8). La valeur publiée 3.308E-7 donnerait un ratio de 97, soit plus
grand que DC = 0.99 (73.8), ce qui briserait également la tendance.

---

## 7. Synthèse

| Critère | Valeur publiée 3.308E-7 | Notre valeur 3.308E-8 |
|---------|-------------------------|----------------------|
| Mantisse identique | ✓ (3.308) | ✓ (3.308) |
| Monotonicité PFH(DC) | ❌ PFH(0.9) > PFH(0.6) | ✓ PFH(0.9) < PFH(0.6) |
| Cohérence avec IEC Eq.(19) colonne | ❌ ratio ×97 (aberrant) | ✓ ratio ×9.7 (tendance normale) |
| Concordance calcul manuel Eq.(22) | ❌ Δ = 900 % | ✓ Δ = 0.006 % |
| Concordance Markov CTMC indépendant | ❌ Δ = 896 % | ✓ Δ = 0.37 % |
| Cohérence avec DC=0.6 et DC=0.99 | ❌ rupture de tendance | ✓ tendance continue |

### Observation

L'ensemble des éléments — calcul analytique direct de l'Eq. (22), solveur Markov CTMC
indépendant, monotonicité physique, et cohérence des ratios entre colonnes — désignent
la valeur **3.308×10⁻⁸** comme résultat attendu pour DC = 0.9.

La valeur publiée **3.308E-7** présente la même mantisse avec un exposant décalé d'une
unité (`E-7` au lieu de `E-8`), de façon identique pour les colonnes MPM et Eq.(22).
Les auteurs du papier sont les mieux placés pour confirmer ou infirmer cette observation.

---

## Annexe — Code de reproduction (PRISM SIL Engine)

```python
from sil_engine.formulas import SubsystemParams, pfh_2oo3, pfh_2oo3_corrected
from sil_engine.markov import compute_exact

for dc in [0.6, 0.9, 0.99]:
    ldu = (1 - dc) * 5e-6
    ldd = dc * 5e-6
    p = SubsystemParams(
        lambda_DU=ldu, lambda_DD=ldd,
        MTTR=8, MTTR_DU=8, T1=4380,
        beta=0.0, beta_D=0.0,
        architecture='2oo3', M=2, N=3
    )
    pfh_iec  = pfh_2oo3(p)
    pfh_eq22 = pfh_2oo3_corrected(p)
    pfh_mkv  = compute_exact(p, 'high_demand')['pfh']
    print(f"DC={dc}: IEC={pfh_iec:.4e}  Eq22={pfh_eq22:.4e}  Markov={pfh_mkv:.4e}")
```

**Sortie :**
```
DC=0.6:  IEC=5.3040e-08  Eq22=1.3217e-07  Markov=1.3043e-07
DC=0.9:  IEC=3.4050e-09  Eq22=3.3078e-08  Markov=3.2966e-08
DC=0.99: IEC=4.4850e-11  Eq22=3.3089e-09  Markov=3.3074e-09
```

---

*Document produit dans le cadre du développement de PRISM SIL Engine (open-source).*
*Calculs réalisés le 10 mars 2026.*
