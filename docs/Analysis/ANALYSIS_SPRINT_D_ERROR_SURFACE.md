# PRISM SIL Engine — Sprint D : Carte d'erreur IEC vs Markov TD
## Domaines de validité des formules IEC 61508-6 §B.3.3
### Version 0.5.0 — Mars 2026

---

## 1. Objectif

Quantifier, pour chaque architecture kooN, l'erreur entre la formule IEC simplifiée
et la référence exacte (Markov Time-Domain), sur la grille bidimensionnelle (λ×T1, DC).

**Résultat pratique** : remplacer le seuil empirique unique `λ×T1 > 0.1` d'IEC 61508-6 §B.1
par des seuils fondés, différenciés par architecture et DC.

---

## 2. Ce qui existe avant ce travail

| Référence | Contribution | Limite |
|---|---|---|
| IEC 61508-6:2010 §B.1 | Seuil unique λT1 < 0.1 | Empirique, non justifié, identique pour toutes architectures |
| Chebila & Innal (2015) JLPPI 34:167-176 | Analyse domaines de validité | Référence = leurs formules analytiques (sous-estimaient pour N-M≥2) |
| Omeiri et al. (2021) JESA 54(6) | Corrections analytiques IEC | Analyse ponctuelle, pas de grille systématique |

**Notre contribution** : première grille (λ×T1, DC) avec le Markov Time-Domain comme
référence exacte unique, séparant deux sources d'erreur distinctes.

---

## 3. Deux sources d'erreur identifiées et séparées

### Source A — Termes manquants IEC (Omeiri 2021)

Présente dès λ×T1 très petit, dépend uniquement de DC.

Exemple : 1oo2 DC=0.9, λ×T1=0.01 → **δ_IEC = −89.8%**

L'IEC omet le terme λ_DU × λ_DD × MTTR (séquence DU→DD pendant qu'un autre canal
est déjà en DU). Ce terme est ×8 plus grand que le terme λ_DU² × tCE pour DC=0.9.

**Correction** : formules Omeiri (pfh_1oo2_corrected, pfh_2oo3_corrected) — erreur résiduelle < 1%.

### Source B — Non-linéarité Taylor (λ×T1 croissant)

Présente même pour DC=0, dépend de l'architecture.

**Loi analytique** : δ_IEC ≈ C × (λ×T1)^p avec p = N−M

