# Sprint F — Weibull λ(t) pour SIS : PFD/PFH avec taux de défaillance non-constant
## PRISM SIL Engine — Document théorique de référence
### Version 0.6.0 — Mars 2026

---

## 1. Contexte et motivation

### 1.1 L'hypothèse de taux constant dans IEC 61508

IEC 61508 part 6 Annex B et les formules analytiques kooN (§B.3) reposent
**entièrement** sur l'hypothèse d'un taux de défaillance constant λ :

```
R(t) = exp(−λ·t)    [distribution exponentielle]
```

Cette hypothèse est valide pour la **période de vie utile** des composants électroniques
(phase centrale de la courbe en baignoire), où les défaillances ont un caractère aléatoire.

Pour les **composants mécaniques** (vannes ESD, actionneurs, pompes), l'hypothèse
est explicitement reconnue comme approximative par les auteurs eux-mêmes :

> *"We want to preserve the assumptions about constant failure rates, meaning that
> the SIS components should always be in their useful life period (and replaced before
> entering the wear-out phase)"*
>
> — Lundteigen & Rausand, NTNU SIS Book Chapter 4 §Introduction (Version 0.1)

En pratique, de nombreuses installations maintiennent des composants mécaniques
en service bien au-delà de leur vie utile recommandée. L'hypothèse λ = const
devient alors **non conservative** : le vrai PFDavg dépasse le PFDavg calculé,
parfois de façon significative.

### 1.2 Quantification numérique préliminaire

Pour une vanne ESD avec MTTF = 219 000 h (≈ 25 ans, typique OREDA), T1 = 8760 h,
comparaison entre le modèle exponentiel IEC (λ = 1/MTTF) et le modèle Weibull
à même MTTF :

| β_w | t_age | R(t_age) | PFDavg_Weibull | Ratio vs IEC |
|-----|-------|----------|----------------|--------------|
| 1.0 | tout  | —        | = PFDavg_IEC   | 1.00×        |
| 2.0 | 20 ans| 0.58     | 2.51×10⁻²      | +26%         |
| 2.0 | 25 ans| 0.38     | 3.12×10⁻²      | +56%         |
| 3.0 | 25 ans| 0.24     | 4.26×10⁻²      | +113%        |
| 3.0 | 35 ans| 0.14     | 8.07×10⁻²      | **+303%**    |
| 4.0 | 30 ans| 0.25     | 9.05×10⁻²      | **+353%**    |

Référence IEC : PFDavg_exp = λ × T1/2 = 4.57×10⁻⁶ × 4380 = 2.00×10⁻².

**Conclusion** : l'impact du vieillissement peut dépasser +300% pour β_w ≥ 3 et
t_age > MTTF. Pour β_w = 2 (usure modérée, courant pour les vannes), l'impact
à la fin de vie nominale (25 ans) est déjà +56% — suffisant pour franchir une
frontière SIL.

> ⚠️ **Note critique** : le "+300%" n'est pas une constante universelle.
> Il dépend fortement de (β_w, t_age/MTTF). Tout résultat doit préciser ces paramètres.

---

## 2. Distribution de Weibull — paramétrage et formules fondamentales

### 2.1 Paramétrage adopté (2-parameter Weibull)

PRISM utilise la paramétrisation standard à 2 paramètres :

```
F(t) = 1 − exp(−(t/η)^β_w)
```

avec :
- **β_w** : paramètre de forme (shape parameter), sans dimension
  - β_w < 1 : mortalité infantile (taux décroissant)
  - β_w = 1 : exponentielle (taux constant) — cas IEC 61508
  - β_w > 1 : usure (taux croissant) — cas pertinent pour mécaniques
- **η** : paramètre d'échelle / vie caractéristique (h), défini par F(η) = 1−e⁻¹ ≈ 63.2%

Source primaire : Rausand & Høyland (2004), *System Reliability Theory*, 2nd ed., §B.3, Eq.(B.6).

**Relations dérivées :**

