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

# ── Programa real ──────────────────────────────────────────────────────────────
REAL_PROGRAM_CODE = "ISOF/ SNIES: 107615"
REAL_PROGRAM_NAME = "Ingeniería de Software"

TERM_DEFINITIONS = [
    ("2026-1", date(2026, 1, 15), date(2026, 5, 15), False),
    ("2026-2", date(2026, 7, 15), date(2026, 11, 15), True),
]

# ── Timeslots ──────────────────────────────────────────────────────────────────
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
    ("Tuesday",   time(18, 0), time(19, 30)),
    ("Tuesday",   time(19, 30), time(21, 0)),
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
    ("Thursday",  time(18, 0), time(19, 30)),
    ("Thursday",  time(19, 30), time(21, 0)),
    # Viernes
    ("Friday",    time(7,  0), time(8,  30)),
    ("Friday",    time(8,  30), time(10, 0)),
    ("Friday",    time(10, 0), time(11, 30)),
    ("Friday",    time(14, 0), time(15, 30)),
    ("Friday",    time(18, 0), time(19, 30)),
    ("Friday",    time(19, 30), time(21, 0)),
    # Sábado
    ("Saturday",  time(8,  0), time(9,  30)),
    ("Saturday",  time(9,  30), time(11, 0)),
]

CLASSROOMS = [
    ("A101", "Salon flexible 1",      1, 25, "SALON"),
    ("A102", "Salon flexible 2",      1, 20, "SALON"),
    ("A103", "Salon flexible 3",      1, 30, "SALON"),
    ("A104", "Salon flexible 4",      1, 35, "SALON"),
    ("B201", "Laboratorio software",  1, 20, "SISTEMAS"),
    ("B202", "Laboratorio analitica", 1, 20, "SISTEMAS"),
    ("B203", "Laboratorio desarrollo",1, 24, "SISTEMAS"),
    ("B204", "Laboratorio redes",     1, 24, "SISTEMAS"),
    ("C301", "Salon magistral",       3, 40, "SALON"),
    ("C302", "Salon magistral 2",     3, 45, "SALON"),
    ("C303", "Salon magistral 3",     3, 50, "SALON"),
    ("D401", "Aula de innovacion",    4, 28, "SALON"),
    ("D402", "Aula de proyectos",     4, 32, "SALON"),
    ("D403", "Laboratorio IA",        4, 22, "SISTEMAS"),
    ("E501", "Auditorio academico",   5, 60, "SALON"),
]

