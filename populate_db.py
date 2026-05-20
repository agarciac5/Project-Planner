import os
from datetime import date, time

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project_planner.settings")
django.setup()

from django.contrib.auth import get_user_model

from access_support.models import StudentProfile
from academic_core.models import AcademicProgram, AcademicTerm, Campus, Course, Faculty, StudyPlan
from classrooms.models import Classroom, TimeSlot
from scheduling_enrollment.models import EnrollmentQueue, TeacherActivity
from teaching.models import Availability, ContractRule, Teacher


User = get_user_model()


TERM_DEFINITIONS = [
    ("2026-1", date(2026, 1, 15), date(2026, 5, 15), False),
    ("2026-2", date(2026, 7, 15), date(2026, 11, 15), True),
]

# ── Timeslots ──────────────────────────────────────────────────────────────────
# Se agregaron franjas nocturnas (18:00-19:30 y 19:30-21:00) para martes, jueves
# y viernes, necesarias para los docentes DOC-SW-003 y DOC-SW-009 (Cátedra
# nocturna).  Sin estos slots, _slot_within_availability() nunca devuelve True
# para ellos y el algoritmo los deja sin candidatos.
TIMESLOTS = [
    # Lunes
    ("Monday",    time(7,  0), time(8,  30)),
    ("Monday",    time(8,  30), time(10, 0)),
    ("Monday",    time(10, 0), time(11, 30)),
    ("Monday",    time(14, 0), time(15, 30)),
    ("Monday",    time(15, 30), time(17, 0)),
    # Martes
    ("Tuesday",   time(7,  0), time(8,  30)),
    ("Tuesday",   time(8,  30), time(10, 0)),
    ("Tuesday",   time(10, 0), time(11, 30)),
    ("Tuesday",   time(14, 0), time(15, 30)),
    ("Tuesday",   time(15, 30), time(17, 0)),
    ("Tuesday",   time(18, 0), time(19, 30)),   # ← nocturno agregado
    ("Tuesday",   time(19, 30), time(21, 0)),   # ← nocturno agregado
    # Miércoles
    ("Wednesday", time(7,  0), time(8,  30)),
    ("Wednesday", time(8,  30), time(10, 0)),
    ("Wednesday", time(10, 0), time(11, 30)),
    ("Wednesday", time(14, 0), time(15, 30)),
    ("Wednesday", time(15, 30), time(17, 0)),
    # Jueves
    ("Thursday",  time(7,  0), time(8,  30)),
    ("Thursday",  time(8,  30), time(10, 0)),
    ("Thursday",  time(10, 0), time(11, 30)),
    ("Thursday",  time(14, 0), time(15, 30)),
    ("Thursday",  time(15, 30), time(17, 0)),
    ("Thursday",  time(18, 0), time(19, 30)),   # ← nocturno agregado
    ("Thursday",  time(19, 30), time(21, 0)),   # ← nocturno agregado
    # Viernes
    ("Friday",    time(7,  0), time(8,  30)),
    ("Friday",    time(8,  30), time(10, 0)),
    ("Friday",    time(10, 0), time(11, 30)),
    ("Friday",    time(14, 0), time(15, 30)),
    ("Friday",    time(18, 0), time(19, 30)),   # ← nocturno agregado
    ("Friday",    time(19, 30), time(21, 0)),   # ← nocturno agregado
    # Sábado
    ("Saturday",  time(8,  0), time(9,  30)),
    ("Saturday",  time(9,  30), time(11, 0)),
]

CLASSROOMS = [
    ("A101", "Salon flexible 1",    1, 25, "SALON"),
    ("A102", "Salon flexible 2",    1, 20, "SALON"),
    ("A103", "Salon flexible 3",    1, 30, "SALON"),
    ("A104", "Salon flexible 4",    1, 35, "SALON"),
    ("B201", "Laboratorio software",1, 20, "SISTEMAS"),
    ("B202", "Laboratorio analitica",1,20, "SISTEMAS"),
    ("B203", "Laboratorio desarrollo",1,24,"SISTEMAS"),
    ("B204", "Laboratorio redes",   1, 24, "SISTEMAS"),
    ("C301", "Salon magistral",     3, 40, "SALON"),
    ("C302", "Salon magistral 2",   3, 45, "SALON"),
    ("C303", "Salon magistral 3",   3, 50, "SALON"),
    ("D401", "Aula de innovacion",  4, 28, "SALON"),
    ("D402", "Aula de proyectos",   4, 32, "SALON"),
    ("D403", "Laboratorio IA",      4, 22, "SISTEMAS"),
    ("E501", "Auditorio academico", 5, 60, "SALON"),
]

