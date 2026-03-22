from django.shortcuts import render, redirect
from django.contrib.auth import login
from .login import EmailLoginForm
from .services.excel_importer import import_excel_users

from academic_core.models import Campus, Faculty, AcademicProgram, Course, StudyPlan
from teaching.models import Teacher
from classrooms.models import Classroom
from .models import StudentProfile


SCHEDULE_ROWS = [
    ("6:00 am", "", "", "Tópicos Especiales", "", ""),
    ("6:30 am", "", "", "Tópicos Especiales", "", ""),
    ("7:00 am", "", "Inglés B2", "Tópicos Especiales", "", ""),
    ("8:00 am", "Cálculo Diferencial", "Inglés B2", "", "", "Cálculo Diferencial"),
    ("8:30 am", "Cálculo Diferencial", "", "", "Programación Web", "Cálculo Diferencial"),
    ("9:00 am", "", "Bases de Datos", "", "Programación Web", ""),
    ("10:30 am", "Telemática", "", "Telemática", "", ""),
    ("11:00 am", "Telemática", "", "Telemática", "", ""),
]

SUBJECT_OPTIONS = [
    {
        "id": "MAT-001",
        "materia": "Cálculo Diferencial",
        "codigo": "MAT101",
        "grupo": "03",
        "aula": "A-305",
        "dia": "Viernes",
        "inicio": "8:00 am",
        "fin": "10:00 am",
        "docente": "Laura González",
        "programa": "Ingeniería de Software",
        "descripcion": "Derivadas y límites",
    },
    {
        "id": "MAT-002",
        "materia": "Telemática",
        "codigo": "TEL401",
        "grupo": "01",
        "aula": "B-204",
        "dia": "Lunes",
        "inicio": "10:30 am",
        "fin": "12:00 pm",
        "docente": "Andrés Pérez",
        "programa": "Ingeniería de Redes",
        "descripcion": "Redes básicas",
    },
    {
        "id": "MAT-003",
        "materia": "Programación Web",
        "codigo": "PRG220",
        "grupo": "02",
        "aula": "C-110",
        "dia": "Jueves",
        "inicio": "8:30 am",
        "fin": "10:30 am",
        "docente": "Diana Rojas",
        "programa": "Ingeniería de Software",
        "descripcion": "Frontend y backend",
    },
    {
        "id": "MAT-004",
        "materia": "Bases de Datos",
        "codigo": "BD201",
        "grupo": "05",
        "aula": "B-104",
        "dia": "Martes",
        "inicio": "9:00 am",
        "fin": "11:00 am",
        "docente": "Sergio Díaz",
        "programa": "Análisis de Datos",
        "descripcion": "Modelado y SQL",
    },
]

TEACHERS = [
    {
        "nombre": "Laura González",
        "cedula": "1.001.223.456",
        "codigo_profesor": "DOC-001",
        "direccion": "Cra. 52 #45-10",
        "nivel_ingles": "B2",
        "programa": "Ingeniería de Software",
        "facultad": "Facultad de Ingeniería",
        "sede": "Sede Principal",
        "materia": "Cálculo Diferencial",
        "codigo_materia": "MAT101",
    },
    {
        "nombre": "Andrés Pérez",
        "cedula": "80.456.123",
        "codigo_profesor": "DOC-002",
        "direccion": "Cl. 12 #30-18",
        "nivel_ingles": "B1",
        "programa": "Ingeniería de Redes",
        "facultad": "Facultad de Ingeniería",
        "sede": "Sede Norte",
        "materia": "Telemática",
        "codigo_materia": "TEL401",
    },
    {
        "nombre": "Diana Rojas",
        "cedula": "52.778.901",
        "codigo_profesor": "DOC-003",
        "direccion": "Av. 80 #65-12",
        "nivel_ingles": "C1",
        "programa": "Ingeniería de Software",
        "facultad": "Facultad de Ingeniería",
        "sede": "Sede Principal",
        "materia": "Programación Web",
        "codigo_materia": "PRG220",
    },
    {
        "nombre": "Sergio Díaz",
        "cedula": "71.009.335",
        "codigo_profesor": "DOC-004",
        "direccion": "Cra. 70 #44-01",
        "nivel_ingles": "B2",
        "programa": "Análisis de Datos",
        "facultad": "Facultad de Ciencias Empresariales",
        "sede": "Sede Sur",
        "materia": "Bases de Datos",
        "codigo_materia": "BD201",
    },
]

