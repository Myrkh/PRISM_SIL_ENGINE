# 14 — Moteur Monte Carlo, Réseaux de Pétri, Analyse d'Incertitude

> Source : **IEC 61508-6:2010 Annexe B §B.5.3 et B.6**  
> Ce document spécifie le troisième moteur de calcul : simulation stochastique.

---

## Positionnement dans l'Architecture du Moteur

```
MOTEUR 1 : IEC Formules simplifiées      ← Instant, approximé
           (TypeScript, déjà implémenté)

MOTEUR 2 : Markov Multiphase             ← 2-10s, exact
           (Python/scipy, cf. 12_MARKOV)

MOTEUR 3 : Monte Carlo / Petri           ← 30s-5min, arbitrairement exact
           (Python/numpy, ce document)
           
USAGE RECOMMANDÉ :
- Moteur 1 : calcul interactif temps réel
- Moteur 2 : vérification SIL 3/4, λ×T1 > 0.1, rapport audit
- Moteur 3 : analyse d'incertitude, architectures complexes, validation croisée
```

---

## B.5.3 — Principe Monte Carlo selon IEC 61508-6

### Générateur de nombre aléatoire pour loi exponentielle

```python
import numpy as np

def sample_exponential(rate: float, rng: np.random.Generator) -> float:
    """
    Temps jusqu'à défaillance selon loi exponentielle de paramètre `rate`.
    Inverse de la CDF : d = -ln(U) / λ
    """
    if rate <= 0:
        return float('inf')
    u = rng.random()
    return -np.log(u) / rate
```

### Algorithme de simulation d'une histoire (IEC B.5.3.2)

