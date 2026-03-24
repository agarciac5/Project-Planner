from django.db import migrations


SEEDED_CLASSROOMS = [
    ("32-107", "Aula Calculo Diferencial", 1, "Sede Principal"),
    ("32-108", "Aula Introduccion a la Programacion", 1, "Sede Principal"),
    ("32-109", "Aula Competencias Comunicativas", 1, "Sede Principal"),
    ("32-207", "Aula Algebra Lineal", 2, "Sede Principal"),
    ("32-208", "Aula Programacion Orientada a Objetos", 2, "Sede Principal"),
    ("32-209", "Aula Ingles I Software", 2, "Sede Principal"),
    ("32-307", "Laboratorio Bases de Datos", 3, "Sede Principal"),
    ("32-308", "Laboratorio Estructuras de Datos", 3, "Sede Principal"),
    ("32-309", "Aula Ingles II Software", 3, "Sede Principal"),
    ("32-407", "Laboratorio Programacion Web", 4, "Sede Principal"),
    ("32-408", "Aula Arquitectura de Software", 4, "Sede Principal"),
    ("32-409", "Aula Investigacion I", 4, "Sede Principal"),
    ("21-107", "Aula Logica", 1, "Sede Norte"),
    ("21-108", "Laboratorio Electronica Basica", 1, "Sede Norte"),
    ("21-109", "Aula Competencias Digitales", 1, "Sede Norte"),
    ("21-207", "Laboratorio Telematica", 2, "Sede Norte"),
    ("21-208", "Laboratorio Fundamentos de Redes", 2, "Sede Norte"),
    ("21-209", "Aula Ingles I Redes", 2, "Sede Norte"),
    ("21-307", "Laboratorio Protocolos de Comunicacion", 3, "Sede Norte"),
    ("21-308", "Laboratorio Seguridad Informatica", 3, "Sede Norte"),
    ("21-309", "Aula Ingles II Redes", 3, "Sede Norte"),
    ("14-107", "Aula Matematica Basica", 1, "Sede Sur"),
    ("14-108", "Sala Herramientas Ofimaticas", 1, "Sede Sur"),
    ("14-109", "Aula Comunicacion Escrita", 1, "Sede Sur"),
    ("14-207", "Laboratorio Estadistica", 2, "Sede Sur"),
    ("14-208", "Laboratorio Bases de Datos Analitica", 2, "Sede Sur"),
    ("14-209", "Sala Visualizacion de Datos", 2, "Sede Sur"),
    ("14-307", "Laboratorio Mineria de Datos", 3, "Sede Sur"),
    ("14-308", "Laboratorio Machine Learning", 3, "Sede Sur"),
    ("14-309", "Aula Analitica de Negocio", 3, "Sede Sur"),
]


def seed_classrooms(apps, schema_editor):
    Campus = apps.get_model("academic_core", "Campus")
    Classroom = apps.get_model("classrooms", "Classroom")

    for classroom_id, name, block, campus_name in SEEDED_CLASSROOMS:
        campus, _ = Campus.objects.get_or_create(name=campus_name)
        Classroom.objects.update_or_create(
            classroom_id=classroom_id,
            defaults={
                "name": name,
                "block": block,
                "campus": campus,
                "is_active": True,
            },
        )


def unseed_classrooms(apps, schema_editor):
    Classroom = apps.get_model("classrooms", "Classroom")
    classroom_ids = [classroom_id for classroom_id, _, _, _ in SEEDED_CLASSROOMS]
    Classroom.objects.filter(classroom_id__in=classroom_ids).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("academic_core", "0002_seed_study_plans_and_courses"),
        ("classrooms", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_classrooms, reverse_code=unseed_classrooms),
    ]
