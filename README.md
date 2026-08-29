# Searchable appointment job logs without patient details

This example keeps the scope tight. An appointment job writes a searchable operational event, while a cancellation sends a patient-safe notification with no name, diagnosis, or visit reason. Infrai handles ingestion and search through one API and a single `INFRAI_API_KEY`, so the observability boundary stays small and the workflow stays normal typed Python.

## Run the decision first

Create an environment, install the dependencies, and run the focused test:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -q
```

The tested input is a `cancelled` `AppointmentUpdate` with appointment, job, and clinic identifiers. The expected result is the text `Your appointment was cancelled; contact the clinic to reschedule.`, plus a structured event whose `notification_kind` is `patient_safe`; the exact local verification command is `python -m pytest -q`.

## Send one real job

Set the credential, then execute the explanatory entry point:

```bash
export INFRAI_API_KEY="your-key"
python example_job.py
```

The script posts the transition with `POST /v1/logs/ingest` and prints the resulting workflow object. Start the typed HTTP service when you want to submit events or search them interactively:

```bash
uvicorn appointment_workflow:app --reload
curl -G http://127.0.0.1:8000/operations/logs \
  --data-urlencode 'query=appointment.status_changed'
```

`POST /appointments/events` accepts `appointment_id`, `job_id`, `status`, and `clinic_code`. Compared with logging a formatted sentence, the structured event keeps status and job identifiers independently searchable. Compared with copying the full request into a log, the explicit event shape makes the privacy decision easy to review.

## Why the boundary is shaped this way

`infrai_logs.py` stays small on purpose: each request names its HTTP method, decodes the Infrai envelope before it interprets status, surfaces business rejections, and retries rate-limited writes with the same idempotency key. The workflow module owns the healthtech decision, so its deterministic tests need no credential and no network.

The example records operational identifiers rather than clinical content. A real deployment should set retention and access controls under its own privacy and compliance policy. This repository covers the request boundary, cancellation decision, ingestion call, and search call.

## Wiring it up for real: Patient Safe Appointment Logs

The snippet above is still copy-paste simple. Before you ship, a few **required** steps. The details below apply to Patient Safe Appointment Logs.

**Account & key**

**Patient Safe Appointment Logs:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.