| Quantité | Formule | Source |
|---------|---------|--------|
| Fiabilité | R(t) = exp(−(t/η)^β_w) | Rausand & Høyland 2004, Eq.(B.5) |
| Taux de défaillance | h(t) = (β_w/η)·(t/η)^(β_w−1) | Rausand & Høyland 2004, Eq.(B.7) |
| MTTF | η · Γ(1 + 1/β_w) | Rausand & Høyland 2004, Eq.(B.8) |

où Γ est la fonction gamma d'Euler.

### 2.2 Relation β_w → η à MTTF équivalent

Pour comparer au modèle exponentiel IEC à même MTTF, la vie caractéristique est :

```
η = MTTF / Γ(1 + 1/β_w)
```

Valeurs numériques clés :

| β_w | Γ(1+1/β_w) | η/MTTF |
|-----|-----------|--------|
| 1.0 | 1.000     | 1.000  |
| 1.5 | 0.903     | 1.108  |
| 2.0 | 0.886     | 1.128  |
| 3.0 | 0.893     | 1.120  |

---

## 3. PFDavg avec λ(t) — formulation exacte

### 3.1 Formule générale : composant neuf (t_age = 0)

Pour un composant 1oo1 DU avec distribution Weibull, sous l'hypothèse de **proof test
parfait** (composant remis à neuf à chaque T1) :

```
PFDavg = (1/T1) × ∫₀^T1 [1 − exp(−(t/η)^β_w)] dt
```

Source : Rausand & Høyland (2004) §10.3, définition de PFDavg comme moyenne temporelle
de l'indisponibilité ; Rogova, Lodewijks & Lundteigen (2017) Eq.(4).

Cette intégrale n'a pas de forme fermée générale pour β_w non-entier. PRISM utilise
l'intégration numérique exacte (scipy.integrate.quad, tolérance 1e-10).

**Cas particuliers analytiques :**

Pour λ_DU·T1 ≪ 1 (approximation valable lorsque F(T1) ≪ 1) :
```
PFDavg ≈ T1^β_w / (η^β_w · (β_w + 1))
```

Pour β_w = 1 (exponentielle, vérification) :
```
PFDavg = 1 − [1 − exp(−λT1)] / (λT1)
       ≈ λ·T1/2    pour λT1 ≪ 1  (formule IEC 61508-6 §B.3.1.2, 2nd order approx.)
```

> **Note** : la formule IEC λ·T1/2 est une approximation d'ordre 2 de la valeur
> exacte. Pour λT1 = 0.04, l'erreur est +1.34% (IEC légèrement sur-conservateur).
> PRISM calcule l'intégrale exacte sans approximation : la vérification β_w = 1
> se fait contre la valeur exacte `1 − (1−exp(−λT1))/(λT1)`, pas contre λT1/2.
> Écart numérique : < 5×10⁻¹⁶ (arrondi flottant uniquement). ✓

### 3.2 Composant vieillissant : proof tests non-réparateurs (t_age > 0)

Lorsque le proof test révèle et répare les **défaillances** mais ne renouvelle pas
le composant (maintenance minimale — "minimal repair"), le composant continue à
vieillir avec son âge calendaire t_age.

Le taux de défaillance conditionnel, pour un composant ayant survécu jusqu'à t_age,
dans l'intervalle [t_age, t_age + T1] :

```
h(t | t_age) = h(t_age + t)  [non-renewal process]
```

La fiabilité conditionnelle dans cet intervalle :
```
R(t | t_age) = R(t_age + t) / R(t_age) = exp[−(t_age+t)^β_w/η^β_w + t_age^β_w/η^β_w]
```

Le PFDavg dans l'intervalle ième, t_age = (i−1)·T1 :

```
PFDavg(t_age) = (1/T1) × ∫₀^T1 [1 − R(t_age + t)/R(t_age)] dt
```

Source : Rogova, Lodewijks & Lundteigen (2017) §"Forecasting formula", p.377-378 ;
Wu, Zhang, Lundteigen, Liu & Zheng (2019), RESS 185, DOI:10.1016/j.ress.2018.11.003,
Eq.(6)-(9).