| Architecture | p = N−M | Loi asymptotique |
|---|---|---|
| 1oo1 | 0 | δ ≈ +λT1/2 |
| 1oo2 | 1 | δ ≈ +(λT1)²/2 |
| 2oo3 | 1 | δ ≈ +(λT1)²/2 |
| 1oo3 | 2 | δ ≈ +(λT1)³/6 (+ correction Bug#11) |

**Correction** : seul le Markov TD est exact pour tout λ×T1. Les formules Omeiri
corrigent Source A mais pas Source B.

---

## 4. Table des seuils de bascule (résultat principal)

### 4a. Seuil IEC brut → Markov (Source A + B combinées)

Pour DC ≥ 0.6, l'IEC standard dépasse 5% d'erreur dès λ×T1 ~ 0.001 (minimum testable).
→ **Le seuil de bascule n'existe pas** : l'IEC brute est toujours insuffisante pour DC élevé.

### 4b. Seuil Omeiri corrigé → Markov (Source B uniquement)

Erreur résiduelle après correction analytique Omeiri. Critère : |δ| > 5%.

```
        ─── Seuil λ×T1 au-delà duquel Markov est requis ───
  Arch   p=N-M  DC=0.0   DC=0.6   DC=0.9   DC=0.99   IEC §B.1 actuel
  1oo1    p=0    0.102    0.250    0.983    >5.0           0.100
  1oo2    p=1    0.051    0.126    0.496    4.213          0.100
  2oo3    p=1    0.033    0.082    0.323    2.866          0.100
```

### Lecture de la table

**1oo1** : le seuil actuel (0.1) est correct pour DC=0. Pour DC=0.9, il est ×10 trop
conservatif — le Markov est déclenché inutilement, coûtant 150ms au lieu de 0.01ms.

**2oo3 DC=0** : le seuil 0.1 est ×3 trop permissif — l'IEC/Omeiri dépasse 5% dès
λ×T1 = 0.033, mais PRISM ne bascule pas sur Markov avant 0.1.

---

## 5. Propriété remarquable : seuil ∝ DC

Pour Source B (après correction Omeiri), le seuil est croissant en DC :

```
Seuil_5pct(arch, DC) ≈ Seuil_5pct(arch, 0) / (1 − DC)^k
```

Plus DC est élevé, plus le seuil de bascule est haut — parce que les termes DD dominent
et leur comportement est linéaire (λDD × MTTR << 1 même pour grand λT1 si MTTR petit).

Conséquence : **un système avec diagnostic élevé tolère mieux l'approximation IEC**
pour la non-linéarité residuelle (Source B), une fois les termes manquants corrigés.

---

## 6. Nouveau fichier : `error_surface.py`

### Ce qu'il fait
- `compute_grid_point(λT1, DC, arch)` : calcule IEC, Omeiri et TD en un point
- `compute_error_surface(arch)` : grille complète 30×20 points
- `find_crossover_thresholds(error_limit)` : seuils par architecture et DC
- `compare_architectures(DC)` : courbes multi-architecture pour publication
- `print_error_report(result)` : rapport structuré

### Ce qu'il ne fait pas
Il ne modifie aucune formule existante. Il *utilise* les moteurs comme boîtes noires.

---

## 7. Impact sur compute_exact (prochaine étape)

Le seuil actuel dans `markov.py` :
```python
if lambda_t1 > 0.1:
    # utiliser Markov
```

Seuil adaptatif fondé (Sprint E) :
```python
THRESHOLDS_5PCT = {
    "1oo1": {0.0: 0.102, 0.6: 0.250, 0.9: 0.983},
    "1oo2": {0.0: 0.051, 0.6: 0.126, 0.9: 0.496},
    "2oo3": {0.0: 0.033, 0.6: 0.082, 0.9: 0.323},
    # interpolation DC intermédiaires
}
```

Gain : 10× moins d'appels Markov inutiles pour DC élevé, 3× plus de précision
pour 2oo3 à DC faible.

---

## 8. Ce qui est original vs ce qui est connu

| Aspect | Connu | Nouveau dans PRISM v0.5.0 |
|---|---|---|
| Que l'IEC simplifie | IEC §B.1 le dit | — |
| Seuil λT1 < 0.1 | IEC §B.1 | Justification quantitative manquait |
| Termes manquants IEC | Omeiri 2021 | — |
| Domaines de validité | Chebila & Innal 2015 | Leur référence était incorrecte pour N-M≥2 |
| **Séparation Sources A et B** | **Aucune source** | **Contribution originale** |
| **Seuils différenciés par (arch, DC)** | **Aucune source** | **Contribution originale** |
| **Propriété seuil ∝ 1/(1−DC)** | **Aucune source** | **Contribution originale** |
| **TD comme référence exacte** | **Aucune source** | **Contribution originale (Bug#11)** |

---

## 9. Sources

- IEC 61508-6:2010 Annexe B §B.3.3 — formules PFH et recommandation λT1 < 0.1
- Omeiri, Innal, Liu (2021) JESA 54(6):871-879 — corrections analytiques Source A
- Chebila & Innal (2015) JLPPI 34:167-176 — première analyse domaines de validité
- PRISM v0.5.0 Bug #11 — TD comme référence exacte, loi 2^p/(p+1)
- PRISM v0.5.0 Sprint D — `error_surface.py`, calcul numérique sur grille (β=0, MTTR=8h)

---

*Document de référence PRISM SIL Engine v0.5.0 — Sprint D*
