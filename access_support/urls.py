from django.urls import path
from .views import (
    dashboard,
    login_view,
    calendar_view,
    add_calendar_view,
    subjects_view,
    subject_detail_view,
    added_success_view,
    teachers_view,
    classrooms_view,
    programs_view,
    import_view,
    profile_view,
    settings_view,
)

urlpatterns = [
    path("login/", login_view, name="login"),
    path("", dashboard, name="home"),
    path("calendario/", calendar_view, name="calendar"),
    path("generar-horario/", add_calendar_view, name="add_calendar"),
    path("buscar-materias/", subjects_view, name="subjects"),
    path("materia/", subject_detail_view, name="subject_detail"),
    path("agregado-exito/", added_success_view, name="added_success"),
    path("docentes/", teachers_view, name="teachers"),
    path("aulas/", classrooms_view, name="classrooms"),
    path("programas/", programs_view, name="programs"),
    path("importar/", import_view, name="import"),
    path("perfil/", profile_view, name="profile"),
    path("ajustes/", settings_view, name="settings"),
]
