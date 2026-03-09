# 11 — Formules IEC 61508-6 Annexe B — Référence Complète Exacte

> Source : **IEC 61508-6:2010 / NF EN 61508-6:2011 — Annexe B (informative)**  
> Ce document reproduit fidèlement toutes les formules, hypothèses, paramètres et tableaux  
> de l'Annexe B pour implémentation dans le moteur de calcul PRISM.

---

## B.1 — Généralités et Classification des Méthodes

L'Annexe B définit deux grandes familles de modèles :

### Modèles statiques (Booléens)
- Diagrammes de fiabilité (RBD)
- Arbres de panne (FTA)
- Arbres d'événements
- **Caractéristique** : liens logiques statiques, pas de dynamique temporelle native

### Modèles de transition d'état (Dynamiques)
- Modèles Markoviens (homogènes = taux constants)
- Réseaux de Pétri
- Langages formels (AltaRica)
- **Caractéristique** : modèlent les transitions d'état en fonction du temps

> **NOTE CRITIQUE** : La présente Annexe distingue explicitement :
> - **Approche simplifiée** (B.3) : formules fermées issues de développements de Taylor (prudentes, approximées)
> - **Approche exacte** (B.5) : calcul direct sur diagrammes de Markov multiphases

---

## B.2 — Paramètres et Définitions

### B.2.1 — Structure SIF

```
PFD_SYS = PFD_S + PFD_L + PFD_FE
PFH_SYS = PFH_S + PFH_L + PFH_FE
```

où :
- `PFD_SYS` = PFD de la fonction de sécurité complète
- `PFD_S` = PFD du sous-système capteur (Sensor)
- `PFD_L` = PFD du sous-système logique (Logic)
- `PFD_FE` = PFD du sous-système élément final (Final Element)

### B.2.2 — Calcul PFD à partir de U(t)

```
PFDavg(T) = MDT(T) = (1/T) × ∫₀ᵀ U_sf(t) dt
```

Pour coupes minimales d'ordre 1 :
```
PFD_D(τ) = (1/τ) × ∫₀^τ λ_D × t × dt = λ_D × τ/2
```

Pour coupes minimales d'ordre 2 (E, F en parallèle) :
```
PFD_EF(τ) = (1/τ) × ∫₀^τ λ_E × λ_F × t² × dt = λ_E × λ_F × τ²/3
```

> **NOTE** : Contrairement à l'idée reçue, la PFD d'un système 1oo2 n'est PAS `(λτ)²/4`  
> mais `(λτ)²/3`. L'erreur classique est de combiner les PFD individuelles.

### B.2.3 — Calcul PFH

Pour un système en mode haute demande / continu :
```
PFH = Λ_as = 1/MTTF  (approx. pour systèmes réparables)
```

Formule exacte via Markov de disponibilité :
```
PFH = 1/(MUT + MDT)
```

où :
- `MUT` = Mean Up Time
- `MDT` = Mean Down Time

---

## B.3 — Hypothèses de l'Approche Simplifiée (B.3.1)

Ces hypothèses s'appliquent à TOUS les tableaux B.2 à B.16 :

