from django.urls import path
from .views import classrooms_view
from access_support.crud_views import (
    ClassroomListView,
    ClassroomCreateView,
    ClassroomUpdateView,
    ClassroomDeleteView,
)

urlpatterns = [

    path("aulas/", classrooms_view, name="classrooms"),


    path("aulas/list/", ClassroomListView.as_view(), name="classroom_list"),
    path("aulas/crear/", ClassroomCreateView.as_view(), name="classroom_create"),
    path("aulas/<int:pk>/editar/", ClassroomUpdateView.as_view(), name="classroom_edit"),
    path("aulas/<int:pk>/eliminar/", ClassroomDeleteView.as_view(), name="classroom_delete"),
]