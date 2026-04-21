import os
from datetime import date, time

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project_planner.settings")
django.setup()

from django.contrib.auth import get_user_model

from academic_core.models import AcademicProgram, AcademicTerm, Campus, Course, Faculty, StudyPlan
from classrooms.models import Classroom, TimeSlot
from scheduling_enrollment.models import EnrollmentQueue, TeacherActivity
from teaching.models import Availability, ContractRule, Teacher


User = get_user_model()


TERM_DEFINITIONS = [
    ("2026-1", date(2026, 1, 15), date(2026, 5, 15), False),
    ("2026-2", date(2026, 7, 15), date(2026, 11, 15), True),
]

TIMESLOTS = [
    ("Monday", time(7, 0), time(8, 30)),
    ("Monday", time(8, 30), time(10, 0)),
    ("Monday", time(10, 0), time(11, 30)),
    ("Monday", time(14, 0), time(15, 30)),
    ("Monday", time(15, 30), time(17, 0)),
    ("Tuesday", time(7, 0), time(8, 30)),
    ("Tuesday", time(8, 30), time(10, 0)),
    ("Tuesday", time(10, 0), time(11, 30)),
    ("Tuesday", time(14, 0), time(15, 30)),
    ("Tuesday", time(15, 30), time(17, 0)),
    ("Wednesday", time(7, 0), time(8, 30)),
    ("Wednesday", time(8, 30), time(10, 0)),
    ("Wednesday", time(10, 0), time(11, 30)),
    ("Wednesday", time(14, 0), time(15, 30)),
    ("Wednesday", time(15, 30), time(17, 0)),
    ("Thursday", time(7, 0), time(8, 30)),
    ("Thursday", time(8, 30), time(10, 0)),
    ("Thursday", time(10, 0), time(11, 30)),
    ("Thursday", time(14, 0), time(15, 30)),
    ("Thursday", time(15, 30), time(17, 0)),
    ("Friday", time(7, 0), time(8, 30)),
    ("Friday", time(8, 30), time(10, 0)),
    ("Friday", time(10, 0), time(11, 30)),
    ("Friday", time(14, 0), time(15, 30)),
    ("Saturday", time(8, 0), time(9, 30)),
    ("Saturday", time(9, 30), time(11, 0)),
]

CLASSROOMS = [
    ("A101", "Salon flexible 1", 1, 25, "SALON"),
    ("A102", "Salon flexible 2", 1, 20, "SALON"),
    ("B201", "Laboratorio software", 2, 20, "SISTEMAS"),
    ("B202", "Laboratorio analitica", 2, 20, "SISTEMAS"),
    ("C301", "Salon magistral", 3, 40, "SALON"),
]

