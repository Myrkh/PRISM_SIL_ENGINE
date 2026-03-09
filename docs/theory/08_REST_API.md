# 17 — Backend FastAPI : Architecture Complète du Solveur Markov

## Vue d'ensemble

Le backend Python expose le moteur Markov exact comme microservice REST,
appelé depuis le frontend TypeScript sil-engine de manière asynchrone.

```
Frontend TS (sil-engine)
    │
    │  POST /api/markov/compute
    │  POST /api/markov/montecarlo
    │  GET  /api/markov/status/{job_id}
    ▼
FastAPI Backend (Python 3.11+)
    ├── MarkovSolver (scipy.linalg)
    ├── MonteCarloEngine (numpy random)
    ├── PSTSolver (multi-phase)
    └── PDSSolver (PTIF/CSU)
```

---

## Structure du Projet

```
sil-engine-api/
├── main.py                    # FastAPI app + routes
├── pyproject.toml             # dépendances
├── solver/
│   ├── __init__.py
│   ├── markov.py              # CTMC solver (fichier 12)
│   ├── montecarlo.py          # MC engine (fichier 14)
│   ├── pst.py                 # PST exact (fichier 15)
│   ├── pds.py                 # PDS/PTIF/CSU (fichier 16)
│   └── formulas.py            # IEC formulas (fichier 11)
├── models/
│   ├── __init__.py
│   ├── request.py             # Pydantic request models
│   └── response.py            # Pydantic response models
├── tasks/
│   ├── __init__.py
│   └── worker.py              # Background jobs (long computations)
└── tests/
    ├── test_markov.py
    ├── test_pst.py
    └── test_verification.py   # Vérification vs IEC tables (fichier 13)
```

---

## Modèles Pydantic

```python
# models/request.py
from pydantic import BaseModel, Field, validator
from typing import Optional, Literal
from enum import Enum

class Architecture(str, Enum):
    OO1 = "1oo1"
    OO2 = "1oo2"
    OO2D = "1oo2D"
    OO3 = "2oo3"
    OO3_1 = "1oo3"
    OO2_2 = "2oo2"
    MOON = "MooN"


class SubsystemRequest(BaseModel):
    name: str
    lambda_du: float = Field(..., gt=0, description="Taux défaillance DU [1/h]")
    lambda_dd: float = Field(0.0, ge=0, description="Taux défaillance DD [1/h]")
    lambda_s: float = Field(0.0, ge=0, description="Taux défaillance sécurité [1/h]")
    DC: float = Field(0.0, ge=0, le=1, description="Couverture diagnostique (0-1)")
    beta: float = Field(0.01, ge=0, le=0.3, description="Facteur CCF beta")
    beta_D: Optional[float] = Field(None, ge=0, le=0.3)
    architecture: Architecture = Architecture.OO1
    M: Optional[int] = Field(None, description="M dans MooN")
    N: Optional[int] = Field(None, description="N dans MooN")
    MTTR: float = Field(8.0, gt=0, description="MTTR [h]")
    count: int = Field(1, ge=1, description="Nombre d'éléments identiques")


class PSTConfig(BaseModel):
    enabled: bool = False
    T_PST: float = Field(720.0, gt=0, description="Intervalle PST [h]")
    c_PST: float = Field(0.7, ge=0, le=1, description="Couverture PST")
    d_PST: float = Field(2.0, gt=0, description="Durée PST [h]")


class PDSConfig(BaseModel):
    enabled: bool = False
    ptif_fraction: float = Field(0.05, ge=0, le=0.5)
    cPT: float = Field(1.0, ge=0, le=1, description="Couverture proof test")
    additional_ptif: float = Field(0.0, ge=0)
    use_csu_for_sil: bool = True


class MarkovComputeRequest(BaseModel):
    """Request principale pour le calcul Markov exact."""
    
    # Paramètres globaux SIF
    T1: float = Field(..., gt=0, le=87600, description="Proof test interval [h]")
    mode: Literal["low_demand", "high_demand"] = "low_demand"
    
    # Subsystems
    subsystems: list[SubsystemRequest] = Field(..., min_items=1)
    
    # Options
    pst: PSTConfig = PSTConfig()
    pds: PDSConfig = PDSConfig()
    
    # Contrôle du calcul
    use_exact_markov: Optional[bool] = None  # None = auto (basé sur λ×T1)
    markov_steps: int = Field(1000, ge=100, le=10000)
    
    @validator("subsystems")
    def validate_moon(cls, subsystems):
        for s in subsystems:
            if s.architecture == Architecture.MOON:
                if s.M is None or s.N is None:
                    raise ValueError(f"MooN requires M and N for subsystem '{s.name}'")
                if s.M > s.N:
                    raise ValueError(f"M must be <= N for subsystem '{s.name}'")
        return subsystems
    
    class Config:
        json_schema_extra = {
            "example": {
                "T1": 8760,
                "mode": "low_demand",
                "subsystems": [
                    {"name": "Capteur PT-101", "lambda_du": 5e-6, "DC": 0.9,
                     "beta": 0.02, "architecture": "1oo2", "MTTR": 8},
                    {"name": "Logic solver", "lambda_du": 1e-6, "DC": 0.99,
                     "beta": 0.01, "architecture": "1oo1", "MTTR": 8},
                    {"name": "Vanne ESD-201", "lambda_du": 2e-5, "DC": 0.0,
                     "beta": 0.05, "architecture": "1oo1", "MTTR": 24}
                ]
            }
        }


class MonteCarloRequest(BaseModel):
    """Request pour Monte Carlo."""
    base_request: MarkovComputeRequest
    n_simulations: int = Field(10000, ge=1000, le=1000000)
    uncertainty: bool = Field(False, description="Propagation incertitudes")
    uncertainty_cov: float = Field(0.3, ge=0.0, le=2.0, description="CoV log-normale")
    seed: Optional[int] = None
    async_mode: bool = Field(True, description="True = retourner job_id immédiatement")
```

