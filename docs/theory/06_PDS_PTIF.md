# 16 — Méthode PDS : PTIF, CSU et Extensions

## Références normatives
- IEC 61508-6:2010, Annexe D, Note 7 (référence [25])
- Hokstad & Corneliussen, *Reliability Engineering and System Safety*, vol. 83, n°1, 2004
- SINTEF PDS Method Handbook (www.sintef.no/pds)

---

## Vue d'ensemble : PDS vs IEC 61508

La méthode PDS (Process-oriented Dependability method for Safety instrumented systems)
est développée par SINTEF (Norvège) et utilisée dans le secteur pétrolier et gazier.

### Différences clés PDS vs IEC 61508

| Concept | IEC 61508 | PDS |
|---|---|---|
| Métrique principale | PFD_avg | PFD_avg + PTIF |
| Défaillances ignorées | — | Test-Independent Failures |
| Disponibilité totale | PFD seul | CSU = PFD + PTIF |
| CCF | Facteur β | Facteur β + modélisation séparée |
| Proof test | Idéal (couvrance 1) | Réel (couvrance partielle) |

---

## PTIF — Probability of Test-Independent Failure

### Définition

Le PTIF est la probabilité que le SIS soit en état de défaillance **indépendamment
de l'essai périodique**. Il regroupe les défaillances qui ne peuvent pas être révélées
par un proof test, même complet :

```
PTIF = P(SIF défaillant | essai périodique parfait passé)
```

### Sources des défaillances test-indépendantes

1. **Défaillances systématiques** : erreurs de spécification, de conception ou de
   configuration qui font échouer le SIS dans des conditions spécifiques non testées.

2. **Défaillances latentes à durée infinie** : pannes physiques dont la durée dépasse T1
   sans être détectées (ex : corrosion lente sur capteur pressostatique dans milieu H₂S).

3. **Défaillances CCF non testées** : certaines causes communes (chocs sismiques,
   contamination chimique) peuvent affecter simultanément tous les canaux sans être
   révélées par les procédures d'essai standards.

4. **Défaillances de mode de demande** : le SIS fonctionne à l'essai mais échoue lors
   de la demande réelle (ex : vanne coincée à hautes températures, non testée à cette T°).

### Modèle PTIF

```python
class PTIFModel:
    """
    Modèle PTIF selon la méthode PDS de SINTEF.
    
    Le PTIF est exprimé comme fraction fixe du taux de défaillance total,
    ou comme probabilité absolue par demande.
    """
    
    def __init__(
        self,
        lambda_sys: float,          # taux défaillance total du système [1/h]
        ptif_fraction: float = 0.1, # fraction systématique / test-indép. (typique 5-15%)
        cov_proof_test: float = 1.0 # couverture proof test (1.0 = parfait)
    ):
        self.lambda_sys = lambda_sys
        self.ptif_fraction = ptif_fraction
        self.cov_proof_test = cov_proof_test
    
    @property
    def ptif(self) -> float:
        """
        PTIF = fraction des défaillances non révélables par proof test.
        
        Pour PDS : PTIF = λ_sys × ptif_fraction × T_ref
        où T_ref est l'horizon de référence (généralement T1).
        
        Note : dans la méthode PDS stricte, PTIF est une constante estimée
        séparément des calculs de fiabilité, pas déduite de λ.
        """
        return self.lambda_sys * self.ptif_fraction
    
    def ptif_absolute(self, T1: float) -> float:
        """PTIF comme probabilité sur un intervalle T1."""
        return self.ptif * T1
    
    @staticmethod
    def estimate_ptif_from_failure_analysis(
        n_revealed: int,        # défaillances révélées par essais (historique)
        n_total_estimated: int, # total estimé (incluant latents)
        T_observation: float    # période d'observation [h]
    ) -> float:
        """
        Estimation empirique du PTIF depuis le retour d'expérience.
        
        PTIF_rate = (n_total - n_revealed) / (n_total × T_observation)
        """
        if n_total_estimated == 0:
            return 0.0
        fraction = (n_total_estimated - n_revealed) / n_total_estimated
        return fraction / T_observation
```

---

## CSU — Critical Safety Unavailability

### Définition

Le CSU (ou CISU : Critical Instrumented Safety Unavailability) est la métrique
de disponibilité **complète** du SIS selon PDS :

```
CSU = PFD_avg + PTIF_avg
```

