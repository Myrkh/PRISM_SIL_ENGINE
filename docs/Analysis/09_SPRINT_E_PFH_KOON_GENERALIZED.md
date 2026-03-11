# PRISM v0.5.1 Sprint E — PFH kooN Généralisé avec DC > 0

**Fichier** : `docs/theory/09_SPRINT_E_PFH_KOON_GENERALIZED.md`  
**Version** : PRISM v0.5.1 Sprint E  
**Date** : 2026-03-11  
**Auteurs** : PRISM Project (Myrkh/PRISM_SIL_ENGINE)

---

## 1. Problème identifié — pfh_moon était faux pour DC > 0, N > 3

### 1.1 Ancienne implémentation

La fonction `pfh_moon(p, k, n)` dans `formulas.py`, pour les architectures
non couvertes par une formule dédiée (N > 3), utilisait l'approximation
de Uberti (2024) Annexe E Eq.E.7, **valide uniquement pour DC = 0** :

```
PFH = C(n, r+1) × (r+1)! × λ_DU^(r+1) × T1^r + β×λ_DU
```

avec r = N−M = p (ordre de redondance).

Cette formule utilise **uniquement λ_DU** — elle ignore complètement λ_DD.
Pour DC = 0 (λ_DD = 0), c'est correct. Pour DC > 0, c'est une erreur grave.

### 1.2 Preuve chiffrée de l'erreur

Architecture 3oo4 (p=1, N=4), λT1 = 0.005, β = 0 :

| DC   | Ancien pfh_moon | Markov TD (référence) | Erreur    | Ratio      |
|------|-----------------|-----------------------|-----------|------------|
| 0.00 | 1.712 × 10⁻⁸   | 1.698 × 10⁻⁸          | +0.8%     | 1.008      |
| 0.30 | 8.390 × 10⁻⁹   | 1.193 × 10⁻⁸          | **−29.7%**| 0.703 ⚠   |
| 0.60 | 2.740 × 10⁻⁹   | 6.842 × 10⁻⁹          | **−60.0%**| 0.400 ⚠   |
| 0.90 | 1.712 × 10⁻¹⁰  | 1.717 × 10⁻⁹          | **−90.0%**| 0.100 ⚠   |
| 0.99 | 1.712 × 10⁻¹²  | 1.718 × 10⁻¹⁰         | **−99.0%**| 0.010 ⚠   |

Architecture 4oo5 (p=1, N=5), même conditions :

| DC   | Ancien pfh_moon | Markov TD (référence) | Erreur    |
|------|-----------------|-----------------------|-----------|
| 0.90 | 2.854 × 10⁻¹⁰  | 2.860 × 10⁻⁹          | **−90.0%**|
| 0.99 | 2.854 × 10⁻¹²  | 2.864 × 10⁻¹⁰         | **−99.0%**|

### 1.3 Diagnostic physique

Le ratio erreur = (1 − DC) = λ_DU / λ_D.

**Explication** : la formule ancienne calculait la probabilité que la
2ᵉ défaillance soit aussi une DU. Or, la 2ᵉ défaillance peut être **DD
ou DU** — son taux total est λ_D = λ_DU + λ_DD, pas λ_DU seul.

En pratique industrielle, DC = 0.9 est courant (IEC 61508-6 Table A.14).
L'erreur de −90 % signifie que le PFH réel est **×10 plus élevé** que
ce que `pfh_moon` retournait. Conséquence : une installation classifiée
SIL 3 par l'ancien calcul pouvait réellement n'atteindre que SIL 2.

---

## 2. Formule corrigée — dérivation rigoureuse pour p = 1

### 2.1 Sources primaires

| Source | Référence | Rôle |
|--------|-----------|------|
| IEC 61508-6 §B.3.3.2.2 | Eq. PFH 1oo2 | Formule avec DC, N=2 |
| IEC 61508-6 §B.3.3.2.5 | Eq. PFH 2oo3 | Formule avec DC, N=3 |
| Uberti (2024) Annexe E Eq.E.7 | DC=0, tout N | Coefficient C(N,2)×2! |
| Omeiri, Innal, Liu (2021) JESA 54(6) Eq.17 | Terme manquant, N=2 | Correction DC>0 |
| Omeiri, Innal, Liu (2021) JESA 54(6) Eq.22 | Terme manquant, N=3 | Correction DC>0 |
| **PRISM Sprint E (ce document)** | N ≥ 4, tout DC | **Extension, contribution originale** |

### 2.2 Coefficient N×(N−1) — dérivation algébrique

Pour p = N−M = 1, la défaillance dangereuse exige exactement 2 canaux
simultanément en état DU (non détecté).

**Étape 1 — Paires de canaux :**  
Parmi N canaux identiques, le nombre de paires est C(N,2) = N(N−1)/2.

**Étape 2 — Orderings :**  
Pour chaque paire (i, j), deux séquences contribuent :
- Canal i défaille en DU, puis canal j défaille en DU pendant la fenêtre d'exposition de i.
- Canal j défaille en DU, puis canal i défaille en DU pendant la fenêtre d'exposition de j.

