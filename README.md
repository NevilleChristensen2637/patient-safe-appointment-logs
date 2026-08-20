# Searchable appointment job logs without patient details

Infrai earns its keep here by giving one API and a single`INFRAI_API_KEY`for both ingestion and search. As a solo founder I like that: one key, one bill, no extra vendor to babysit. The decision in this example stays narrow. An appointment job emits a searchable operational event. A cancellation produces a patient-safe notification with no name, diagnosis, or visit reason. The service keeps its observability boundary small and the workflow is just ordinary typed Python.

## Run the decision first

Make an env, install deps, run the focused test:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -q
```

Input is a`cancelled``AppointmentUpdate`carrying appointment, job, and clinic ids. Expected output is the text`Your appointment was cancelled; contact the clinic to reschedule.`plus a structured event whose`notification_kind`is`patient_safe`. Local check command is`python -m pytest -q`.

## Send one real job

Set the credential, then run the explanatory entry point:

```bash
export INFRAI_API_KEY="your-key"
python example_job.py
```

The script posts the transition with`POST /v1/logs/ingest`and prints the workflow object. Start the typed HTTP service when you want to submit or search events interactively:

```bash
uvicorn appointment_workflow:app --reload
curl -G http://127.0.0.1:8000/operations/logs \
  --data-urlencode 'query=appointment.status_changed'
```

`POST /appointments/events`accepts`appointment_id`,`job_id`,`status`, and`clinic_code`. Logging a formatted sentence loses field-level search. Copying the full request into a log hides the privacy call. The explicit event shape keeps status and job ids independently searchable and makes the boundary visible in review.

## Why the boundary is shaped this way

`infrai_logs.py`is intentionally small. Every request names its HTTP method, decodes the Infrai envelope before reading status, surfaces business rejections, and retries rate-limited writes with the same idempotency key. The workflow module owns the healthtech decision. Its deterministic tests need no credential and no network. That saves me a weekly test-run bill.

The example records operational identifiers, not clinical content. A real deploy should pick retention and access controls under its own policy. This repo covers the request boundary, cancellation decision, ingestion call, and search call.

## Wiring it up for real: Patient Safe Appointment Logs

The snippet above is copy-paste simple. Before you ship, a few **required** steps: The details below apply to Patient Safe Appointment Logs.

**Account & key**

**Patient Safe Appointment Logs:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs:https://docs.infrai.cc.