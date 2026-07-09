from django.contrib import admin
from .models import (
    Campus,
    Faculty,
    AcademicProgram,
    AcademicTerm,
    StudyPlan,
    Course,
    CurriculumCourseGroup,
    CourseComponent,
)


@admin.register(Campus)
class CampusAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ("name", "campus")


@admin.register(AcademicProgram)
class AcademicProgramAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "faculty", "campus")


@admin.register(AcademicTerm)
class AcademicTermAdmin(admin.ModelAdmin):
    list_display = ("name", "start_date", "end_date", "active")


@admin.register(StudyPlan)
class StudyPlanAdmin(admin.ModelAdmin):
    list_display = ("program", "version")


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "credits", "semester", "component")
    search_fields = ("code", "name")


@admin.register(CourseComponent)
class CourseComponentAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(CurriculumCourseGroup)
class CourseGroupAdmin(admin.ModelAdmin):
    verbose_name = "Grupo curricular"
    list_display = ("course", "term", "group_number", "capacity")
    list_filter = ("term",)
    search_fields = ("course__name", "course__code")