```python
class ComponentHistory:
    """
    Simule l'histoire d'un composant soumis à essais périodiques.
    Implémente le réseau de Pétri de la Figure B.33 de l'IEC 61508-6.
    """
    
    def __init__(self, lambda_DU: float, lambda_DD: float,
                 mu_repair: float, T1: float, T_total: float,
                 pi: float = 0.0,       # durée essai
                 theta: float = 0.0,    # décalage initial essai
                 PTC: float = 1.0,      # couverture essai périodique
                 gamma: float = 0.0,    # prob défaillance par sollicitation
                 sigma: float = 0.0,    # prob non-détection à l'essai
                 seed: int = None):
        
        self.lDU = lambda_DU
        self.lDD = lambda_DD
        self.mu = mu_repair
        self.T1 = T1
        self.T_total = T_total
        self.pi = pi
        self.theta = theta
        self.PTC = PTC
        self.gamma = gamma
        self.sigma = sigma
        self.rng = np.random.default_rng(seed)
    
    def run(self) -> dict:
        """
        Simule une histoire complète du composant sur T_total.
        Retourne les temps dans chaque état.
        """
        t = 0.0
        state = 'W'  # Commence en fonctionnement
        
        # Temps cumulés dans chaque état
        time_in_state = {'W': 0.0, 'DU': 0.0, 'DD': 0.0, 'R': 0.0, 'TST': 0.0}
        
        # Prochain essai
        next_test = self.theta if self.theta > 0 else self.T1
        test_number = 0
        
        while t < self.T_total:
            if state == 'W':
                # Prochains événements possibles depuis W
                t_DU = t + sample_exponential(self.lDU, self.rng)
                t_DD = t + sample_exponential(self.lDD, self.rng)
                t_event = min(t_DU, t_DD, next_test, self.T_total)
                
                time_in_state['W'] += t_event - t
                t = t_event
                
                if t >= self.T_total:
                    break
                elif t == next_test:
                    # Essai périodique
                    t, state, next_test, test_number = self._do_test(
                        t, state, next_test, test_number, time_in_state)
                elif t_DU < t_DD:
                    state = 'DU'
                else:
                    state = 'DD'
                    
            elif state == 'DD':
                # Réparation immédiate
                t_repair = t + sample_exponential(self.mu, self.rng)
                t_event = min(t_repair, self.T_total)
                
                time_in_state['DD'] += t_event - t
                t = t_event
                
                if t < self.T_total:
                    state = 'W'
                    
            elif state == 'DU':
                # Attend l'essai (pas de réparation)
                # Mais peut aussi tomber en CCF (géré au niveau système)
                t_event = min(next_test, self.T_total)
                
                time_in_state['DU'] += t_event - t
                t = t_event
                
                if t >= self.T_total:
                    break
                    
                # Essai périodique
                t, state, next_test, test_number = self._do_test(
                    t, state, next_test, test_number, time_in_state)
                    
            elif state == 'R':
                # En réparation
                t_repair = t + sample_exponential(self.mu, self.rng)
                t_event = min(t_repair, next_test, self.T_total)
                
                time_in_state['R'] += t_event - t
                t = t_event
                
                if t >= self.T_total:
                    break
                elif t == t_repair:
                    state = 'W'
                else:
                    # Prochain essai pendant réparation
                    t, state, next_test, test_number = self._do_test(
                        t, state, next_test, test_number, time_in_state)
                        
            elif state == 'TST':
                # En cours d'essai
                t_end = t + self.pi
                t_event = min(t_end, self.T_total)
                
                time_in_state['TST'] += t_event - t
                t = t_event
                
                if t < self.T_total:
                    # Fin essai → W (si était W avant)
                    state = 'W'
        
        return time_in_state
    
    def _do_test(self, t, state, next_test, test_number, time_in_state):
        """
        Gère un essai périodique selon les paramètres du composant.
        """
        test_number += 1
        
        # Durée d'essai (si applicable)
        if self.pi > 0 and state == 'W':
            t_end_test = min(t + self.pi, self.T_total)
            time_in_state['TST'] += t_end_test - t
            t = t_end_test
        
        # Résultat de l'essai
        if state == 'DU':
            # Détection selon PTC
            if self.rng.random() < self.PTC:
                # Détection → réparation
                if self.rng.random() > self.sigma:
                    state = 'R'
                # else : non détection (erreur), reste DU
            else:
                pass  # Défaillance non couverte, reste DU jusqu'à T2
        elif state == 'W':
            # Probabilité de défaillance par sollicitation
            if self.rng.random() < self.gamma:
                state = 'R'
        
        # Prochain essai
        next_test += self.T1
        
        return t, state, next_test, test_number
```

---

## Simulateur Système Complet (Monte Carlo)

