from django.db import migrations

SEEDED_PROGRAMS = [
    {
        "program_name": "Ingeniería de Software",
        "program_code": "ISOF/ SNIES: 107615",
        "faculty_name": "Facultad de Ingeniería",
        "campus_name": "COA BELLO",
        "study_plan_version": "2026-1",
        "study_plan_description": "Plan de estudios completo de Ingeniería de Software.",
        "courses": [


            # BÁSICO PROFESIONAL
            ("ISOFBL011", "Precálculo", 1, 3, "BASICO"),
            ("ISOFBL071", "Introducción a la Ingeniería", 1, 3, "BASICO"),
            ("CBASBL021", "Cálculo Diferencial", 2, 2, "BASICO"),
            ("CBASBL151", "Cálculo Integral", 3, 3, "BASICO"),
            ("ISOFBL041", "Cálculo Vectorial", 6, 2, "BASICO"),
            ("ISOFBL021", "Álgebra Lineal", 4, 3, "BASICO"),
            ("ISOFBL031", "Ecuaciones Diferenciales", 4, 3, "BASICO"),
            ("ISOFBL051", "Física Mecánica", 3, 2, "BASICO"),
            ("ISOFBL061", "Física Electromagnética", 6, 3, "BASICO"),
            ("ESTA1061", "Probabilidad y Estadística", 1, 3, "BASICO"),

           
            # MINUTO DE DIOS
            ("FHUM1010", "Proyecto de Vida", 1, 2, "MINUTO"),
            ("FHUM1020", "Cátedra Minuto de Dios", 2, 0, "MINUTO"),
            ("PRAC1020", "Desarrollo Social Contemporáneo", 4, 2, "MINUTO"),
            ("PRAC1010", "Práctica en Responsabilidad Social", 5, 3, "MINUTO"),


            # PROFESIONAL
            ("ISOFBL063", "Lógica de Programación", 1, 3, "PROFESIONAL"),
            ("ISOFBL073", "Programación Básica", 2, 3, "PROFESIONAL"),
            ("ISOFBL083", "Programación Orientada a Objetos", 3, 3, "PROFESIONAL"),
            ("ISOFBL093", "Estructura de Datos", 4, 3, "PROFESIONAL"),
            ("ISOFBL103", "Programación Web", 5, 3, "PROFESIONAL"),
            ("ISOFBL113", "Programación de Aplicaciones Móviles", 6, 3, "PROFESIONAL"),

            ("ISOFBL153", "Análisis y Diseño de Bases de Datos", 2, 3, "PROFESIONAL"),
            ("ISOFBL163", "Sistemas de Gestión de Bases de Datos", 3, 3, "PROFESIONAL"),
            ("ISOFBL183", "Arquitectura de Datos", 6, 2, "PROFESIONAL"),

            ("ISOFBL213", "Requerimientos de Software", 2, 2, "PROFESIONAL"),
            ("ISOFBL223", "Modelamiento de Software", 4, 2, "PROFESIONAL"),
            ("ISOFBL233", "Diseño de Software", 5, 2, "PROFESIONAL"),
            ("ISOFBL243", "Métodos de Ingeniería de Software", 6, 2, "PROFESIONAL"),

            ("ISOFBL013", "Arquitectura de Computadores", 4, 3, "PROFESIONAL"),
            ("ISOFBL023", "Sistemas Operativos", 5, 2, "PROFESIONAL"),
            ("ISOFBL033", "Redes de Computadores", 6, 2, "PROFESIONAL"),

            ("ISOFBL043", "Sistemas Telemáticos", 7, 2, "PROFESIONAL"),
            ("ISOFBL123", "Programación Integrada y Tecnologías Web", 7, 2, "PROFESIONAL"),
            ("ISOFBL193", "Simulación de Sistemas", 7, 3, "PROFESIONAL"),

            ("ISOFBL053", "Seguridad de la Información", 8, 3, "PROFESIONAL"),
            ("ISOFBL133", "Inteligencia Artificial", 8, 3, "PROFESIONAL"),

            ("ISOFBL143", "Sistemas Expertos", 9, 4, "PROFESIONAL"),
            ("ISOFBL263", "Gerencia de Proyectos de Software", 9, 2, "PROFESIONAL"),

            ("ISOFBL203", "Almacenamiento y Minería de Datos", 10, 3, "PROFESIONAL"),
            ("ISOFBL273", "Fundamentos en Derechos de Software", 10, 2, "PROFESIONAL"),


            # COMPLEMENTARIO
            ("LENG1010", "Comunicación Escrita y Procesos Lectores I", 1, 2, "COMPLEMENTARIO"),
            ("LENG1020", "Comunicación Escrita y Procesos Lectores II", 2, 2, "COMPLEMENTARIO"),

            ("INGL1010", "Inglés I", 2, 4, "COMPLEMENTARIO"),
            ("INGL1020", "Inglés II", 3, 4, "COMPLEMENTARIO"),
            ("INGL1030", "Inglés III", 4, 4, "COMPLEMENTARIO"),

            ("CIDUBL011", "Metodología de la Investigación", 3, 2, "COMPLEMENTARIO"),
            ("ISOFBL081", "Formulación y Evaluación de Proyectos", 6, 2, "COMPLEMENTARIO"),

            ("ADMI1060", "Emprendimiento", 8, 2, "COMPLEMENTARIO"),
            ("ETIC190", "Ética Profesional", 9, 2, "COMPLEMENTARIO"),

            # Electivas
            ("ISOFBL014", "Electiva CPC I", 6, 2, "COMPLEMENTARIO"),
            ("ISOFBL024", "Electiva CPC II", 7, 2, "COMPLEMENTARIO"),
            ("ISOFBL034", "Electiva CPC III", 8, 2, "COMPLEMENTARIO"),
            ("ISOFBL044", "Electiva CPC IV", 9, 2, "COMPLEMENTARIO"),

            ("ISOFBL012", "Electiva CMD I", 7, 3, "COMPLEMENTARIO"),
            ("ISOFBL022", "Electiva CMD II", 8, 3, "COMPLEMENTARIO"),
            ("ISOFBL032", "Electiva CMD III", 10, 3, "COMPLEMENTARIO"),

            # Finales
            ("ISOFBL054", "Práctica Profesional", 9, 2, "COMPLEMENTARIO"),
            ("ISOFBL064", "Opción de Grado", 10, 2, "COMPLEMENTARIO"),
        ],
    },
    {
        "program_name": "Ingeniería Industrial",
        "program_code": "IIND",
        "faculty_name": "Facultad de Ingeniería",
        "campus_name": "Sede Principal",
        "study_plan_version": "2026-1",
        "study_plan_description": "Plan de estudios de Ingeniería Industrial.",
        "courses": [

            # BÁSICO
            ("IINUBL010", "Precálculo", 1, 3, "BASICO"),
            ("IINUBL020", "Geometría", 1, 2, "BASICO"),
            ("IINUBL030", "Cálculo Diferencial", 2, 3, "BASICO"),
            ("IINUBL080", "Cálculo Integral", 4, 3, "BASICO"),
            ("IINUBL090", "Cálculo Vectorial", 5, 3, "BASICO"),
            ("IINUBL110", "Ecuaciones Diferenciales", 6, 3, "BASICO"),
            ("IINUBL050", "Álgebra Lineal", 3, 3, "BASICO"),
            ("IINUBL060", "Física Mecánica", 3, 3, "BASICO"),
            ("IINUBL100", "Física Electrónica", 5, 3, "BASICO"),
            ("IINUBL043", "Probabilidad y Estadística", 3, 3, "BASICO"),
            ("IINUBL040", "Química", 2, 3, "BASICO"),


            # MINUTO DE DIOS
            ("FHUM1010", "Proyecto de Vida", 1, 2, "MINUTO"),
            ("FHUM1020", "Cátedra Minuto de Dios", 2, 2, "MINUTO"),
            ("PRAC1020", "Desarrollo Social Contemporáneo", 4, 2, "MINUTO"),
            ("PRAC1010", "Práctica en Responsabilidad Social", 6, 3, "MINUTO"),


            # PROFESIONAL
            ("IINUBL013", "Introducción a la Ingeniería Industrial", 1, 1, "PROFESIONAL"),
            ("IINUBL023", "Fundamentos de Gestión", 1, 2, "PROFESIONAL"),
            ("IINUBL033", "Dibujo", 2, 3, "PROFESIONAL"),
            ("IINUBL070", "Fundamentos de Programación", 3, 2, "PROFESIONAL"),

            ("IINUBL053", "Costos de Productos y Servicios", 3, 2, "PROFESIONAL"),
            ("IINUBL063", "Ingeniería de Métodos", 4, 3, "PROFESIONAL"),
            ("IINUBL083", "Materiales de Ingeniería", 5, 3, "PROFESIONAL"),
            ("IINUBL093", "Investigación de Operaciones I", 5, 3, "PROFESIONAL"),
            ("IINUBL143", "Investigación de Operaciones II", 6, 3, "PROFESIONAL"),

            ("IINUBL123", "Economía", 6, 2, "PROFESIONAL"),
            ("IINUBL133", "Matemáticas Financieras", 6, 2, "PROFESIONAL"),
            ("IINUBL113", "Diseño Industrial", 6, 2, "PROFESIONAL"),

            ("IINUBL120", "Termodinámica", 7, 3, "PROFESIONAL"),
            ("IINUBL183", "Distribución en Planta", 7, 2, "PROFESIONAL"),
            ("IINUBL163", "Mercadeo de Productos y Servicios", 7, 2, "PROFESIONAL"),
            ("IINUBL173", "Administración y Control de Producción", 7, 3, "PROFESIONAL"),
            ("IINUBL153", "Logística Empresarial", 7, 3, "PROFESIONAL"),

            ("IINUBL233", "Procesos Industriales", 8, 3, "PROFESIONAL"),
            ("IINUBL193", "Automatización", 8, 2, "PROFESIONAL"),
            ("IINUBL203", "Producción Más Limpia", 8, 3, "PROFESIONAL"),
            ("IINUBL213", "Sistemas Flexibles de Manufactura", 8, 3, "PROFESIONAL"),
            ("IINUBL223", "Herramientas de Calidad", 8, 2, "PROFESIONAL"),

            ("IINUBL243", "Simulación", 9, 3, "PROFESIONAL"),
            ("IINUBL253", "Gestión de Calidad en Productos y Servicios", 9, 2, "PROFESIONAL"),

            ("IINUBL273", "Seguridad Industrial y Salud Ocupacional", 10, 3, "PROFESIONAL"),
            ("IINUBL283", "Gestión de Proyectos Industriales", 10, 3, "PROFESIONAL"),


            # COMPLEMENTARIO
            ("INFO1010", "Gestión Básica de la Información", 1, 3, "COMPLEMENTARIO"),
            ("LENG1010", "Comunicación Escrita I", 1, 2, "COMPLEMENTARIO"),
            ("LENG1020", "Comunicación Escrita II", 2, 2, "COMPLEMENTARIO"),

            ("INGL1010", "Inglés I", 2, 3, "COMPLEMENTARIO"),
            ("INGL1020", "Inglés II", 4, 3, "COMPLEMENTARIO"),
            ("INGL1030", "Inglés III", 9, 3, "COMPLEMENTARIO"),

            ("CIDUBL011", "Metodología de la Investigación", 3, 2, "COMPLEMENTARIO"),
            ("ADMI1060", "Emprendimiento", 3, 2, "COMPLEMENTARIO"),
            ("ETIC190", "Ética Profesional", 8, 2, "COMPLEMENTARIO"),

            # Electivas
            ("IINUBL012", "Electiva CMD I", 4, 3, "COMPLEMENTARIO"),
            ("IINUBL022", "Electiva CMD II", 7, 3, "COMPLEMENTARIO"),
            ("IINUBL032", "Electiva CMD III", 9, 3, "COMPLEMENTARIO"),
            ("IINUBL042", "Electiva CMD IV", 10, 2, "COMPLEMENTARIO"),

            ("IINUBL014", "Electiva CPC I", 5, 3, "COMPLEMENTARIO"),
            ("IINUBL024", "Electiva CPC II", 6, 3, "COMPLEMENTARIO"),
            ("IINUBL034", "Electiva CPC III", 8, 2, "COMPLEMENTARIO"),
            ("IINUBL263", "Electiva CP", 10, 3, "COMPLEMENTARIO"),

            # Finales
            ("IINUBL044", "Práctica Profesional", 9, 6, "COMPLEMENTARIO"),
            ("IINUBL054", "Opción de Grado", 10, 3, "COMPLEMENTARIO"),

          
            # APOYO (TLOG)
            ("TLOGBL093", "Procesos Logísticos de Producción", 3, 3, "PROFESIONAL"),
            ("TLOGBL103", "Métodos y Tiempos", 4, 2, "PROFESIONAL"),
            ("TLOGBL113", "Investigación de Operaciones", 4, 3, "PROFESIONAL"),
            ("TLOGBL024", "Electiva CPC", 5, 2, "COMPLEMENTARIO"),
            ("TLOGBL044", "Electiva CPC", 6, 2, "COMPLEMENTARIO"),
        ],
    }
]