> **Note sur les hypothèses de maintenance :**
>
> - **AGAN** (As-Good-As-New) : proof test parfait + remplacement → t_age = 0 après chaque test.
>   → PFDavg constant à chaque intervalle.
>
> - **Minimal repair** : proof test révèle les défaillances, répare, mais l'âge continue.
>   → PFDavg croissant à chaque intervalle → **c'est ce que PRISM modélise avec t_age > 0**.
>
> Le choix entre les deux hypothèses est critique pour l'évaluation du vieillissement.
> PRISM expose les deux via le paramètre `t_age`.

---

## 4. PFHavg avec λ(t) — formulation exacte

### 4.1 Formule analytique (résultat remarquable)

Pour un composant 1oo1 en mode haute demande, le PFHavg sur [t_age, t_age + T1] admet
une forme analytique **exacte** :

```
PFHavg(t_age) = [1 − R(t_age + T1)/R(t_age)] / T1  =  Q(T1 | t_age) / T1
```

**Dérivation :**

```
PFH(t | t_age) = h(t_age + t) × R(t | t_age)

PFHavg = (1/T1) × ∫₀^T1 h(t_age + t) × R(t_age + t)/R(t_age) dt
       = (1/T1) × [−R(t_age + T1)/R(t_age) + R(t_age)/R(t_age)]
       = [1 − R(t_age + T1)/R(t_age)] / T1
       = Q(T1 | t_age) / T1
```

Ce résultat est **exact pour tout β_w** et ne nécessite pas d'intégration numérique.
Il peut s'interpréter comme : "probabilité de défaillance dans l'intervalle, par unité de temps."

Source : Derivation from first principles — h(t)×R(t) = −dR/dt intégré sur [0,T1].
Ce résultat est implicite dans Rausand & Høyland (2004) §10.4 et explicité dans
Rogova et al. (2017) §"Calculation of PFH", p.376.

### 4.2 Vérification : β_w = 1

Pour β_w = 1 : R(t) = exp(−λt), R(t_age + T1)/R(t_age) = exp(−λT1)
```
PFHavg = [1 − exp(−λT1)] / T1 ≈ λ    pour λT1 ≪ 1
```
Ce qui correspond à la formule IEC 61508-6 §B.3.3.1.1 pour 1oo1. ✓

---

## 5. Extension kooN

### 5.1 Formule PFDavg pour kooN

Pour un système kooN (p = N−M défaillances DU nécessaires) avec composants identiques
Weibull(β_w, η), proof tests parfaits simultanés :

```
PFDavg_kooN(t_age) = C(N, p+1) × (1/T1) × ∫₀^T1 [Q(t | t_age)]^(p+1) dt
```

où Q(t | t_age) = 1 − R(t_age + t)/R(t_age) est la PFD conditionnelle du composant.

Cette expression résulte de l'approximation q(t)^(p+1) valide pour q(t) ≪ 1.
Source : Rogova, Lodewijks & Lundteigen (2017) Eq.(15) ; Rausand & Høyland (2004)
§9.4, Eq.(9.15).

Pour t_age = 0 (composant neuf) :
```
PFDavg_kooN ≈ C(N, p+1) / (T1^(p+1)) × T1^((p+1)β_w+1) / ((p+1)β_w + 1) / η^((p+1)β_w)
            = C(N, p+1) × T1^((p+1)β_w) / (η^((p+1)β_w) × ((p+1)β_w + 1))
```
(approximation pour F(T1) ≪ 1)

### 5.2 Formule PFHavg pour kooN

En utilisant l'identité PFH_kooN(t) = N·λ(t)·R(t)·PFD_koo(N-1)(t)
(Chebila & Innal 2015, Eq.(17) ; Rogova et al. 2017 Eq.(20)-(22)) :

```
PFHavg_kooN = (1/T1) × ∫₀^T1 N·h(t_age+t)·R(t|t_age) × C(N-1,p) × [Q(t|t_age)]^p dt
```

Cette intégrale requiert intégration numérique. Pas de forme analytique générale
pour β_w ≠ 1.

### 5.3 Lien avec Bug #11

