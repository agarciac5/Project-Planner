from datetime import date, time
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from academic_core.models import (
    AcademicProgram,
    AcademicTerm,
    Campus,
    Course,
    Faculty,
    StudyPlan,
)
from access_support.models import StudentProfile, User
from classrooms.models import Classroom, TimeSlot
from scheduling_enrollment.models import EnrollmentQueue
from teaching.models import Availability, ContractRule, Teacher


DEMO_ACCOUNTS = [
    {
        "role": "student",
        "label": "Estudiante",
        "email": "estudiante.demo@uniminuto.edu.co",
        "password": "Estudiante2026!",
    },
    {
        "role": "teacher",
        "label": "Docente",
        "email": "docente.demo@uniminuto.edu.co",
        "password": "Docente2026!",
    },
    {
        "role": "admin",
        "label": "Administrador",
        "email": "admin.demo@uniminuto.edu.co",
        "password": "Admin2026!",
        "is_staff": True,
    },
    {
        "role": "coordinator",
        "label": "Director academico",
        "email": "director.demo@uniminuto.edu.co",
        "password": "Director2026!",
        "is_staff": True,
    },
]


class Command(BaseCommand):
    help = "Prepara cuentas y datos ficticios para una demostracion local."

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError(
                "Las cuentas demo solo pueden crearse cuando DJANGO_DEBUG=True."
            )

        campus, _ = Campus.objects.get_or_create(name="Sede Demo")
        faculty, _ = Faculty.objects.get_or_create(
            name="Facultad Demo",
            defaults={"campus": campus},
        )
        program, _ = AcademicProgram.objects.get_or_create(
            name="Ingenieria de Software Demo",
            defaults={"code": "IS-DEMO", "faculty": faculty, "campus": campus},
        )
        study_plan, _ = StudyPlan.objects.get_or_create(
            program=program,
            version="2026-1",
            defaults={"description": "Plan demo para probar vistas por rol."},
        )

        users_by_role = {}
        for account in DEMO_ACCOUNTS:
            user, _ = User.objects.get_or_create(email=account["email"])
            user.role = account["role"]
            user.is_staff = account.get("is_staff", False)
            user.is_active = True
            user.set_password(account["password"])
            user.save()
            users_by_role[account["role"]] = user

            if account["role"] == "student":
                StudentProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        "student_code": "EST-DEMO-001",
                        "full_name": "Estudiante Demo",
                        "document_type": "CC",
                        "document_number": "1000000001",
                        "program": program,
                        "faculty": faculty,
                        "campus": campus,
                        "level": "Pregrado",
                        "jornada": "Nocturna",
                        "address": "Direccion demo",
                    },
                )

            if account["role"] == "teacher":
                teacher, _ = Teacher.objects.get_or_create(
                    user=user,
                    defaults={
                        "teacher_id": "DOC-DEMO-001",
                        "first_name": "Docente",
                        "last_name": "Demo",
                        "program": program,
                        "faculty": faculty,
                        "campus": campus,
                        "is_active": True,
                    },
                )

        self._create_planner_demo_data(
            campus=campus,
            faculty=faculty,
            program=program,
            study_plan=study_plan,
            teacher=teacher,
            demo_student=users_by_role["student"],
        )
        self._write_credentials_file()
        self.stdout.write(
            self.style.SUCCESS(
                "Cuentas y datos demo creados/actualizados correctamente."
            )
        )
        self.stdout.write("Credenciales guardadas en docs/credenciales_demo_roles.md")

    def _create_planner_demo_data(
        self,
        *,
        campus,
        faculty,
        program,
        study_plan,
        teacher,
        demo_student,
    ):
        active_term = AcademicTerm.objects.filter(active=True).first()
        term, _ = AcademicTerm.objects.get_or_create(
            name="2026-2 Demo",
            defaults={
                "start_date": date(2026, 7, 20),
                "end_date": date(2026, 11, 28),
                "active": active_term is None,
            },
        )

        contract, _ = ContractRule.objects.get_or_create(
            contract_type="Tiempo completo demo",
            defaults={
                "min_teaching_hours": 0,
                "max_teaching_hours": 24,
                "max_advisory_hours": 8,
                "max_research_hours": 8,
                "max_total_hours": 40,
            },
        )
        teacher.program = program
        teacher.faculty = faculty
        teacher.campus = campus
        teacher.contract = contract
        teacher.is_active = True
        teacher.save(
            update_fields=[
                "program",
                "faculty",
                "campus",
                "contract",
                "is_active",
            ]
        )

        courses = []
        for code, name, semester in [
            ("DEMO101", "Fundamentos de Programacion", 1),
            ("DEMO201", "Bases de Datos", 2),
        ]:
            course, _ = Course.objects.get_or_create(
                code=code,
                defaults={
                    "name": name,
                    "credits": 3,
                    "semester": semester,
                    "study_plan": study_plan,
                },
            )
            courses.append(course)
        teacher.qualified_courses.add(*courses)

        for classroom_id, name, capacity, classroom_type in [
            ("AULA-DEMO-1", "Aula Demo 1", 30, "SALON"),
            ("LAB-DEMO-1", "Laboratorio Demo", 25, "SISTEMAS"),
        ]:
            Classroom.objects.get_or_create(
                classroom_id=classroom_id,
                defaults={
                    "name": name,
                    "block": 1,
                    "campus": campus,
                    "capacity": capacity,
                    "classroom_type": classroom_type,
                    "is_active": True,
                },
            )

        for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
            Availability.objects.get_or_create(
                teacher=teacher,
                day=day,
                start_time=time(7, 0),
                end_time=time(17, 0),
            )
            for start, end in [
                (time(7, 0), time(8, 30)),
                (time(8, 30), time(10, 0)),
                (time(10, 0), time(11, 30)),
                (time(14, 0), time(15, 30)),
            ]:
                TimeSlot.objects.get_or_create(
                    day=day,
                    start_time=start,
                    end_time=end,
                )

        students = [demo_student]
        for index in range(2, 9):
            email = f"estudiante.demo{index}@uniminuto.edu.co"
            student, _ = User.objects.get_or_create(email=email)
            student.role = "student"
            student.is_active = True
            student.set_password("Estudiante2026!")
            student.save()
            StudentProfile.objects.get_or_create(
                user=student,
                defaults={
                    "student_code": f"EST-DEMO-{index:03d}",
                    "full_name": f"Estudiante Demo {index}",
                    "document_type": "CC",
                    "document_number": f"10000000{index:02d}",
                    "program": program,
                    "faculty": faculty,
                    "campus": campus,
                    "level": "Pregrado",
                    "jornada": "Nocturna",
                    "address": "Direccion demo",
                },
            )
            students.append(student)

        for student in students:
            for course in courses:
                EnrollmentQueue.objects.get_or_create(
                    student=student,
                    course=course,
                    term=term,
                    defaults={"status": "waiting"},
                )

    def _write_credentials_file(self):
        docs_dir = Path("docs")
        docs_dir.mkdir(exist_ok=True)
        lines = [
            "# Credenciales demo por rol",
            "",
            "Estas cuentas son solo para probar las vistas separadas por rol en ambiente local.",
            "No deben usarse en produccion y las contrasenas deben cambiarse antes de una entrega real.",
            "",
            "| Rol | Correo | Contrasena |",
            "|---|---|---|",
        ]
        for account in DEMO_ACCOUNTS:
            lines.append(
                f"| {account['label']} | `{account['email']}` | `{account['password']}` |"
            )
        lines.extend(
            [
                "",
                "## Como crearlas en la base local",
                "",
                "```bash",
                "python manage.py migrate",
                "python manage.py create_demo_role_accounts",
                "```",
            ]
        )
        (docs_dir / "credenciales_demo_roles.md").write_text("\n".join(lines), encoding="utf-8")
