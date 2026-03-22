from django.contrib import admin
from .models import (
    Campus,
    Faculty,
    AcademicProgram,
    AcademicTerm,
    StudyPlan,
    Course,
    CourseGroup,
)

admin.site.register(Campus)
admin.site.register(Faculty)
admin.site.register(AcademicProgram)
admin.site.register(AcademicTerm)
admin.site.register(StudyPlan)
admin.site.register(Course)
admin.site.register(CourseGroup)