où :
- `PFD_avg` = probabilité de défaillance sur demande (calculé par IEC ou Markov)
- `PTIF_avg` = probabilité de défaillance test-indépendante (estimée séparément)

### Calcul CSU

```python
def compute_csu(
    pfd_avg: float,
    lambda_du: float,
    T1: float,
    ptif_fraction: float = 0.05,
    additional_ptif: float = 0.0
) -> dict:
    """
    Calcul du CSU (Critical Safety Unavailability) selon méthode PDS.
    
    Args:
        pfd_avg       : PFD moyen calculé (IEC ou Markov)
        lambda_du     : taux de défaillance DU du système [1/h]
        T1            : intervalle proof test [h]
        ptif_fraction : fraction des défaillances qui sont test-indépendantes
                        (valeur typique : 0.05 à 0.15 selon type de process)
        additional_ptif : PTIF absolu additionnel (erreurs systématiques, CCF spéciaux)
    
    Returns:
        dict avec csu, ptif, sil_from_csu
    """
    # PTIF dû aux défaillances latentes
    ptif_latent = lambda_du * ptif_fraction * T1
    
    # PTIF total
    ptif_total = ptif_latent + additional_ptif
    
    # CSU
    csu = pfd_avg + ptif_total
    
    # SIL depuis CSU
    sil_from_csu = _sil_from_pfd(csu)
    
    return {
        "pfd_avg": pfd_avg,
        "ptif": ptif_total,
        "ptif_latent": ptif_latent,
        "ptif_additional": additional_ptif,
        "csu": csu,
        "sil_from_pfd": _sil_from_pfd(pfd_avg),
        "sil_from_csu": sil_from_csu,
        "csu_penalty": ptif_total / pfd_avg if pfd_avg > 0 else 0.0
    }


def _sil_from_pfd(pfd: float) -> int:
    """SIL depuis PFD selon IEC 61508."""
    if pfd < 1e-4:
        return 4
    elif pfd < 1e-3:
        return 3
    elif pfd < 1e-2:
        return 2
    elif pfd < 1e-1:
        return 1
    else:
        return 0
```

---

## Couverture Partielle du Proof Test (cPT < 1)

### Modèle IEC 61508-6 (approché)

L'IEC 61508-6 Annexe B donne pour un proof test imparfait (couverture PTC) :

```
PFD_avg_imparfait ≈ (1 - PTC) × λ_DU × T1 / 2
                  + PTC × λ_DU × T1 / 2  × (fraction non testée cumulée)
```

Plus précisément (Tableau B.9 IEC) :

```
PFD_avg = λ_DU × T1 / 2 × [1 - PTC/2]
```

**Note** : cette formule est une approximation du premier ordre.

### Modèle Markov exact avec proof test imparfait

```python
def proof_test_jump_matrix(cPT: float) -> np.ndarray:
    """
    Matrice de transition lors d'un proof test de couverture cPT.
    
    Les DU sont révélés avec probabilité cPT.
    Les DU non révélés restent en état DU.
    
    États : 0=W, 1=DU, 2=DD, 3=R
    """
    M = np.eye(4)
    M[1, 1] = 1 - cPT   # DU non révélés restent DU
    M[3, 1] = cPT        # DU révélés → réparation
    return M


def compute_pfd_imperfect_pt(
    lambda_du: float,
    lambda_dd: float,
    mu_dd: float,
    mu_repair: float,
    T1: float,
    cPT: float,           # couverture proof test (0-1)
    n_intervals: int = 10 # nombre d'intervalles T1 à simuler (régime permanent)
) -> dict:
    """
    PFD exact avec proof test imparfait par Markov.
    
    Simule n_intervals intervalles T1 pour atteindre le régime permanent.
    La distribution initiale de chaque intervalle = état final de l'intervalle précédent
    après application du saut PT.
    """
    from scipy.linalg import expm
    
    Q = np.array([
        [-(lambda_du + lambda_dd), lambda_du, lambda_dd, 0],
        [0, 0, 0, 0],
        [0, 0, -mu_dd, mu_dd],
        [mu_repair, 0, 0, -mu_repair]
    ])
    
    M_PT = proof_test_jump_matrix(cPT)
    Phi_T1 = expm(Q * T1)
    
    # État initial
    state = np.array([1.0, 0.0, 0.0, 0.0])
    
    pfd_history = []
    
    for interval in range(n_intervals):
        # Intégrer p_DU sur [0, T1] depuis état actuel
        pDU_integral = _integrate_pdu_trapz(state, Q, T1, n_steps=500)
        pfd_interval = pDU_integral / T1
        pfd_history.append(pfd_interval)
        
        # Propager jusqu'à T1
        state = Phi_T1 @ state
        
        # Appliquer proof test imparfait
        state = M_PT @ state
    
    # Régime permanent = moyenne des derniers intervalles (convergence)
    pfd_steady_state = np.mean(pfd_history[-3:])
    
    return {
        "pfdavg": pfd_steady_state,
        "pfd_history": pfd_history,
        "converged": abs(pfd_history[-1] - pfd_history[-2]) / pfd_history[-1] < 0.01,
        "method": "markov_imperfect_pt"
    }


def _integrate_pdu_trapz(state0, Q, T, n_steps=500):
    """Intégrale de p_DU(t) par trapèzes."""
    from scipy.linalg import expm
    dt = T / n_steps
    Phi_dt = expm(Q * dt)
    s = state0.copy()
    integral = 0.0
    prev = s[1]
    for _ in range(n_steps):
        s = Phi_dt @ s
        integral += 0.5 * (prev + s[1]) * dt
        prev = s[1]
    return integral
```

