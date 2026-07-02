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
from scheduling_enrollment.models import EnrollmentQueue, TeacherActivity
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

        full_time_contract, _ = ContractRule.objects.update_or_create(
            contract_type="Tiempo completo demo",
            defaults={
                "min_teaching_hours": 8,
                "max_teaching_hours": 12,
                "max_advisory_hours": 8,
                "max_research_hours": 8,
                "max_total_hours": 40,
            },
        )
        adjunct_contract, _ = ContractRule.objects.update_or_create(
            contract_type="Catedra demo",
            defaults={
                "min_teaching_hours": 3,
                "max_teaching_hours": 6,
                "max_advisory_hours": 2,
                "max_research_hours": 0,
                "max_total_hours": 8,
            },
        )

        courses = []
        for code, name, semester, credits in [
            ("DEMO101", "Fundamentos de Programacion", 1, 3),
            ("DEMO201", "Bases de Datos", 2, 3),
            ("DEMO301", "Estructuras de Datos", 3, 4),
            ("DEMO401", "Ingenieria de Software", 4, 3),
            ("DEMO501", "Analitica de Datos", 5, 3),
        ]:
            course, _ = Course.objects.update_or_create(
                code=code,
                defaults={
                    "name": name,
                    "credits": credits,
                    "semester": semester,
                    "study_plan": study_plan,
                },
            )
            courses.append(course)

        teacher_specs = [
            {
                "email": "docente.demo@uniminuto.edu.co",
                "teacher_id": "DOC-DEMO-001",
                "first_name": "Laura",
                "last_name": "Martinez",
                "contract": full_time_contract,
                "courses": ["DEMO101", "DEMO301"],
                "availability": [
                    ("Monday", time(7, 0), time(11, 30)),
                    ("Tuesday", time(7, 0), time(11, 30)),
                ],
            },
            {
                "email": "docente.demo2@uniminuto.edu.co",
                "teacher_id": "DOC-DEMO-002",
                "first_name": "Carlos",
                "last_name": "Ramirez",
                "contract": full_time_contract,
                "courses": ["DEMO201", "DEMO301", "DEMO401"],
                "availability": [
                    ("Tuesday", time(8, 30), time(15, 30)),
                    ("Wednesday", time(7, 0), time(15, 30)),
                ],
            },
            {
                "email": "docente.demo3@uniminuto.edu.co",
                "teacher_id": "DOC-DEMO-003",
                "first_name": "Diana",
                "last_name": "Gomez",
                "contract": adjunct_contract,
                "courses": ["DEMO101", "DEMO401"],
                "availability": [
                    ("Wednesday", time(7, 0), time(11, 30)),
                    ("Thursday", time(7, 0), time(11, 30)),
                ],
            },
            {
                "email": "docente.demo4@uniminuto.edu.co",
                "teacher_id": "DOC-DEMO-004",
                "first_name": "Andres",
                "last_name": "Lopez",
                "contract": adjunct_contract,
                "courses": ["DEMO201", "DEMO501"],
                "availability": [
                    ("Monday", time(10, 0), time(15, 30)),
                    ("Thursday", time(10, 0), time(15, 30)),
                ],
            },
        ]
        teachers = []
        courses_by_code = {course.code: course for course in courses}
        for spec in teacher_specs:
            teacher_user, _ = User.objects.get_or_create(email=spec["email"])
            teacher_user.role = "teacher"
            teacher_user.is_active = True
            teacher_user.set_password("Docente2026!")
            teacher_user.save()

            current_teacher, _ = Teacher.objects.update_or_create(
                teacher_id=spec["teacher_id"],
                defaults={
                    "user": teacher_user,
                    "first_name": spec["first_name"],
                    "last_name": spec["last_name"],
                    "program": program,
                    "faculty": faculty,
                    "campus": campus,
                    "contract": spec["contract"],
                    "is_active": True,
                },
            )
            current_teacher.qualified_courses.set(
                courses_by_code[code] for code in spec["courses"]
            )
            current_teacher.availabilities.all().delete()
            for day, start_time, end_time in spec["availability"]:
                Availability.objects.create(
                    teacher=current_teacher,
                    day=day,
                    start_time=start_time,
                    end_time=end_time,
                )
            teachers.append(current_teacher)

        for classroom_id, name, capacity, classroom_type in [
            ("AULA-DEMO-1", "Aula pequena", 18, "SALON"),
            ("AULA-DEMO-2", "Aula mediana", 22, "SALON"),
            ("LAB-DEMO-1", "Laboratorio de sistemas", 28, "SISTEMAS"),
            ("AUD-DEMO-1", "Auditorio demo", 35, "AUDITORIO"),
        ]:
            Classroom.objects.update_or_create(
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

        for day in ["Monday", "Tuesday", "Wednesday", "Thursday"]:
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

        TeacherActivity.objects.filter(term=term, teacher__in=teachers).delete()
        for current_teacher, activity_type, day, start_time, end_time in [
            (teachers[0], "investigacion", "Monday", time(8, 30), time(10, 0)),
            (teachers[1], "asesoria", "Wednesday", time(10, 0), time(11, 30)),
            (teachers[2], "asesoria", "Thursday", time(8, 30), time(10, 0)),
            (teachers[3], "investigacion", "Monday", time(10, 0), time(11, 30)),
        ]:
            TeacherActivity.objects.create(
                teacher=current_teacher,
                term=term,
                activity_type=activity_type,
                day=day,
                start_time=start_time,
                end_time=end_time,
            )

        students = [demo_student]
        for index in range(2, 25):
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

        demand_by_course = {
            "DEMO101": students[:24],
            "DEMO201": students[:20],
            "DEMO301": students[:16],
            "DEMO401": students[8:20],
            "DEMO501": students[16:24],
        }
        for course_code, course_students in demand_by_course.items():
            course = courses_by_code[course_code]
            for student in course_students:
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
