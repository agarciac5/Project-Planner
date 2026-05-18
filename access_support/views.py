import random
import re
import string
import unicodedata
from urllib.parse import urlencode

import pandas as pd
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse

from academic_core.models import AcademicProgram, AcademicTerm, Campus, Course, Faculty, StudyPlan
from academic_core.services.academic_services import get_programs
from classrooms.models import Classroom
from scheduling_enrollment.models import Enrollment, EnrollmentQueue, SemesterScheduleRun
from teaching.models import Teacher

from .forms import (
    INSTITUTIONAL_EMAIL_DOMAIN,
    StudentSelfProfileCreateForm,
    StudentSelfProfileForm,
    StudentSelfReadonlyForm,
    UserRoleAssignmentForm,
    UserRoleSearchForm,
)
from .login import EmailLoginForm
from .models import StudentProfile, User
from .role_access import (
    ACADEMIC_MANAGEMENT_ROLES,
    SCHEDULE_READ_ROLES,
    normalize_role,
    role_dashboard_template,
    role_label,
    roles_required,
)


def _is_institutional_email(email):
    return str(email or "").strip().lower().endswith(INSTITUTIONAL_EMAIL_DOMAIN)


def _student_profiles():
    return StudentProfile.objects.select_related("user", "faculty", "campus", "program")


def _teacher_profile_for_user(user):
    return getattr(user, "teacher_profile", None)


def _full_name_from_email(email):
    local_part = str(email or "").split("@", 1)[0]
    normalized = re.sub(r"[._-]+", " ", local_part)
    normalized = " ".join(normalized.split()).strip()
    return normalized.title() or "Usuario Institucional"


def _split_person_name(full_name, email):
    normalized = " ".join(str(full_name or "").split()).strip() or _full_name_from_email(email)
    parts = normalized.split()
    first_name = parts[0][:50]
    last_name = " ".join(parts[1:])[:50] if len(parts) > 1 else "Autogenerado"
    return first_name, last_name


def _generate_teacher_id_for_user(user):
    email_local_part = str(user.email or "").split("@", 1)[0]
    base = "".join(ch for ch in email_local_part.upper() if ch.isalnum()) or str(user.id)
    teacher_id = f"DOC-AUTO-{base[:10]}"
    suffix = 1
    while Teacher.objects.filter(teacher_id=teacher_id).exclude(user=user).exists():
        suffix += 1
        teacher_id = f"DOC-AUTO-{base[:7]}{suffix:03d}"
    return teacher_id


def _ensure_teacher_profile(user):
    teacher_profile = _teacher_profile_for_user(user)
    if teacher_profile:
        return teacher_profile, False

    student_profile = (
        _student_profiles()
        .filter(user=user)
        .first()
    )
    full_name = student_profile.full_name if student_profile else ""
    first_name, last_name = _split_person_name(full_name, user.email)
    program = student_profile.program if student_profile else None
    faculty = student_profile.faculty if student_profile and student_profile.faculty else (
        program.faculty if program else None
    )
    campus = student_profile.campus if student_profile and student_profile.campus else (
        program.campus if program else None
    )

    teacher_profile = Teacher.objects.create(
        user=user,
        teacher_id=_generate_teacher_id_for_user(user),
        first_name=first_name,
        last_name=last_name,
        address=student_profile.address if student_profile else "",
        program=program,
        faculty=faculty,
        campus=campus,
        is_active=True,
    )
    return teacher_profile, True


def _ensure_student_profile(user):
    student_profile = _student_profiles().filter(user=user).first()
    if student_profile:
        return student_profile, False

    teacher_profile = _teacher_profile_for_user(user)
    full_name = _full_name_from_email(user.email)
    address = ""
    program = None
    faculty = None
    campus = None

    if teacher_profile:
        full_name = " ".join(
            part for part in [teacher_profile.first_name, teacher_profile.last_name] if part
        ).strip() or full_name
        address = teacher_profile.address
        program = teacher_profile.program
        faculty = teacher_profile.faculty if teacher_profile.faculty else (
            program.faculty if program else None
        )
        campus = teacher_profile.campus if teacher_profile.campus else (
            program.campus if program else None
        )

    student_profile = StudentProfile.objects.create(
        user=user,
        student_code=generar_codigo_estudiantil(),
        full_name=full_name,
        address=address,
        program=program,
        faculty=faculty,
        campus=campus,
    )
    return student_profile, True


def _detach_teacher_profile(user):
    teacher_profile = _teacher_profile_for_user(user)
    if not teacher_profile:
        return None
    teacher_profile.user = None
    teacher_profile.save(update_fields=["user"])
    return teacher_profile


