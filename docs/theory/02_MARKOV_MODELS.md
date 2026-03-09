# 12 — Modèles Markov Exacts — Espaces d'États par Architecture

> Source primaire : **IEC 61508-6:2010 Annexe B §B.5.2**  
> Sources académiques : Lundteigen & Rausand (NTNU), PDS Method Handbook (SINTEF)  
> Ce document définit les matrices Q exactes pour chaque architecture.

---

## Principe Fondamental : Markov Multiphase

Le calcul exact repose sur l'alternance de deux types de phases :

```
┌─────────────────────────────────────────────────────────────────┐
│  PHASE NORMALE          │  PHASE ESSAI     │  PHASE NORMALE    │
│  (durée τ = T1)         │  (durée π)        │  (durée τ = T1)   │
│                          │                   │                   │
│  Matrice [M]_normal     │  Matrice [M]_test │  Matrice [M]_norm │
│                          │                   │                   │
│  P_{i+1}(0) = [L]×P_i(τ) ──────────────────────────────────►   │
└─────────────────────────────────────────────────────────────────┘
```

**Résolution numérique :**
```python
# scipy.linalg.expm pour exp(τ × [M])
# scipy.integrate.solve_ivp pour résolution ODE raide
# numpy.trapz pour intégration PFDavg
```

---

## Modèle 1 — Architecture 1oo1 (Composant Simple)

### Espace d'états

```
État  | Signification          | Disponible ?
------|------------------------|-------------
W     | Working (fonctionnel)  | OUI
DU    | Dangerous Undetected   | NON (latent)
DD    | Dangerous Detected     | NON (en attente)
R     | Repair in progress     | NON
```

### Phase normale (entre essais) — Matrice Q_normal

```
     W           DU          DD           R
W  [-λ_DU-λ_DD  λ_DU        λ_DD         0       ]
DU [  0          0           0            0       ]  ← attend essai
DD [  μ_DD       0          -μ_DD         0       ]  ← réparation immédiate DD
R  [  μ_R        0           0           -μ_R     ]  ← réparation après essai DU
```

où :
- `λ_DU = λ_D × (1-DC)` — taux DU
- `λ_DD = λ_D × DC` — taux DD
- `μ_DD = 1/MTTR` — taux réparation DD
- `μ_R = 1/MRT` — taux réparation après essai

### Matrice de liaison [L] au moment de l'essai (sans durée d'essai)

```
     W(0)  DU(0)  DD(0)  R(0)
W(τ)  [ 1    0      0      0  ]    ← W reste W
DU(τ) [ 0    σ      0      1-σ]    ← DU → R (détection) ou DU (σ = taux non-détection)
DD(τ) [ 1    0      0      0  ]    ← DD réparé → W  (si MTTR très court vs T1)
R(τ)  [ 0    0      0      1  ]    ← R continue si non terminée
```

**Cas simplifié** (essai parfait σ=0, MTTR << T1) :
```
[L] = 
     W(0)  DU(0)  R(0)
W(τ)  [ 1    0      0  ]
DU(τ) [ 0    0      1  ]    ← DU → R
R(τ)  [ 0    0      1  ]    ← R continue
```

### Avec durée d'essai π — Phase test

Pendant l'essai, composant indisponible → état Tst (Test in progress)

**Matrice de liaison pré-test [L_pre] :**
```
W  → W_tst  : composant déconnecté pour test
DU → DU_tst : composant en test (toujours défaillant)
R  → R       : réparation continue
```

**Matrice de liaison post-test [L_post] :**
```
W_tst  → W     : essai passé
DU_tst → R     : défaillance détectée, mise en réparation
R      → R     : continue
```

---

## Modèle 2 — Architecture 1oo2

### Espace d'états complet (sans CCF)

```
État  | Canal A | Canal B | Système dispo ? | Signification
------|---------|---------|-----------------|------------------
  1   |   W     |   W     |      OUI        | Tous fonctionnels
  2   |   DU    |   W     |      OUI        | A défaillant, B OK
  3   |   W     |   DU    |      OUI        | B défaillant, A OK
  4   |   DU    |   DU    |      NON        | Double défaillance DU
  5   |   DD    |   W     |      OUI        | A défaillant DD, réparation
  6   |   W     |   DD    |      OUI        | B défaillant DD, réparation
  7   |   DU    |   DD    |      NON        | A DU + B DD
  8   |   DD    |   DU    |      NON        | A DD + B DU
  9   |   R     |   W     |      OUI        | A en réparation, B OK
  10  |   W     |   R     |      OUI        | B en réparation, A OK
  11  |   R     |   DU    |      NON        | A en réparation + B DU
  12  |   DU    |   R     |      NON        | A DU + B en réparation
```