# ── Docentes ───────────────────────────────────────────────────────────────────
# DOC-SW-003 (Diana Rojas) y DOC-SW-009 (Valentina Castro): su disponibilidad
# original era "18:00-21:00".  Se desglosa en dos bloques de 1:30 h que ahora
# coinciden exactamente con los timeslots nocturnos agregados arriba.
TEACHER_DEFINITIONS = [
    {
        "teacher_id": "DOC-SW-001",
        "first_name": "Laura",
        "last_name": "Gonzalez",
        "contract_type": "Tiempo Completo",
        "qualified_codes": ["ISOFBL063", "ISOFBL073", "ISOFBL083", "ISOFBL103", "ISOFBL123"],
        "availability": [
            ("Monday",    time(7,  0), time(12, 0)),
            ("Tuesday",   time(7,  0), time(12, 0)),
            ("Wednesday", time(14, 0), time(18, 0)),
            ("Thursday",  time(7,  0), time(12, 0)),
        ],
        "activities": [
            ("asesoria", "Tuesday", time(10, 0), time(11, 30)),
        ],
    },
    {
        "teacher_id": "DOC-SW-002",
        "first_name": "Andres",
        "last_name": "Perez",
        "contract_type": "Medio Tiempo",
        "qualified_codes": ["ISOFBL153", "ISOFBL163", "ISOFBL183", "ESTA1061", "ISOFBL203"],
        "availability": [
            ("Monday",   time(14, 0), time(18, 0)),
            ("Wednesday",time(7,  0), time(12, 0)),
            ("Thursday", time(14, 0), time(18, 0)),
            ("Friday",   time(7,  0), time(11, 30)),
        ],
        "activities": [
            ("investigacion", "Thursday", time(15, 30), time(17, 0)),
        ],
    },
    {
        # Cátedra nocturna — disponibilidad alineada con los timeslots nocturnos
        "teacher_id": "DOC-SW-003",
        "first_name": "Diana",
        "last_name": "Rojas",
        "contract_type": "Catedra",
        "qualified_codes": ["ISOFBL213", "ISOFBL223", "ISOFBL233", "ISOFBL243", "ISOFBL263"],
        "availability": [
            ("Tuesday",  time(18, 0), time(21, 0)),   # cubre 18:00-19:30 y 19:30-21:00
            ("Thursday", time(18, 0), time(21, 0)),   # cubre 18:00-19:30 y 19:30-21:00
            ("Saturday", time(8,  0), time(11, 0)),   # cubre 8:00-9:30 y 9:30-11:00
        ],
        "activities": [],
    },
    {
        "teacher_id": "DOC-SW-004",
        "first_name": "Sergio",
        "last_name": "Diaz",
        "contract_type": "Tiempo Completo",
        "qualified_codes": ["CBASBL021", "CBASBL151", "ISOFBL021", "ISOFBL031", "ISOFBL041", "ISOFBL051"],
        "availability": [
            ("Monday",    time(7, 0), time(12, 0)),
            ("Wednesday", time(7, 0), time(12, 0)),
            ("Friday",    time(7, 0), time(12, 0)),
        ],
        "activities": [
            ("asesoria", "Wednesday", time(10, 0), time(11, 30)),
        ],
    },
    {
        "teacher_id": "DOC-SW-005",
        "first_name": "Camilo",
        "last_name": "Restrepo",
        "contract_type": "Tiempo Completo",
        "qualified_codes": ["ISOFBL013", "ISOFBL023", "ISOFBL033", "ISOFBL043", "ISOFBL053", "ISOFBL133"],
        "availability": [
            ("Tuesday",   time(7,  0), time(12, 0)),
            ("Wednesday", time(14, 0), time(18, 0)),
            ("Thursday",  time(7,  0), time(12, 0)),
            ("Friday",    time(14, 0), time(18, 0)),
        ],
        "activities": [],
    },
    {
        "teacher_id": "DOC-SW-006",
        "first_name": "Paula",
        "last_name": "Ramirez",
        "contract_type": "Tiempo Completo",
        "qualified_codes": ["ISOFBL083", "ISOFBL103", "ISOFBL123", "ISOFBL223", "ISOFBL233"],
        "availability": [
            ("Monday",   time(14, 0), time(18, 0)),
            ("Tuesday",  time(7,  0), time(12, 0)),
            ("Thursday", time(7,  0), time(12, 0)),
            ("Friday",   time(7,  0), time(12, 0)),
        ],
        "activities": [
            ("investigacion", "Friday", time(10, 0), time(11, 30)),
        ],
    },
    {
        "teacher_id": "DOC-SW-007",
        "first_name": "Natalia",
        "last_name": "Moreno",
        "contract_type": "Medio Tiempo",
        "qualified_codes": ["CBASBL021", "CBASBL151", "ESTA1061", "ISOFBL021", "ISOFBL031"],
        "availability": [
            ("Monday",   time(7,  0), time(12, 0)),
            ("Tuesday",  time(14, 0), time(18, 0)),
            ("Thursday", time(14, 0), time(18, 0)),
        ],
        "activities": [],
    },
    {
        "teacher_id": "DOC-SW-008",
        "first_name": "Mauricio",
        "last_name": "Torres",
        "contract_type": "Tiempo Completo",
        "qualified_codes": ["ISOFBL013", "ISOFBL023", "ISOFBL033", "ISOFBL043", "ISOFBL053"],
        "availability": [
            ("Monday",    time(7,  0), time(12, 0)),
            ("Wednesday", time(14, 0), time(18, 0)),
            ("Thursday",  time(7,  0), time(12, 0)),
            ("Friday",    time(14, 0), time(18, 0)),
        ],
        "activities": [
            ("asesoria", "Thursday", time(8, 30), time(10, 0)),
        ],
    },
    {
        # Cátedra nocturna — misma corrección que DOC-SW-003
        "teacher_id": "DOC-SW-009",
        "first_name": "Valentina",
        "last_name": "Castro",
        "contract_type": "Catedra",
        "qualified_codes": ["ISOFBL153", "ISOFBL163", "ISOFBL183", "ISOFBL203", "ISOFBL263"],
        "availability": [
            ("Tuesday",  time(7,  0), time(12, 0)),
            ("Thursday", time(7,  0), time(12, 0)),
            ("Saturday", time(8,  0), time(11, 0)),
        ],
        "activities": [],
    },
    {
        "teacher_id": "DOC-SW-010",
        "first_name": "Felipe",
        "last_name": "Suarez",
        "contract_type": "Tiempo Completo",
        "qualified_codes": ["ISOFBL073", "ISOFBL083", "ISOFBL103", "ISOFBL123", "ISOFBL133"],
        "availability": [
            ("Monday",    time(7,  0), time(12, 0)),
            ("Tuesday",   time(14, 0), time(18, 0)),
            ("Wednesday", time(7,  0), time(12, 0)),
            ("Friday",    time(7,  0), time(12, 0)),
        ],
        "activities": [
            ("investigacion", "Wednesday", time(8, 30), time(10, 0)),
        ],
    },
    {
        "teacher_id": "DOC-SW-011",
        "first_name": "Liliana",
        "last_name": "Pardo",
        "contract_type": "Medio Tiempo",
        "qualified_codes": ["ISOFBL213", "ISOFBL223", "ISOFBL233", "ISOFBL243"],
        "availability": [
            ("Monday",    time(14, 0), time(18, 0)),
            ("Wednesday", time(14, 0), time(18, 0)),
            ("Friday",    time(14, 0), time(18, 0)),
        ],
        "activities": [],
    },
    {
        "teacher_id": "DOC-SW-012",
        "first_name": "Ricardo",
        "last_name": "Quintero",
        "contract_type": "Tiempo Completo",
        "qualified_codes": ["ISOFBL041", "ISOFBL051", "ISOFBL163", "ISOFBL183", "ESTA1061"],
        "availability": [
            ("Tuesday",   time(7,  0), time(12, 0)),
            ("Wednesday", time(7,  0), time(12, 0)),
            ("Thursday",  time(14, 0), time(18, 0)),
            ("Friday",    time(7,  0), time(12, 0)),
        ],
        "activities": [
            ("asesoria", "Tuesday", time(10, 0), time(11, 30)),
        ],
    },
    {
        "teacher_id": "DOC-SW-013",
        "first_name": "Sandra",
        "last_name": "Vargas",
        "contract_type": "Catedra",
        "qualified_codes": ["CBASBL021", "CBASBL151", "ISOFBL021", "ISOFBL031", "ISOFBL041"],
        "availability": [
            ("Tuesday",  time(14, 0), time(18, 0)),
            ("Thursday", time(14, 0), time(18, 0)),
            ("Saturday", time(8,  0), time(11, 0)),
        ],
        "activities": [],
    },
    {
        "teacher_id": "DOC-SW-014",
        "first_name": "Julian",
        "last_name": "Mejia",
        "contract_type": "Tiempo Completo",
        "qualified_codes": ["ISOFBL023", "ISOFBL033", "ISOFBL043", "ISOFBL053", "ISOFBL263"],
        "availability": [
            ("Monday",   time(14, 0), time(18, 0)),
            ("Tuesday",  time(7,  0), time(12, 0)),
            ("Thursday", time(7,  0), time(12, 0)),
            ("Friday",   time(14, 0), time(18, 0)),
        ],
        "activities": [
            ("investigacion", "Monday", time(15, 30), time(17, 0)),
        ],
    },
    {
        "teacher_id": "DOC-SW-015",
        "first_name": "Andrea",
        "last_name": "Lopez",
        "contract_type": "Tiempo Completo",
        "qualified_codes": ["ISOFBL133", "ISOFBL153", "ISOFBL203", "ISOFBL223", "ISOFBL243"],
        "availability": [
            ("Monday",    time(7,  0), time(12, 0)),
            ("Wednesday", time(7,  0), time(12, 0)),
            ("Thursday",  time(14, 0), time(18, 0)),
            ("Friday",    time(7,  0), time(12, 0)),
        ],
        "activities": [
            ("asesoria", "Thursday", time(14, 0), time(15, 30)),
        ],
    },
]

