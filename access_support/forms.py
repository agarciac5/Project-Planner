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
            "contract",        # reemplaza type_of_contract
            "qualified_courses",
            "is_active",
        ]


class ClassroomForm(forms.ModelForm):
    class Meta:
        model = Classroom
        fields = [
            "classroom_id",
            "name",
            "block",
            "campus",
            "capacity",
            "classroom_type",
            "is_active",
        ]
        labels = {
            "classroom_id": "Código aula",
            "name": "Nombre",
            "block": "Bloque",
            "campus": "Sede",
            "capacity": "Capacidad",
            "classroom_type": "Tipo de aula",
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
        labels = {
            "level": "Pregrado",
        }


class StudentSelfProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ["address"]
        labels = {
            "address": "Direccion",
        }


class StudentSelfReadonlyForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = [
            "full_name",
            "document_type",
            "document_number",
            "program",
            "faculty",
            "campus",
            "level",
            "jornada",
        ]
        labels = {
            "full_name": "Nombre completo",
            "document_type": "Tipo de documento",
            "document_number": "Numero de documento",
            "address": "Direccion",
            "program": "Programa",
            "faculty": "Facultad",
            "campus": "Sede",
            "level": "Pregrado",
            "jornada": "Jornada",
        }
