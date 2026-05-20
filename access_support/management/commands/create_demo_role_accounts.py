from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from academic_core.models import AcademicProgram, Campus, Faculty, StudyPlan
from access_support.models import StudentProfile, User
from teaching.models import Teacher


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
    help = "Crea una cuenta demo por cada rol funcional y guarda las credenciales en docs/credenciales_demo_roles.md."

    @transaction.atomic
    def handle(self, *args, **options):
        campus, _ = Campus.objects.get_or_create(name="Sede Demo")
        faculty, _ = Faculty.objects.get_or_create(
            name="Facultad Demo",
            defaults={"campus": campus},
        )
        program, _ = AcademicProgram.objects.get_or_create(
            name="Ingenieria de Software Demo",
            defaults={"code": "IS-DEMO", "faculty": faculty, "campus": campus},
        )
        StudyPlan.objects.get_or_create(
            program=program,
            version="2026-1",
            defaults={"description": "Plan demo para probar vistas por rol."},
        )

        for account in DEMO_ACCOUNTS:
            user, _ = User.objects.get_or_create(email=account["email"])
            user.role = account["role"]
            user.is_staff = account.get("is_staff", False)
            user.is_active = True
            user.set_password(account["password"])
            user.save()

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
                Teacher.objects.get_or_create(
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

        self._write_credentials_file()
        self.stdout.write(self.style.SUCCESS("Cuentas demo creadas/actualizadas correctamente."))
        self.stdout.write("Credenciales guardadas en docs/credenciales_demo_roles.md")

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
