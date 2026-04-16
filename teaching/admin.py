from django.contrib import admin
from .models import Teacher, Availability, ContractRule


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = (
        "teacher_id",
        "first_name",
        "last_name",
        "contract",
        "is_active",
    )
    list_filter = ("contract", "is_active")
    search_fields = ("teacher_id", "first_name", "last_name")


@admin.register(Availability)
class AvailabilityAdmin(admin.ModelAdmin):
    list_display = ("teacher", "day", "start_time", "end_time")
    list_filter = ("day", "teacher")
    search_fields = ("teacher__first_name", "teacher__last_name", "teacher__teacher_id")


@admin.register(ContractRule)
class ContractRuleAdmin(admin.ModelAdmin):
    list_display = (
        "contract_type",
        "min_teaching_hours",
        "max_teaching_hours",
        "max_advisory_hours",
        "max_research_hours",
        "max_total_hours",
    )