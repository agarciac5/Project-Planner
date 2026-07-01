import random
import time
from datetime import time as clock_time

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.test import Client
from django.urls import reverse

from academic_core.models import AcademicProgram, AcademicTerm, Campus, Course, Faculty, StudyPlan
from access_support.models import StudentProfile
from classrooms.models import Classroom, TimeSlot
from scheduling_enrollment.models import Enrollment, EnrollmentQueue, ScheduleSession
from scheduling_enrollment.services.enrollment_service import get_active_term
from scheduling_enrollment.services.scheduling_service import (
    generate_semester_schedule_options,
    publish_semester_schedule_run,
)
from teaching.models import Availability, ContractRule, Teacher


class Command(BaseCommand):
    help = "Prueba el flujo estudiante -> matricula -> algoritmo genetico -> horario publicado."

    def add_arguments(self, parser):
        parser.add_argument(
            "--keep-data",
            action="store_true",
            help="Conserva los datos de prueba creados. Por defecto se hace rollback.",
        )

    def handle(self, *args, **options):
        keep_data = options["keep_data"]

        try:
            with transaction.atomic():
                summary = self._run_flow()
                self._print_summary(summary, keep_data)
                if not keep_data:
                    transaction.set_rollback(True)
        except Exception as exc:
            raise CommandError(f"Flujo fallido: {exc}") from exc

    def _run_flow(self):
        suffix = int(time.time())
        password = "ClaveSegura123"
        email = f"test1.flow.{suffix}@uniminuto.edu.co"

        campus = Campus.objects.create(name=f"Campus Test1 {suffix}")
        faculty = Faculty.objects.create(name=f"Facultad Test1 {suffix}", campus=campus)
        program = AcademicProgram.objects.create(
            name=f"Ingenieria Test1 {suffix}",
            code=f"T1-{suffix}",
            faculty=faculty,
            campus=campus,
        )
        study_plan = StudyPlan.objects.create(
            program=program,
            version=f"test1-{suffix}",
            description="Plan temporal para probar flujo completo.",
        )
        course = Course.objects.create(
            name="Materia Flujo Test1",
            code=f"T1F{str(suffix)[-6:]}",
            credits=3,
            semester=1,
            study_plan=study_plan,
        )

        term = get_active_term()
        if term is None:
            term = AcademicTerm.objects.create(
                name=f"Periodo Test1 {suffix}",
                start_date="2026-01-15",
                end_date="2026-05-15",
                active=True,
            )

        contract = ContractRule.objects.create(
            contract_type=f"Contrato Test1 {suffix}",
            min_teaching_hours=0,
            max_teaching_hours=12,
            max_advisory_hours=2,
            max_research_hours=2,
            max_total_hours=16,
        )
        teacher = Teacher.objects.create(
            teacher_id=f"T1DOC{str(suffix)[-6:]}",
            first_name="Docente",
            last_name="Test1",
            program=program,
            faculty=faculty,
            campus=campus,
            contract=contract,
            is_active=True,
        )
        teacher.qualified_courses.add(course)
        Availability.objects.create(
            teacher=teacher,
            day="Monday",
            start_time=clock_time(7, 0),
            end_time=clock_time(12, 0),
        )
        classroom = Classroom.objects.create(
            classroom_id=f"T1A{str(suffix)[-6:]}",
            name="Aula Test1",
            block=1,
            campus=campus,
            capacity=30,
            classroom_type="SALON",
            is_active=True,
        )
        TimeSlot.objects.get_or_create(
            day="Monday",
            start_time=clock_time(7, 0),
            end_time=clock_time(8, 30),
        )

        client = Client()
        self._assert_status(client.get(reverse("register")), 200, "GET registro")
        response = client.post(
            reverse("register"),
            {"email": email, "password": password, "confirm": password},
        )
        self._assert_redirect(response, reverse("student_profile_setup"), "POST registro")

        user = get_user_model().objects.get(email=email)
        response = client.post(
            reverse("student_profile_setup"),
            {
                "full_name": "Estudiante Flujo Test1",
                "document_type": "CC",
                "document_number": str(suffix),
                "address": "Direccion Test1",
                "program": program.id,
                "faculty": "",
                "campus": "",
                "level": "Pregrado",
                "jornada": "Diurna",
            },
        )
        self._assert_redirect(response, reverse("profile"), "POST perfil estudiantil")
        profile = StudentProfile.objects.get(user=user)

        self._assert_status(client.get(reverse("enrollment")), 200, "GET matricula")
        response = client.post(reverse("enrollment"), {"course_id": course.id})
        self._assert_redirect(response, reverse("enrollment"), "POST matricula")
        request = EnrollmentQueue.objects.get(student=user, course=course, term=term)
        if request.status != "waiting":
            raise AssertionError("La solicitud no quedo en waiting antes del algoritmo.")

        random.seed(7)
        run = generate_semester_schedule_options(
            term.id,
            auto_apply_best=True,
            course_ids={course.id},
        )
        if run is None:
            raise AssertionError("El algoritmo no genero plan semestral.")
        run.refresh_from_db()
        if run.status == "ready_to_publish":
            publish_semester_schedule_run(run)
            run.refresh_from_db()

        request.refresh_from_db()
        enrollment = Enrollment.objects.filter(
            student=user,
            course_group__course=course,
            term=term,
            status="active",
        ).first()
        if enrollment is None:
            raise AssertionError("El estudiante no quedo asignado a un grupo activo.")
        if request.status != "enrolled":
            raise AssertionError("La solicitud no cambio a enrolled.")
        if not ScheduleSession.objects.filter(group=enrollment.course_group).exists():
            raise AssertionError("El grupo asignado no tiene sesiones de horario.")

        response = client.get(reverse("my_student_schedule"))
        self._assert_status(response, 200, "GET mi horario")
        content = response.content.decode("utf-8", errors="ignore")
        if course.code not in content:
            raise AssertionError("Mi horario no muestra la materia asignada.")

        return {
            "email": email,
            "program": profile.program.name,
            "student_code": profile.student_code,
            "term": term.name,
            "course": f"{course.code} - {course.name}",
            "run_status": run.status,
            "queue_status": request.status,
            "group": enrollment.course_group.nrc or f"Grupo {enrollment.course_group_id}",
            "sessions": ScheduleSession.objects.filter(group=enrollment.course_group).count(),
        }

    def _assert_status(self, response, expected_status, label):
        if response.status_code != expected_status:
            raise AssertionError(f"{label}: esperado {expected_status}, recibido {response.status_code}.")

    def _assert_redirect(self, response, expected_url, label):
        if response.status_code != 302 or response.url != expected_url:
            raise AssertionError(
                f"{label}: redireccion esperada a {expected_url}, "
                f"recibido {response.status_code} -> {getattr(response, 'url', '')}."
            )

    def _print_summary(self, summary, keep_data):
        self.stdout.write(self.style.SUCCESS("Flujo completo OK."))
        for key, value in summary.items():
            self.stdout.write(f"{key}: {value}")
        if keep_data:
            self.stdout.write(self.style.WARNING("Datos de prueba conservados en la base local."))
        else:
            self.stdout.write("Rollback aplicado: la base local queda sin estos datos de prueba.")