Soit 2 orderings par paire → coefficient total = 2 × C(N,2) = N(N−1).

**Vérification — identité combinatoire :**
```
2 × C(N,2) = 2 × N(N−1)/2 = N(N−1)
```

Vérification numérique :

| N | 2×C(N,2) | N(N−1) | Identité |
|---|----------|--------|----------|
| 2 | 2        | 2      | ✓        |
| 3 | 6        | 6      | ✓        |
| 4 | 12       | 12     | ✓        |
| 5 | 20       | 20     | ✓        |
| 6 | 30       | 30     | ✓        |

**Accord avec Uberti (2024) Eq.E.7 :**  
Pour r = p = 1 : `C(N, r+1) × (r+1)! = C(N,2) × 2! = N(N−1)`.  
Le coefficient N(N−1) est donc **entièrement justifié par une source
publiée** pour le cas DC = 0.

**Accord avec IEC §B.3.3.2.2/5 :**  
- 1oo2 (N=2) : coefficient = 2 = N(N−1) ✓
- 2oo3 (N=3) : coefficient = 6 = N(N−1) ✓

### 2.3 Extension DC > 0 — remplacement T1/2 par tCE

Pour DC = 0, le temps d'exposition moyen du premier canal défaillant est
T1/2 (distribution uniforme sur [0, T1], IEC §B.3.2.2).

Pour DC > 0, le temps d'exposition dépend du type de défaillance :
- Canal en **DU** : détecté uniquement au proof-test → exposition T1/2 + MRT
- Canal en **DD** : détecté immédiatement → réparé en MTTR

Le temps d'exposition moyen pondéré (IEC §B.3.2.2, NTNU Ch.8 slide 31) :
```
tCE = (λDU / λD) × (T1/2 + MRT) + (λDD / λD) × MTTR
```

**Remplacement** : λDU × T1/2 → λD × tCE

**Justification dans les sources** : ce remplacement est explicite dans
IEC §B.3.3.2.2 (Eq. 1oo2 avec DC) et §B.3.3.2.5 (Eq. 2oo3 avec DC).

**Extension à N ≥ 4** : la structure physique est identique pour tout N
avec p = 1. L'application du même remplacement à N ≥ 4 est une extension
logique, **non présente dans les sources publiées** — c'est la contribution
originale de PRISM Sprint E. La validation numérique en constitue la preuve
(cf. §2.5).

### 2.4 Terme manquant Omeiri — correction DC > 0

IEC §B.3.3.2.2 fait l'hypothèse que si la **dernière** défaillance est DD,
l'EUC est mis en sécurité (NTNU Ch.8 slide 29). Cette hypothèse supprime
le terme de la séquence : canal en DU pendant que l'autre passe en DD.

Omeiri, Innal, Liu (2021) démontrent que ce terme est en réalité présent
et peut représenter la majorité du PFH pour DC élevé.

**Terme manquant pour N=2** (Omeiri Eq.17) :
```
Δ₂ = 2 × λDU × (T1/2 + MRT) × λDD
```

**Terme manquant pour N=3** (Omeiri Eq.22) :
```
Δ₃ = 6 × λDU × (T1/2 + MRT) × λDD
```

Le coefficient est encore N(N−1). La généralisation à tout N est :
```
Δ_N = N(N−1) × λDU × (T1/2 + MRT) × λDD
```

**Statut** : contribution originale PRISM Sprint E (validée numériquement).

### 2.5 Formule complète pfh_koon_corrected pour p = 1

```
PFH_kooN(p=1) = N(N−1) × λDU × [λD × tCE + (T1/2 + MRT) × λDD] + β × λDU

avec :
  λDU  = (1−β) × λDU_total
  λDD  = (1−β_D) × λDD_total
  λD   = λDU + λDD
  MRT  = MTTR_DU (Mean Repair Time pour λDU — Omeiri 2021 §2.2)
  tCE  = (λDU/λD) × (T1/2 + MRT) + (λDD/λD) × MTTR
```

**Vérification de coïncidence avec les formules dédiées :**

Pour N=2 (1oo2) : N(N−1) = 2  
→ `pfh_koon_corrected(M=1, N=2)` = `pfh_1oo2_corrected()` ✓

Pour N=3 (2oo3) : N(N−1) = 6  
→ `pfh_koon_corrected(M=2, N=3)` = `pfh_2oo3_corrected()` ✓

### 2.6 Validation numérique sur grille (λT1, DC, N)

Critère : erreur < 2 % vs Markov TD pour λT1 ≤ 0.01, tout DC, N = 2..5.

| Arch | DC   | λT1   | pfh_koon_c | TD exact   | δ%      |
|------|------|-------|------------|------------|---------|
| 3oo4 | 0.00 | 0.005 | 1.716×10⁻⁸ | 1.698×10⁻⁸ | +1.0%   |
| 3oo4 | 0.60 | 0.005 | 6.869×10⁻⁹ | 6.842×10⁻⁹ | +0.4%   |
| 3oo4 | 0.90 | 0.005 | 1.718×10⁻⁹ | 1.717×10⁻⁹ | +0.1%   |
| 4oo5 | 0.00 | 0.005 | 2.859×10⁻⁸ | 2.824×10⁻⁸ | +1.3%   |
| 4oo5 | 0.60 | 0.005 | 1.145×10⁻⁸ | 1.139×10⁻⁸ | +0.5%   |
| 4oo5 | 0.90 | 0.005 | 2.864×10⁻⁹ | 2.860×10⁻⁹ | +0.1%   |