TEACHER_DEFINITIONS = [
    {
        "teacher_id": "DOC-SW-001",
        "first_name": "Laura",
        "last_name": "Gonzalez",
        "contract_type": "Tiempo Completo",
        "qualified_codes": ["ISOFBL063", "ISOFBL073", "ISOFBL083", "ISOFBL103", "ISOFBL123"],
        "availability": [
            ("Monday", time(7, 0), time(12, 0)),
            ("Tuesday", time(7, 0), time(12, 0)),
            ("Wednesday", time(14, 0), time(18, 0)),
            ("Thursday", time(7, 0), time(12, 0)),
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
            ("Monday", time(14, 0), time(18, 0)),
            ("Wednesday", time(7, 0), time(12, 0)),
            ("Thursday", time(14, 0), time(18, 0)),
            ("Friday", time(7, 0), time(11, 30)),
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
        "qualified_codes": ["ISOFBL213", "ISOFBL223", "ISOFBL233", "ISOFBL243", "ISOFBL263"],
        "availability": [
            ("Tuesday", time(18, 0), time(21, 0)),
            ("Thursday", time(18, 0), time(21, 0)),
            ("Saturday", time(8, 0), time(12, 0)),
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
            ("Monday", time(7, 0), time(12, 0)),
            ("Wednesday", time(7, 0), time(12, 0)),
            ("Friday", time(7, 0), time(12, 0)),
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
            ("Tuesday", time(7, 0), time(12, 0)),
            ("Wednesday", time(14, 0), time(18, 0)),
            ("Thursday", time(7, 0), time(12, 0)),
            ("Friday", time(14, 0), time(18, 0)),
        ],
        "activities": [],
    },
]

DEMAND_PLAN = [
    ("CBASBL021", 38),
    ("ISOFBL073", 33),
    ("ISOFBL153", 26),
    ("ISOFBL103", 24),
    ("ISOFBL213", 17),
    ("ISOFBL023", 15),
    ("ISOFBL133", 11),
    ("ESTA1061", 8),
    ("ISOFBL263", 6),
    ("ISOFBL203", 4),
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
        ("CBASBL021", "Calculo Diferencial", 2, 3),
        ("ESTA1061", "Probabilidad y Estadistica", 3, 3),
        ("ISOFBL073", "Programacion Basica", 2, 3),
        ("ISOFBL103", "Programacion Web", 5, 3),
        ("ISOFBL153", "Analisis y Diseno de Bases de Datos", 3, 3),
        ("ISOFBL213", "Requerimientos de Software", 4, 2),
        ("ISOFBL023", "Sistemas Operativos", 5, 2),
        ("ISOFBL133", "Inteligencia Artificial", 8, 3),
        ("ISOFBL263", "Gerencia de Proyectos de Software", 9, 2),
        ("ISOFBL203", "Almacenamiento y Mineria de Datos", 10, 3),
        ("ISOFBL021", "Algebra Lineal", 3, 3),
        ("ISOFBL031", "Ecuaciones Diferenciales", 4, 3),
        ("CBASBL151", "Calculo Integral", 3, 3),
        ("ISOFBL041", "Calculo Vectorial", 6, 2),
        ("ISOFBL051", "Fisica Mecanica", 3, 2),
        ("ISOFBL083", "Programacion Orientada a Objetos", 3, 3),
        ("ISOFBL123", "Programacion Integrada y Tecnologias Web", 7, 2),
        ("ISOFBL163", "Sistemas de Gestion de Bases de Datos", 4, 3),
        ("ISOFBL183", "Arquitectura de Datos", 6, 2),
        ("ISOFBL223", "Modelamiento de Software", 5, 2),
        ("ISOFBL233", "Diseno de Software", 6, 2),
        ("ISOFBL243", "Metodos de Ingenieria de Software", 7, 2),
        ("ISOFBL013", "Arquitectura de Computadores", 4, 3),
        ("ISOFBL033", "Redes de Computadores", 6, 2),
        ("ISOFBL043", "Sistemas Telematicos", 7, 2),
        ("ISOFBL053", "Seguridad de la Informacion", 8, 3),
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
                name=name,
                start_date=start,
                end_date=end,
                active=active,
            )
        else:
            term.start_date = start
            term.end_date = end
            term.active = active
            term.save(update_fields=["start_date", "end_date", "active"])
            matches.exclude(id=term.id).delete()
        terms[name] = term
    return terms


def ensure_timeslots():
    for day, start_time, end_time in TIMESLOTS:
        TimeSlot.objects.get_or_create(
            day=day,
            start_time=start_time,
            end_time=end_time,
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
        teacher, _ = Teacher.objects.update_or_create(
            teacher_id=spec["teacher_id"],
            defaults={
                "first_name": spec["first_name"],
                "last_name": spec["last_name"],
                "program": program,
                "faculty": faculty,
                "campus": campus,
                "contract": contracts[spec["contract_type"]],
                "is_active": True,
            },
        )
        teacher.qualified_courses.set([course_map[code] for code in spec["qualified_codes"] if code in course_map])

        Availability.objects.filter(teacher=teacher).delete()
        for day, start_time, end_time in spec["availability"]:
            Availability.objects.create(
                teacher=teacher,
                day=day,
                start_time=start_time,
                end_time=end_time,
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

    total_students = sum(demand for _, demand in DEMAND_PLAN)
    students = []
    for index in range(1, total_students + 1):
        email = f"sim.student{index:03d}@uniminuto.edu.co"
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "role": "student",
                "is_active": True,
            },
        )
        if created:
            user.set_password("Student123*")
            user.save(update_fields=["password"])
        students.append(user)

    offset = 0
    for course_code, demand in DEMAND_PLAN:
        course = course_map[course_code]
        for user in students[offset: offset + demand]:
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

    print("\nAhora puedes ejecutar el planificador semestral sobre /scheduling/plan-semestral/")


def create_data():
    campus, faculty, program, study_plan = ensure_program_structure()
    course_map = ensure_courses(study_plan)
    terms = ensure_terms()
    ensure_timeslots()
    ensure_classrooms(campus)
    contracts = create_contracts()
    target_term = terms["2026-2"]
    ensure_teachers(program, faculty, campus, contracts, course_map, target_term)
    ensure_students_and_demand(course_map, target_term)
    print_summary(target_term)


if __name__ == "__main__":
    create_data()