1. **λ × T1 << 1** — Les taux de défaillance et intervalles de test sont tels que la probabilité de défaillance multiple est négligeable
2. **Composants identiques** — Chaque canal du groupe à logique majoritaire a le même λ_D et le même DC
3. **Essai périodique parfait** sauf si PTC < 1 (voir B.3.2.5)
4. **T1 >> MTTR** — L'intervalle entre essais est bien supérieur à la durée de réparation
5. **Un seul intervalle d'essai T1** par sous-système
6. **MTTR = MRT = 8h** (valeur par défaut utilisée dans les tableaux)
7. **Pour 1oo2, 1oo2D, 1oo3, 2oo3** : toute réparation est réalisée pendant l'essai périodique (pas de réparation entre essais)
8. **Pour 1oo1, 2oo2** : une défaillance DD est supposée détectée quasi instantanément (MTTR de l'état DD ≈ MTTR global)
9. **β = 2 × β_D** dans tous les tableaux B.2 à B.13

---

## B.3.2 — Tableau des Paramètres (Tableau B.1)

| Symbole | Définition | Valeurs dans les tableaux |
|---------|------------|--------------------------|
| T1 | Intervalle essai périodique (h) | 730, 2190, 4380, 8760, 17520, 87600 h |
| MTTR | Durée moyenne de rétablissement (h) | 8 h |
| MRT | Temps moyen de dépannage (h) | 8 h |
| DC | Couverture de diagnostic (fraction) | 0%, 60%, 90%, 99% |
| β | Proportion CCF non détectées (fraction) | 2%, 10%, 20% |
| β_D | Proportion CCF détectées par diagnostic | 1%, 5%, 10% |
| λ_DU | Taux défaillances DU du canal (h⁻¹) | 5E-8 à 2.5E-5 |
| λ_DD | = λ_D × DC | — |
| λ_DU | = λ_D × (1-DC) | — |
| λ_D | = λ_DD + λ_DU | — |
| t_CE | Temps indisponibilité moyen équivalent canal (h) | calculé |
| t_GE | Temps indisponibilité moyen équivalent groupe (h) | calculé |
| PTC | Couverture essai périodique | 0-1 |
| K | Efficacité circuit autotest 1oo2D | 0.98 (défaut) |

---

## B.3.2.2 — Formules PFD Mode Faible Sollicitation (Basse Demande)

### Temps d'indisponibilité équivalent de canal

```
t_CE = (λ_DU/λ_D) × (T1/2 + MRT) + (λ_DD/λ_D) × MTTR
```

**Forme développée :**
```
t_CE = λ_DU × (T1/2 + MRT) / λ_D  +  λ_DD × MTTR / λ_D
```

**Avec** : `λ_DU = λ_D × (1-DC)` et `λ_DD = λ_D × DC`

---

### B.3.2.2.1 — Architecture 1oo1

```
λ_D = λ_DU + λ_DD
λ_DU = λ_D × (1-DC)
λ_DD = λ_D × DC

t_CE = (λ_DU/λ_D) × (T1/2 + MRT) + (λ_DD/λ_D) × MTTR

PFD_G(1oo1) = (λ_DU + λ_DD) × t_CE
            = λ_D × t_CE
```

**Formule simplifiée (DC=0)** :
```
PFD_G(1oo1) ≈ λ_DU × T1/2
```

---

### B.3.2.2.2 — Architecture 1oo2

Temps d'indisponibilité équivalent du GROUPE :
```
t_GE = (λ_DU/λ_D) × (T1/3 + MRT) + (λ_DD/λ_D) × MTTR
```

> **NOTE** : t_GE utilise T1/3 (et non T1/2 comme t_CE)

Formule complète :
```
PFD_G(1oo2) = 2 × [(1-β_D)×λ_DD + (1-β)×λ_DU]² × t_CE × t_GE
            + β_D × λ_DD × MTTR
            + β × λ_DU × (T1/2 + MRT)
```

Décomposition :
- **Terme 1** : défaillances indépendantes doubles
- **Terme 2** : CCF détectées (β_D)
- **Terme 3** : CCF non détectées (β)

---

### B.3.2.2.3 — Architecture 2oo2

```
PFD_G(2oo2) = 2 × λ_D × t_CE
```

> Identique à deux 1oo1 en série côté sécurité.

---

### B.3.2.2.4 — Architecture 1oo2D

Paramètre additionnel :
```
λ_SD = λ_S × DC   (taux défaillances en sécurité détectées)
```

Temps d'indisponibilité modifiés :
```
t'_CE = [λ_DU × (T1/2 + MRT) + (λ_DD + λ_SD) × MTTR]
        / (λ_DU + λ_DD + λ_SD)

t'_GE = T1/3 + MRT
```

Formule :
```
PFD_G(1oo2D) = 2×(1-β)×λ_DU × [(1-β_D)×λ_DD + (1-β)×λ_DU + λ_SD] × t'_CE × t'_GE
             + 2×(1-K)×λ_DD × t'_CE
             + β_D×λ_DD×MTTR
             + β×λ_DU × (T1/2 + MRT)
```

où K = efficacité du mécanisme de comparaison/commutation de canal (défaut K=0.98)

---

### B.3.2.2.5 — Architecture 2oo3

```
PFD_G(2oo3) = 6 × [(1-β_D)×λ_DD + (1-β)×λ_DU]² × t_CE × t_GE
            + β_D × λ_DD × MTTR
            + β × λ_DU × (T1/2 + MRT)
```

Mêmes t_CE et t_GE que 1oo2.

---

### B.3.2.2.6 — Architecture 1oo3

Temps additionnel :
```
t_G2E = (λ_DU/λ_D) × (T1/4 + MRT) + (λ_DD/λ_D) × MTTR
```

Formule :
```
PFD_G(1oo3) = 6 × [(1-β_D)×λ_DD + (1-β)×λ_DU]³ × t_CE × t_GE × t_G2E
            + β_D × λ_DD × MTTR
            + β × λ_DU × (T1/2 + MRT)
```

---

### B.3.2.5 — Essai Périodique Imparfait (PTC < 1)

Avec couverture partielle PTC et période de sollicitation T2 :

```
t_CE(imperfect) = (λ_DU×PTC/λ_D) × (T1/2 + MRT)
                + (λ_DU×(1-PTC)/λ_D) × (T2/2 + MRT)
                + (λ_DD/λ_D) × MTTR

t_GE(imperfect) = (λ_DU×PTC/λ_D) × (T1/3 + MRT)
                + (λ_DU×(1-PTC)/λ_D) × (T2/3 + MRT)
                + (λ_DD/λ_D) × MTTR
```

Formule PFD 1oo2 avec essai imparfait :
```
PFD_G(1oo2, PTC<1) = 2 × [(1-β_D)×λ_DD + (1-β)×λ_DU]² × t_CE × t_GE
                   + β_D × λ_DD × MTTR
                   + β × λ_DU × PTC × (T1/2 + MRT)
                   + β × λ_DU × (1-PTC) × (T2/2 + MRT)
```

---

## B.3.3 — Formules PFH Mode Haute Demande / Continu

### B.3.3.2.1 — Architecture 1oo1

```
PFH_G(1oo1) = λ_DU
```

> Simple : le taux de défaillance dangereuse non détectée est directement la fréquence de défaillance.

### B.3.3.2.2 — Architecture 1oo2

```
PFH_G(1oo2) = 2 × [(1-β_D)×λ_DD + (1-β)×λ_DU] × (1-β)×λ_DU × t_CE
            + β × λ_DU
```

### B.3.3.2.3 — Architecture 2oo2

```
PFH_G(2oo2) = 2 × λ_DU
```

### B.3.3.2.4 — Architecture 1oo2D

```
λ_SD = λ_S × DC / 2   (λ_S ≈ λ_D par convention)

t'_CE = [λ_DU × (T1/2 + MRT) + (λ_DD + λ_SD) × MTTR]
        / (λ_DU + λ_DD + λ_SD)

PFH_G(1oo2D) = 2×(1-β)×λ_DU × [(1-β_D)×λ_DD + (1-β)×λ_DU + λ_SD] × t'_CE
             + 2×(1-K)×λ_DD
             + β × λ_DU
```

### B.3.3.2.5 — Architecture 2oo3

```
PFH_G(2oo3) = 6 × [(1-β_D)×λ_DD + (1-β)×λ_DU] × (1-β)×λ_DU × t_CE
            + β × λ_DU
```

### B.3.3.2.6 — Architecture 1oo3

```
PFH_G(1oo3) = 6 × [(1-β_D)×λ_DD + (1-β)×λ_DU]² × (1-β)×λ_DU × t_CE × t_GE
            + β × λ_DU
```

---

## B.3.3.3 — Tableaux de Référence PFH (Tableaux B.10 à B.13)

### Tableau B.10 — PFH, T1 = 1 mois (730h), MTTR = 8h

| Architecture | DC | λ_D=5E-8 β=2% | λ_D=2.5E-7 β=2% | λ_D=5E-7 β=2% |
|---|---|---|---|---|
| 1oo1 | 0% | 5.0E-8 | 2.5E-7 | 5.0E-7 |
| 1oo1 | 60% | 2.0E-8 | 1.0E-7 | 2.0E-7 |
| 1oo1 | 90% | 5.0E-9 | 2.5E-8 | 5.0E-8 |
| 1oo1 | 99% | 5.0E-10 | 2.5E-9 | 5.0E-9 |
| 1oo2 | 0% | 1.0E-9 | 5.0E-9 | 1.0E-8 |
| 1oo2 | 60% | 4.0E-10 | 2.0E-9 | 4.0E-9 |
| 1oo2 | 90% | 1.0E-10 | 5.0E-10 | 1.0E-9 |
| 1oo2 | 99% | 1.0E-11 | 5.0E-11 | 1.0E-10 |
| 2oo2 | 0% | 1.0E-7 | 5.0E-7 | 1.0E-6 |
| 2oo3 | 0% | 1.0E-9 | 5.1E-9 | 1.1E-8 |
| 2oo3 | 60% | 4.0E-10 | 2.0E-9 | 4.1E-9 |
| 2oo3 | 90% | 1.0E-10 | 5.0E-10 | 1.0E-9 |

*(Tableaux complets B.10-B.13 dans le fichier 13_VERIFICATION_TABLES.md)*

---

## B.4 — Approche Booléenne : Principes de Calcul PFD

### Formule générale d'intégration

```
PFDavg(T) = (1/T) × ∫₀ᵀ U_sf(t) dt
```

### Décomposition par coupes minimales (Poincaré)

```
P(⋃Cᵢ) = Σ P(Cⱼ) - ΣΣ P(Cⱼ∩Cᵢ) + ΣΣΣ P(Cⱼ∩Cᵢ∩Cₖ) - ...
```

### Indisponibilité instantanée U(t) — Courbe en dents de scie

Pour composant soumis à essais périodiques τ :
```
U_i(t) = λ_DU × ζ   où ζ = t modulo τ
```

**Effet du décalage des essais** (staggering) :
- Réduit la PFDavg
- Augmente la fréquence d'essai effective des CCF
- Exemple IEC : décalage de τ/2 → PFD divisé par ~1.7 (SIL 3 → SIL 4 dans l'exemple)

---

## B.5.2 — Approche Markov : Formulation Mathématique Exacte

### Équation de base de Markov

```
P_i(t+dt) = Σ_{k≠i} P_k(t) × λ_{ki} × dt + P_i(t) × (1 - Σ_{k≠i} λ_{ik} × dt)
```

### Formulation matricielle

```
dP(t)/dt = [M] × P(t)
```

Solution générale :
```
P(t) = exp(t × [M]) × P(0)
```

**Propriété Markovienne** :
```
P(t) = exp((t-t1)×[M]) × exp(t1×[M]) × P(0) = exp((t-t1)×[M]) × P(t1)
```

### Calcul PFDavg via Markov

```
U(t) = Σₖ qₖ × Pₖ(t)
```

où `qₖ = 1` si état k est indisponible, `0` sinon.

```
MCT(T) = ∫₀ᵀ P(t) dt      (vecteur des temps cumulés dans chaque état)

PFDavg(T) = (1/T) × Σₖ qₖ × MCT_k(T)
```

---

## B.5.2.1 — Modèle Markov Multiphase (Phase entre Essais)

### Phase normale (entre deux essais)

**États** : W (Working), DU (Dangerous Undetected), R (Repair)

**Matrice de Markov [M]_between :**
```
     W        DU       R
W  [-λ_DU    λ_DU     0  ]
DU [ 0        0       0  ]   ← pas de réparation entre essais
R  [ μ       0       -μ  ]
```

où `μ = 1/MRT`

### Matrice de liaison [L] au moment de l'essai

```
[P_DU(0)]   [0  0  1] [P_DU(τ)]
[P_W(0) ] = [0  1  0] [P_W(τ) ]   ≡ P_{i+1}(0) = [L] × P_i(τ)
[P_R(0) ]   [0  0  1] [P_R(τ) ]
```

Interprétation :
- DU(τ) → R(0) : défaillance détectée à l'essai → mise en réparation
- W(τ) → W(0) : composant OK → reste W
- R(τ) → R(0) : réparation non terminée → continue

### Équation de récurrence

```
P_{i+1}(0) = [L] × exp(τ × [M]) × P_i(0)
```

### Calcul de PFD(t) à tout instant

Pour t = i×τ + ζ (ζ dans [0, τ)) :
```
P(t) = exp(ζ × [M]) × P_i(0)
PFD(t) = P_DU(t) + P_R(t)
```

---

## B.5.2.1 — Modèle Markov avec Défaillances DD et DU

**États** : W, DD (Detected Dangerous), DU (Undetected), R

**Matrice [M]_between :**
```
     W          DD         DU         R
W  [-λ_DD-λ_DU  λ_DD       λ_DU       0    ]
DD [  μ_DD      -μ_DD       0          0    ]   ← réparation immédiate si DD
DU [  0          0          0          0    ]   ← attend essai
R  [  μ_DU       0          0         -μ_DU]
```

où :
- `μ_DD = 1/MTTR` (réparation directe après détection DD)
- `μ_DU = 1/MRT` (réparation après essai)

**Matrice de liaison [L] :**
```
DD(τ) → W(0)  : réparation déjà faite (μ_DD)
DU(τ) → R(0)  : détection à l'essai → début réparation
W(τ)  → W(0)  : rien
R(τ)  → R(0)  : réparation continue
```

---

## B.5.2.1 — Modèle avec Durée d'Essai π

**Phase 1** : Fonctionnement normal (durée τ)
**Phase test** : Essai en cours (durée π) — composant indisponible en Tst

**États pendant l'essai** : W, DU, Tst (Test in progress), R

```
PFD_test = P_Tst + P_R    (indisponible pendant essai)
```

**Contribution à PFDavg :**
```
PFD_avg_test ≈ π/T1    (si π << T1)
```

---

## B.5.2.1 — Modèle avec Effet de Sollicitation (γ, σ)

**γ** = probabilité de défaillance lors de la sollicitation (test)  
**σ** = probabilité que la défaillance ne soit pas détectée par l'essai (erreur humaine)

**Matrice de liaison modifiée :**
```
DU(τ) → R(0)  avec probabilité (1-σ)    : détection normale
DU(τ) → DU(0) avec probabilité σ        : non détection (erreur)
W(τ)  → W(0)  avec probabilité (1-γ)    : composant OK
W(τ)  → R(0)  avec probabilité γ        : défaillance par sollicitation
```

**Effet sur courbe en dents de scie** : à chaque essai, saut discontinu de probabilité = γ

---

## B.5.2.2 — Calcul PFH via Markov

### Cas DD (réparable immédiatement) — Modèle monophase

```
PFH = P_4(T)/T   avec état 4 absorbant = défaillance système
```

Ou via MTTF :
```
PFH ≈ 1/MTTF
```

Avec :
```
MTTF = lim_{t→∞} Σₖ aₖ × MCT_k(t)
```

où `aₖ = 1` si état k est fonctionnel, 0 sinon.

### Cas système totalement réparable (DD) — Calcul direct

Pour le diagramme de Markov de disponibilité (pas d'état absorbant) :

**Probabilités asymptotiques** P_{i,as} = lim P_i(t)

```
MUT = Σ_i (1-qᵢ) × P_{i,as} / λᵢ
MDT = Σ_i qᵢ × P_{i,as} / λᵢ

PFH = 1/(MUT + MDT) = λᵢ / Σ_i P_{i,as}
```

où `λᵢ = Σ_{j≠i} λ_{ij}`

### Cas multiphase (DU + essais périodiques)

```
PFH(T) = [Σ_{ϕ=1}^{n} Σ_{i≠f} λ_{if} × MCT_i(T_ϕ)] / Σ_{ϕ=1}^{n} T_ϕ
```

---

## B.6 — Traitement des Incertitudes

### Modèle log-normal pour λ

Paramètres : valeur médiane λ_50% et facteur d'erreur ef_α

```
λ_inf,α = λ_50% / ef_α
λ_sup,α = λ_50% × ef_α
ef_α ≈ √(λ_sup,α / λ_inf,α)
```

Si n défaillances observées sur temps T :
```
λ̂ = n/T                                    (estimateur max. vraisemblance)
λ_inf,5% = χ²_{90%,2n} / (2T)              (borne inf à 5%)
λ_sup,5% = χ²_{10%,2(n+1)} / (2T)          (borne sup à 5%)
```

### Propagation Monte Carlo

```
Algorithme :
1. Tirer λᵢ selon distribution (log-normale, uniforme, triangulaire)
2. Calculer PFDavg ou PFH avec λᵢ tirés
3. Enregistrer résultat
4. Répéter N fois (N ≥ 1000)
5. Calculer : moyenne X̄, variance σ², IC 90% = 1.64×σ/√N
```

---

## B.3.2.3 / B.3.3.3 — Résumé des Tableaux de Référence

### Tableaux PFD (mode basse demande) :

| Tableau | T1 | MTTR |
|---------|-----|------|
| B.2 | 6 mois (4 380 h) | 8 h |
| B.3 | 1 an (8 760 h) | 8 h |
| B.4 | 2 ans (17 520 h) | 8 h |
| B.5 | 10 ans (87 600 h) | 8 h |

### Tableaux PFH (mode haute demande / continu) :

| Tableau | T1 | MTTR |
|---------|-----|------|
| B.10 | 1 mois (730 h) | 8 h |
| B.11 | 3 mois (2 190 h) | 8 h |
| B.12 | 6 mois (4 380 h) | 8 h |
| B.13 | 1 an (8 760 h) | 8 h |

**Paramètres variables dans tous les tableaux :**
- λ_D : 5E-8, 2.5E-7, 5E-7, 2.5E-6, 5E-6, 2.5E-5 (h⁻¹)
- DC : 0%, 60%, 90%, 99%
- β : 2%, 10%, 20%
- β_D : 1%, 5%, 10%
- Architectures : 1oo1, 1oo2, 2oo2, 1oo2D, 2oo3, 1oo3

> **Tous les tableaux numériques complets sont dans 13_VERIFICATION_TABLES.md**

---

## Récapitulatif des Formules par Architecture

| Architecture | PFD_G (basse demande) | PFH_G (haute demande) |
|---|---|---|
| **1oo1** | λ_D × t_CE | λ_DU |
| **2oo2** | 2 × λ_D × t_CE | 2 × λ_DU |
| **1oo2** | 2[(1-β_D)λ_DD+(1-β)λ_DU]² × t_CE×t_GE + CCF | 2[(1-β_D)λ_DD+(1-β)λ_DU](1-β)λ_DU×t_CE + β×λ_DU |
| **2oo3** | 6[(1-β_D)λ_DD+(1-β)λ_DU]² × t_CE×t_GE + CCF | 6[(1-β_D)λ_DD+(1-β)λ_DU](1-β)λ_DU×t_CE + β×λ_DU |
| **1oo3** | 6[...]³ × t_CE×t_GE×t_G2E + CCF | 6[...]²(1-β)λ_DU×t_CE×t_GE + β×λ_DU |
| **1oo2D** | formule étendue avec λ_SD, K | formule étendue avec λ_SD, K |

**Terme CCF (plancher commun, identique pour 1oo2 et 2oo3) :**
```
PFD_CCF = β_D × λ_DD × MTTR + β × λ_DU × (T1/2 + MRT)
```

**Temps d'indisponibilité :**
```
t_CE  : utilise T1/2  → contribution d'un canal (1oo1, tous)
t_GE  : utilise T1/3  → contribution du groupe 1oo2, 2oo3
t_G2E : utilise T1/4  → contribution du groupe 1oo3
```
