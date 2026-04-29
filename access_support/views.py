import random
import string
import unicodedata

import pandas as pd
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from academic_core.models import AcademicProgram, AcademicTerm, Campus, Course, Faculty, StudyPlan
from academic_core.services.academic_services import get_programs
from classrooms.models import Classroom
from scheduling_enrollment.models import Enrollment, EnrollmentQueue, SemesterScheduleRun
from teaching.models import Teacher

from .forms import StudentSelfProfileForm, StudentSelfReadonlyForm
from .login import EmailLoginForm
from .models import StudentProfile, User
from .role_access import (
    ACADEMIC_MANAGEMENT_ROLES,
    SCHEDULE_MANAGEMENT_ROLES,
    SCHEDULE_READ_ROLES,
    normalize_role,
    role_dashboard_template,
    role_label,
    roles_required,
)


def _base_context(request):
    user_name = request.user.email if request.user.is_authenticated else "Invitado"
    return {
        "user_name": user_name,
        "role_label": role_label(request.user),
    }


def _dashboard_card(label, value, helper=""):
    return {"label": label, "value": value, "helper": helper}


def _role_dashboard_context(request):
    """Contexto separado para cada rol. Mantiene el home limpio y sin condicionales gigantes."""
    user = request.user
    role = normalize_role(user)
    context = _base_context(request)
    active_term = AcademicTerm.objects.filter(active=True).order_by("-start_date").first()
    context["active_term"] = active_term

    if role == "student":
        student_profile = (
            StudentProfile.objects.select_related("program", "faculty", "campus")
            .filter(user=user)
            .first()
        )
        waiting_count = 0
        enrolled_count = 0
        if active_term:
            waiting_count = EnrollmentQueue.objects.filter(
                student=user, term=active_term, status="waiting"
            ).count()
            enrolled_count = Enrollment.objects.filter(
                student=user, term=active_term, status="active"
            ).count()
        context.update(
            {
                "student_profile": student_profile,
                "stats": [
                    _dashboard_card("Materias activas", enrolled_count, "Cursos asignados al periodo"),
                    _dashboard_card("Solicitudes en espera", waiting_count, "Materias pendientes por grupo"),
                    _dashboard_card("Programa", student_profile.program if student_profile and student_profile.program else "Sin definir"),
                ],
            }
        )
        return context

    if role == "teacher":
        teacher = getattr(user, "teacher_profile", None)
        assigned_groups = 0
        if teacher and active_term:
            assigned_groups = teacher.coursegroup_set.filter(term=active_term).count()
        context.update(
            {
                "teacher": teacher,
                "stats": [
                    _dashboard_card("Grupos asignados", assigned_groups, "Para el periodo activo"),
                    _dashboard_card("Disponibilidades", teacher.availabilities.count() if teacher else 0, "Bloques registrados"),
                    _dashboard_card("Rol", "Docente", "Vista limitada a horario y datos propios"),
                ],
            }
        )
        return context

    if role == "admin":
        context.update(
            {
                "stats": [
                    _dashboard_card("Estudiantes", StudentProfile.objects.count(), "Perfiles registrados"),
                    _dashboard_card("Docentes", Teacher.objects.count(), "Docentes activos y registrados"),
                    _dashboard_card("Materias", Course.objects.count(), "Catalogo academico"),
                    _dashboard_card("Aulas", Classroom.objects.count(), "Recursos fisicos"),
                ]
            }
        )
        return context

    # coordinator/director y superusuario funcional
    context.update(
        {
            "stats": [
                _dashboard_card("Planes semestrales", SemesterScheduleRun.objects.count(), "Generados o guardados"),
                _dashboard_card("Periodos", AcademicTerm.objects.count(), "Periodos academicos"),
                _dashboard_card("Programas", AcademicProgram.objects.count(), "Programas configurados"),
                _dashboard_card("Docentes", Teacher.objects.count(), "Recursos docentes"),
            ]
        }
    )
    return context


@login_required
def dashboard(request):
    context = _role_dashboard_context(request)
    return render(request, role_dashboard_template(request.user), context)


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