```python
class SystemMonteCarlo:
    """
    Simule un système SIF complet (capteurs + logique + EF).
    Utilise la structure logique pour combiner les composants.
    """
    
    def __init__(self, 
                 n_simulations: int = 10000,
                 T_total: float = 87600,   # 10 ans
                 seed: int = 42):
        self.N = n_simulations
        self.T_total = T_total
        self.rng = np.random.default_rng(seed)
    
    def simulate_pfdavg(self, components: list, 
                         architecture: str = '1oo2',
                         T1: float = 8760) -> dict:
        """
        Monte Carlo pour PFDavg d'un sous-système.
        
        architecture : '1oo1', '1oo2', '2oo2', '2oo3', '1oo2D', '1oo3'
        """
        pfd_samples = []
        
        for sim in range(self.N):
            # Simuler chaque composant
            comp_unavail = []
            for comp in components:
                history = ComponentHistory(
                    lambda_DU=comp['lambda_DU'],
                    lambda_DD=comp['lambda_DD'],
                    mu_repair=comp.get('mu_repair', 1/8),
                    T1=T1,
                    T_total=self.T_total,
                    pi=comp.get('pi', 0),
                    PTC=comp.get('PTC', 1.0),
                    gamma=comp.get('gamma', 0),
                    sigma=comp.get('sigma', 0),
                    seed=self.rng.integers(0, 2**32)
                )
                times = history.run()
                unavail_time = times['DU'] + times['R'] + times['TST']
                pfd_comp = unavail_time / self.T_total
                comp_unavail.append(pfd_comp)
            
            # Combiner selon architecture
            pfd_sys = self._combine_architecture(comp_unavail, architecture)
            pfd_samples.append(pfd_sys)
        
        # Statistiques
        pfd_mean = np.mean(pfd_samples)
        pfd_std = np.std(pfd_samples)
        ci_90 = 1.645 * pfd_std / np.sqrt(self.N)
        
        return {
            'pfdavg': pfd_mean,
            'std': pfd_std,
            'ci_90_lower': pfd_mean - ci_90,
            'ci_90_upper': pfd_mean + ci_90,
            'ci_90_half': ci_90,
            'rrf': 1.0 / pfd_mean if pfd_mean > 0 else float('inf'),
            'n_simulations': self.N,
            'samples': pfd_samples  # Pour histogramme
        }
    
    def _combine_architecture(self, unavail_list: list, 
                               architecture: str) -> float:
        """
        Combine les indisponibilités selon la logique de vote.
        
        Pour un système kooN : la panne système requiert >= (n-k+1) canaux en panne.
        """
        n = len(unavail_list)
        u = sorted(unavail_list, reverse=True)  # Plus disponibles en premier
        
        if architecture == '1oo1':
            return u[0]
        elif architecture == '2oo2':
            return 1 - (1-u[0]) * (1-u[1])  # Série = produit disponibilités
        elif architecture == '1oo2':
            # Défaillance si les 2 tombent ensemble
            # Approximation MC : PFD_sys ≈ prod des PFD
            return u[0] * u[1]
        elif architecture == '2oo3':
            # Défaillance si >= 2 sur 3 défaillants
            # Approximation : combinaisons
            p = u  # probabilités d'indisponibilité
            pfd = p[0]*p[1] + p[0]*p[2] + p[1]*p[2] - 2*p[0]*p[1]*p[2]
            return pfd
        elif architecture == '1oo3':
            return u[0] * u[1] * u[2]
        else:
            # kooN générique
            k_str, n_str = architecture.split('oo')
            k, n_arch = int(k_str), int(n_str)
            n_fail_required = n_arch - k + 1
            # ... calcul combinatoire
            return self._koon_pfd(u[:n_arch], n_fail_required)
    
    def _koon_pfd(self, unavail: list, n_fail_required: int) -> float:
        """
        PFD pour kooN par enumération des combinaisons.
        """
        from itertools import combinations
        n = len(unavail)
        
        # Probabilité d'exactement j composants en panne
        # via inclusion-exclusion
        pfd = 0.0
        for j in range(n_fail_required, n + 1):
            for combo in combinations(range(n), j):
                term = 1.0
                for idx in combo:
                    term *= unavail[idx]
                for idx in range(n):
                    if idx not in combo:
                        term *= (1 - unavail[idx])
                pfd += term
        return pfd
    
    def simulate_pfh(self, components: list,
                     architecture: str = '1oo2',
                     T1: float = 8760,
                     n_periods: int = 10) -> dict:
        """
        Monte Carlo pour PFH (mode haute demande).
        Compte les transitions vers l'état de défaillance système.
        """
        failure_counts = []
        
        for sim in range(self.N):
            # Compter les défaillances système sur T_total
            n_failures = self._count_system_failures(
                components, architecture, T1, n_periods)
            failure_counts.append(n_failures)
        
        mean_failures = np.mean(failure_counts)
        pfh = mean_failures / self.T_total
        
        return {
            'pfh': pfh,
            'mean_failures_per_Ttotal': mean_failures,
            'std_pfh': np.std(failure_counts) / self.T_total,
            'n_simulations': self.N
        }
    
    def _count_system_failures(self, components, architecture, T1, n_periods):
        """
        Compte les transitions vers défaillance système dans T_total.
        Implémente la logique de surveillance continue.
        """
        # ... implémentation détaillée
        pass
```

---

