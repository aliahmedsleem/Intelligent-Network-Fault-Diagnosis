from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .engine import diagnose_fault, evaluate
from .models import FaultExperiment, TrafficExperiment

app = FastAPI(title="Intelligent Network Fault Diagnosis API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/api/health")
def health():
    return {"status": "ok", "engine": "analytical-baseline", "version": "0.1.0"}


@app.post("/api/experiments/analytical")
def experiment(payload: TrafficExperiment):
    try:
        return evaluate(payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/experiments/link-fault")
def fault(payload: FaultExperiment):
    try:
        return diagnose_fault(payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

from .measurements import MeasuredRun, analyze


@app.post("/api/measurements/analyze")
def analyze_measurements(payload: MeasuredRun):
    """Analyze imported Mininet measurements; never launch privileged commands."""
    return analyze(payload)

from .localization import LocalizationRequest, localize


@app.post("/api/localization/analyze")
def analyze_localization(payload: LocalizationRequest):
    try:
        return localize(payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

from .probe_pipeline import ProbeBatch, analyze_batch


@app.post("/api/localization/probe-batch")
def analyze_measured_probe_batch(payload: ProbeBatch):
    try:
        return analyze_batch(payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

from .remediation import RemediationReport, analyze_remediation


@app.post("/api/remediation/analyze")
def analyze_remediation_report(payload: RemediationReport):
    return analyze_remediation(payload)

from .lifecycle import LifecycleRequest, plan_lifecycle


@app.post("/api/lifecycle/plan")
def create_lifecycle_plan(payload: LifecycleRequest):
    try:
        return plan_lifecycle(payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

from .evaluation import EvaluationDataset, evaluate_dataset


@app.post("/api/evaluation/localization")
def evaluate_localization_trials(payload: EvaluationDataset):
    try:
        return evaluate_dataset(payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

from .closed_loop import ClosedLoopArtifact, inspect_closed_loop


@app.post("/api/lifecycle/inspect")
def inspect_measured_lifecycle(payload: ClosedLoopArtifact):
    try:
        return inspect_closed_loop(payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

from .medium_models import MediumBudgetRequest, calculate_budget


@app.post("/api/models/link-budget")
def evaluate_medium_budget(payload: MediumBudgetRequest):
    return calculate_budget(payload)

from .ns3_results import Ns3WifiRun, inspect_ns3_run


@app.post("/api/ns3/wifi/inspect")
def inspect_ns3_wifi_result(payload: Ns3WifiRun):
    return inspect_ns3_run(payload)

from .gns3_adapter import router as gns3_router
app.include_router(gns3_router)
