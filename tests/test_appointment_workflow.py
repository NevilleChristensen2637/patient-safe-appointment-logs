from uuid import UUID

from appointment_workflow import AppointmentUpdate, process_appointment


class RecordingLogs:
    def __init__(self) -> None:
        self.event: dict[str, object] = {}
        self.event_id = ""

    def ingest(self, event: dict[str, object], event_id: str) -> dict[str, object]:
        self.event = event
        self.event_id = event_id
        return {"accepted": True}


def test_cancelled_appointment_emits_safe_notice_and_searchable_event() -> None:
    logs = RecordingLogs()
    update = AppointmentUpdate(
        appointment_id=UUID("7af8d943-3d31-44d7-ac58-762b64012351"),
        job_id=UUID("e4be716e-526b-4f6d-aa86-057b80e39c1c"),
        status="cancelled",
        clinic_code="north-02",
    )

    result = process_appointment(update, logs)

    assert result.notification == (
        "Your appointment was cancelled; contact the clinic to reschedule."
    )
    assert logs.event["status"] == "cancelled"
    assert logs.event["notification_kind"] == "patient_safe"
    assert "patient_name" not in logs.event
    assert logs.event_id == (
        "appointment-7af8d943-3d31-44d7-ac58-762b64012351-cancelled"
    )


def test_confirmed_appointment_does_not_request_notification() -> None:
    logs = RecordingLogs()
    update = AppointmentUpdate(
        appointment_id=UUID("7af8d943-3d31-44d7-ac58-762b64012351"),
        job_id=UUID("e4be716e-526b-4f6d-aa86-057b80e39c1c"),
        status="confirmed",
        clinic_code="north-02",
    )

    result = process_appointment(update, logs)

    assert result.notification is None
    assert logs.event["notification_kind"] == "none"