## B.6 — Analyse d'Incertitude sur les Paramètres

### Modèles de distribution pour paramètres λ

```python
from scipy import stats
import numpy as np

class UncertaintyModel:
    """
    Modèle d'incertitude sur les paramètres de fiabilité.
    IEC 61508-6 §B.6 : utiliser loi log-normale pour λ.
    """
    
    def __init__(self, lambda_mean: float, error_factor: float = 3.0,
                 dist_type: str = 'lognormal'):
        """
        lambda_mean  : estimateur central (λ̂ ou médiane)
        error_factor : ef = √(λ_sup/λ_inf), typiquement 3 (±1 ordre de grandeur)
        dist_type    : 'lognormal', 'uniform', 'triangular', 'chi2'
        """
        self.lambda_mean = lambda_mean
        self.ef = error_factor
        self.dist_type = dist_type
        
        # Paramètres log-normale
        # λ_inf = λ_mean/ef, λ_sup = λ_mean*ef
        # σ_ln = ln(ef) / 1.645 (pour IC 90%)
        self.sigma_ln = np.log(error_factor) / 1.645
        self.mu_ln = np.log(lambda_mean)
    
    def sample(self, n: int, rng: np.random.Generator) -> np.ndarray:
        """
        Tire n valeurs selon la distribution choisie.
        """
        if self.dist_type == 'lognormal':
            return rng.lognormal(self.mu_ln, self.sigma_ln, n)
        elif self.dist_type == 'uniform':
            lower = self.lambda_mean / self.ef
            upper = self.lambda_mean * self.ef
            return rng.uniform(lower, upper, n)
        elif self.dist_type == 'triangular':
            lower = self.lambda_mean / self.ef
            upper = self.lambda_mean * self.ef
            return rng.triangular(lower, self.lambda_mean, upper, n)
    
    def confidence_interval(self, alpha: float = 0.05) -> tuple:
        """
        Calcule l'intervalle de confiance à (1-2α)*100% .
        """
        if self.dist_type == 'lognormal':
            q_low = stats.lognorm.ppf(alpha, s=self.sigma_ln, scale=np.exp(self.mu_ln))
            q_high = stats.lognorm.ppf(1-alpha, s=self.sigma_ln, scale=np.exp(self.mu_ln))
            return q_low, q_high
        
    @staticmethod
    def from_observations(n_failures: int, T_observation: float, 
                          alpha: float = 0.05) -> 'UncertaintyModel':
        """
        Construit modèle d'incertitude depuis données d'observation.
        IEC 61508-6 §B.6 : utiliser distribution Chi-2.
        
        λ̂ = n/T  (estimateur maximum vraisemblance)
        λ_inf = χ²_{1-α, 2n} / (2T)
        λ_sup = χ²_{α, 2(n+1)} / (2T)
        """
        lambda_hat = n_failures / T_observation
        
        # IC 90% (α=5%)
        lambda_inf = stats.chi2.ppf(1-alpha, 2*n_failures) / (2*T_observation)
        lambda_sup = stats.chi2.ppf(alpha, 2*(n_failures+1)) / (2*T_observation)
        
        ef = np.sqrt(lambda_sup / lambda_inf) if lambda_inf > 0 else 3.0
        
        return UncertaintyModel(lambda_hat, ef, 'lognormal')


def propagate_uncertainty_pfdavg(
        components: list,
        architecture: str,
        T1: float,
        n_monte_carlo: int = 10000,
        seed: int = 42) -> dict:
    """
    Propage les incertitudes sur λ vers l'incertitude sur PFDavg.
    Implémente la Figure B.38 de l'IEC 61508-6.
    
    Algo (IEC B.6) :
    1. Tirer λᵢ selon distribution (log-normale)
    2. Calculer PFDavg avec λᵢ (via formule IEC ou Markov)
    3. Enregistrer résultat
    4. Répéter N fois
    5. Analyser histogramme
    """
    rng = np.random.default_rng(seed)
    pfd_samples = []
    
    for _ in range(n_monte_carlo):
        # Tirer λ pour chaque composant selon distribution d'incertitude
        sampled_components = []
        for comp in components:
            lambda_D = comp['uncertainty'].sample(1, rng)[0]
            DC = comp.get('DC', 0.0)
            sampled_comp = {
                'lambda_DU': lambda_D * (1 - DC),
                'lambda_DD': lambda_D * DC,
                'DC': DC,
                'T1': T1,
                'beta': comp.get('beta', 0.02),
                'beta_D': comp.get('beta_D', 0.01),
                'MTTR': comp.get('MTTR', 8.0)
            }
            sampled_components.append(sampled_comp)
        
        # Calculer PFDavg avec ces paramètres (via formule IEC)
        pfd = compute_pfdavg_iec(sampled_components, architecture)
        pfd_samples.append(pfd)
    
    pfd_samples = np.array(pfd_samples)
    
    return {
        'mean': np.mean(pfd_samples),
        'median': np.median(pfd_samples),
        'std': np.std(pfd_samples),
        'p5': np.percentile(pfd_samples, 5),
        'p10': np.percentile(pfd_samples, 10),
        'p50': np.percentile(pfd_samples, 50),
        'p90': np.percentile(pfd_samples, 90),
        'p95': np.percentile(pfd_samples, 95),
        'ci_90': (np.percentile(pfd_samples, 5), np.percentile(pfd_samples, 95)),
        'ci_90_half': 1.645 * np.std(pfd_samples) / np.sqrt(n_monte_carlo),
        'histogram': pfd_samples  # Pour affichage
    }
```

