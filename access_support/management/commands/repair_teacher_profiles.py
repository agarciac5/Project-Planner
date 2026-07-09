from django.core.management.base import BaseCommand

from access_support.models import User
from teaching.models import Teacher


class Command(BaseCommand):
    help = "Vincula perfiles Teacher faltantes a usuarios role=teacher de forma automatica."

    def handle(self, *args, **options):
        repaired = 0
        skipped = 0
        created_profiles = 0

        free_teacher_users = list(
            User.objects.filter(role="teacher").exclude(teacher_profile__isnull=False).order_by("id")
        )

        for teacher in Teacher.objects.filter(user__isnull=True).order_by("id"):
            base = "".join(ch.lower() for ch in str(teacher.teacher_id).strip() if ch.isalnum())
            if not base:
                base = f"teacher{teacher.id}"

            email = f"teacher.{base}@autogen.local"
            suffix = 1
            while User.objects.filter(email=email).exists():
                suffix += 1
                email = f"teacher.{base}.{suffix}@autogen.local"

            try:
                if free_teacher_users:
                    user = free_teacher_users.pop(0)
                else:
                    user = User.objects.create_user(
                        email=email,
                        password="CambioObligatorio2026!",
                        role="teacher",
                    )
                teacher.user = user
                teacher.save(update_fields=["user"])
                repaired += 1
            except Exception:
                skipped += 1

        # Caso inverso: usuarios teacher sin Teacher asociado.
        for user in User.objects.filter(role="teacher").exclude(teacher_profile__isnull=False):
            base = user.email.split("@", 1)[0].upper().replace(".", "").replace("-", "")
            if not base:
                base = str(user.id)
            teacher_id = f"DOC-AUTO-{base[:10]}"
            suffix = 1
            while Teacher.objects.filter(teacher_id=teacher_id).exists():
                suffix += 1
                teacher_id = f"DOC-AUTO-{base[:7]}{suffix:03d}"
            try:
                Teacher.objects.create(
                    user=user,
                    teacher_id=teacher_id,
                    first_name="Docente",
                    last_name="Autogenerado",
                    is_active=True,
                )
                created_profiles += 1
            except Exception:
                skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Repair completado. Vinculados: {repaired}. Perfiles creados: {created_profiles}. Omitidos por error: {skipped}."
            )
        )
