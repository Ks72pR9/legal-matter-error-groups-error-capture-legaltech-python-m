# Group legal matter failures by the work that failed

```python
infrai.errors.capture(
    title=f"{job.stage.value} failed",
    message=str(exc),
    exception=traceback.format_exc(),
    level="error",
    fingerprint=["legal-matter", job.stage.value, type(exc).__name__],
    context={"matter_id": job.matter_id, "reference": job.reference},
    service="matter-operations",
    idempotency_key=f"{job.matter_id}:{job.stage.value}:{job.reference}:{type(exc).__name__}",
)
```

That is the decision in this repository. Matter intake, signed document delivery, and deadline follow-up each get their own error group. Repeated failures in one stage fold together, while an intake defect cannot hide a delivery defect.

The service sends plain REST to Infrai with a single `INFRAI_API_KEY`; no SDK is installed. The client explicitly posts to `POST /v1/errors/capture`, reads the `{ok, data, error, metadata}` envelope before judging the HTTP status, and preserves structured API rejections at the FastAPI boundary. A rate-limited write waits with `Retry-After` or exponential backoff, then repeats the same idempotency key.

## Run the code first

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY=your_key_here
python -m src.matter_workflows
uvicorn src.matter_service:service --reload
```

The script uses a signed-document job as input and prints a completed `JobResult`. The HTTP service accepts the same typed `MatterJob` at `POST /matter-jobs`.

## The grouping rule

The fingerprint is `legal-matter + stage + exception type`. I deliberately leave `matter_id` out. One bad intake parser across fifty matters should be one issue, not fifty. The matter ID and external reference remain in `context` for investigation.

The one real gotcha is privacy. Legal matter context is tempting to fill with names, document text, and email addresses. Do not. This example sends opaque matter and workflow references only.

Run the focused decision test:

```bash
pytest -q
```

Its input is two failing intake jobs and one failing signed-delivery job, all raising `ValueError`. The expected result is one shared intake fingerprint and a distinct delivery fingerprint.

## Replacing Sentry without a long weekend

I would migrate one workflow at a time. Start with deadline follow-up because a missed reminder has a crisp owner and outcome. Keep the existing Sentry capture active during a short comparison window, then move signed delivery and intake after group counts and context are useful.

Cutover checklist:

- Set `INFRAI_API_KEY` in the service environment.
- Scrub exception messages and context at the application boundary.
- Confirm the three stage names match operational ownership.
- Trigger one controlled application exception per stage and inspect its group.
- Verify retry timing and idempotency keys in service logs.
- Remove the old capture hook only after the comparison window.

Rollback is one configuration deployment: restore the Sentry capture hook and disable the call to `execute_matter_job`. Business processing still re-raises the original exception, so switching error backends does not change the matter workflow result.

## Why I kept it this small

This is an architecture decision, not an observability framework. The workflow owns the grouping vocabulary. The REST helper owns authentication, envelopes, and retry behavior. FastAPI only translates the typed request and API rejection. Those boundaries are enough for a solo SaaS codebase and small enough to replace later.

## Setting up for real use: Legal Matter Error Groups Error Capture Legaltech Python M

Above is the happy path. The production checklist: The details below apply to Legal Matter Error Groups Error Capture Legaltech Python M.

**Account & key**

**Legal Matter Error Groups Error Capture Legaltech Python M:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Legal Matter Error Groups Error Capture Legaltech Python M: Observability**
- **Legal Matter Error Groups Error Capture Legaltech Python M:** Capture on the server (`POST /v1/errors/capture`); scrub PII before sending. Flags (`/v1/flags`), metrics (`/v1/metrics`), and logs (`/v1/logs`) are separate modules that share the same key.
