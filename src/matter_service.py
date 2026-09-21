"""HTTP boundary for matter operations."""

from fastapi import FastAPI, HTTPException

from .infrai_client import InfraiError
from .matter_workflows import JobResult, MatterJob, complete_job, execute_matter_job


service = FastAPI(title="Matter operations")


@service.post("/matter-jobs", response_model=JobResult)
def run_job(job: MatterJob) -> JobResult:
    try:
        return execute_matter_job(job, lambda: complete_job(job))
    except InfraiError as exc:
        client_status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(
            status_code=client_status,
            detail={"code": exc.code, "message": str(exc)},
        ) from exc
