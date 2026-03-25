from django.contrib import admin
from .models import CourseGroup, ProposedSchedule, ScheduleSession, EnrollmentQueue


@admin.register(CourseGroup)
class CourseGroupAdmin(admin.ModelAdmin):
    list_display = ("course", "teacher", "term", "nrc", "capacity", "is_virtual")
    list_filter = ("term", "teacher", "is_virtual")
    search_fields = ("nrc", "course__name", "teacher__first_name", "teacher__last_name")


@admin.register(ProposedSchedule)
class ProposedScheduleAdmin(admin.ModelAdmin):
    list_display = ("teacher", "term", "status", "fitness_score", "created_at")
    list_filter = ("status", "term")


@admin.register(ScheduleSession)
class ScheduleSessionAdmin(admin.ModelAdmin):
    list_display = ("group", "day", "start_time", "end_time", "classroom")
    list_filter = ("day", "schedule__term")


@admin.register(EnrollmentQueue)
class EnrollmentQueueAdmin(admin.ModelAdmin):
    list_display = ("student", "course", "status", "request_date")
    list_filter = ("status",)