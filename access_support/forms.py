from django import forms
from academic_core.models import Campus, Faculty, AcademicProgram, Course, StudyPlan
from teaching.models import Teacher
from classrooms.models import Classroom
from .models import StudentProfile


class CampusForm(forms.ModelForm):
    class Meta:
        model = Campus
        fields = ["name"]


class FacultyForm(forms.ModelForm):
    class Meta:
        model = Faculty
        fields = ["name", "campus"]


class AcademicProgramForm(forms.ModelForm):
    class Meta:
        model = AcademicProgram
        fields = ["name", "code", "faculty", "campus"]


class StudyPlanForm(forms.ModelForm):
    class Meta:
        model = StudyPlan
        fields = ["program", "version", "description"]


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ["name", "code", "credits", "semester", "study_plan"]


class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = [
            "teacher_id",
            "first_name",
            "last_name",
            "address",
            "program",
            "faculty",
            "campus",
            "type_of_contract",
            "is_active",
        ]


class ClassroomForm(forms.ModelForm):
    class Meta:
        model = Classroom
        fields = ["classroom_id", "name", "block", "campus", "is_active"]
        labels = {
            "classroom_id": "Código aula",
            "name": "Nombre",
            "block": "Bloque",
            "campus": "Sede",
            "is_active": "Activo",
        }


class StudentForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = [
            "full_name",
            "document_type",
            "document_number",
            "student_code",
            "address",
            "program",
            "faculty",
            "campus",
            "level",
            "jornada",
        ]