**NOTE** : Les états 4, 7, 8, 11, 12 sont INDISPONIBLES (défaillance système).

### Réduction pour CCF

Avec CCF (β-factor), états supplémentaires :
```
CCF_DU : défaillance commune DU (λ_CCF = β × λ_DU_indep)
CCF_R  : réparation commune après CCF
```

### Matrice Q pour 1oo2 (simplifiée, 4 états principaux)

Pour le moteur, utiliser les 4 états principaux avec taux effectifs :

```
λ_DU_indep = (1-β) × λ_DU    ← taux DU indépendant par canal
λ_DD_indep = (1-β_D) × λ_DD  ← taux DD indépendant par canal
λ_CCF_DU = β × λ_DU           ← taux CCF dangereuse non détectée
λ_CCF_DD = β_D × λ_DD         ← taux CCF dangereuse détectée
```

**Matrice Q_normal (4 états : OK, 1-fail, 2-fail-DU, CCF):**

```
         OK         1-fail-DU    2-fail-DU    CCF-DU
OK     [-2λ_DU_i    2λ_DU_i       0           λ_CCF]
       [-2λ_DD_i    ·             ·            λ_CCFd]
1DU    [ 0          -(λ_DU_i)     λ_DU_i       0    ]
2DU    [ 0           0             0            0    ]   ← état absorbant (essai)
CCF    [ 0           0             0            0    ]   ← état absorbant
```

**Formulation complète (cf. IEC B.5.2, Figure B.30):**

```
Pendant la phase normale, les transitions possibles sont :
- OK → 1DU_A : λ_DU_i (canal A tombe en DU)
- OK → 1DU_B : λ_DU_i (canal B tombe en DU)
- OK → CCF_DU: λ_CCF_DU (CCF DU)
- OK → 1DD_A : λ_DD_i (canal A tombe en DD, réparation immédiate)
- 1DU → 2DU  : λ_DU_i (deuxième canal tombe en DU → indisponibilité)
- 1DU → CCF  : λ_CCF_DU (CCF pendant qu'un canal est déjà DU)
- 1DD → W    : μ_DD = 1/MTTR (réparation DD terminée)
```

---

## Modèle 3 — Architecture 2oo3

### Espace d'états simplifié

```
État              | Canaux DU | Système dispo ? | Vote MooN
------------------|-----------|-----------------|----------
OK (3W)           |     0     |      OUI        | 2oo3 OK
1DU (2W+1DU)      |     1     |      OUI        | vote 2oo2 sur 2 restants
2DU (1W+2DU)      |     2     |      NON        | vote ne peut pas passer
3DU (3DU)         |     3     |      NON        | tout défaillant
CCF               |    tous   |      NON        | CCF
```

**Transitions (en mode basse demande, DU uniquement) :**
```
OK   → 1DU : 3 × λ_DU_i      (l'un des 3 canaux tombe)
1DU  → 2DU : 2 × λ_DU_i      (l'un des 2 restants tombe)
2DU  → 3DU : 1 × λ_DU_i      (le dernier tombe)
OK   → CCF : λ_CCF_DU         (CCF)
```

**Au moment de l'essai (matrice [L]) :**
```
2DU → 2R  (les 2 canaux DU détectés → réparation)
1DU → 1R  (le canal DU détecté → réparation)
```

**Changement de vote après 1ère défaillance DD détectée :**
Selon IEC B.5.2 Figure B.30 : passage de 2oo3 → 1oo2 (plus sûr après 1 défaillance DD)

---

## Modèle 4 — Architecture MooN générique

### Formule générale pour k-out-of-n (kooN)

Pour un système kooN avec n canaux identiques :

**Nombre d'états** = n+1 états DU + états R + états CCF

**Taux de transition depuis état i-DU (i canaux en DU) :**
```
λ_transition(i → i+1) = (n-i) × λ_DU_i    ← prochain canal tombe
```

**Condition de défaillance système (mode basse demande) :**
```
Système indisponible si DU_count ≥ (n - k + 1)
```