TEACHER_DEFINITIONS = [
    {
        "teacher_id": "DOC-SW-001",
        "first_name": "Laura",
        "last_name": "Gonzalez",
        "contract_type": "Tiempo Completo",
        "qualified_codes": [
            "ISOFBL063", "ISOFBL073", "ISOFBL083", "ISOFBL103", "ISOFBL123",
        ],
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
        "qualified_codes": [
            "ISOFBL153", "ISOFBL163", "ISOFBL173", "ISOFBL183", "ESTA1061", "ISOFBL203",
        ],
        "availability": [
            ("Monday",    time(14, 0), time(18, 0)),
            ("Wednesday", time(7,  0), time(12, 0)),
            ("Thursday",  time(14, 0), time(18, 0)),
            ("Friday",    time(7,  0), time(11, 30)),
        ],
        "activities": [
            ("investigacion", "Thursday", time(15, 30), time(17, 0)),
        ],
    },
    {
        "teacher_id": "DOC-SW-003",
        "first_name": "Diana",
        "last_name": "Rojas",
        "contract_type": "Catedra",
        "qualified_codes": [
            "ISOFBL213", "ISOFBL223", "ISOFBL233", "ISOFBL243", "ISOFBL253", "ISOFBL263",
        ],
        "availability": [
            ("Tuesday",  time(18, 0), time(21, 0)),
            ("Thursday", time(18, 0), time(21, 0)),
            ("Saturday", time(8,  0), time(11, 0)),
        ],
        "activities": [],
    },
    {
        "teacher_id": "DOC-SW-004",
        "first_name": "Sergio",
        "last_name": "Diaz",
        "contract_type": "Tiempo Completo",
        "qualified_codes": [
            "ISOFBL011", "CBASBL021", "CBASBL151", "ISOFBL021", "ISOFBL031",
            "ISOFBL041", "ISOFBL051", "ISOFBL061", "ISOFBL071",
        ],
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
        "qualified_codes": [
            "ISOFBL013", "ISOFBL023", "ISOFBL033", "ISOFBL043", "ISOFBL053",
            "ISOFBL093", "ISOFBL133", "ISOFBL143", "ISOFBL193",
        ],
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
        "qualified_codes": [
            "ISOFBL083", "ISOFBL103", "ISOFBL113", "ISOFBL123", "ISOFBL223", "ISOFBL233",
        ],
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
        "qualified_codes": [
            "ISOFBL011", "CBASBL021", "CBASBL151", "ESTA1061", "ISOFBL021", "ISOFBL031",
        ],
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
        "qualified_codes": [
            "ISOFBL013", "ISOFBL023", "ISOFBL033", "ISOFBL043", "ISOFBL053",
            "ISOFBL093", "ISOFBL113", "ISOFBL193",
        ],
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
        "teacher_id": "DOC-SW-009",
        "first_name": "Valentina",
        "last_name": "Castro",
        "contract_type": "Catedra",
        "qualified_codes": [
            "ISOFBL153", "ISOFBL163", "ISOFBL173", "ISOFBL183", "ISOFBL203", "ISOFBL263",
        ],
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
        "qualified_codes": [
            "ISOFBL063", "ISOFBL073", "ISOFBL083", "ISOFBL103", "ISOFBL123", "ISOFBL133",
        ],
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
        "qualified_codes": [
            "ISOFBL213", "ISOFBL223", "ISOFBL233", "ISOFBL243", "ISOFBL253",
            "INFO1010", "LENG1010", "LENG1020", "INGL1010", "INGL1020", "INGL1030",
            "ISOFBL012", "ISOFBL014", "ISOFBL022", "ISOFBL024", "ISOFBL032",
            "ISOFBL034", "ISOFBL044",
        ],
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
        "qualified_codes": [
            "ISOFBL041", "ISOFBL051", "ISOFBL061", "ISOFBL163", "ISOFBL183", "ESTA1061",
        ],
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
        "qualified_codes": [
            "ISOFBL011", "CBASBL021", "CBASBL151", "ISOFBL021", "ISOFBL031",
            "INFO1010", "LENG1010", "LENG1020", "INGL1010", "INGL1020", "INGL1030",
            "FHUM1010", "FHUM1020", "FHUM1120",
        ],
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
        "qualified_codes": [
            "ISOFBL013", "ISOFBL023", "ISOFBL033", "ISOFBL043", "ISOFBL053", "ISOFBL263",
            "PRAC1010", "PRAC1020", "CIDUBLO11", "ADMI1060",
            "ISOFBL081", "ISOFBL273", "ISOFBL054", "ISOFBL064", "ISOFBL071",
        ],
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
        "qualified_codes": [
            "ISOFBL133", "ISOFBL143", "ISOFBL153", "ISOFBL193", "ISOFBL203",
            "ISOFBL223", "ISOFBL243", "ISOFBL253",
            "PRAC1010", "PRAC1020", "CIDUBLO11", "ETIC190",
            "ISOFBL081", "ISOFBL273", "ISOFBL054", "ISOFBL064",
        ],
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

# ── Pensum completo ────────────────────────────────────────────────────────────
FULL_COURSE_SPECS = [
    ("INFO1010",  "Gestión Básica de la Información",                 1, 2),
    ("LENG1010",  "Comunicación Escrita y Procesos Lectores I",        1, 2),
    ("ISOFBL011", "Precálculo",                                        1, 3),
    ("ISOFBL071", "Introducción a la Ingeniería",                      1, 2),
    ("FHUM1010",  "Proyecto de Vida",                                  1, 2),
    ("ISOFBL063", "Lógica de Programación",                            1, 3),
    ("INGL1010",  "Inglés I",                                          1, 2),
    ("ESTA1061",  "Probabilidad y Estadística",                        2, 3),
    ("LENG1020",  "Comunicación Escrita y Procesos Lectores II",       2, 2),
    ("CBASBL021", "Cálculo Diferencial",                               2, 3),
    ("FHUM1020",  "Cátedra Minuto de Dios",                           2, 2),
    ("ISOFBL073", "Programación Básica",                               2, 3),
    ("INGL1020",  "Inglés II",                                         2, 2),
    ("CBASBL151", "Cálculo Integral",                                  3, 3),
    ("ISOFBL051", "Física Mecánica",                                   3, 2),
    ("CIDUBLO11", "Metodología de la Investigación",                   3, 2),
    ("ISOFBL083", "Programación Orientada a Objetos",                  3, 3),
    ("ISOFBL153", "Análisis y Diseño de Bases de Datos",               3, 3),
    ("INGL1030",  "Inglés III",                                        3, 2),
    ("ISOFBL021", "Álgebra Lineal",                                    3, 3),
    ("ISOFBL031", "Ecuaciones Diferenciales",                          4, 3),
    ("PRAC1020",  "Desarrollo Social Contemporáneo",                   4, 2),
    ("ISOFBL013", "Arquitectura de Computadores",                      4, 3),
    ("ISOFBL093", "Estructura de Datos",                               4, 3),
    ("ISOFBL163", "Sistemas de Gestión de Bases de Datos",             4, 3),
    ("ISOFBL213", "Requerimientos de Software",                        4, 2),
    ("ISOFBL223", "Modelamiento de Software",                          5, 2),
    ("PRAC1010",  "Práctica en Responsabilidad Social",                5, 2),
    ("ISOFBL023", "Sistemas Operativos",                               5, 2),
    ("ISOFBL103", "Programación Web",                                  5, 3),
    ("ISOFBL173", "Sistemas Transaccionales",                          5, 3),
    ("ISOFBL233", "Diseño de Software",                                6, 2),
    ("ISOFBL041", "Cálculo Vectorial",                                 6, 2),
    ("ISOFBL061", "Física Electromagnética",                           6, 2),
    ("ISOFBL081", "Formulación y Evaluación de Proyectos",             6, 2),
    ("ISOFBL033", "Redes de Computadores",                             6, 2),
    ("ISOFBL113", "Programación de Aplicaciones Móviles",              6, 3),
    ("ISOFBL183", "Arquitectura de Datos",                             6, 2),
    ("ISOFBL243", "Métodos de Ingeniería de Software",                 7, 2),
    ("ISOFBL014", "Electiva CPC I",                                    7, 4),
    ("ISOFBL012", "Electiva CMD I",                                    7, 2),
    ("ISOFBL043", "Sistemas Telemáticos",                               7, 2),
    ("ISOFBL123", "Programación Integrada y Tecnología Web",            7, 2),
    ("ISOFBL193", "Simulación de Sistemas",                            7, 3),
    ("ISOFBL253", "Aseguramiento de Calidad de Software",               7, 3),
    ("ISOFBL024", "Electiva CPC II",                                   8, 4),
    ("ISOFBL022", "Electiva CMD II",                                   8, 2),
    ("ADMI1060",  "Emprendimiento",                                    8, 2),
    ("ISOFBL053", "Seguridad de la Información",                       8, 3),
    ("ISOFBL133", "Inteligencia Artificial",                           8, 3),
    ("ISOFBL034", "Electiva CPC III",                                  9, 4),
    ("ETIC190",   "Ética Profesional",                                 9, 2),
    ("ISOFBL143", "Sistemas Expertos",                                 9, 3),
    ("ISOFBL263", "Gerencia de Proyectos de Software",                 9, 2),
    ("ISOFBL044", "Electiva CPC IV",                                  10, 4),
    ("ISOFBL054", "Práctica Profesional",                             10, 4),
    ("ISOFBL032", "Electiva CMD III",                                 10, 2),
    ("FHUM1120",  "Constitución Política",                            10, 2),
    ("ISOFBL203", "Almacenamiento y Minería de Datos",                10, 3),
    ("ISOFBL273", "Fundamentos en Derechos de Software",              10, 2),
    ("ISOFBL064", "Opción de Grado",                                  10, 4),
]

# ── Demanda: 6 estudiantes simulados por materia ──────────────────────────────
# Solo se incluyen materias que el algoritmo genético puede planificar
# (requieren docente + aula). Electivas y prácticas se omiten de la demanda.
DEMAND_PLAN = [
    ("ISOFBL011",  6),   # Precálculo
    ("CBASBL021",  6),   # Cálculo Diferencial
    ("CBASBL151",  6),   # Cálculo Integral
    ("ISOFBL021",  6),   # Álgebra Lineal
    ("ISOFBL031",  6),   # Ecuaciones Diferenciales
    ("ISOFBL041",  6),   # Cálculo Vectorial
    ("ISOFBL051",  6),   # Física Mecánica
    ("ISOFBL061",  6),   # Física Electromagnética
    ("ESTA1061",   6),   # Probabilidad y Estadística
    ("ISOFBL063",  6),   # Lógica de Programación
    ("ISOFBL073",  6),   # Programación Básica
    ("ISOFBL083",  6),   # POO
    ("ISOFBL093",  6),   # Estructura de Datos
    ("ISOFBL103",  6),   # Programación Web
    ("ISOFBL113",  6),   # Apps Móviles
    ("ISOFBL123",  6),   # Prog. Integrada y Tec. Web
    ("ISOFBL133",  6),   # Inteligencia Artificial
    ("ISOFBL143",  6),   # Sistemas Expertos
    ("ISOFBL153",  6),   # Análisis y Diseño BD
    ("ISOFBL163",  6),   # SGBD
    ("ISOFBL173",  6),   # Sistemas Transaccionales
    ("ISOFBL183",  6),   # Arquitectura de Datos
    ("ISOFBL193",  6),   # Simulación de Sistemas
    ("ISOFBL203",  6),   # Almacenamiento y Minería
    ("ISOFBL013",  6),   # Arq. Computadores
    ("ISOFBL023",  6),   # Sistemas Operativos
    ("ISOFBL033",  6),   # Redes de Computadores
    ("ISOFBL043",  6),   # Sistemas Telemáticos
    ("ISOFBL053",  6),   # Seguridad de la Información
    ("ISOFBL071",  6),   # Intro Ingeniería
    ("ISOFBL213",  6),   # Requerimientos de Software
    ("ISOFBL223",  6),   # Modelamiento de Software
    ("ISOFBL233",  6),   # Diseño de Software
    ("ISOFBL243",  6),   # Métodos de IS
    ("ISOFBL253",  6),   # Aseguramiento de Calidad
    ("ISOFBL263",  6),   # Gerencia de Proyectos
    ("INFO1010",   6),   # Gestión Básica de la Información
    ("LENG1010",   6),   # Comunicación Escrita I
    ("LENG1020",   6),   # Comunicación Escrita II
    ("INGL1010",   6),   # Inglés I
    ("INGL1020",   6),   # Inglés II
    ("INGL1030",   6),   # Inglés III
    ("FHUM1010",   6),   # Proyecto de Vida
    ("FHUM1020",   6),   # Cátedra Minuto de Dios
    ("FHUM1120",   6),   # Constitución Política
    ("CIDUBLO11",  6),   # Metodología de la Investigación
    ("ADMI1060",   6),   # Emprendimiento
    ("ETIC190",    6),   # Ética Profesional
    ("ISOFBL081",  6),   # Form. y Eval. Proyectos
    ("ISOFBL273",  6),   # Derechos de Software
]


# ── Funciones ─────────────────────────────────────────────────────────────────

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
    faculty, _ = Faculty.objects.get_or_create(
        name="Facultad de Ingenieria",
        defaults={"campus": campus},
    )
    if faculty.campus_id != campus.id:
        faculty.campus = campus
        faculty.save(update_fields=["campus"])

    # Usa el programa real, no crea uno nuevo
    try:
        program = AcademicProgram.objects.get(code=REAL_PROGRAM_CODE)
    except AcademicProgram.DoesNotExist:
        program = AcademicProgram.objects.create(
            code=REAL_PROGRAM_CODE,
            name=REAL_PROGRAM_NAME,
            faculty=faculty,
            campus=campus,
        )

    study_plan, _ = StudyPlan.objects.get_or_create(
        program=program,
        version="2026-2",
        defaults={"description": "Plan de estudios Ingeniería de Software 2026-2"},
    )
    return campus, faculty, program, study_plan


def ensure_courses(study_plan):
    course_map = {}
    for code, name, semester, credits in FULL_COURSE_SPECS:
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


def ensure_students_and_demand(course_map, term, program):
    EnrollmentQueue.objects.filter(term=term, student__email__startswith="sim.student").delete()
    StudentProfile.objects.filter(user__email__startswith="sim.student").delete()

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
                "program": program,           # ← programa real
                "faculty": program.faculty,
                "campus": program.campus,
                "level": "Pregrado",
                "jornada": "Diurna",
            },
        )
        students.append(user)

    offset = 0
    for course_code, demand in DEMAND_PLAN:
        course = course_map.get(course_code)
        if not course:
            print(f"  ⚠  Curso {course_code} no encontrado, saltando demanda.")
            offset += demand
            continue
        for user in students[offset: offset + demand]:
            EnrollmentQueue.objects.get_or_create(
                student=user,
                course=course,
                term=term,
                defaults={"status": "waiting"},
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
    print(f"Programa usado: {REAL_PROGRAM_CODE}\n")
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
    print("  - Estudiantes simulados: sim.student001@uniminuto.edu.co / Student123*")
    print("  - Docentes simulados:    doc-sw-001@uniminuto.edu.co / Teacher123*")
    print("\nAhora puedes ejecutar el planificador semestral sobre /scheduling/plan-semestral/")


def create_data():
    campus, faculty, program, study_plan = ensure_program_structure()
    course_map   = ensure_courses(study_plan)
    terms        = ensure_terms()
    ensure_timeslots()
    ensure_classrooms(campus)
    contracts    = create_contracts()
    target_term  = terms["2026-2"]
    ensure_teachers(program, faculty, campus, contracts, course_map, target_term)
    ensure_students_and_demand(course_map, target_term, program)
    print_summary(target_term)


if __name__ == "__main__":
    create_data()