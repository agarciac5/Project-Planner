import os
from datetime import time

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project_planner.settings")
django.setup()

from django.contrib.auth import get_user_model

from access_support.models import StudentProfile
from academic_core.models import AcademicTerm, Course
from classrooms.models import Classroom
from scheduling_enrollment.models import (
    CourseGroup,
    Enrollment,
    EnrollmentQueue,
    ProposedSchedule,
    ScheduleSession,
    SemesterScheduleAssignment,
    SemesterScheduleOption,
    SemesterScheduleRun,
)
from teaching.models import Teacher


User = get_user_model()

PASSWORD = "Estudiante123*"
TERM_NAME = "2026-2"
COURSE_CODES = ["CBASBL021", "CBASBL151", "ESTA1061", "ISOFBL021", "ISOFBL031"]
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
STARTS = [time(7, 0), time(8, 30), time(10, 0), time(14, 0), time(15, 30)]
ENDS = [time(8, 30), time(10, 0), time(11, 30), time(15, 30), time(17, 0)]


def main():
    term = AcademicTerm.objects.get(name=TERM_NAME)
    courses = list(
        Course.objects.filter(code__in=COURSE_CODES)
        .select_related("study_plan__program")
        .order_by("code")
    )
    if len(courses) != len(COURSE_CODES):
        found = {course.code for course in courses}
        missing = sorted(set(COURSE_CODES) - found)
        raise RuntimeError(f"Faltan materias para la prueba: {', '.join(missing)}")

    program = courses[0].study_plan.program
    classroom = (
        Classroom.objects.filter(is_active=True)
        .exclude(classroom_type="VIRTUAL")
        .order_by("id")
        .first()
    )
    if not classroom:
        raise RuntimeError("No hay aulas activas para crear grupos de prueba.")

    emails = [f"qa.student{i:02d}@uniminuto.edu.co" for i in range(0, 11)]
    old_users = list(User.objects.filter(email__in=emails))
    Enrollment.objects.filter(student__in=old_users).delete()
    EnrollmentQueue.objects.filter(student__in=old_users).delete()
    StudentProfile.objects.filter(user__in=old_users).delete()
    for user in old_users:
        user.delete()

    old_groups = CourseGroup.objects.filter(term=term, nrc__startswith="QA20262")
    old_schedule_ids = list(
        ScheduleSession.objects.filter(group__in=old_groups).values_list(
            "schedule_id", flat=True
        )
    )
    old_groups.delete()
    ProposedSchedule.objects.filter(id__in=old_schedule_ids).delete()
    SemesterScheduleRun.objects.filter(options__summary__qa_seed=True).distinct().delete()

    run = SemesterScheduleRun.objects.create(term=term, status="published")
    option = SemesterScheduleOption.objects.create(
        run=run,
        rank=1,
        score=100.0,
        demand_covered=50,
        demand_total=50,
        sections_opened=len(courses),
        is_best=True,
        selected=True,
        applied=True,
        summary={"qa_seed": True, "description": "Grupos publicados para estudiantes QA"},
    )

    course_groups = []
    schedules_by_teacher = {}
    for index, course in enumerate(courses, start=1):
        teacher = (
            Teacher.objects.filter(is_active=True, qualified_courses=course)
            .order_by("teacher_id")
            .first()
            or Teacher.objects.filter(is_active=True).order_by("teacher_id").first()
        )
        if not teacher:
            raise RuntimeError(f"No hay docente activo para {course.code}.")

        schedule = schedules_by_teacher.get(teacher.id)
        if schedule is None:
            schedule = ProposedSchedule.objects.create(
                teacher=teacher,
                term=term,
                status="approved",
                fitness_score=100.0,
                rank=1,
            )
            schedules_by_teacher[teacher.id] = schedule

        group = CourseGroup.objects.create(
            course=course,
            teacher=teacher,
            term=term,
            nrc=f"QA20262{index:02d}",
            capacity=30,
            is_virtual=False,
        )
        ScheduleSession.objects.create(
            schedule=schedule,
            group=group,
            classroom=classroom,
            day=DAYS[index - 1],
            start_time=STARTS[index - 1],
            end_time=ENDS[index - 1],
        )
        SemesterScheduleAssignment.objects.create(
            option=option,
            course=course,
            teacher=teacher,
            classroom=classroom,
            generated_group=group,
            generated_schedule=schedule,
            section_number=1,
            nrc=group.nrc,
            day=DAYS[index - 1],
            start_time=STARTS[index - 1],
            end_time=ENDS[index - 1],
            students_assigned=10,
            capacity=30,
        )
        course_groups.append((course, group))

    created = []
    for i in range(0, 11):
        email = f"qa.student{i:02d}@uniminuto.edu.co"
        user = User.objects.create_user(
            email=email,
            password=PASSWORD,
            role="student",
            is_active=True,
        )
        StudentProfile.objects.create(
            user=user,
            student_code=f"QA20262{i:02d}",
            full_name=f"Estudiante QA {i:02d}" if i else "Estudiante QA Sin Matricula",
            program=program,
            faculty=program.faculty,
            campus=program.campus,
            level="Pregrado",
            jornada="Diurna",
        )

        enrolled_count = 0
        if i > 0:
            for course, group in course_groups:
                request = EnrollmentQueue.objects.create(
                    student=user,
                    course=course,
                    course_group=group,
                    term=term,
                    status="enrolled",
                )
                Enrollment.objects.create(
                    request=request,
                    student=user,
                    course_group=group,
                    term=term,
                    status="active",
                )
                enrolled_count += 1
        created.append((email, enrolled_count))

    waiting = EnrollmentQueue.objects.filter(term=term, status="waiting").count()
    print(f"Periodo: {term.name} | solicitudes waiting para algoritmo: {waiting}")
    print(f"Run publicado QA: {run.id} | grupos QA: {len(course_groups)}")
    for email, count in created:
        print(f"{email} | {PASSWORD} | materias matriculadas: {count}")


if __name__ == "__main__":
    main()
