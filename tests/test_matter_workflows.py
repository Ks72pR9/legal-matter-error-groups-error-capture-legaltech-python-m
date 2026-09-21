from unittest.mock import patch

import pytest

from src.matter_workflows import MatterJob, MatterStage, execute_matter_job


def test_failures_group_by_stage_and_exception_type() -> None:
    intake = MatterJob(matter_id="MAT-7", stage=MatterStage.INTAKE, reference="form-2")
    delivery = MatterJob(
        matter_id="MAT-7",
        stage=MatterStage.SIGNED_DELIVERY,
        reference="envelope-9",
    )

    with patch("src.matter_workflows.infrai.errors.capture") as capture:
        for job in (intake, intake, delivery):
            with pytest.raises(ValueError, match="missing client name"):
                execute_matter_job(
                    job,
                    lambda: (_ for _ in ()).throw(ValueError("missing client name")),
                )

    fingerprints = [call.kwargs["fingerprint"] for call in capture.call_args_list]
    assert fingerprints[0] == fingerprints[1]
    assert fingerprints[0] != fingerprints[2]
    assert fingerprints[0] == ["legal-matter", "matter_intake", "ValueError"]
    assert capture.call_args_list[0].kwargs["context"]["matter_id"] == "MAT-7"
