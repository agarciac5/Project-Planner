from django.urls import path
from .views import (
    teachers_view,
    teacher_create_view,
    add_availability,
    teacher_edit_view,
    teacher_delete_view,
)

urlpatterns = [
    path("", teachers_view, name="teacher_list"),
    path("create/", teacher_create_view, name="teacher_create"),
    path("<int:teacher_id>/edit/", teacher_edit_view, name="teacher_edit"),
    path("<int:teacher_id>/delete/", teacher_delete_view, name="teacher_delete"),
    path("<int:teacher_id>/availability/", add_availability, name="add_availability"),
]