```python
# models/response.py
from pydantic import BaseModel
from typing import Optional
from enum import Enum

class SILLevel(int, Enum):
    NONE = 0
    SIL1 = 1
    SIL2 = 2
    SIL3 = 3
    SIL4 = 4


class ContributionResult(BaseModel):
    name: str
    pfdavg: float
    contribution_pct: float
    lambda_du: float
    architecture: str


class PSTResult(BaseModel):
    pfdavg_without_pst: float
    pfdavg_with_pst: float
    improvement_factor: float
    n_pst_per_interval: int
    method: str


class PDSResult(BaseModel):
    pfd_avg: float
    ptif: float
    ptif_latent: float
    ptif_additional: float
    csu: float
    sil_from_pfd: SILLevel
    sil_from_csu: SILLevel
    csu_penalty: float


class MarkovComputeResponse(BaseModel):
    """Réponse complète du calcul Markov."""
    
    # Métriques principales
    pfdavg: float
    pfh: Optional[float] = None
    rrf: float
    mttps: Optional[float] = None
    
    # SIL
    sil_from_pfd: SILLevel
    sil_achieved: SILLevel
    sil_architectural: Optional[SILLevel] = None
    
    # Détails
    contributions: list[ContributionResult]
    
    # Extensions
    pst: Optional[PSTResult] = None
    pds: Optional[PDSResult] = None
    
    # Méta
    method_used: str  # "iec_simplified" | "markov_exact" | "markov_multiphase"
    lambda_T1: float  # indicateur de non-linéarité
    warnings: list[str] = []
    computation_time_ms: float


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class AsyncJobResponse(BaseModel):
    job_id: str
    status: JobStatus
    progress_pct: Optional[float] = None
    result: Optional[MarkovComputeResponse] = None
    error: Optional[str] = None
    eta_seconds: Optional[float] = None
```

---

## Application FastAPI principale

