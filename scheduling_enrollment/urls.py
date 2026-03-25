from django.urls import path
from .views import generate_schedule_view, schedule_list_view, schedule_detail_view
 
urlpatterns = [
    path("generar-horario/", generate_schedule_view, name="generate_schedule"),
    path("horarios/", schedule_list_view, name="schedule_list"),
    path("horarios/<int:schedule_id>/", schedule_detail_view, name="schedule_detail"),
]