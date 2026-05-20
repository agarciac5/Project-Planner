from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("scheduling_enrollment", "0008_semesterscheduleassignment_generated_schedule"),
    ]

    operations = [
        migrations.AddField(
            model_name="enrollmentqueue",
            name="course_group",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="student_enrollments",
                to="scheduling_enrollment.coursegroup",
            ),
        ),
    ]