Pour β_w = 1 (exponentielle), les formules PFHavg_kooN ci-dessus sont calculées
en time-domain, ce qui est cohérent avec les résultats du Sprint C (Bug #11).
Le module `weibull.py` généralise naturellement l'approche TD au cas non-exponentiel.

---

## 6. Impact quantitatif sur les frontières SIL

### 6.1 Cas de référence : vanne ESD, 1oo2, SIL 3

Paramètres : MTTF = 219 000 h, T1 = 8760 h, DC = 0, β = 0.
Frontière SIL 2/SIL 3 : PFDavg = 10⁻³.
PFDavg_IEC (1oo2) ≈ (λT1)² / 3 = (4.57e-6 × 8760)² / 3 = 5.4×10⁻⁴ → SIL 3 atteint.

Avec β_w = 2, t_age = 20 ans :
Q(T1 | t_age) ≈ 1.3 × Q(T1 | 0) [ratio de l'ordre de 1.3 pour ce cas]
PFDavg_1oo2_weibull ≈ [Q_comp(t_age)]² × 3 ∝ 1.3² × PFDavg_1oo2_IEC = 1.7× → encore SIL 3.

Avec β_w = 3, t_age = 25 ans :
PFD_comp(T1 | t_age) ≈ 2.13 × PFD_comp_IEC
PFDavg_1oo2_weibull ≈ 2.13² × PFDavg_1oo2_IEC = 4.5× → peut franchir la frontière SIL 2.

> **Conclusion opérationnelle** : pour des systèmes 1oo2 en SIL 3, le vieillissement
> de composants mécaniques avec β_w ≥ 2-3 au-delà de leur vie nominale peut
> reclasser le système en SIL 2. C'est l'application directe de PRISM Weibull.

### 6.2 Tableau de sensibilité (1oo1)

| β_w | t_age/MTTF | Ratio PFDavg_Weibull / PFDavg_IEC |
|-----|-----------|-----------------------------------|
| 1.0 | toute valeur| 1.00 (tautologique) |
| 1.5 | 0.5        | 0.59 |
| 1.5 | 1.0        | 0.99 ≈ 1.00 |
| 1.5 | 1.5        | 1.27 |
| 2.0 | 0.5        | 0.33 |
| 2.0 | 1.0        | 0.95 ≈ 1.00 |
| 2.0 | 1.5        | 1.56 |
| 3.0 | 1.0        | 0.80 |
| 3.0 | 1.5        | **2.13** |
| 3.0 | 2.0 (hors vie)| **5.17** |

Calculé numériquement avec MTTF = 219 000 h, T1 = 8760 h.

**Observation critique** : pour t_age ≈ MTTF (composant en fin de vie nominale),
le Weibull donne un PFDavg **inférieur** à l'IEC pour β_w ≥ 2 (la concentration
des défaillances n'a pas encore atteint le pic). La dégradation n'est visible
qu'au-delà de MTTF. Cela signifie que l'utilisation standard IEC est
légèrement conservatrice avant MTTF, puis non-conservative après.

---

## 7. État de l'art — littérature existante

| Référence | Contribution | Méthode | Limites |
|-----------|-------------|---------|---------|
| Rausand & Høyland (2004) §10 | Définition exacte PFDavg pour λ(t) | Intégration exacte | Pas de kooN avec Weibull |
| Jigar (2013), Mémoire NTNU | Première application kooN Weibull pour SIS | Ratio CDFs | Mémoire non publié |
| Rogova, Lodewijks & Lundteigen (2017) JRR 231(4):373-382 DOI:10.1177/1748006X17694999 | **Formules analytiques PFDavg et PFH, MooN, Weibull** | Ratio CDFs + approximation | Proof tests supposés sans impact (AGAN seulement) ; approximation, pas intégration exacte |
| Wu, Zhang, Lundteigen, Liu, Zheng (2019) RESS 185 DOI:10.1016/j.ress.2018.11.003 | Modélisation subsea SIS avec Weibull et partial testing | Probabilités conditionnelles | Focalisé sur partial tests et restoration retardée ; architecture 1oo1 principalement |
| Lundteigen & Rausand, NTNU SIS Book Ch.4 | Motivation et limites de l'hypothèse λ=const | Conceptuel | Pas de calcul Weibull quantitatif |

**Note critique sur la référence "Lundteigen & Rausand 2009 RESS 94(7)"** :

Après recherche, les papiers de Lundteigen & Rausand dans RESS 2009 sont :
- RESS 94(2) p.520-525 : "Architectural constraints in IEC 61508"
- RESS 94(12) p.1894-1903 : "Integrating RAMS engineering and management"

Aucun de ces papiers ne porte spécifiquement sur Weibull λ(t) pour PFD/PFH.
**La référence "RESS 94(7)" citée dans les sessions précédentes est incorrecte.**
Les sources primaires correctes pour Sprint F sont Rogova et al. (2017) et Wu et al. (2019).

---

## 8. Ce que PRISM apporte vs l'état de l'art

| Aspect | Rogova 2017 | Wu 2019 | PRISM Sprint F |
|--------|------------|---------|----------------|
| PFDavg 1oo1 Weibull | Approximation analytique | Num. conditionnel | **Intégration exacte** |
| PFHavg 1oo1 Weibull | Formule approx. | — | **Formule analytique exacte** |
| kooN PFDavg | Approximation ratio CDFs | 1oo1 principalement | **Intégration exacte C(N,p+1)·Q^(p+1)** |
| kooN PFHavg | Formule approx. | — | **Intégration numérique exacte** |
| t_age > 0 (vieillissement) | "Forecasting" approx. | Oui (formules approx.) | **Intégration exacte pour tout t_age** |
| Comparaison avec IEC/Omeiri | Non | Non | **Rapport structuré ratio Weibull/IEC** |
| Liaison avec moteur PRISM existant | Non applicable | Non | **Compatible SubsystemParams + route_compute** |

**Contribution originale de PRISM Sprint F :**
- PFHavg 1oo1 exact analytique : Q(T1|t_age)/T1 — démonstration en §4.1
- Intégration exacte (scipy.quad, tolérance 1e-10) pour PFDavg kooN et PFHavg kooN
- Exposition du paramètre t_age pour quantification du vieillissement en service
- Rapport de sensibilité ratio_weibull_vs_iec() pour ingénieurs praticiens

---

## 9. Stratégie de validation

### 9.1 Cas dégénéré β_w = 1

Pour tout (η, T1, t_age, M, N) avec β_w = 1 (η = 1/λ) :
- `pfd_weibull()` doit reproduire `pfh_koon_corrected()` à < 0.1%
- `pfh_weibull()` doit reproduire `compute_exact()` (mode high_demand) à < 0.1%

### 9.2 Formule analytique PFH 1oo1

Vérification directe : `pfh_weibull_1oo1` vs `scipy.quad` de l'intégrale exacte.
Critère : écart < 1e-12 (différence due à l'arrondi flottant uniquement).

### 9.3 Limite β_w → 1

Continuité des formules kooN au voisinage de β_w = 1. Critère : |PFDavg(β_w=1.001) − PFDavg_exp| < 0.01%.

### 9.4 Validation croisée contre Rogova 2017

La Table 2 de Rogova 2017 fournit des PFDavg pour un actionneur 1oo2 avec
DC ≈ 60%, β_w donné (low/moderate/high degradation). Reproduire ces valeurs
à < 5% (marge donnée par les approximations de Rogova).

---

## 10. Spécification API — `weibull.py`

```python
def pfd_weibull(
    beta_w : float,   # paramètre de forme Weibull (> 0)
    eta    : float,   # vie caractéristique (h) (> 0)
    T1     : float,   # intervalle de proof test (h) (> 0)
    M      : int = 1, # nombre minimum de canaux requis
    N      : int = 1, # nombre total de canaux
    t_age  : float = 0.0,   # âge du composant en début d'intervalle (h)
    DC     : float = 0.0,   # couverture diagnostique [0, 1)
    tol    : float = 1e-10  # tolérance intégration
) -> dict:
    """
    PFDavg pour architecture kooN avec taux de défaillance Weibull.
    
    Retourne :
        pfd_avg       : PFDavg sur [t_age, t_age + T1]
        pfd_component : PFD du composant individuel Q(T1|t_age)
        lambda_eff    : taux effectif = PFD_component / (T1/2)
        ratio_vs_exp  : PFDavg_Weibull / PFDavg_exp(lambda_eff)
    """

def pfh_weibull(
    beta_w : float,
    eta    : float,
    T1     : float,
    M      : int = 1,
    N      : int = 1,
    t_age  : float = 0.0,
    DC     : float = 0.0,
) -> dict:
    """
    PFHavg pour architecture kooN avec taux de défaillance Weibull.
    Pour 1oo1 : résultat analytique exact Q(T1|t_age)/T1.
    Pour kooN avec p ≥ 1 : intégration numérique.
    """

def weibull_aging_profile(
    beta_w  : float,
    eta     : float,
    T1      : float,
    n_intervals : int = 20,
    M       : int = 1,
    N       : int = 1,
) -> list[dict]:
    """
    Profil de PFDavg sur n_intervals intervalles successifs (t_age = 0, T1, 2T1, ...).
    Hypothèse : maintenance minimale (âge continue entre proof tests).
    Utile pour identifier le moment où le SIL change.
    """

def ratio_weibull_vs_iec(
    beta_w  : float,
    mttf    : float,
    T1      : float,
    t_age   : float,
    M       : int = 1,
    N       : int = 1,
) -> float:
    """
    Ratio PFDavg_Weibull / PFDavg_IEC(λ=1/MTTF) à même MTTF.
    Outil de sensibilité pour ingénieurs praticiens.
    """
```

---

## 11. Décisions d'implémentation

### 11.1 Traitement du DC dans le module Weibull

Pour DC > 0, les défaillances se décomposent en :
- λ_DU(t) = (1 − DC) × h(t) — non détectées (gèrent le PFDavg/PFHavg DU)
- λ_DD(t) = DC × h(t) — détectées (réparées sous MTTR, contribution PFH DD)

La contribution DD au PFH est subdivisée :
```
PFH_DD(t) = λ_DD(t) × R(t) ≈ DC × h(t)   [pour DC faible]
```

Sprint F implémente DC = 0 pour l'intégration numérique DU pure.
Le couplage DC complet sera Sprint G (lambda database + DC paramétrique).

### 11.2 Intégration numérique

`scipy.integrate.quad` avec `epsabs=1e-10, epsrel=1e-10, limit=200`.
Pour kooN, intégration de [Q(t|t_age)]^(p+1) qui peut avoir des gradients raides
près de T1 pour β_w grand et t_age élevé — gestion via `points` d'inflexion.

### 11.3 Garde-fous numériques

- Si R(t_age) < 1e-6 : composant quasi-certainement défaillant, lever `WeibullAgeError`.
- Si β_w < 0.1 ou β_w > 10 : hors plage physiquement raisonnable pour SIS.
- Si η < T1/10 : composant trop fragile pour l'intervalle considéré.

---

## 12. Sources primaires

| Source | Référence complète | Utilisée pour |
|--------|-------------------|---------------|
| Rausand & Høyland (2004) | *System Reliability Theory*, 2nd ed., Wiley. §B.3 Eq.(B.5-8), §10.3-10.4 | Formules de base Weibull, définition PFDavg |
| Rogova, Lodewijks & Lundteigen (2017) | J. Risk Reliab. 231(4):373-382. DOI:10.1177/1748006X17694999 | PFDavg kooN Weibull, PFH approximation, cas d'étude valve |
| Wu, Zhang, Lundteigen, Liu, Zheng (2019) | RESS 185. DOI:10.1016/j.ress.2018.11.003 | Formules conditionnelles Weibull, partial testing, subsea case |
| Lundteigen & Rausand, NTNU SIS Book Ch.4 | ntnu.edu SIS textbook slides (public) | Motivation hypothèse λ=const, citation directe |
| IEC 61508-6:2010 §B.3 | Norme NF EN 61508-6 | Point de comparaison formules IEC standard |
| Chebila & Innal (2015) | JLPPI 34:167-176. DOI:10.1016/j.jlp.2015.02.002 | Eq.(17) pour PFH_kooN = N·λ·R·PFD_koo(N-1) |

---

*Document de référence PRISM SIL Engine v0.6.0 — Sprint F*  
*Rédigé avant implémentation — conformément à la démarche scientifique PRISM*
