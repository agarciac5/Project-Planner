import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project_planner.settings")
django.setup()

from django.contrib.auth import get_user_model

from access_support.models import StudentProfile
from academic_core.models import AcademicTerm, Course
from scheduling_enrollment.models import EnrollmentQueue


User = get_user_model()

TERM_NAME = "2026-2"
PASSWORD = "Student123*"
REQUESTS_PER_COURSE = 1

COURSE_CODES = [
    "CBASBL021",
    "CBASBL151",
    "ESTA1061",
    "ISOFBL021",
    "ISOFBL031",
    "ISOFBL041",
    "ISOFBL051",
    "ISOFBL073",
    "ISOFBL083",
    "ISOFBL103",
    "ISOFBL123",
    "ISOFBL133",
    "ISOFBL153",
    "ISOFBL163",
    "ISOFBL183",
    "ISOFBL203",
    "ISOFBL213",
    "ISOFBL223",
    "ISOFBL233",
    "ISOFBL243",
    "ISOFBL023",
    "ISOFBL033",
    "ISOFBL043",
    "ISOFBL053",
    "ISOFBL263",
]


def main():
    term = AcademicTerm.objects.get(name=TERM_NAME)
    courses = list(
        Course.objects.filter(code__in=COURSE_CODES)
        .select_related("study_plan__program")
        .order_by("code")
    )
    program = courses[0].study_plan.program
    needed_students = len(courses) * REQUESTS_PER_COURSE

    EnrollmentQueue.objects.filter(
        term=term,
        student__email__startswith="sim.student",
    ).delete()

    students = []
    for index in range(1, needed_students + 1):
        email = f"sim.student{index:03d}@uniminuto.edu.co"
        user, created = User.objects.get_or_create(
            email=email,
            defaults={"role": "student", "is_active": True},
        )
        if created:
            user.set_password(PASSWORD)
        user.role = "student"
        user.is_active = True
        user.save()

        StudentProfile.objects.update_or_create(
            user=user,
            defaults={
                "student_code": f"SIM{index:04d}",
                "full_name": f"Estudiante Simulado {index:03d}",
                "program": program,
                "faculty": program.faculty,
                "campus": program.campus,
                "level": "Pregrado",
                "jornada": "Diurna",
            },
        )
        students.append(user)

    offset = 0
    for course in courses:
        for user in students[offset : offset + REQUESTS_PER_COURSE]:
            EnrollmentQueue.objects.create(
                student=user,
                course=course,
                term=term,
                status="waiting",
            )
        offset += REQUESTS_PER_COURSE

    waiting_total = EnrollmentQueue.objects.filter(term=term, status="waiting").count()
    print(
        f"Demanda liviana creada: {waiting_total} solicitudes waiting "
        f"({REQUESTS_PER_COURSE} por materia) para {term.name}."
    )


if __name__ == "__main__":
    main()
