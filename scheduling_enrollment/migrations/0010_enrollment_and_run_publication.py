from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("access_support", "0003_alter_studentprofile_document_type"),
        ("academic_core", "0004_alter_academicprogram_id_alter_academicterm_id_and_more"),
        ("scheduling_enrollment", "0009_enrollmentqueue_course_group"),
    ]

    operations = [
        migrations.AlterField(
            model_name="semesterschedulerun",
            name="status",
            field=models.CharField(
                choices=[
                    ("draft", "Borrador"),
                    ("saved", "Guardado"),
                    ("ready_to_publish", "Listo para emitir"),
                    ("published", "Publicado"),
                ],
                default="draft",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="semesterschedulerun",
            name="published_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name="Enrollment",
            fields=[
                (
                    "id",
                    models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID"),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[("active", "Activa"), ("cancelled", "Cancelada")],
                        default="active",
                        max_length=20,
                    ),
                ),
                ("assigned_at", models.DateTimeField(auto_now_add=True)),
                (
                    "course_group",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="enrollments",
                        to="scheduling_enrollment.coursegroup",
                    ),
                ),
                (
                    "request",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="enrollment_record",
                        to="scheduling_enrollment.enrollmentqueue",
                    ),
                ),
                (
                    "student",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="enrollments",
                        to="access_support.user",
                    ),
                ),
                (
                    "term",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="enrollments",
                        to="academic_core.academicterm",
                    ),
                ),
            ],
            options={
                "ordering": ["course_group__course__code", "student__email"],
                "unique_together": {("student", "course_group")},
            },
        ),
    ]