DEMAND_PLAN = [
    ("CBASBL021", 72),
    ("CBASBL151", 48),
    ("ESTA1061",  41),
    ("ISOFBL021", 36),
    ("ISOFBL031", 32),
    ("ISOFBL041", 28),
    ("ISOFBL051", 24),
    ("ISOFBL073", 63),
    ("ISOFBL083", 44),
    ("ISOFBL103", 52),
    ("ISOFBL123", 29),
    ("ISOFBL133", 27),
    ("ISOFBL153", 55),
    ("ISOFBL163", 34),
    ("ISOFBL183", 22),
    ("ISOFBL203", 18),
    ("ISOFBL213", 39),
    ("ISOFBL223", 26),
    ("ISOFBL233", 21),
    ("ISOFBL243", 19),
    ("ISOFBL023", 31),
    ("ISOFBL033", 23),
    ("ISOFBL043", 17),
    ("ISOFBL053", 14),
    ("ISOFBL263", 12),
]


def create_contracts():
    contracts = {}
    contracts["Tiempo Completo"], _ = ContractRule.objects.update_or_create(
        contract_type="Tiempo Completo",
        defaults={
            "min_teaching_hours": 12,
            "max_teaching_hours": 18,
            "max_advisory_hours": 4,
            "max_research_hours": 6,
            "max_total_hours": 28,
        },
    )
    contracts["Medio Tiempo"], _ = ContractRule.objects.update_or_create(
        contract_type="Medio Tiempo",
        defaults={
            "min_teaching_hours": 8,
            "max_teaching_hours": 12,
            "max_advisory_hours": 2,
            "max_research_hours": 2,
            "max_total_hours": 16,
        },
    )
    contracts["Catedra"], _ = ContractRule.objects.update_or_create(
        contract_type="Catedra",
        defaults={
            "min_teaching_hours": 3,
            "max_teaching_hours": 6,
            "max_advisory_hours": 0,
            "max_research_hours": 0,
            "max_total_hours": 6,
        },
    )
    return contracts