---

## Valeurs Typiques PTIF par Type d'Industrie

| Secteur | PTIF fraction typique | Justification |
|---|---|---|
| Offshore O&G (NORSOK) | 5–10% | Défaillances de mode de demande valves sous-marines |
| Pétrochimie (onshore) | 3–7% | Conditionnement process, T° extrêmes |
| Nucléaire | 1–5% | Défaillances systématiques logiciel |
| Process chimique | 5–15% | Corrosion, bouchage, gel |
| Machines industrielles | 2–5% | Bien défini, essais représentatifs |

---

## Intégration dans PRISM : API PDS

```python
def compute_sif_pds(
    sif_params: dict,
    pds_config: dict
) -> dict:
    """
    Calcul SIF avec méthode PDS (CSU = PFD + PTIF).
    
    pds_config = {
        "ptif_fraction": 0.05,       # fraction test-indépendante
        "cPT": 1.0,                  # couverture proof test
        "additional_ptif": 0.0,      # PTIF additionnel absolu
        "use_csu_for_sil": True      # SIL calculé depuis CSU (pas PFD)
    }
    
    Retourne le dict standard computeSIF + champs PDS.
    """
    # Calcul PFD standard (IEC ou Markov selon λ×T1)
    base_result = compute_base_pfd(sif_params)
    
    # Correction proof test imparfait
    if pds_config.get("cPT", 1.0) < 1.0:
        pt_result = compute_pfd_imperfect_pt(
            lambda_du=sif_params["lambda_du_total"],
            lambda_dd=sif_params.get("lambda_dd_total", 0),
            mu_dd=1/sif_params.get("MTTR_dd", 8),
            mu_repair=1/sif_params.get("MTTR", 8),
            T1=sif_params["T1"],
            cPT=pds_config["cPT"]
        )
        pfd_corrected = pt_result["pfdavg"]
    else:
        pfd_corrected = base_result["pfdavg"]
    
    # Calcul CSU
    csu_result = compute_csu(
        pfd_avg=pfd_corrected,
        lambda_du=sif_params["lambda_du_total"],
        T1=sif_params["T1"],
        ptif_fraction=pds_config.get("ptif_fraction", 0.05),
        additional_ptif=pds_config.get("additional_ptif", 0.0)
    )
    
    # SIL depuis CSU ou PFD selon config
    use_csu = pds_config.get("use_csu_for_sil", True)
    sil_final = csu_result["sil_from_csu"] if use_csu else csu_result["sil_from_pfd"]
    
    return {
        **base_result,
        "pfdavg": pfd_corrected,  # PFD corrigé cPT
        "silAchieved": sil_final,
        "pds": {
            **csu_result,
            "cPT": pds_config.get("cPT", 1.0),
            "method": "PDS_CSU"
        }
    }
```

---

## Résumé : Quand Appliquer la Méthode PDS

| Condition | Recommandation |
|---|---|
| Secteur O&G offshore | PDS obligatoire (NORSOK S-001) |
| Process H₂S ou corrosif | PTIF ≥ 5% recommandé |
| Proof test < 100% couverture | cPT < 1 obligatoire |
| SIL 3 demandé | CSU recommandé (impact potentiel ±0.5 SIL) |
| Valves sous-marines | PTIF fraction jusqu'à 15% |
| Environnement contrôlé, essais complets | IEC seul suffisant |