Pour 1oo2 : indisponible si ≥ 2 canaux DU  
Pour 2oo3 : indisponible si ≥ 2 canaux DU  
Pour 1oo3 : indisponible si ≥ 3 canaux DU  
Pour 2oo2 : indisponible si ≥ 1 canal DU  

---

## Matrice Q Complète — Exemple 1oo1 avec DD et DU

```python
import numpy as np

def build_Q_1oo1(lambda_DU, lambda_DD, mu_DD, mu_R):
    """
    États : [W, DU, DD, R]
    Indices:  0   1   2   3
    
    W  → DU : λ_DU (défaillance non détectée)
    W  → DD : λ_DD (défaillance détectée)
    DD → W  : μ_DD = 1/MTTR (réparation immédiate)
    R  → W  : μ_R = 1/MRT (fin réparation post-essai)
    DU → R  : uniquement via matrice de liaison L à l'essai
    """
    Q = np.zeros((4, 4))
    
    # Ligne W (état 0)
    Q[0, 1] = lambda_DU   # W → DU
    Q[0, 2] = lambda_DD   # W → DD
    Q[0, 0] = -(lambda_DU + lambda_DD)
    
    # Ligne DU (état 1) : pas de sortie entre essais
    Q[1, 1] = 0
    
    # Ligne DD (état 2)
    Q[2, 0] = mu_DD        # DD → W (réparation)
    Q[2, 2] = -mu_DD
    
    # Ligne R (état 3)
    Q[3, 0] = mu_R         # R → W (fin réparation)
    Q[3, 3] = -mu_R
    
    return Q

def build_L_1oo1(sigma=0.0, gamma=0.0):
    """
    Matrice de liaison à l'essai.
    sigma = prob. non-détection DU à l'essai
    gamma = prob. défaillance par sollicitation
    
    Mapping : [W, DU, DD, R] → [W, DU, DD, R]
    """
    L = np.zeros((4, 4))
    
    # W(τ) → W(0) avec prob (1-γ), W(0) → R(0) avec prob γ
    L[0, 0] = 1.0 - gamma   # W → W
    L[3, 0] = gamma           # W → R (défaillance par sollicitation)
    
    # DU(τ) → R(0) avec prob (1-σ), DU(0) avec prob σ
    L[1, 1] = sigma           # DU → DU (non détection)
    L[3, 1] = 1.0 - sigma     # DU → R (détection)
    
    # DD(τ) → W(0) : déjà réparé (μ_DD agit pendant la phase)
    L[0, 2] = 1.0             # DD → W (essai = vérification)
    
    # R(τ) → R(0) si réparation non terminée, sinon R(τ) → W(0)
    # Simplification : MRT << T1, donc R → W
    L[0, 3] = 1.0             # R → W (réparation terminée)
    
    return L
```

---

## Résolution Numérique Complète