def ensure_program_structure():
    campus, _ = Campus.objects.get_or_create(name="Sede Principal")
    faculty, _ = Faculty.objects.get_or_create(name="Facultad de Ingenieria", defaults={"campus": campus})
    if faculty.campus_id != campus.id:
        faculty.campus = campus
        faculty.save(update_fields=["campus"])

    program, _ = AcademicProgram.objects.get_or_create(
        code="ISOF/SIM",
        defaults={
            "name": "Ingenieria de Software",
            "faculty": faculty,
            "campus": campus,
        },
    )
    changed = []
    if program.name != "Ingenieria de Software":
        program.name = "Ingenieria de Software"
        changed.append("name")
    if program.faculty_id != faculty.id:
        program.faculty = faculty
        changed.append("faculty")
    if program.campus_id != campus.id:
        program.campus = campus
        changed.append("campus")
    if changed:
        program.save(update_fields=changed)

    study_plan, _ = StudyPlan.objects.get_or_create(
        program=program,
        version="2026-2-SIM",
        defaults={"description": "Plan resumido para pruebas del algoritmo genetico semestral."},
    )
    return campus, faculty, program, study_plan


def ensure_courses(study_plan):
    course_specs = [
        ("CBASBL021", "Calculo Diferencial",                       2, 3),
        ("ESTA1061",  "Probabilidad y Estadistica",                3, 3),
        ("ISOFBL073", "Programacion Basica",                       2, 3),
        ("ISOFBL103", "Programacion Web",                          5, 3),
        ("ISOFBL153", "Analisis y Diseno de Bases de Datos",       3, 3),
        ("ISOFBL213", "Requerimientos de Software",                4, 2),
        ("ISOFBL023", "Sistemas Operativos",                       5, 2),
        ("ISOFBL133", "Inteligencia Artificial",                   8, 3),
        ("ISOFBL263", "Gerencia de Proyectos de Software",         9, 2),
        ("ISOFBL203", "Almacenamiento y Mineria de Datos",        10, 3),
        ("ISOFBL021", "Algebra Lineal",                            3, 3),
        ("ISOFBL031", "Ecuaciones Diferenciales",                  4, 3),
        ("CBASBL151", "Calculo Integral",                          3, 3),
        ("ISOFBL041", "Calculo Vectorial",                         6, 2),
        ("ISOFBL051", "Fisica Mecanica",                           3, 2),
        ("ISOFBL083", "Programacion Orientada a Objetos",          3, 3),
        ("ISOFBL123", "Programacion Integrada y Tecnologias Web",  7, 2),
        ("ISOFBL163", "Sistemas de Gestion de Bases de Datos",     4, 3),
        ("ISOFBL183", "Arquitectura de Datos",                     6, 2),
        ("ISOFBL223", "Modelamiento de Software",                  5, 2),
        ("ISOFBL233", "Diseno de Software",                        6, 2),
        ("ISOFBL243", "Metodos de Ingenieria de Software",         7, 2),
        ("ISOFBL013", "Arquitectura de Computadores",              4, 3),
        ("ISOFBL033", "Redes de Computadores",                     6, 2),
        ("ISOFBL043", "Sistemas Telematicos",                      7, 2),
        ("ISOFBL053", "Seguridad de la Informacion",               8, 3),
    ]
    course_map = {}
    for code, name, semester, credits in course_specs:
        course, _ = Course.objects.update_or_create(
            code=code,
            defaults={
                "name": name,
                "semester": semester,
                "credits": credits,
                "study_plan": study_plan,
            },
        )
        course_map[code] = course
    return course_map