---

## Graphiques à Produire (Specs visuelles complètes)

### Graphique 1 : Courbe en dents de scie PFD(t)

```
Spécification :
- Axe X : temps (heures ou années)
- Axe Y : PFD(t) (échelle logarithmique)
- Courbe principale : PFDavg (ligne horizontale rouge)
- Courbe en dents de scie : PFD instantanée (bleu)
- Marqueurs : moments des essais (triangles)
- Annotations : valeur PFDavg, SIL atteint

Données sources :
- Moteur Markov : P_unavail(t) = Σ P_indispo(t)
- Moteur Monte Carlo : moyenne sur N simulations à chaque t

Exemple Python (matplotlib) :
```

```python
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

def plot_pfd_curve(t_array: np.ndarray, pfd_t: np.ndarray,
                   pfdavg: float, T1: float, architecture: str,
                   title: str = "PFD(t) — Courbe en dents de scie") -> plt.Figure:
    """
    Reproduit la Figure B.19/B.25 de l'IEC 61508-6.
    """
    fig, ax = plt.subplots(figsize=(12, 5))
    
    # SIL bands
    sil_bands = [
        (1e-5, 1e-4, '#00800030', 'SIL 3 (10⁻⁵ – 10⁻⁴)'),
        (1e-4, 1e-3, '#FFFF0030', 'SIL 2 (10⁻⁴ – 10⁻³)'),
        (1e-3, 1e-2, '#FFA50030', 'SIL 1 (10⁻³ – 10⁻²)'),
    ]
    for low, high, color, label in sil_bands:
        ax.axhspan(low, high, alpha=0.3, color=color, label=label)
    
    # Courbe PFD(t)
    ax.semilogy(t_array / 8760, pfd_t, 'b-', linewidth=1.5, 
                label='PFD(t) instantanée', alpha=0.8)
    
    # PFDavg
    ax.axhline(y=pfdavg, color='red', linestyle='--', linewidth=2.5,
               label=f'PFDavg = {pfdavg:.2e} (RRF = {1/pfdavg:.0f})')
    
    # Marqueurs d'essai
    test_times = np.arange(T1, t_array[-1] + 1, T1) / 8760
    for tt in test_times:
        ax.axvline(x=tt, color='gray', linestyle=':', alpha=0.5, linewidth=0.8)
    
    # Formatage
    ax.set_xlabel("Temps (années)", fontsize=12)
    ax.set_ylabel("PFD(t)", fontsize=12)
    ax.set_title(f"{title}\nArchitecture: {architecture}", fontsize=13)
    ax.legend(loc='upper right', fontsize=10)
    ax.grid(True, which='both', alpha=0.3)
    ax.set_ylim([1e-8, 1e-1])
    
    return fig
```