```python
import numpy as np
from scipy.linalg import expm
from scipy.integrate import solve_ivp

class MarkovSolver:
    """
    Solveur Markov multiphase pour un composant SIF.
    """
    
    def __init__(self, Q: np.ndarray, L: np.ndarray, 
                 unavailable_states: list, T1: float, n_cycles: int = 10):
        self.Q = Q           # Matrice de transition
        self.L = L           # Matrice de liaison (essai)
        self.unavail = unavailable_states
        self.T1 = T1
        self.n_cycles = n_cycles
        self.n_states = Q.shape[0]
    
    def solve_one_cycle(self, P0: np.ndarray) -> tuple:
        """
        Résout un cycle T1 et retourne (P_final, cumulative_unavail_time).
        """
        # Résolution ODE
        def ode(t, P):
            return self.Q.T @ P
        
        sol = solve_ivp(
            ode, [0, self.T1], P0,
            method='Radau',     # Stable pour systèmes raides
            dense_output=True,
            rtol=1e-10, atol=1e-12
        )
        
        # Calcul du temps cumulé indisponible
        t_eval = np.linspace(0, self.T1, 1000)
        P_t = sol.sol(t_eval)  # (n_states, n_t)
        
        unavail_t = sum(P_t[i, :] for i in self.unavail)
        MCT_unavail = np.trapz(unavail_t, t_eval)
        
        P_end = sol.sol(self.T1)
        
        return P_end, MCT_unavail, t_eval, unavail_t
    
    def compute_pfdavg(self, P0: np.ndarray = None) -> dict:
        """
        Calcule PFDavg sur n_cycles cycles.
        Retourne PFDavg, PFD(t), et les probabilités d'état à chaque instant.
        """
        if P0 is None:
            P0 = np.zeros(self.n_states)
            P0[0] = 1.0  # Commence en état W
        
        all_unavail = []
        all_t = []
        total_MCT = 0.0
        total_T = 0.0
        
        P_current = P0.copy()
        
        for cycle in range(self.n_cycles):
            t_offset = cycle * self.T1
            P_end, mct, t_local, unavail_local = self.solve_one_cycle(P_current)
            
            all_t.extend(t_local + t_offset)
            all_unavail.extend(unavail_local)
            total_MCT += mct
            total_T += self.T1
            
            # Application matrice de liaison (essai)
            P_current = self.L @ P_end
            
            # Normalisation (stabilité numérique)
            P_current = np.abs(P_current)
            P_current /= P_current.sum()
        
        pfdavg = total_MCT / total_T
        
        return {
            'pfdavg': pfdavg,
            'pfd_curve': (np.array(all_t), np.array(all_unavail)),
            'rrf': 1.0 / pfdavg if pfdavg > 0 else float('inf')
        }
    
    def compute_pfh(self, P0: np.ndarray = None) -> float:
        """
        Calcule PFH via MTTF (état absorbant requis).
        """
        if P0 is None:
            P0 = np.zeros(self.n_states)
            P0[0] = 1.0
        
        # Intégrer jusqu'à convergence
        T_max = 10 * self.T1 * self.n_cycles
        
        def ode(t, P):
            return self.Q.T @ P
        
        sol = solve_ivp(ode, [0, T_max], P0, method='Radau',
                       rtol=1e-10, atol=1e-12)
        
        # MCT dans états fonctionnels
        t_eval = sol.t
        P_t = sol.y
        
        functioning_states = [i for i in range(self.n_states) 
                              if i not in self.unavail]
        
        mct_up = sum(np.trapz(P_t[i, :], t_eval) for i in functioning_states)
        mct_down = sum(np.trapz(P_t[i, :], t_eval) for i in self.unavail)
        
        mttf = mct_up  # Approx: MTTF ≈ temps total en état UP
        return 1.0 / mttf if mttf > 0 else float('inf')
```

---

## Modèle Markov Exact 1oo2 avec CCF

