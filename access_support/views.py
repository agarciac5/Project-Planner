from django.shortcuts import render, redirect
from django.contrib.auth import login
from .login import EmailLoginForm
from .services.excel_importer import import_excel_users


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
        "materia": "Telemática",
        "codigo": "TEL401",
        "grupo": "01",
        "aula": "B-204",
        "dia": "Lunes",
        "inicio": "10:30 am",
        "fin": "12:00 pm",
        "docente": "Andrés Pérez",
        "descripcion": "Redes básicas",
    },
    {
        "materia": "Telemática",
        "codigo": "TEL402",
        "grupo": "02",
        "aula": "B-208",
        "dia": "Miércoles",
        "inicio": "10:30 am",
        "fin": "12:00 pm",
        "docente": "Diana Rojas",
        "descripcion": "Protocolos y conectividad",
    },
    {
        "materia": "Cálculo Diferencial",
        "codigo": "MAT101",
        "grupo": "03",
        "aula": "A-305",
        "dia": "Viernes",
        "inicio": "8:00 am",
        "fin": "10:00 am",
        "docente": "Laura González",
        "descripcion": "Derivadas y límites",
    },
]

TEACHERS = [
    ("Laura González", "1.001.223.456", "B2", "Cálculo Diferencial", "MAT101"),
    ("Laura González", "1.001.223.456", "B2", "Métodos Cuantitativos", "MAT203"),
    ("Andrés Pérez", "80.456.123", "B1", "Telemática", "TEL401"),
    ("Diana Rojas", "52.778.901", "C1", "Programación Web", "PRG220"),
]

CLASSROOMS = [
    ("A", "201", "Aula estándar (30 puestos)", "6:00 am", "10:00 pm"),
    ("A", "305", "Aula con proyector", "7:00 am", "9:00 pm"),
    ("B", "104", "Laboratorio de sistemas", "6:30 am", "8:00 pm"),
    ("C", "110", "Sala de innovación", "8:00 am", "6:00 pm"),
]

PROGRAMS = [
    ("Ingeniería de Software", "ISW", "10 semestres", "Pregrado", "Activo"),
    ("Telemática", "TEL", "8 semestres", "Tecnología", "Activo"),
    ("Análisis de Datos", "ADS", "8 semestres", "Tecnología", "Activo"),
    ("Diseño Multimedia", "DMM", "8 semestres", "Tecnología", "Activo"),
]


def _base_context(request):
    user_name = request.user.email if request.user.is_authenticated else "Invitado"
    return {
        "user_name": user_name,
        "schedule_rows": SCHEDULE_ROWS,
        "subject_options": SUBJECT_OPTIONS,
        "teachers": TEACHERS,
        "classrooms": CLASSROOMS,
        "programs": PROGRAMS,
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
    return render(request, "dashboard/subjects.html", context)


def subject_detail_view(request):
    context = _base_context(request)
    context["selected_subject"] = SUBJECT_OPTIONS[2]
    return render(request, "dashboard/subject_detail.html", context)


def added_success_view(request):
    context = _base_context(request)
    context["selected_subject"] = SUBJECT_OPTIONS[2]
    return render(request, "dashboard/success.html", context)


def teachers_view(request):
    context = _base_context(request)
    return render(request, "dashboard/teachers.html", context)


def classrooms_view(request):
    context = _base_context(request)
    return render(request, "dashboard/classrooms.html", context)


def programs_view(request):
    context = _base_context(request)
    return render(request, "dashboard/programs.html", context)


def import_view(request):
    context = _base_context(request)
    return render(request, "dashboard/import.html", context)


def profile_view(request):
    context = _base_context(request)
    return render(request, "dashboard/profile.html", context)


def settings_view(request):
    context = _base_context(request)
    return render(request, "dashboard/settings.html", context)