STUDENTS = [
    {
        "nombre": "Camila Torres",
        "cedula": "1.011.445.900",
        "codigo_estudiante": "EST-202401",
        "direccion": "Cra. 43 #21-18",
        "facultad": "Facultad de Ingeniería",
        "sede": "Sede Principal",
    },
    {
        "nombre": "Juan David Restrepo",
        "cedula": "1.020.334.667",
        "codigo_estudiante": "EST-202402",
        "direccion": "Cl. 54 #80-11",
        "facultad": "Facultad de Educación",
        "sede": "Sede Norte",
    },
    {
        "nombre": "Mariana López",
        "cedula": "1.033.778.991",
        "codigo_estudiante": "EST-202403",
        "direccion": "Av. 33 #65-72",
        "facultad": "Facultad de Ciencias Empresariales",
        "sede": "Sede Sur",
    },
]

CAMPUSES = [
    {"id": "SED-01", "nombre": "Sede Principal"},
    {"id": "SED-02", "nombre": "Sede Norte"},
    {"id": "SED-03", "nombre": "Sede Sur"},
]

FACULTIES = [
    {"id": "FAC-01", "nombre": "Facultad de Ingeniería"},
    {"id": "FAC-02", "nombre": "Facultad de Educación"},
    {"id": "FAC-03", "nombre": "Facultad de Ciencias Empresariales"},
]

PROGRAMS = [
    {"id": "PRO-01", "nombre": "Ingeniería de Software"},
    {"id": "PRO-02", "nombre": "Ingeniería de Redes"},
    {"id": "PRO-03", "nombre": "Análisis de Datos"},
]

STUDY_PLANS = [
    {
        "programa": "Ingeniería de Software",
        "semestres": [
            {"numero": 1, "materias": ["Cálculo Diferencial", "Introducción a la Programación", "Competencias Comunicativas"]},
            {"numero": 2, "materias": ["Álgebra Lineal", "Programación Orientada a Objetos", "Inglés I"]},
            {"numero": 3, "materias": ["Bases de Datos", "Estructuras de Datos", "Inglés II"]},
            {"numero": 4, "materias": ["Programación Web", "Arquitectura de Software", "Investigación I"]},
        ],
    },
    {
        "programa": "Ingeniería de Redes",
        "semestres": [
            {"numero": 1, "materias": ["Lógica", "Electrónica Básica", "Competencias Digitales"]},
            {"numero": 2, "materias": ["Telemática", "Fundamentos de Redes", "Inglés I"]},
            {"numero": 3, "materias": ["Protocolos de Comunicación", "Seguridad Informática", "Inglés II"]},
        ],
    },
    {
        "programa": "Análisis de Datos",
        "semestres": [
            {"numero": 1, "materias": ["Matemática Básica", "Herramientas Ofimáticas", "Comunicación Escrita"]},
            {"numero": 2, "materias": ["Estadística", "Bases de Datos", "Visualización de Datos"]},
            {"numero": 3, "materias": ["Minería de Datos", "Machine Learning", "Analítica de Negocio"]},
        ],
    },
]

CLASSROOMS = [
    ("A", "201", "Aula estándar (30 puestos)", "6:00 am", "10:00 pm"),
    ("A", "305", "Aula con proyector", "7:00 am", "9:00 pm"),
    ("B", "104", "Laboratorio de sistemas", "6:30 am", "8:00 pm"),
    ("C", "110", "Sala de innovación", "8:00 am", "6:00 pm"),
]


def _base_context(request):
    user_name = request.user.email if request.user.is_authenticated else "Invitado"
    return {
        "user_name": user_name,
        "schedule_rows": SCHEDULE_ROWS,
        "subject_options": SUBJECT_OPTIONS,
        "teachers": TEACHERS,
        "students": STUDENTS,
        "campuses": CAMPUSES,
        "faculties": FACULTIES,
        "programs": PROGRAMS,
        "study_plans": STUDY_PLANS,
        "classrooms": CLASSROOMS,
    }


