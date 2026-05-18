"""Herramientas centralizadas para separar vistas y permisos por rol.

Roles usados en el proyecto:
- student: Estudiante
- teacher: Docente
- admin: Personal administrativo
- coordinator: Director academico / super admin funcional

La idea es que las vistas no tengan condicionales repetidos ni codigo espagueti.
Cada URL se protege con decoradores/mixins y el navbar se arma desde ROLE_NAV_ITEMS.
"""

from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import NoReverseMatch, reverse


ROLE_STUDENT = "student"
ROLE_TEACHER = "teacher"
ROLE_ADMIN = "admin"
ROLE_COORDINATOR = "coordinator"

ROLE_LABELS = {
    ROLE_STUDENT: "Estudiante",
    ROLE_TEACHER: "Docente",
    ROLE_ADMIN: "Administrador",
    ROLE_COORDINATOR: "Director academico",
}

DIRECTOR_ROLES = {ROLE_COORDINATOR}
ACADEMIC_MANAGEMENT_ROLES = {ROLE_ADMIN, ROLE_COORDINATOR}
SCHEDULE_MANAGEMENT_ROLES = {ROLE_ADMIN, ROLE_COORDINATOR}
SCHEDULE_READ_ROLES = {ROLE_ADMIN, ROLE_COORDINATOR}


ROLE_NAV_ITEMS = {
    ROLE_STUDENT: [
        {"label": "Inicio", "url_name": "home"},
        {"label": "Matricula", "url_name": "enrollment"},
        {"label": "Mi horario", "url_name": "my_student_schedule"},
        {"label": "Plan de estudios", "url_name": "study_plan"},
        {"label": "Perfil estudiantil", "url_name": "student_profile_setup"},
    ],
    ROLE_TEACHER: [
        {"label": "Inicio", "url_name": "home"},
        {"label": "Mi horario docente", "url_name": "my_teacher_schedule"},
        {"label": "Plan de estudios", "url_name": "study_plan"},
        {"label": "Perfil", "url_name": "profile"},
    ],
    ROLE_ADMIN: [
        {"label": "Inicio", "url_name": "home"},
        {"label": "Materias", "url_name": "subjects"},
        {"label": "Docentes", "url_name": "teacher_list"},
        {"label": "Estudiantes", "url_name": "students"},
        {"label": "Programas", "url_name": "programs"},
        {"label": "Roles y permisos", "url_name": "assign_roles"},
        {"label": "Plan de estudios", "url_name": "study_plan"},
        {"label": "Facultades", "url_name": "faculties"},
        {"label": "Sedes", "url_name": "campuses"},
        {"label": "Aulas", "url_name": "classrooms"},
        {"label": "Plan semestral", "url_name": "semester_planner"},
        {"label": "Horario docente", "url_name": "teacher_complete_schedule"},
        {"label": "Horario estudiantil", "url_name": "student_complete_schedule"},
        {"label": "Planes guardados", "url_name": "saved_semester_runs"},
        {"label": "Importar", "url_name": "import"},
    ],
    ROLE_COORDINATOR: [
        {"label": "Inicio", "url_name": "home"},
        {"label": "Plan semestral", "url_name": "semester_planner"},
        {"label": "Planes guardados", "url_name": "saved_semester_runs"},
        {"label": "Horario docente", "url_name": "teacher_complete_schedule"},
        {"label": "Horario estudiantil", "url_name": "student_complete_schedule"},
        {"label": "Materias", "url_name": "subjects"},
        {"label": "Docentes", "url_name": "teacher_list"},
        {"label": "Estudiantes", "url_name": "students"},
        {"label": "Programas", "url_name": "programs"},
        {"label": "Roles y permisos", "url_name": "assign_roles"},
        {"label": "Aulas", "url_name": "classrooms"},
        {"label": "Importar", "url_name": "import"},
    ],
}


ROLE_DASHBOARD_TEMPLATES = {
    ROLE_STUDENT: "dashboard/roles/student.html",
    ROLE_TEACHER: "dashboard/roles/teacher.html",
    ROLE_ADMIN: "dashboard/roles/admin.html",
    ROLE_COORDINATOR: "dashboard/roles/director.html",
}


def normalize_role(user):
    if not getattr(user, "is_authenticated", False):
        return None
    if getattr(user, "is_superuser", False):
        return ROLE_COORDINATOR
    return getattr(user, "role", None) or ROLE_STUDENT


def role_label(user):
    return ROLE_LABELS.get(normalize_role(user), "Invitado")


def role_nav_items(user):
    role = normalize_role(user)
    items = ROLE_NAV_ITEMS.get(role, [])
    resolved_items = []
    for item in items:
        try:
            resolved_items.append({**item, "url": reverse(item["url_name"])})
        except NoReverseMatch:
            # Si una ruta no existe durante desarrollo, no se rompe toda la pagina.
            continue
    return resolved_items


def role_dashboard_template(user):
    return ROLE_DASHBOARD_TEMPLATES.get(normalize_role(user), "dashboard/dashboard.html")


def user_has_any_role(user, allowed_roles):
    if not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_superuser", False):
        return True
    return normalize_role(user) in set(allowed_roles)


def roles_required(*allowed_roles):
    """Decorador para funciones: login obligatorio + validacion de rol."""

    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if user_has_any_role(request.user, allowed_roles):
                return view_func(request, *args, **kwargs)
            messages.warning(request, "No tienes permisos para acceder a este modulo.")
            return redirect("home")

        return _wrapped

    return decorator


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin para vistas basadas en clase."""

    allowed_roles = ()

    def test_func(self):
        return user_has_any_role(self.request.user, self.allowed_roles)

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.warning(self.request, "No tienes permisos para acceder a este modulo.")
            return redirect("home")
        return super().handle_no_permission()


class AcademicManagementRequiredMixin(RoleRequiredMixin):
    allowed_roles = tuple(ACADEMIC_MANAGEMENT_ROLES)


class ScheduleReadRequiredMixin(RoleRequiredMixin):
    allowed_roles = tuple(SCHEDULE_READ_ROLES)


class ScheduleManagementRequiredMixin(RoleRequiredMixin):
    allowed_roles = tuple(SCHEDULE_MANAGEMENT_ROLES)
