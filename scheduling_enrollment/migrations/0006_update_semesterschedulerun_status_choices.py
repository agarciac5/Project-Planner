from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("scheduling_enrollment", "0005_enrollmentqueue_term_and_semester_planner_models"),
    ]

    operations = [
        migrations.AlterField(
            model_name="semesterschedulerun",
            name="status",
            field=models.CharField(
                choices=[
                    ("draft", "Borrador"),
                    ("saved", "Guardado"),
                    ("applied", "Aplicado"),
                ],
                default="draft",
                max_length=20,
            ),
        ),
    ]
