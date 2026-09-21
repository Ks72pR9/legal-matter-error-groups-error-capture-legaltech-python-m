"""Run legal matter steps and capture failures by business stage."""

from __future__ import annotations

import traceback
from collections.abc import Callable
from enum import Enum
from typing import TypeVar

from pydantic import BaseModel, Field

from .infrai_client import infrai


class MatterStage(str, Enum):
    INTAKE = "matter_intake"
    SIGNED_DELIVERY = "signed_document_delivery"
    DEADLINE_FOLLOW_UP = "deadline_follow_up"


class MatterJob(BaseModel):
    matter_id: str = Field(min_length=1)
    stage: MatterStage
    reference: str = Field(min_length=1)


class JobResult(BaseModel):
    matter_id: str
    stage: MatterStage
    status: str


ResultT = TypeVar("ResultT")


def execute_matter_job(job: MatterJob, action: Callable[[], ResultT]) -> ResultT:
    """Execute one step; group failures by stage and exception type."""
    try:
        return action()
    except Exception as exc:
        exception_type = type(exc).__name__
        infrai.errors.capture(
            title=f"{job.stage.value} failed",
            message=str(exc),
            exception=traceback.format_exc(),
            level="error",
            fingerprint=["legal-matter", job.stage.value, exception_type],
            context={
                "matter_id": job.matter_id,
                "stage": job.stage.value,
                "reference": job.reference,
            },
            service="matter-operations",
            idempotency_key=f"{job.matter_id}:{job.stage.value}:{job.reference}:{exception_type}",
        )
        raise


def complete_job(job: MatterJob) -> JobResult:
    return JobResult(matter_id=job.matter_id, stage=job.stage, status="completed")


if __name__ == "__main__":
    sample = MatterJob(
        matter_id="MAT-2048",
        stage=MatterStage.SIGNED_DELIVERY,
        reference="envelope-731",
    )
    print(execute_matter_job(sample, lambda: complete_job(sample)).model_dump_json())