@login_required
def calendar_view(request):
    schedule_rows = [
        ("07:00 - 08:30", "", "", "", "", ""),
        ("08:30 - 10:00", "", "", "", "", ""),
        ("10:00 - 11:30", "", "", "", "", ""),
        ("11:30 - 13:00", "", "", "", "", ""),
        ("14:30 - 16:00", "", "", "", "", ""),
        ("16:00 - 17:30", "", "", "", "", ""),
        ("18:00 - 19:30", "", "", "", "", ""),
        ("19:30 - 21:00", "", "", "", "", ""),
    ]
    context = _base_context(request)
    context["schedule_rows"] = schedule_rows
    return render(request, "scheduling/schedule.html", context)


@roles_required(*SCHEDULE_MANAGEMENT_ROLES)
def add_calendar_view(request):
    return redirect("generate_schedule")


@roles_required(*ACADEMIC_MANAGEMENT_ROLES)
def students_view(request):
    context = _base_context(request)
    context["items"] = StudentProfile.objects.select_related("user", "faculty", "campus", "program").order_by("id")
    return render(request, "dashboard/students.html", context)


@roles_required(*ACADEMIC_MANAGEMENT_ROLES)
def programs_view(request):
    context = _base_context(request)
    context["items"] = get_programs()
    return render(request, "dashboard/programs.html", context)


def generar_password(longitud=10):
    caracteres = string.ascii_letters + string.digits
    return "".join(random.sample(caracteres, longitud))


def generar_codigo_estudiantil():
    base = "EST-"
    ultimo = (
        StudentProfile.objects.exclude(student_code__isnull=True)
        .exclude(student_code="")
        .order_by("-id")
        .values_list("student_code", flat=True)
    )

    max_number = 0
    for code in ultimo:
        if not code or not code.startswith(base):
            continue
        suffix = code.replace(base, "", 1)
        if suffix.isdigit():
            max_number = max(max_number, int(suffix))

    next_number = max_number + 1
    while True:
        candidate = f"{base}{next_number:06d}"
        if not StudentProfile.objects.filter(student_code=candidate).exists():
            return candidate
        next_number += 1


@roles_required(*ACADEMIC_MANAGEMENT_ROLES)
def import_view(request):
    context = _base_context(request)

    if request.method == "POST":
        archivo = request.FILES.get("archivo")

        if not archivo:
            messages.error(request, "No se subio ningun archivo")
            return render(request, "dashboard/import.html", context)

        try:
            df = pd.read_excel(archivo)
            df = df.drop_duplicates(subset=["CORREO_ESTUDIANTE"])
        except Exception:
            messages.error(request, "Error al leer el archivo Excel")
            return render(request, "dashboard/import.html", context)

        def normalize_text(value):
            text = str(value or "").strip().lower()
            text = unicodedata.normalize("NFKD", text)
            text = "".join(char for char in text if not unicodedata.combining(char))
            return " ".join(text.split())

        allowed_programs = {
            "ingenieria industrial",
            "ingenieria de software",
        }

        resultados = []
        created_count = 0
        skipped_program_count = 0
        skipped_existing_count = 0
        skipped_existing_profile_count = 0
        skipped_empty_email_count = 0
        error_count = 0

        for _, row in df.iterrows():
            email = str(row.get("CORREO_ESTUDIANTE", "")).strip().lower().replace(" ", "")
            if not email or email == "nan":
                skipped_empty_email_count += 1
                continue

            program_name = normalize_text(row.get("DESCRIPCION_PROGRAMA", ""))
            if program_name not in allowed_programs:
                skipped_program_count += 1
                continue

            try:
                user = User.objects.filter(email=email).first()
                if user:
                    skipped_existing_count += 1
                    if StudentProfile.objects.filter(user=user).exists():
                        skipped_existing_profile_count += 1
                        continue
                    password = "Usuario existente"
                else:
                    password = generar_password()
                    user = User.objects.create_user(email=email, password=password, role="student")

                campus_name = str(row.get("DESCRIPCION_SEDE", "")).strip() or "Sede sin definir"
                campus = Campus.objects.filter(name=campus_name).first()
                if campus is None:
                    campus = Campus.objects.create(name=campus_name)

                faculty_name = (
                    str(row.get("DESCRIPCION_FACULTAD", "")).strip() or "Facultad sin definir"
                )
                faculty = Faculty.objects.filter(name=faculty_name).first()
                if faculty is None:
                    faculty = Faculty.objects.create(name=faculty_name, campus=campus)

                program_name_raw = (
                    str(row.get("DESCRIPCION_PROGRAMA", "")).strip() or "Programa sin definir"
                )
                program = AcademicProgram.objects.filter(name=program_name_raw).first()
                if program is None:
                    program = AcademicProgram.objects.create(
                        name=program_name_raw,
                        faculty=faculty,
                        campus=campus,
                    )

                StudentProfile.objects.create(
                    user=user,
                    student_code=str(row.get("CODIGO", "")) or generar_codigo_estudiantil(),
                    document_type=str(row.get("TIPO_DOCUMENTO", "")),
                    document_number=str(row.get("NUM_DOCUMENTO", "")),
                    full_name=str(row.get("NOMBRES", "")),
                    campus=campus,
                    faculty=faculty,
                    program=program,
                    level=str(row.get("DESCRIPCION_NIVEL", "")),
                    jornada=str(row.get("JORNADA", "")),
                    address="",
                )
                created_count += 1
                resultados.append({"email": email, "password": password})
            except Exception as exc:
                error_count += 1
                resultados.append({"email": email, "password": f"Error: {exc}"})

        context["resultados"] = resultados
        context["success_message"] = (
            "Importacion completada. "
            f"Creados: {created_count}. "
            f"Omitidos por programa: {skipped_program_count}. "
            f"Omitidos por correo existente: {skipped_existing_count}. "
            f"Omitidos por usuario con perfil existente: {skipped_existing_profile_count}. "
            f"Omitidos por correo vacio: {skipped_empty_email_count}. "
            f"Errores: {error_count}."
        )

    return render(request, "dashboard/import.html", context)