def _sync_role_profiles(user, previous_role, new_role):
    notices = []

    if new_role == "student":
        _, created_student_profile = _ensure_student_profile(user)
        if created_student_profile:
            notices.append(
                "Se creo un perfil estudiantil basico para esta cuenta. "
                "Completa sus datos despues si hace falta."
            )

    if new_role == "teacher":
        teacher_profile, created_teacher_profile = _ensure_teacher_profile(user)
        if created_teacher_profile:
            notices.append(
                f"Se creo el perfil docente {teacher_profile.teacher_id} y quedo vinculado "
                "automaticamente a la cuenta."
            )

    if previous_role == "teacher" and new_role != "teacher":
        detached_teacher_profile = _detach_teacher_profile(user)
        if detached_teacher_profile:
            notices.append(
                f"El perfil docente {detached_teacher_profile.teacher_id} quedo desvinculado "
                "del usuario para conservar su historial."
            )

    return notices


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
                    _dashboard_card(
                        "Estudiantes",
                        StudentProfile.objects.filter(user__role="student").count(),
                        "Perfiles de usuarios con rol estudiantil",
                    ),
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


@roles_required(*ACADEMIC_MANAGEMENT_ROLES)
def students_view(request):
    context = _base_context(request)
    context["items"] = (
        _student_profiles()
        .filter(user__role="student")
        .order_by("id")
    )
    return render(request, "dashboard/students.html", context)


@roles_required(*ACADEMIC_MANAGEMENT_ROLES)
def programs_view(request):
    context = _base_context(request)
    context["items"] = get_programs()
    return render(request, "dashboard/programs.html", context)


def _institutional_users():
    return User.objects.filter(email__iendswith=INSTITUTIONAL_EMAIL_DOMAIN).order_by("email")


def _role_assignment_rows(users, search_term):
    rows = []
    for user in users:
        has_teacher_profile = bool(_teacher_profile_for_user(user))
        has_student_profile = _student_profiles().filter(user=user).exists()
        rows.append(
            {
                "user": user,
                "has_teacher_profile": has_teacher_profile,
                "has_student_profile": has_student_profile,
                "form": UserRoleAssignmentForm(
                    initial={
                        "user_id": user.id,
                        "role": user.role,
                        "search": search_term,
                    }
                ),
            }
        )
    return rows


@roles_required(*ACADEMIC_MANAGEMENT_ROLES)
def assign_roles_view(request):
    query = ""
    users = User.objects.none()
    searched = False

    if request.method == "POST":
        assignment_form = UserRoleAssignmentForm(request.POST)
        search_form = UserRoleSearchForm(initial={"email_query": request.POST.get("search", "")})

        if assignment_form.is_valid():
            user = assignment_form.get_user()
            new_role = assignment_form.cleaned_data["role"]
            search_term = assignment_form.cleaned_data["search"]
            previous_role = user.role
            role_labels = dict(User.ROLE_CHOICES)
            previous_role_label = role_labels.get(previous_role, previous_role)
            notices = []

            with transaction.atomic():
                if previous_role != new_role:
                    user.role = new_role
                    user.save(update_fields=["role"])
                    notices = _sync_role_profiles(user, previous_role, new_role)
                    messages.success(
                        request,
                        f"El rol de {user.email} cambio de {previous_role_label} a "
                        f"{role_labels[new_role]}.",
                    )
                else:
                    notices = _sync_role_profiles(user, previous_role, new_role)
                    messages.success(
                        request,
                        f"{user.email} ya tiene el rol {previous_role_label}.",
                    )

            for notice in notices:
                messages.info(request, notice)

            redirect_url = reverse("assign_roles")
            if search_term:
                redirect_url = f"{redirect_url}?{urlencode({'email_query': search_term})}"
            return redirect(redirect_url)

        error_messages = []
        for field_errors in assignment_form.errors.values():
            error_messages.extend(field_errors)
        messages.error(
            request,
            " ".join(error_messages)
            or "No fue posible actualizar el rol. Verifica el usuario y el rol seleccionado.",
        )
        query = request.POST.get("search", "").strip().lower()
        searched = bool(query)
        if query:
            users = _institutional_users().filter(email__icontains=query)[:50]
    else:
        search_form = UserRoleSearchForm(request.GET or None)
        if search_form.is_valid():
            query = search_form.cleaned_data["email_query"]
            searched = bool(query)
            if query:
                users = _institutional_users().filter(email__icontains=query)[:50]

    context = _base_context(request)
    context.update(
        {
            "search_form": search_form,
            "rows": _role_assignment_rows(users, query),
            "searched": searched,
            "search_term": query,
        }
    )
    return render(request, "access_support/assign_roles.html", context)


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
    has_profile = profile is not None
    if profile is None:
        profile = StudentProfile(user=request.user)

    readonly_form = None
    if has_profile:
        readonly_form = StudentSelfReadonlyForm(instance=profile)
        for field in readonly_form.fields.values():
            field.disabled = True

    if request.method == "POST":
        form_class = StudentSelfProfileForm if has_profile else StudentSelfProfileCreateForm
        form = form_class(request.POST, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
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
        form_class = StudentSelfProfileForm if has_profile else StudentSelfProfileCreateForm
        form = form_class(instance=profile)

    return render(
        request,
        "access_support/student_profile_setup.html",
        {
            "form": form,
            "readonly_form": readonly_form,
            "has_profile": has_profile,
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

        if not _is_institutional_email(email):
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