def ensure_terms():
    terms = {}
    for name, start, end, active in TERM_DEFINITIONS:
        matches = AcademicTerm.objects.filter(name=name).order_by("id")
        term = matches.first()
        if term is None:
            term = AcademicTerm.objects.create(
                name=name, start_date=start, end_date=end, active=active,
            )
        else:
            term.start_date = start
            term.end_date   = end
            term.active     = active
            term.save(update_fields=["start_date", "end_date", "active"])
            matches.exclude(id=term.id).delete()
        terms[name] = term
    return terms


def ensure_timeslots():
    for day, start_time, end_time in TIMESLOTS:
        TimeSlot.objects.get_or_create(
            day=day, start_time=start_time, end_time=end_time,
        )


def ensure_classrooms(campus):
    classroom_map = {}
    for classroom_id, name, block, capacity, classroom_type in CLASSROOMS:
        classroom, _ = Classroom.objects.update_or_create(
            classroom_id=classroom_id,
            defaults={
                "name": name,
                "block": block,
                "campus": campus,
                "capacity": capacity,
                "classroom_type": classroom_type,
                "is_active": True,
            },
        )
        classroom_map[classroom_id] = classroom
    return classroom_map


def ensure_teachers(program, faculty, campus, contracts, course_map, term):
    teachers = []
    for spec in TEACHER_DEFINITIONS:
        teacher_email = f"{spec['teacher_id'].lower()}@uniminuto.edu.co"
        teacher_user, created = User.objects.get_or_create(
            email=teacher_email,
            defaults={"role": "teacher", "is_active": True},
        )
        if created:
            teacher_user.set_password("Teacher123*")
            teacher_user.save(update_fields=["password"])

        teacher, _ = Teacher.objects.update_or_create(
            teacher_id=spec["teacher_id"],
            defaults={
                "user": teacher_user,
                "first_name": spec["first_name"],
                "last_name": spec["last_name"],
                "program": program,
                "faculty": faculty,
                "campus": campus,
                "contract": contracts[spec["contract_type"]],
                "is_active": True,
            },
        )
        teacher.qualified_courses.set(
            [course_map[code] for code in spec["qualified_codes"] if code in course_map]
        )

        Availability.objects.filter(teacher=teacher).delete()
        for day, start_time, end_time in spec["availability"]:
            Availability.objects.create(
                teacher=teacher, day=day, start_time=start_time, end_time=end_time,
            )

        TeacherActivity.objects.filter(teacher=teacher, term=term).delete()
        for activity_type, day, start_time, end_time in spec["activities"]:
            TeacherActivity.objects.create(
                teacher=teacher,
                term=term,
                activity_type=activity_type,
                day=day,
                start_time=start_time,
                end_time=end_time,
            )

        teachers.append(teacher)
    return teachers