@login_required
def profile_view(request):
    context = _base_context(request)
    student_profile = None
    teacher = None

    if request.user.role == "student":
        student_profile = (
            StudentProfile.objects.select_related("program", "faculty", "campus")
            .filter(user=request.user)
            .first()
        )
    elif request.user.role == "teacher":
        teacher = getattr(request.user, "teacher_profile", None)

    context["student_profile"] = student_profile
    context["teacher"] = teacher
    return render(request, "dashboard/profile.html", context)


@login_required
def student_profile_setup_view(request):
    if request.user.role != "student":
        messages.warning(request, "Este apartado solo esta disponible para estudiantes.")
        return redirect("profile")

    profile = StudentProfile.objects.filter(user=request.user).first()
    if profile is None:
        profile = StudentProfile(user=request.user)

    readonly_form = StudentSelfReadonlyForm(instance=profile)
    for field in readonly_form.fields.values():
        field.disabled = True

    if request.method == "POST":
        form = StudentSelfProfileForm(request.POST, instance=profile)
        if form.is_valid():
            profile = StudentProfile.objects.filter(user=request.user).first() or StudentProfile(
                user=request.user
            )
            profile.address = form.cleaned_data["address"]
            profile.user = request.user
            if not profile.student_code:
                profile.student_code = generar_codigo_estudiantil()
            if profile.program and not profile.faculty:
                profile.faculty = profile.program.faculty
            if profile.program and not profile.campus:
                profile.campus = profile.program.campus
            profile.save()
            messages.success(request, "Tu perfil estudiantil fue guardado correctamente.")
            return redirect("profile")
    else:
        form = StudentSelfProfileForm(instance=profile)

    return render(
        request,
        "access_support/student_profile_setup.html",
        {
            "form": form,
            "readonly_form": readonly_form,
            "has_profile": profile.pk is not None,
            "user_email": request.user.email,
        },
    )


@login_required
def settings_view(request):
    context = _base_context(request)
    return render(request, "dashboard/settings.html", context)


def register_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password")
        confirm = request.POST.get("confirm")

        if not email.endswith("@uniminuto.edu.co"):
            messages.error(request, "Solo se permiten correos institucionales (@uniminuto.edu.co)")
            return render(request, "access_support/register.html")

        if password != confirm:
            messages.error(request, "Las contrasenas no coinciden")
            return redirect("register")

        if User.objects.filter(email=email).exists():
            messages.error(request, "El correo ya esta registrado")
            return redirect("register")

        user = User.objects.create_user(email=email, password=password, role="student")
        login(request, user)
        messages.success(request, "Usuario creado correctamente. Ahora completa tu perfil estudiantil.")
        return redirect("student_profile_setup")

    return render(request, "access_support/register.html")


def logout_view(request):
    logout(request)
    return redirect("login")
