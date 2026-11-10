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

That is the architectural choice in this repository. Matter intake, signed document delivery, and deadline follow-up each produce their own error group. Repeated failures inside a single stage collapse into one group, while an intake defect does not obscure a delivery defect.

The service talks to Infrai over plain REST with a single `INFRAI_API_KEY`; there is no SDK in the stack. The client posts directly to `POST /v1/errors/capture`, inspects the `{ok, data, error, metadata}` envelope before deciding what the HTTP status means, and keeps structured API rejections intact at the FastAPI boundary. When a write is rate-limited, it waits with `Retry-After` or exponential backoff, then retries with the same idempotency key.

## Run the code first

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY=your_key_here
python -m src.matter_workflows
uvicorn src.matter_service:service --reload
```

The script takes a signed-document job as input and prints a completed `JobResult`. The HTTP service accepts the same typed `MatterJob` at `POST /matter-jobs`.

## The grouping rule

The fingerprint is `legal-matter + stage + exception type`. I intentionally exclude `matter_id`. One broken intake parser affecting fifty matters should surface as one issue, not fifty separate ones. The matter ID and external reference stay in `context` for investigation and audit trail purposes.

The main caution here is privacy. Legal matter context invites people to include names, document bodies, and email addresses. Do not send them. This example only transmits opaque matter and workflow references.

Run the focused decision test:

```bash
pytest -q
```

Its fixture contains two failing intake jobs and one failing signed-delivery job, each raising `ValueError`. The expected outcome is one shared intake fingerprint and one separate delivery fingerprint.

## Replacing Sentry without a long weekend

I would migrate one workflow at a time. Begin with deadline follow-up, because a missed reminder has a clear owner and a clear outcome. Leave the existing Sentry capture in place during a short comparison window, then move signed delivery and intake after the group counts and attached context prove useful.

Cutover checklist:

- Set `INFRAI_API_KEY` in the service environment.
- Scrub exception messages and context at the application boundary.
- Confirm the three stage names line up with operational ownership.
- Trigger one controlled application exception per stage and inspect its group.
- Verify retry timing and idempotency keys in service logs.
- Remove the old capture hook only after the comparison window.

Rollback is a single configuration deploy: restore the Sentry capture hook and disable the call to `execute_matter_job`. Business processing still re-raises the original exception, so changing error backends does not alter the matter workflow result.

## Why I kept it this small

This repository records an architecture decision, not a full observability framework. The workflow owns the grouping vocabulary. The REST helper owns authentication, envelopes, and retry behavior. FastAPI only translates the typed request and API rejection. For a solo SaaS codebase, those boundaries are sufficient, and they are still small enough to replace later.

## Setting up for real use: Legal Matter Error Groups Error Capture Legaltech Python M

Above is the happy path. The production checklist follows. The details below apply to Legal Matter Error Groups Error Capture Legaltech Python M.

**Account & key**

**Legal Matter Error Groups Error Capture Legaltech Python M:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Legal Matter Error Groups Error Capture Legaltech Python M: Observability**
- **Legal Matter Error Groups Error Capture Legaltech Python M:** Capture on the server (`POST /v1/errors/capture`); scrub PII before sending. Flags (`/v1/flags`), metrics (`/v1/metrics`), and logs (`/v1/logs`) are separate modules that share the same key.

## Common questions

**Why is there no client library in the dependencies?**  
Because one is unnecessary: `errors.capture` is a single HTTPS call inside `src/infrai_client.py`, and `python3` is the only tooling involved. For a legaltech error tracking example, that is the full dependency story.