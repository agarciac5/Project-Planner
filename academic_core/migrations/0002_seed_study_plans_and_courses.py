from django.db import migrations


SEEDED_PROGRAMS = [
    {
        "program_name": "Ingenieria de Software",
        "program_code": "ISW",
        "faculty_name": "Facultad de Ingenieria",
        "campus_name": "Sede Principal",
        "study_plan_version": "2026-1",
        "study_plan_description": "Plan base sembrado desde la interfaz de planeacion.",
        "courses": [
            ("Calculo Diferencial", "ISW-101", 1, 4),
            ("Introduccion a la Programacion", "ISW-102", 1, 3),
            ("Competencias Comunicativas", "ISW-103", 1, 2),
            ("Algebra Lineal", "ISW-201", 2, 3),
            ("Programacion Orientada a Objetos", "ISW-202", 2, 3),
            ("Ingles I", "ISW-203", 2, 2),
            ("Bases de Datos", "ISW-301", 3, 3),
            ("Estructuras de Datos", "ISW-302", 3, 3),
            ("Ingles II", "ISW-303", 3, 2),
            ("Programacion Web", "ISW-401", 4, 3),
            ("Arquitectura de Software", "ISW-402", 4, 3),
            ("Investigacion I", "ISW-403", 4, 2),
        ],
    },
    {
        "program_name": "Ingenieria de Redes",
        "program_code": "IRD",
        "faculty_name": "Facultad de Ingenieria",
        "campus_name": "Sede Norte",
        "study_plan_version": "2026-1",
        "study_plan_description": "Plan base sembrado desde la interfaz de planeacion.",
        "courses": [
            ("Logica", "IRD-101", 1, 3),
            ("Electronica Basica", "IRD-102", 1, 3),
            ("Competencias Digitales", "IRD-103", 1, 2),
            ("Telematica", "IRD-201", 2, 3),
            ("Fundamentos de Redes", "IRD-202", 2, 3),
            ("Ingles I", "IRD-203", 2, 2),
            ("Protocolos de Comunicacion", "IRD-301", 3, 3),
            ("Seguridad Informatica", "IRD-302", 3, 3),
            ("Ingles II", "IRD-303", 3, 2),
        ],
    },
    {
        "program_name": "Analisis de Datos",
        "program_code": "ADS",
        "faculty_name": "Facultad de Ciencias Empresariales",
        "campus_name": "Sede Sur",
        "study_plan_version": "2026-1",
        "study_plan_description": "Plan base sembrado desde la interfaz de planeacion.",
        "courses": [
            ("Matematica Basica", "ADS-101", 1, 3),
            ("Herramientas Ofimaticas", "ADS-102", 1, 2),
            ("Comunicacion Escrita", "ADS-103", 1, 2),
            ("Estadistica", "ADS-201", 2, 3),
            ("Bases de Datos", "ADS-202", 2, 3),
            ("Visualizacion de Datos", "ADS-203", 2, 3),
            ("Mineria de Datos", "ADS-301", 3, 3),
            ("Machine Learning", "ADS-302", 3, 3),
            ("Analitica de Negocio", "ADS-303", 3, 3),
        ],
    },
]


def seed_study_plans_and_courses(apps, schema_editor):
    Campus = apps.get_model("academic_core", "Campus")
    Faculty = apps.get_model("academic_core", "Faculty")
    AcademicProgram = apps.get_model("academic_core", "AcademicProgram")
    StudyPlan = apps.get_model("academic_core", "StudyPlan")
    Course = apps.get_model("academic_core", "Course")

    for program_data in SEEDED_PROGRAMS:
        campus, _ = Campus.objects.get_or_create(name=program_data["campus_name"])

        faculty, _ = Faculty.objects.get_or_create(
            name=program_data["faculty_name"],
            defaults={"campus": campus},
        )
        if faculty.campus_id is None:
            faculty.campus = campus
            faculty.save(update_fields=["campus"])

        program, _ = AcademicProgram.objects.get_or_create(
            code=program_data["program_code"],
            defaults={
                "name": program_data["program_name"],
                "faculty": faculty,
                "campus": campus,
            },
        )
        updated_fields = []
        if program.name != program_data["program_name"]:
            program.name = program_data["program_name"]
            updated_fields.append("name")
        if program.faculty_id != faculty.id:
            program.faculty = faculty
            updated_fields.append("faculty")
        if program.campus_id != campus.id:
            program.campus = campus
            updated_fields.append("campus")
        if updated_fields:
            program.save(update_fields=updated_fields)

        study_plan, _ = StudyPlan.objects.get_or_create(
            program=program,
            version=program_data["study_plan_version"],
            defaults={"description": program_data["study_plan_description"]},
        )
        if study_plan.description != program_data["study_plan_description"]:
            study_plan.description = program_data["study_plan_description"]
            study_plan.save(update_fields=["description"])

        for course_name, course_code, semester, credits in program_data["courses"]:
            Course.objects.update_or_create(
                code=course_code,
                defaults={
                    "name": course_name,
                    "credits": credits,
                    "semester": semester,
                    "study_plan": study_plan,
                },
            )


def unseed_study_plans_and_courses(apps, schema_editor):
    AcademicProgram = apps.get_model("academic_core", "AcademicProgram")
    StudyPlan = apps.get_model("academic_core", "StudyPlan")
    Course = apps.get_model("academic_core", "Course")

    course_codes = []
    program_codes = []
    for program_data in SEEDED_PROGRAMS:
        program_codes.append(program_data["program_code"])
        for _, course_code, _, _ in program_data["courses"]:
            course_codes.append(course_code)

    Course.objects.filter(code__in=course_codes).delete()
    StudyPlan.objects.filter(
        program__code__in=program_codes,
        version="2026-1",
    ).delete()
    AcademicProgram.objects.filter(code__in=program_codes).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("academic_core", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            seed_study_plans_and_courses,
            reverse_code=unseed_study_plans_and_courses,
        ),
    ]
