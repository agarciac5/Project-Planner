from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("access_support", "0003_alter_studentprofile_document_type"),
        ("teaching", "0003_alter_availability_id_alter_contractrule_id_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="teacher",
            name="user",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="teacher_profile",
                to="access_support.user",
            ),
        ),
    ]
