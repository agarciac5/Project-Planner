from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("scheduling_enrollment", "0007_semesterscheduleoption_selected"),
    ]

    operations = [
        migrations.AddField(
            model_name="semesterscheduleassignment",
            name="generated_schedule",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="semester_assignments",
                to="scheduling_enrollment.proposedschedule",
            ),
        ),
    ]