### Graphique 2 : Contribution par sous-système (Waterfall / Camembert)

```python
def plot_contributions(contributions: dict, pfdavg_total: float) -> plt.Figure:
    """
    Graphique de contribution S/L/FE à la PFD totale.
    Reproduit le concept de Figure B.3 de l'IEC.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Barres horizontales (waterfall)
    labels = list(contributions.keys())
    values = list(contributions.values())
    percents = [v/pfdavg_total*100 for v in values]
    
    bars = ax1.barh(labels, percents, color=['#2196F3', '#4CAF50', '#FF5722'])
    ax1.set_xlabel("Contribution (%)")
    ax1.set_title(f"Contributions à PFDavg = {pfdavg_total:.2e}")
    
    for bar, pct, val in zip(bars, percents, values):
        ax1.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                f'{val:.2e} ({pct:.1f}%)', va='center')
    
    # Camembert
    ax2.pie(percents, labels=labels, autopct='%1.1f%%',
            colors=['#2196F3', '#4CAF50', '#FF5722'])
    ax2.set_title("Part relative")
    
    return fig
```

### Graphique 3 : Analyse de Sensibilité (Tornado Chart)

```python
def plot_tornado(sensitivity_results: list, pfd_base: float) -> plt.Figure:
    """
    Tornado chart : impact de ±20% de chaque paramètre sur PFDavg.
    
    sensitivity_results : liste de dict {
        'param': 'λ_DU capteur',
        'pfd_low': ...,   # PFD si paramètre -20%
        'pfd_high': ...,  # PFD si paramètre +20%
    }
    """
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Trier par amplitude de variation
    results = sorted(sensitivity_results, 
                     key=lambda x: abs(x['pfd_high'] - x['pfd_low']),
                     reverse=True)
    
    y_pos = range(len(results))
    
    for i, r in enumerate(results):
        low_delta = (r['pfd_low'] - pfd_base) / pfd_base * 100
        high_delta = (r['pfd_high'] - pfd_base) / pfd_base * 100
        
        # Barre negative (paramètre bas → PFD plus bas)
        if low_delta < 0:
            ax.barh(i, low_delta, left=0, color='#4CAF50', alpha=0.7, height=0.6)
        else:
            ax.barh(i, low_delta, left=0, color='#F44336', alpha=0.7, height=0.6)
            
        # Barre positive
        if high_delta > 0:
            ax.barh(i, high_delta, left=0, color='#F44336', alpha=0.7, height=0.6)
        else:
            ax.barh(i, high_delta, left=0, color='#4CAF50', alpha=0.7, height=0.6)
    
    ax.set_yticks(list(y_pos))
    ax.set_yticklabels([r['param'] for r in results])
    ax.axvline(0, color='black', linewidth=1.5)
    ax.set_xlabel("Variation PFDavg (%)")
    ax.set_title("Analyse de Sensibilité (±20% de chaque paramètre)")
    ax.grid(True, axis='x', alpha=0.3)
    
    return fig
```

### Graphique 4 : Histogramme d'Incertitude (Figure B.38 IEC)