```python
def build_system_1oo2_markov(lambda_DU, lambda_DD, mu_DD, mu_R, beta, beta_D):
    """
    Espace d'états pour 1oo2 avec CCF :
    
    États :
    0: (W,W)          - Les deux fonctionnels
    1: (DU,W)         - Canal A en DU, B OK
    2: (W,DU)         - Canal A OK, B en DU
    3: (DU,DU)        - Défaillance double DU → INDISPONIBLE
    4: (DD,W)         - Canal A en DD (réparation), B OK
    5: (W,DD)         - Canal A OK, B en DD
    6: (DD,DU)        - A en réparation, B en DU → INDISPONIBLE
    7: (DU,DD)        - A en DU, B en réparation → INDISPONIBLE
    8: (R,W)          - A en réparation post-essai, B OK
    9: (W,R)          - A OK, B en réparation post-essai
    10: (CCF_DU)      - CCF DU → INDISPONIBLE
    11: (CCF_DD)      - CCF DD détectée → réparation
    """
    
    lDU = (1 - beta) * lambda_DU     # DU indépendant
    lDD = (1 - beta_D) * lambda_DD   # DD indépendant
    lCCF_DU = beta * lambda_DU       # CCF DU
    lCCF_DD = beta_D * lambda_DD     # CCF DD
    muDD = mu_DD
    muR = mu_R
    
    n = 12
    Q = np.zeros((n, n))
    
    # État 0 (W,W)
    Q[0, 1] = lDU       # → (DU,W)
    Q[0, 2] = lDU       # → (W,DU)
    Q[0, 4] = lDD       # → (DD,W)
    Q[0, 5] = lDD       # → (W,DD)
    Q[0, 10] = lCCF_DU  # → CCF_DU
    Q[0, 11] = lCCF_DD  # → CCF_DD
    Q[0, 0] = -(2*lDU + 2*lDD + lCCF_DU + lCCF_DD)
    
    # État 1 (DU,W)
    Q[1, 3] = lDU       # → (DU,DU) : INDISPO
    Q[1, 6] = lDD       # → (DD,DU) : INDISPO
    Q[1, 10] = lCCF_DU  # → CCF
    Q[1, 1] = -(lDU + lDD + lCCF_DU)
    
    # État 2 (W,DU) — symétrique à 1
    Q[2, 3] = lDU
    Q[2, 7] = lDD
    Q[2, 10] = lCCF_DU
    Q[2, 2] = -(lDU + lDD + lCCF_DU)
    
    # État 3 (DU,DU) — INDISPONIBLE, attend essai
    Q[3, 3] = 0
    
    # État 4 (DD,W) — A en réparation immédiate
    Q[4, 0] = muDD      # → (W,W) : A réparé
    Q[4, 7] = lDU       # → (DU,DD) : B tombe en DU
    Q[4, 10] = lCCF_DU
    Q[4, 4] = -(muDD + lDU + lCCF_DU)
    
    # État 5 (W,DD) — symétrique à 4
    Q[5, 0] = muDD
    Q[5, 6] = lDU
    Q[5, 10] = lCCF_DU
    Q[5, 5] = -(muDD + lDU + lCCF_DU)
    
    # États 6, 7 (DD,DU) et (DU,DD) — INDISPONIBLE
    # Réparation DD amène à état DU seul, puis essai
    Q[6, 2] = muDD      # DD réparé → (W,DU)
    Q[6, 6] = -muDD
    
    Q[7, 1] = muDD      # DD réparé → (DU,W)
    Q[7, 7] = -muDD
    
    # États R (8,9) — post essai
    Q[8, 0] = muR       # R → (W,W)
    Q[8, 8] = -muR
    
    Q[9, 0] = muR
    Q[9, 9] = -muR
    
    # CCF_DU (état 10) — attend essai
    Q[10, 10] = 0
    
    # CCF_DD (état 11) — réparation
    Q[11, 0] = muDD
    Q[11, 11] = -muDD
    
    unavailable = [3, 6, 7, 10]  # états indisponibles
    
    return Q, unavailable

def build_L_1oo2(sigma=0.0):
    """
    Matrice de liaison à l'essai pour 1oo2.
    À l'essai : DU détecté → R, CCF_DU détectée → réparation.
    """
    n = 12
    L = np.eye(n)
    
    # État 3 (DU,DU) → (R,R) ou → R combinée
    # Simplification : (DU,DU) → (R,W) + (W,R) → réparation séquentielle
    L[3, 3] = 0
    L[8, 3] = 0.5    # A entre en réparation
    L[9, 3] = 0.5    # B entre en réparation
    
    # État 1 (DU,W) → (R,W)
    L[1, 1] = sigma        # non-détection
    L[8, 1] += (1-sigma)   # détection → R
    # Correction : L doit être colonne-stochastique
    
    # État 2 (W,DU) → (W,R)
    L[2, 2] = sigma
    L[9, 2] += (1-sigma)
    
    # État 10 (CCF_DU) → réparation
    L[10, 10] = 0
    L[0, 10] = 1.0    # CCF réparée → OK (simplification)
    
    return L
```

---

## Modèle 5 — Markov pour PFH (Mode Haute Demande)

Pour le calcul PFH, utiliser un **modèle de fiabilité avec état absorbant** :