```python
# main.py
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from models.request import MarkovComputeRequest, MonteCarloRequest
from models.response import MarkovComputeResponse, AsyncJobResponse, JobStatus
from solver.markov import MarkovSolver
from solver.pst import compute_sif_with_pst
from solver.pds import compute_sif_pds
from solver.formulas import compute_iec_simplified


# Store en mémoire pour les jobs async (Redis en production)
_jobs: dict[str, dict[str, Any]] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialisation et nettoyage du backend."""
    print("sil-engine API starting...")
    yield
    print("sil-engine API shutting down.")


app = FastAPI(
    title="sil-engine Solver",
    version="1.0.0",
    description="Exact CTMC solver for IEC 61508 SIL calculations",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://your-app.example.com"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _should_use_markov(request: MarkovComputeRequest) -> bool:
    """Détermine si le calcul Markov exact est nécessaire."""
    if request.use_exact_markov is not None:
        return request.use_exact_markov
    
    # Calcul λ_total × T1
    lambda_du_total = sum(s.lambda_du for s in request.subsystems)
    lambda_T1 = lambda_du_total * request.T1
    
    # Critère : λ×T1 > 0.1 OU SIL 3/4 demandé OU PST actif
    return lambda_T1 > 0.1 or request.pst.enabled


def _compute_sync(request: MarkovComputeRequest) -> MarkovComputeResponse:
    """Calcul synchrone (utilisé par endpoint /compute)."""
    t_start = time.perf_counter()
    
    use_markov = _should_use_markov(request)
    warnings = []
    
    # Calcul par subsystem
    contributions = []
    pfd_total = 0.0
    lambda_du_total = 0.0
    
    for sub in request.subsystems:
        lambda_T1_sub = sub.lambda_du * request.T1
        
        if use_markov or lambda_T1_sub > 0.1:
            solver = MarkovSolver(
                lambda_du=sub.lambda_du,
                lambda_dd=sub.lambda_dd,
                DC=sub.DC,
                beta=sub.beta,
                beta_D=sub.beta_D,
                MTTR=sub.MTTR,
                architecture=sub.architecture.value,
                M=sub.M,
                N=sub.N
            )
            result = solver.compute_pfd(T1=request.T1, n_steps=request.markov_steps)
            method = "markov_exact"
        else:
            result = compute_iec_simplified(
                lambda_du=sub.lambda_du,
                lambda_dd=sub.lambda_dd,
                DC=sub.DC,
                beta=sub.beta,
                MTTR=sub.MTTR,
                architecture=sub.architecture.value,
                T1=request.T1
            )
            method = "iec_simplified"
        
        sub_pfd = result["pfdavg"] * sub.count
        pfd_total += sub_pfd
        lambda_du_total += sub.lambda_du * sub.count
        
        contributions.append({
            "name": sub.name,
            "pfdavg": sub_pfd,
            "contribution_pct": 0.0,  # calculé après
            "lambda_du": sub.lambda_du,
            "architecture": sub.architecture.value
        })
    
    # Normaliser contributions
    for c in contributions:
        c["contribution_pct"] = c["pfdavg"] / pfd_total * 100 if pfd_total > 0 else 0
    
    # Avertissements
    lambda_T1 = lambda_du_total * request.T1
    if lambda_T1 > 0.1 and not use_markov:
        warnings.append(f"λ×T1={lambda_T1:.3f} > 0.1 : calcul Markov exact recommandé")
    if lambda_T1 > 1.0:
        warnings.append(f"λ×T1={lambda_T1:.3f} >> 1 : formules IEC très imprécises")
    
    # PST
    pst_result = None
    if request.pst.enabled:
        pst_data = compute_sif_with_pst(
            {"lambda_du_total": lambda_du_total, "pfdavg": pfd_total, "T1": request.T1},
            {
                "T_PST": request.pst.T_PST,
                "c_PST": request.pst.c_PST,
                "d_PST": request.pst.d_PST
            }
        )
        pfd_total = pst_data["pfdavg"]
        pst_result = pst_data["pst"]
    
    # PDS
    pds_result = None
    if request.pds.enabled:
        pds_data = compute_sif_pds(
            {"lambda_du_total": lambda_du_total, "pfdavg": pfd_total, "T1": request.T1},
            {
                "ptif_fraction": request.pds.ptif_fraction,
                "cPT": request.pds.cPT,
                "additional_ptif": request.pds.additional_ptif,
                "use_csu_for_sil": request.pds.use_csu_for_sil
            }
        )
        pds_result = pds_data["pds"]
        if request.pds.use_csu_for_sil:
            pfd_total = pds_data["pds"]["csu"]  # SIL depuis CSU
    
    # SIL
    def sil_from_pfd(pfd):
        if pfd < 1e-4: return 4
        if pfd < 1e-3: return 3
        if pfd < 1e-2: return 2
        if pfd < 1e-1: return 1
        return 0
    
    t_elapsed = (time.perf_counter() - t_start) * 1000
    
    return MarkovComputeResponse(
        pfdavg=pfd_total,
        rrf=1/pfd_total if pfd_total > 0 else float("inf"),
        sil_from_pfd=sil_from_pfd(sum(c["pfdavg"] for c in contributions)),
        sil_achieved=sil_from_pfd(pfd_total),
        contributions=contributions,
        pst=pst_result,
        pds=pds_result,
        method_used=method,
        lambda_T1=lambda_T1,
        warnings=warnings,
        computation_time_ms=t_elapsed
    )


@app.post("/api/markov/compute", response_model=MarkovComputeResponse)
async def compute_markov(request: MarkovComputeRequest):
    """
    Calcul Markov synchrone (< 30s).
    Préférer pour SIL 1-2 et architectures simples.
    """
    try:
        return _compute_sync(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/markov/montecarlo", response_model=AsyncJobResponse)
async def compute_montecarlo(
    request: MonteCarloRequest,
    background_tasks: BackgroundTasks
):
    """
    Monte Carlo asynchrone — retourne job_id immédiatement.
    Interroger /api/markov/status/{job_id} pour le résultat.
    """
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"status": JobStatus.PENDING, "progress": 0, "result": None}
    
    def run_mc():
        _jobs[job_id]["status"] = JobStatus.RUNNING
        try:
            from solver.montecarlo import SystemMonteCarlo
            mc = SystemMonteCarlo(request.base_request, seed=request.seed)
            result = mc.run(
                n_simulations=request.n_simulations,
                with_uncertainty=request.uncertainty,
                uncertainty_cov=request.uncertainty_cov,
                progress_callback=lambda p: _jobs[job_id].update({"progress": p})
            )
            _jobs[job_id]["status"] = JobStatus.DONE
            _jobs[job_id]["result"] = result
        except Exception as e:
            _jobs[job_id]["status"] = JobStatus.FAILED
            _jobs[job_id]["error"] = str(e)
    
    background_tasks.add_task(run_mc)
    
    return AsyncJobResponse(job_id=job_id, status=JobStatus.PENDING)


@app.get("/api/markov/status/{job_id}", response_model=AsyncJobResponse)
async def get_job_status(job_id: str):
    """Interroge le statut d'un job Monte Carlo asynchrone."""
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    job = _jobs[job_id]
    return AsyncJobResponse(
        job_id=job_id,
        status=job["status"],
        progress_pct=job.get("progress"),
        result=job.get("result"),
        error=job.get("error")
    )


@app.get("/api/markov/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": "1.0.0"}


@app.post("/api/markov/verify")
async def verify_iec_tables():
    """
    Lance la vérification vs tableaux IEC 61508-6.
    Retourne les résultats des 14 cas de test du fichier 13.
    """
    from tests.test_verification import run_all_verification_cases
    return run_all_verification_cases()
```

