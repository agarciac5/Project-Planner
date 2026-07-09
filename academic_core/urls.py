from django.urls import path
from academic_core.views import campuses_view, faculties_view
from access_support.crud_views import (
    CourseListView,
    CourseCreateView,
    CourseUpdateView,
    CourseDeleteView,
    CampusListView,
    CampusCreateView,
    CampusUpdateView,
    CampusDeleteView,
    FacultyListView,
    FacultyCreateView,
    FacultyUpdateView,
    FacultyDeleteView,
)

urlpatterns = [
  
    path("sedes/", CampusListView.as_view(), name="campuses"),
    path("sedes/", CampusListView.as_view(), name="campus_list"),
    path("sedes/crear/", CampusCreateView.as_view(), name="campus_create"),
    path("sedes/<int:pk>/editar/", CampusUpdateView.as_view(), name="campus_edit"),
    path("sedes/<int:pk>/eliminar/", CampusDeleteView.as_view(), name="campus_delete"),

    
    path("facultades/", FacultyListView.as_view(), name="faculties"),
    path("facultades/", FacultyListView.as_view(), name="faculty_list"),
    path("facultades/crear/", FacultyCreateView.as_view(), name="faculty_create"),
    path("facultades/<int:pk>/editar/", FacultyUpdateView.as_view(), name="faculty_edit"),
    path("facultades/<int:pk>/eliminar/", FacultyDeleteView.as_view(), name="faculty_delete"),

  
    path("materias/", CourseListView.as_view(), name="subjects"),
    path("materias/", CourseListView.as_view(), name="course_list"),
    path("materias/crear/", CourseCreateView.as_view(), name="create_subject"),
    path("materias/crear/", CourseCreateView.as_view(), name="course_create"),
    path("materias/<int:pk>/editar/", CourseUpdateView.as_view(), name="edit_subject"),
    path("materias/<int:pk>/editar/", CourseUpdateView.as_view(), name="course_edit"),
    path("materias/<int:pk>/eliminar/", CourseDeleteView.as_view(), name="delete_subject"),
    path("materias/<int:pk>/eliminar/", CourseDeleteView.as_view(), name="course_delete"),
]