def ensure_students_and_demand(course_map, term):
    EnrollmentQueue.objects.filter(term=term).delete()
    StudentProfile.objects.filter(user__email__startswith="sim.student").delete()
    sample_course = next(iter(course_map.values()))
    program = sample_course.study_plan.program

    total_students = sum(demand for _, demand in DEMAND_PLAN)
    students = []
    for index in range(1, total_students + 1):
        email = f"sim.student{index:03d}@uniminuto.edu.co"
        user, created = User.objects.get_or_create(
            email=email,
            defaults={"role": "student", "is_active": True},
        )
        if created:
            user.set_password("Student123*")
            user.save(update_fields=["password"])
        else:
            changed = []
            if user.role != "student":
                user.role = "student"
                changed.append("role")
            if not user.is_active:
                user.is_active = True
                changed.append("is_active")
            if changed:
                user.save(update_fields=changed)

        StudentProfile.objects.update_or_create(
            user=user,
            defaults={
                "student_code": f"SIM{index:04d}",
                "full_name": f"Estudiante Simulado {index:03d}",
                "program": program,
                "faculty": program.faculty,
                "campus": program.campus,
                "level": "Pregrado",
                "jornada": "Diurna",
            },
        )
        students.append(user)

    offset = 0
    for course_code, demand in DEMAND_PLAN:
        course = course_map[course_code]
        for user in students[offset : offset + demand]:
            EnrollmentQueue.objects.create(
                student=user,
                course=course,
                term=term,
                status="waiting",
            )
        offset += demand


def print_summary(term):
    demand_rows = (
        EnrollmentQueue.objects.filter(term=term, status="waiting")
        .values_list("course__code", "course__name")
        .order_by("course__code")
    )
    grouped = {}
    for code, name in demand_rows:
        grouped.setdefault((code, name), 0)
        grouped[(code, name)] += 1

    print("\nDatos de prueba creados correctamente.\n")
    print(f"Periodo objetivo del algoritmo: {term.name}")
    print("Demanda cargada:")
    for (code, name), total in grouped.items():
        print(f"  - {code} | {name}: {total} solicitudes")

    print("\nDocentes disponibles:")
    for teacher in Teacher.objects.filter(is_active=True).order_by("teacher_id"):
        qualified = teacher.qualified_courses.count()
        print(
            f"  - {teacher.teacher_id}: {teacher.first_name} {teacher.last_name} | "
            f"{teacher.contract.contract_type if teacher.contract else 'Sin contrato'} | "
            f"{qualified} materias calificadas"
        )

    print("\nCredenciales de prueba:")
    print("  - Estudiantes simulados: correo sim.student001@uniminuto.edu.co, clave Student123*")
    print("  - Docentes simulados: correo doc-sw-001@uniminuto.edu.co, clave Teacher123*")
    print("\nAhora puedes ejecutar el planificador semestral sobre /scheduling/plan-semestral/")


def create_data():
    campus, faculty, program, study_plan = ensure_program_structure()
    course_map = ensure_courses(study_plan)
    terms      = ensure_terms()
    ensure_timeslots()
    ensure_classrooms(campus)
    contracts    = create_contracts()
    target_term  = terms["2026-2"]
    ensure_teachers(program, faculty, campus, contracts, course_map, target_term)
    ensure_students_and_demand(course_map, target_term)
    print_summary(target_term)


if __name__ == "__main__":
    create_data()