```python
def plot_uncertainty_histogram(pfd_samples: np.ndarray, 
                                pfd_deterministic: float) -> plt.Figure:
    """
    Reproduit la Figure B.38 de l'IEC 61508-6.
    Distribution de PFDavg avec incertitude sur λ.
    """
    fig, ax = plt.subplots(figsize=(10, 5))
    
    # Histogramme en échelle log
    log_pfd = np.log10(pfd_samples[pfd_samples > 0])
    
    ax.hist(log_pfd, bins=50, density=True, color='#2196F3', alpha=0.7,
            label=f'Distribution MC (N={len(pfd_samples)})')
    
    # Valeur déterministe
    ax.axvline(np.log10(pfd_deterministic), color='red', linewidth=2,
               label=f'PFD déterministe = {pfd_deterministic:.2e}')
    
    # Médiane et percentiles
    ax.axvline(np.percentile(log_pfd, 50), color='green', linestyle='--',
               label=f'Médiane = {10**np.percentile(log_pfd, 50):.2e}')
    ax.axvline(np.percentile(log_pfd, 5), color='orange', linestyle=':',
               label=f'P5 = {10**np.percentile(log_pfd, 5):.2e}')
    ax.axvline(np.percentile(log_pfd, 95), color='orange', linestyle=':',
               label=f'P95 = {10**np.percentile(log_pfd, 95):.2e}')
    
    # SIL zones
    for thresh, sil in [(1e-4, 'SIL 3'), (1e-3, 'SIL 2'), (1e-2, 'SIL 1')]:
        ax.axvline(np.log10(thresh), color='gray', linestyle='-', alpha=0.3)
        ax.text(np.log10(thresh), ax.get_ylim()[1]*0.9, sil, 
                ha='center', fontsize=9, color='gray')
    
    ax.set_xlabel("log₁₀(PFDavg)")
    ax.set_ylabel("Densité de probabilité")
    ax.set_title("Propagation d'Incertitude sur PFDavg")
    ax.legend(fontsize=9)
    
    return fig
```

### Graphique 5 : Optimisation T1 (Courbe de Frontière SIL)

```python
def plot_t1_optimization(lambda_D: float, DC: float, beta: float,
                          target_sil: int, architecture: str) -> plt.Figure:
    """
    Affiche PFDavg en fonction de T1 et la frontière SIL.
    Permet de lire directement T1_max pour tenir un SIL donné.
    """
    SIL_BOUNDS = {1: (1e-3, 1e-2), 2: (1e-4, 1e-3), 3: (1e-5, 1e-4), 4: (1e-6, 1e-5)}
    
    T1_range = np.logspace(np.log10(30), np.log10(87600), 200)  # 30h à 10 ans
    pfd_values = []
    
    for T1 in T1_range:
        pfd = compute_pfdavg_iec_simple(lambda_D, DC, beta, T1, architecture)
        pfd_values.append(pfd)
    
    pfd_values = np.array(pfd_values)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Zones SIL
    sil_colors = {1: '#FFA500', 2: '#FFFF00', 3: '#00FF00', 4: '#0000FF'}
    for sil, (low, high) in SIL_BOUNDS.items():
        ax.axhspan(low, high, alpha=0.15, 
                   color=sil_colors[sil], label=f'SIL {sil}')
    
    # Courbe PFDavg(T1)
    T1_years = T1_range / 8760
    ax.loglog(T1_years, pfd_values, 'b-', linewidth=2.5, 
              label=f'PFDavg({architecture})')
    
    # T1 max pour SIL cible
    target_low, target_high = SIL_BOUNDS[target_sil]
    # Trouver T1 où PFDavg = borne haute du SIL cible
    t1_max_idx = np.argmax(pfd_values < target_high)
    if t1_max_idx > 0:
        T1_max = T1_range[t1_max_idx] / 8760
        ax.axvline(T1_max, color='red', linestyle='--', linewidth=2,
                   label=f'T1 max = {T1_max:.2f} ans pour SIL {target_sil}')
    
    ax.set_xlabel("Intervalle d'essai T1 (années)", fontsize=12)
    ax.set_ylabel("PFDavg", fontsize=12)
    ax.set_title(f"PFDavg vs T1 — {architecture}\nλ_D={lambda_D:.2e}, DC={DC*100:.0f}%, β={beta*100:.0f}%")
    ax.legend(fontsize=10)
    ax.grid(True, which='both', alpha=0.3)
    
    return fig
```

