import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project_planner.settings")
django.setup()

from django.db import transaction

from academic_core.models import AcademicTerm
from scheduling_enrollment.models import EnrollmentQueue
from scheduling_enrollment.services.scheduling_service import (
    apply_semester_schedule_run,
    generate_semester_schedule_options,
    get_run_assignment_summary,
)


class RollbackCheck(Exception):
    pass


def main():
    term = AcademicTerm.objects.get(name="2026-2")
    try:
        with transaction.atomic():
            run = generate_semester_schedule_options(term_id=term.id, auto_apply_best=False)
            option = apply_semester_schedule_run(run)
            summary = get_run_assignment_summary(run)
            print(
                "Prueba rollback:",
                f"run={run.id}",
                f"opcion={option.rank}",
                f"pendientes={summary['waiting_total']}",
                f"asignadas={summary['assigned_total']}",
            )
            for course in summary["pending_by_course"]:
                print(
                    "Pendiente:",
                    course["code"],
                    course["name"],
                    course["pending"],
                    course["reason"],
                )
            raise RollbackCheck()
    except RollbackCheck:
        pass

    waiting = EnrollmentQueue.objects.filter(term=term, status="waiting").count()
    print(f"Solicitudes waiting conservadas en base: {waiting}")


if __name__ == "__main__":
    main()