def dashboard(request):
    context = _base_context(request)
    return render(request, "dashboard/dashboard.html", context)


def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = EmailLoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data["user"]
            login(request, user)
            return redirect("home")
    else:
        form = EmailLoginForm()

    return render(request, "access_support/login.html", {"form": form})


def upload_excel(request):
    if request.method == "POST":
        excel_file = request.FILES["excel_file"]
        import_excel_users(excel_file)
        return render(
            request,
            "admin/upload_excel.html",
            {"message": "Import completed successfully"},
        )

    return render(request, "admin/upload_excel.html")


def calendar_view(request):
    context = _base_context(request)
    return render(request, "scheduling/schedule.html", context)


def add_calendar_view(request):
    context = _base_context(request)
    return render(request, "dashboard/add_calendar.html", context)


def subjects_view(request):
    context = _base_context(request)
    context["items"] = Course.objects.all().order_by("id")
    return render(request, "dashboard/subjects.html", context)


def create_subject_view(request):
    context = _base_context(request)

    context["teachers_db"] = Teacher.objects.all().order_by("first_name", "last_name")
    context["classrooms_db"] = Classroom.objects.all().order_by("classroom_id")
    context["programs_db"] = AcademicProgram.objects.all().order_by("name")

    form_data = {}

    if request.method == "POST":
        form_data = {
            "id": request.POST.get("id", ""),
            "materia": request.POST.get("materia", ""),
            "codigo": request.POST.get("codigo", ""),
            "grupo": request.POST.get("grupo", ""),
            "docente": request.POST.get("docente", ""),
            "aula": request.POST.get("aula", ""),
            "dia": request.POST.get("dia", ""),
            "inicio": request.POST.get("inicio", ""),
            "fin": request.POST.get("fin", ""),
            "programa": request.POST.get("programa", ""),
            "descripcion": request.POST.get("descripcion", ""),
        }
        context["success_message"] = "Materia diligenciada correctamente."

    context["form_data"] = form_data
    return render(request, "dashboard/create_subject.html", context)


def subject_detail_view(request):
    context = _base_context(request)
    context["selected_subject"] = SUBJECT_OPTIONS[0]
    return render(request, "dashboard/subject_detail.html", context)


def added_success_view(request):
    context = _base_context(request)
    context["selected_subject"] = SUBJECT_OPTIONS[0]
    return render(request, "dashboard/success.html", context)


def teachers_view(request):
    context = _base_context(request)
    context["items"] = Teacher.objects.all().order_by("id")
    return render(request, "dashboard/teachers.html", context)


def students_view(request):
    context = _base_context(request)
    context["items"] = StudentProfile.objects.all().order_by("id")
    return render(request, "dashboard/students.html", context)


def campuses_view(request):
    context = _base_context(request)
    context["items"] = Campus.objects.all().order_by("id")
    return render(request, "dashboard/campuses.html", context)


def faculties_view(request):
    context = _base_context(request)
    context["items"] = Faculty.objects.all().order_by("id")
    return render(request, "dashboard/faculties.html", context)


def classrooms_view(request):
    context = _base_context(request)
    context["items"] = Classroom.objects.all().order_by("id")
    return render(request, "dashboard/classrooms.html", context)


def programs_view(request):
    context = _base_context(request)
    context["items"] = AcademicProgram.objects.all().order_by("id")
    return render(request, "dashboard/programs.html", context)


def study_plan_view(request):
    context = _base_context(request)
    selected_program = request.GET.get("program")

    if selected_program:
        filtered_plans = [plan for plan in STUDY_PLANS if plan["programa"] == selected_program]
    else:
        filtered_plans = STUDY_PLANS

    context["selected_program"] = selected_program
    context["filtered_plans"] = filtered_plans
    context["items"] = StudyPlan.objects.all().order_by("id")
    return render(request, "dashboard/study_plan.html", context)


def import_view(request):
    context = _base_context(request)
    return render(request, "dashboard/import.html", context)


def profile_view(request):
    context = _base_context(request)
    return render(request, "dashboard/profile.html", context)


def settings_view(request):
    context = _base_context(request)
    return render(request, "dashboard/settings.html", context)