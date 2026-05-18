from django.urls import path
from academic_core.views import study_plan_view
from .views import (
    dashboard,
    login_view,
    calendar_view,
    logout_view,
    register_view,
    students_view,
    programs_view,
    import_view,
    profile_view,
    settings_view,
    student_profile_setup_view,
)
from .crud_views import (
    CampusListView,
    CampusCreateView,
    CampusUpdateView,
    CampusDeleteView,
    FacultyListView,
    FacultyCreateView,
    FacultyUpdateView,
    FacultyDeleteView,
    ProgramListView,
    ProgramCreateView,
    ProgramUpdateView,
    ProgramDeleteView,
    StudentListView,
    StudentCreateView,
    StudentUpdateView,
    StudentDeleteView,
    StudyPlanListView,
)

urlpatterns = [
    path("import/", import_view, name="import"),
    path("login/", login_view, name="login"),
    path("register/", register_view, name="register"),
    path("logout/", logout_view, name="logout"),
    path("", dashboard, name="home"),
    path("calendario/", calendar_view, name="calendar"),
    path("estudiantes/", students_view, name="students"),
    path("programas/", programs_view, name="programs"),
    path("plan-estudios/", study_plan_view, name="study_plan"),
    path("importar/", import_view, name="import"),
    path("perfil/", profile_view, name="profile"),
    path("perfil-estudiantil/", student_profile_setup_view, name="student_profile_setup"),
    path("ajustes/", settings_view, name="settings"),
    path("sedes/", CampusListView.as_view(), name="campus_list"),
    path("sedes/crear/", CampusCreateView.as_view(), name="campus_create"),
    path("sedes/<int:pk>/editar/", CampusUpdateView.as_view(), name="campus_edit"),
    path("sedes/<int:pk>/eliminar/", CampusDeleteView.as_view(), name="campus_delete"),
    path("facultades/", FacultyListView.as_view(), name="faculty_list"),
    path("facultades/crear/", FacultyCreateView.as_view(), name="faculty_create"),
    path(
        "facultades/<int:pk>/editar/", FacultyUpdateView.as_view(), name="faculty_edit"
    ),
    path(
        "facultades/<int:pk>/eliminar/",
        FacultyDeleteView.as_view(),
        name="faculty_delete",
    ),
    path("programas/", ProgramListView.as_view(), name="program_list"),
    path("programas/crear/", ProgramCreateView.as_view(), name="program_create"),
    path(
        "programas/<int:pk>/editar/", ProgramUpdateView.as_view(), name="program_edit"
    ),
    path(
        "programas/<int:pk>/eliminar/",
        ProgramDeleteView.as_view(),
        name="program_delete",
    ),
  
    path("estudiantes/", StudentListView.as_view(), name="student_list"),
    path("estudiantes/crear/", StudentCreateView.as_view(), name="student_create"),
    path(
        "estudiantes/<int:pk>/editar/", StudentUpdateView.as_view(), name="student_edit"
    ),
    path(
        "estudiantes/<int:pk>/eliminar/",
        StudentDeleteView.as_view(),
        name="student_delete",
    ),

    path("plan-estudios/", StudyPlanListView.as_view(), name="study_plan_list"),
]