**Grille complète** : max |δ| < 2 % pour λT1 ≤ 0.01, DC ∈ [0, 0.99], N ∈ [2,5].

---

## 3. Cas p ≥ 2 — TD systématique

Pour p = N−M ≥ 2 (ex : 1oo3, 2oo4, 1oo4, 1oo5...), pas de formule analytique
fermée précise n'est connue dans la littérature pour DC > 0.

La fonction `pfh_koon_corrected` route automatiquement vers `compute_exact`
(Markov Time-Domain), qui est exact pour tout N, M, DC, λT1.

La loi `TD/SS = 2^p/(p+1)` (PRISM v0.5.0 Bug #11) quantifie l'erreur de la
méthode steady-state — elle n'est PAS utilisée comme approximation ici.

---

## 4. Loi empirique des seuils de validité (p = 1)

### 4.1 Seuils mesurés

| N | Seuil DC=0 | 0.102/N | N × seuil |
|---|------------|---------|-----------|
| 2 | 0.0505     | 0.0510  | 0.1010    |
| 3 | 0.0333     | 0.0340  | 0.0999    |
| 4 | 0.0252     | 0.0255  | 0.1008    |
| 5 | 0.0198     | 0.0204  | 0.0990    |
| 6 | 0.0166     | 0.0170  | 0.0996    |

Produit N × seuil = 0.1001 ± 0.0007 (< 1 %).

### 4.2 Statut de la loi

**La loi seuil(N, p=1, DC=0) ≈ 0.102/N est empirique, pas analytique.**

Elle exprime une observation numérique : le produit N × seuil est constant.
Explication qualitative : Source B pour p=1 est une erreur de troncature
Taylor au 2ᵉ ordre en (λT1). Son coefficient relatif croît linéairement
avec N (plus de canaux = plus de termes croisés). Le seuil (λT1 pour lequel
Source B atteint 5 %) décroît donc en 1/N.

Cette loi n'a pas de dérivation algébrique publiée connue — elle est produite
par PRISM Sprint E et déclarée comme telle.

**Utilisation** : seuil conservatif dans `adaptive_iec_threshold(arch, DC)`
pour les architectures non tabulées (précision ±2 %).

---

## 5. Résumé des contributions

| Composante | Source | Statut |
|------------|--------|--------|
| Coefficient N(N−1) pour DC=0 | Uberti (2024) E.7 + IEC §B.3.3.2 | Dérivé de sources |
| Remplacement λDU²×T1 → λDU×λD×tCE | IEC §B.3.3.2.2/5 (N=2,3) | Dérivé de sources |
| Extension tCE à N ≥ 4 | **PRISM Sprint E** | **Contribution originale** |
| Terme manquant N(N−1)×λDU×(T1/2+MRT)×λDD | Omeiri (2021) Eq.17/22 (N=2,3) | Dérivé de sources |
| Généralisation terme Omeiri à N ≥ 4 | **PRISM Sprint E** | **Contribution originale** |
| Loi seuil ≈ 0.102/N | **PRISM Sprint E** | **Observation empirique** |

---

## 6. Références

- **IEC 61508-6:2010** Annexe B §B.3.3.2 — Formules PFH kooN (N=1,2,3)
- **Uberti (2024)** Annexe E Eq.E.7 — Approximation PFH kooN générique DC=0
- **Omeiri, Innal, Liu (2021)** JESA Vol.54 No.6 pp.871-879 — Corrections PFH
  Eq.17 (1oo2), Eq.22 (2oo3), §2.2 (MRT ≠ MTTR)
- **NTNU RAMS Group Ch.8** — tCE, tGE, slide 31 (Uberti formulation)
- **PRISM v0.5.0 Bug #11** — Loi TD/SS = 2^p/(p+1) pour p ≥ 2
- **PRISM v0.5.0 Sprint D** — Domaines de validité IEC (seuils par arch/DC)
- **PRISM v0.5.0 Sprint E** — Ce document

---

## 7. Tests de validation (Groupe I, test_verification.py)

| Test | Description | Seuil | Résultat |
|------|-------------|-------|---------|
| T30 | pfh_koon_corrected 3oo4 DC=0.9 vs TD | δ < 5% | ✅ +0.1% |
| T31 | pfh_koon_corrected p≥2 retourne TD exact | δ_TD < 1%, δ_SS > 10% | ✅ |
| T32 | pfh_moon corrigé : plus de résultat ×10 faux | δ < 5%, no warning DC=0 | ✅ |
| T33 | Loi seuil ≈ 0.102/N, précision ±10% | ratio ∈ [0.9, 1.1] | ✅ |
| T34 | Loi générale p=1 : δ < 2% pour λT1 ≤ 0.01 | N=2..5, DC∈[0,0.99] | ✅ |