### Graphique 6 : Comparaison IEC approx vs Markov exact

```python
def plot_iec_vs_markov_comparison(results_iec: dict, results_markov: dict,
                                   parameter_name: str, parameter_range: np.ndarray) -> plt.Figure:
    """
    Compare IEC simplifié vs Markov exact sur une plage de paramètres.
    Met en évidence où l'IEC est insuffisant.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Axe 1 : PFDavg absolu
    ax1.loglog(parameter_range, results_iec['pfdavg'], 'b-', 
               linewidth=2, label='IEC approx (formule simplifiée)')
    ax1.loglog(parameter_range, results_markov['pfdavg'], 'r--', 
               linewidth=2, label='Markov exact')
    ax1.set_xlabel(parameter_name)
    ax1.set_ylabel('PFDavg')
    ax1.legend()
    ax1.grid(True, which='both', alpha=0.3)
    ax1.set_title('PFDavg : IEC vs Markov')
    
    # Axe 2 : Écart relatif
    ecart = (np.array(results_iec['pfdavg']) - np.array(results_markov['pfdavg'])) \
            / np.array(results_markov['pfdavg']) * 100
    
    ax2.semilogx(parameter_range, ecart, 'g-', linewidth=2)
    ax2.axhline(5, color='orange', linestyle='--', label='Seuil ±5%')
    ax2.axhline(-5, color='orange', linestyle='--')
    ax2.axhline(10, color='red', linestyle=':', label='Seuil ±10%')
    ax2.axhline(-10, color='red', linestyle=':')
    ax2.set_xlabel(parameter_name)
    ax2.set_ylabel('Écart relatif (%)')
    ax2.set_title('Écart IEC vs Markov\n(positif = IEC surestime le risque)')
    ax2.legend()
    ax2.grid(True, which='both', alpha=0.3)
    
    # Annotation zone "Markov requis"
    lambda_T1_crit = 0.1  # valeur λ×T1 critique
    ax1.axvspan(lambda_T1_crit, parameter_range[-1], alpha=0.1, color='red',
               label='Zone Markov recommandé')
    
    return fig
```

---

## Performance et Parallélisation

```python
import concurrent.futures
from functools import partial

def monte_carlo_parallel(simulate_func, n_simulations: int, 
                          n_workers: int = 4, chunk_size: int = 1000) -> list:
    """
    Monte Carlo parallèle pour gain de temps.
    
    Performance attendue :
    - 1 000 simulations : ~0.5s
    - 10 000 simulations : ~5s  
    - 100 000 simulations : ~50s (parallélisé)
    """
    chunks = [(i, min(chunk_size, n_simulations - i)) 
              for i in range(0, n_simulations, chunk_size)]
    
    results = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=n_workers) as executor:
        futures = [executor.submit(simulate_func, start, size, seed=start)
                  for start, size in chunks]
        for future in concurrent.futures.as_completed(futures):
            results.extend(future.result())
    
    return results
```

---

## Récapitulatif : Quand utiliser quel moteur ?

| Condition | Moteur 1 (IEC) | Moteur 2 (Markov) | Moteur 3 (MC) |
|---|---|---|---|
| λ×T1 < 0.05 | ✅ Parfait | Inutile | Inutile |
| λ×T1 0.05-0.1 | ✅ Acceptable | 🔷 Recommandé | — |
| λ×T1 > 0.1 | ⚠️ Approximatif | ✅ Requis | — |
| SIL 3-4 | ⚠️ | ✅ | ✅ validation |
| PST complexe | ⚠️ | ✅ | ✅ |
| Analyse incertitude | ❌ | ⚠️ | ✅ Requis |
| Architecture rare | ❌ | ⚠️ | ✅ Requis |
| Validation croisée | — | — | ✅ Requis |
| Temps de calcul | ~1ms | ~2-30s | ~30s-5min |
