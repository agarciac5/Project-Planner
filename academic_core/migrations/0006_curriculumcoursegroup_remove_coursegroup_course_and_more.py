from datetime import timedelta

from django.db import migrations, models


def normalize_academic_data(apps, schema_editor):
    AcademicTerm = apps.get_model("academic_core", "AcademicTerm")
    StudyPlan = apps.get_model("academic_core", "StudyPlan")
    CurriculumCourseGroup = apps.get_model(
        "academic_core", "CurriculumCourseGroup"
    )

    active_terms = list(
        AcademicTerm.objects.filter(active=True).order_by("-start_date", "-id")
    )
    if len(active_terms) > 1:
        AcademicTerm.objects.filter(
            id__in=[term.id for term in active_terms[1:]]
        ).update(active=False)

    for term in AcademicTerm.objects.all():
        if term.end_date <= term.start_date:
            term.end_date = term.start_date + timedelta(days=1)
            term.save(update_fields=["end_date"])

    seen_plans = set()
    for plan in StudyPlan.objects.order_by("id"):
        key = (plan.program_id, plan.version)
        if key in seen_plans:
            plan.version = f"{plan.version[:10]}-dup-{plan.id}"[:20]
            plan.save(update_fields=["version"])
            key = (plan.program_id, plan.version)
        seen_plans.add(key)

    used_groups = set()
    for group in CurriculumCourseGroup.objects.order_by("id"):
        if group.capacity <= 0:
            group.capacity = 30
        key = (group.course_id, group.term_id, group.group_number)
        while key in used_groups:
            group.group_number += 1
            key = (group.course_id, group.term_id, group.group_number)
        used_groups.add(key)
        group.save(update_fields=["capacity", "group_number"])


class Migration(migrations.Migration):

    dependencies = [
        (
            "academic_core",
            "0005_alter_academicprogram_id_alter_academicterm_id_and_more",
        ),
    ]

    operations = [
        migrations.RenameModel(
            old_name="CourseGroup",
            new_name="CurriculumCourseGroup",
        ),
        migrations.RunPython(normalize_academic_data, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="academicterm",
            constraint=models.CheckConstraint(
                condition=models.Q(end_date__gt=models.F("start_date")),
                name="academic_term_dates_valid",
            ),
        ),
        migrations.AddConstraint(
            model_name="academicterm",
            constraint=models.UniqueConstraint(
                condition=models.Q(active=True),
                fields=("active",),
                name="only_one_active_academic_term",
            ),
        ),
        migrations.AddConstraint(
            model_name="studyplan",
            constraint=models.UniqueConstraint(
                fields=("program", "version"),
                name="unique_study_plan_version_per_program",
            ),
        ),
        migrations.AddConstraint(
            model_name="curriculumcoursegroup",
            constraint=models.UniqueConstraint(
                fields=("course", "term", "group_number"),
                name="unique_curriculum_group_per_term",
            ),
        ),
        migrations.AddConstraint(
            model_name="curriculumcoursegroup",
            constraint=models.CheckConstraint(
                condition=models.Q(capacity__gt=0),
                name="curriculum_group_capacity_positive",
            ),
        ),
    ]
