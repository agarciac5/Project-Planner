from django.contrib import admin
from .models import Teacher, Availability

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('teacher_id', 'first_name', 'last_name', 'type_of_contract', 'is_active', 'min_hours_per_week', 'max_hours_per_week')
    list_filter = ('type_of_contract', 'is_active')
    search_fields = ('teacher_id', 'first_name', 'last_name')

@admin.register(Availability)
class AvailabilityAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'day', 'start_time', 'end_time')
    list_filter = ('day', 'teacher')
    search_fields = ('teacher__first_name', 'teacher__last_name', 'teacher__teacher_id')