def seed_study_plans_and_courses(apps, schema_editor):
    Campus = apps.get_model("academic_core", "Campus")
    Faculty = apps.get_model("academic_core", "Faculty")
    AcademicProgram = apps.get_model("academic_core", "AcademicProgram")
    StudyPlan = apps.get_model("academic_core", "StudyPlan")
    Course = apps.get_model("academic_core", "Course")
    CourseComponent = apps.get_model("academic_core", "CourseComponent")

    # Crear componentes
    basic, _ = CourseComponent.objects.get_or_create(name="Básico Profesional")
    professional, _ = CourseComponent.objects.get_or_create(name="Profesional")
    md, _ = CourseComponent.objects.get_or_create(name="Minuto de Dios")
    complementary, _ = CourseComponent.objects.get_or_create(name="Complementario")

    # MAPEO 
    component_map = {
        "BASICO": basic,
        "PROFESIONAL": professional,
        "MINUTO": md,
        "COMPLEMENTARIO": complementary,
    }

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

        # CREACIÓN DE CURSOS
        for code, name, semester, credits, component_key in program_data["courses"]:
            Course.objects.update_or_create(
                code=code,
                defaults={
                    "name": name,
                    "credits": credits,
                    "semester": semester,
                    "component_id": component_map.get(component_key).id if component_map.get(component_key) else None,
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
        for course in program_data["courses"]:
            course_code = course[0]
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
