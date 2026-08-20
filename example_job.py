"""Run one cancellation job without starting the web service."""

from uuid import UUID

from appointment_workflow import AppointmentUpdate, process_appointment
from infrai_logs import InfraiLogs


def main() -> None:
    update = AppointmentUpdate(
        appointment_id=UUID("7af8d943-3d31-44d7-ac58-762b64012351"),
        job_id=UUID("e4be716e-526b-4f6d-aa86-057b80e39c1c"),
        status="cancelled",
        clinic_code="north-02",
    )
    result = process_appointment(update, InfraiLogs())
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