```python
def build_Q_1oo2_pfh(lambda_DU, lambda_DD, mu_DD, beta, beta_D):
    """
    Modèle PFH pour 1oo2, mode continu.
    État absorbant = défaillance système (pas de réparation système).
    """
    lDU_i = (1-beta) * lambda_DU
    lDD_i = (1-beta_D) * lambda_DD
    lCCF = beta * lambda_DU
    
    # États simplifiés :
    # 0: (W,W)     — fonctionnel
    # 1: (DU,W)    — 1 canal DU (système encore OK)
    # 2: (DD,W)    — 1 canal DD (réparé rapidement)
    # 3: FAILED    — absorbant (double DU ou CCF)
    
    Q = np.zeros((4, 4))
    
    # (W,W)
    Q[0, 1] = 2 * lDU_i    # → 1 canal DU
    Q[0, 2] = 2 * lDD_i    # → 1 canal DD
    Q[0, 3] = lCCF          # → CCF → défaillance
    Q[0, 0] = -(2*lDU_i + 2*lDD_i + lCCF)
    
    # (1DU, W)
    Q[1, 3] = lDU_i + lCCF  # 2ème DU ou CCF → défaillance
    Q[1, 2] = lDD_i          # autre canal → DD
    Q[1, 1] = -(lDU_i + lDD_i + lCCF)
    
    # (DD, W) — réparation rapide
    Q[2, 0] = mu_DD           # → (W,W) après réparation
    Q[2, 1] = lDU_i            # → (DU,DU) approximé
    Q[2, 3] = lCCF
    Q[2, 2] = -(mu_dd + lDU_i + lCCF)
    
    # FAILED — absorbant
    Q[3, 3] = 0
    
    return Q

def compute_pfh_from_Q(Q, T_mission=8760*10):
    """
    Calcule PFH = F(T)/T où F(T) = probabilité dans état absorbant.
    """
    P0 = np.array([1.0, 0.0, 0.0, 0.0])
    
    def ode(t, P):
        return Q.T @ P
    
    sol = solve_ivp(ode, [0, T_mission], P0, method='Radau',
                   rtol=1e-10, atol=1e-12)
    
    P_failed = sol.y[3, -1]  # Probabilité état absorbant en T
    pfh = P_failed / T_mission
    
    # Vérification : PFH ≈ 1/MTTF
    mttf = np.trapz(1 - sol.y[3, :], sol.t)
    pfh_check = 1.0 / mttf if mttf > 0 else float('inf')
    
    return pfh, pfh_check
```

---

## Validation Numérique : Convergence Markov → Formule IEC

Pour valider le moteur Markov, vérifier la convergence vers les formules IEC quand λ×T1 << 1 :

```python
def validate_markov_vs_iec(architecture='1oo1', 
                            lambda_D=5e-7, DC=0.9, T1=8760,
                            MTTR=8, beta=0.02, beta_D=0.01):
    """
    Compare résultat Markov exact vs formule IEC simplifiée.
    L'écart doit être < 5% si λ×T1 < 0.1.
    """
    lambda_DU = lambda_D * (1 - DC)
    lambda_DD = lambda_D * DC
    mu_DD = 1.0 / MTTR
    mu_R = 1.0 / (T1 / 2)  # MRT ≈ T1/2 approximation
    
    # Calcul IEC
    t_CE = (lambda_DU/lambda_D) * (T1/2 + MTTR) + (lambda_DD/lambda_D) * MTTR
    pfd_iec = lambda_D * t_CE  # 1oo1
    
    # Calcul Markov
    Q = build_Q_1oo1(lambda_DU, lambda_DD, mu_DD, mu_R)
    L = build_L_1oo1()
    solver = MarkovSolver(Q, L, unavailable_states=[1,2,3], 
                          T1=T1, n_cycles=20)
    result = solver.compute_pfdavg()
    pfd_markov = result['pfdavg']
    
    ecart = abs(pfd_markov - pfd_iec) / pfd_iec * 100
    
    print(f"λ_D={lambda_D:.2e}, T1={T1}h, λ×T1={lambda_D*T1:.4f}")
    print(f"IEC approx  : PFDavg = {pfd_iec:.4e}")
    print(f"Markov exact: PFDavg = {pfd_markov:.4e}")
    print(f"Écart       : {ecart:.2f}%")
    
    return pfd_iec, pfd_markov, ecart
```

---

## Synthèse des Modèles par Architecture

| Architecture | N états (minimal) | États indispo | Modèle CCF | Complexité |
|---|---|---|---|---|
| 1oo1 | 4 (W, DU, DD, R) | DU, DD, R | + état CCF | Simple |
| 1oo2 | 12 | 4 | β inclus | Moyen |
| 2oo2 | 4 (série) | DU, DD | — | Simple |
| 2oo3 | 15+ | 6 | β inclus | Complexe |
| 1oo2D | 14 | 5 | β inclus + λ_SD | Complexe |
| 1oo3 | 20+ | 8 | β inclus | Très complexe |
| kooN générique | O(2ⁿ) | dépend k,n | β inclus | Exponentiel |

**Stratégie implémentation :**
- 1oo1, 2oo2 : modèle complet (4 états)
- 1oo2 : modèle 12 états
- 2oo3 : modèle 15 états simplifié ou formule semi-analytique
- kooN > 2oo3 : Monte Carlo ou décomposition