---

## Dépendances (pyproject.toml)

```toml
[project]
name = "sil-engine-api"
version = "1.0.0"
requires-python = ">=3.11"

dependencies = [
    "fastapi>=0.111.0",
    "uvicorn[standard]>=0.30.0",
    "pydantic>=2.7.0",
    "numpy>=1.26.0",
    "scipy>=1.13.0",
    "pandas>=2.2.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "httpx>=0.27.0",
]
```

---

## Lancement

```bash
# Développement
uvicorn main:app --reload --port 8001

# Production
uvicorn main:app --host 0.0.0.0 --port 8001 --workers 4

# Docker
docker build -t sil-engine .
docker run -p 8001:8001 sil-engine
```

---

## Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

COPY . .

EXPOSE 8001
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "2"]
```

---

## Intégration TypeScript → Python

```typescript
// Dans le moteur TS existant (prism-calc-engine)

const MARKOV_BACKEND_URL = process.env.MARKOV_BACKEND_URL ?? 'http://localhost:8001';

export async function computeExact(params: SIFParams): Promise<SIFResult> {
  const threshold = 0.1;
  const lambdaT1 = params.subsystems.reduce((s, sub) => s + sub.lambdaDU, 0) * params.T1;
  
  // Calcul local IEC si non nécessaire
  if (lambdaT1 <= threshold && !params.pst?.enabled) {
    return computeSIF(params);  // moteur TS existant
  }
  
  // Délégation au backend Markov
  const response = await fetch(`${MARKOV_BACKEND_URL}/api/markov/compute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(toMarkovRequest(params)),
    signal: AbortSignal.timeout(30_000)  // 30s timeout
  });
  
  if (!response.ok) {
    const err = await response.text();
    throw new Error(`Markov backend error: ${err}`);
  }
  
  return fromMarkovResponse(await response.json());
}
```
