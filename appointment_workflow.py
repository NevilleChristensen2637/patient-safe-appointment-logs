"""Typed appointment workflow service and patient-safe notification decision."""

from __future__ import annotations

from typing import Literal, Protocol
from uuid import UUID

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from infrai_logs import InfraiError, InfraiLogs


class AppointmentUpdate(BaseModel):
    appointment_id: UUID
    job_id: UUID
    status: Literal["confirmed", "rescheduled", "cancelled"]
    clinic_code: str = Field(min_length=2, max_length=32)


class WorkflowResult(BaseModel):
    appointment_id: UUID
    status: str
    notification: str | None


class LogWriter(Protocol):
    def ingest(self, event: dict[str, object], event_id: str) -> dict[str, object]: ...


def process_appointment(update: AppointmentUpdate, logs: LogWriter) -> WorkflowResult:
    """Record the transition and reveal only a non-identifying cancellation notice."""
    notification = (
        "Your appointment was cancelled; contact the clinic to reschedule."
        if update.status == "cancelled"
        else None
    )
    event_id = f"appointment-{update.appointment_id}-{update.status}"
    logs.ingest(
        {
            "event_id": event_id,
            "event": "appointment.status_changed",
            "level": "info",
            "appointment_id": str(update.appointment_id),
            "job_id": str(update.job_id),
            "clinic_code": update.clinic_code,
            "status": update.status,
            "notification_kind": "patient_safe" if notification else "none",
        },
        event_id,
    )
    return WorkflowResult(
        appointment_id=update.appointment_id,
        status=update.status,
        notification=notification,
    )


app = FastAPI(title="Appointment operations logger")


@app.post("/appointments/events", response_model=WorkflowResult)
def appointment_event(update: AppointmentUpdate) -> WorkflowResult:
    try:
        return process_appointment(update, InfraiLogs())
    except InfraiError as exc:
        status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(status_code=status, detail=exc.detail) from exc


class LogSearch(BaseModel):
    query: str = Field(min_length=1, max_length=200)


@app.get("/operations/logs")
def search_logs(query: str) -> dict[str, object]:
    request = LogSearch(query=query)
    try:
        return InfraiLogs().search(request.query)
    except InfraiError as exc:
        status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(status_code=status, detail=exc.detail) from exc
