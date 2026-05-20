from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("scheduling_enrollment", "0006_update_semesterschedulerun_status_choices"),
    ]

    operations = [
        migrations.AddField(
            model_name="semesterscheduleoption",
            name="selected",
            field=models.BooleanField(default=False),
        ),
    ]
