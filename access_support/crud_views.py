from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from academic_core.models import Campus, Faculty, AcademicProgram, Course, StudyPlan
from teaching.models import Teacher
from classrooms.models import Classroom
from .models import StudentProfile
from .forms import (
    CampusForm,
    FacultyForm,
    AcademicProgramForm,
    CourseForm,
    StudyPlanForm,
    TeacherForm,
    ClassroomForm,
    StudentForm,
)


class CampusListView(ListView):
    model = Campus
    template_name = "crud/campus_list.html"
    context_object_name = "items"


class CampusCreateView(CreateView):
    model = Campus
    form_class = CampusForm
    template_name = "crud/form.html"
    success_url = reverse_lazy("campus_list")


class CampusUpdateView(UpdateView):
    model = Campus
    form_class = CampusForm
    template_name = "crud/form.html"
    success_url = reverse_lazy("campus_list")


class CampusDeleteView(DeleteView):
    model = Campus
    template_name = "crud/delete_confirm.html"
    success_url = reverse_lazy("campus_list")


class FacultyListView(ListView):
    model = Faculty
    template_name = "crud/faculty_list.html"
    context_object_name = "items"


class FacultyCreateView(CreateView):
    model = Faculty
    form_class = FacultyForm
    template_name = "crud/form.html"
    success_url = reverse_lazy("faculty_list")


class FacultyUpdateView(UpdateView):
    model = Faculty
    form_class = FacultyForm
    template_name = "crud/form.html"
    success_url = reverse_lazy("faculty_list")


class FacultyDeleteView(DeleteView):
    model = Faculty
    template_name = "crud/delete_confirm.html"
    success_url = reverse_lazy("faculty_list")


class ProgramListView(ListView):
    model = AcademicProgram
    template_name = "crud/program_list.html"
    context_object_name = "items"


class ProgramCreateView(CreateView):
    model = AcademicProgram
    form_class = AcademicProgramForm
    template_name = "crud/form.html"
    success_url = reverse_lazy("program_list")


class ProgramUpdateView(UpdateView):
    model = AcademicProgram
    form_class = AcademicProgramForm
    template_name = "crud/form.html"
    success_url = reverse_lazy("program_list")


class ProgramDeleteView(DeleteView):
    model = AcademicProgram
    template_name = "crud/delete_confirm.html"
    success_url = reverse_lazy("program_list")


class CourseListView(ListView):
    model = Course
    template_name = "crud/course_list.html"
    context_object_name = "items"


class CourseCreateView(CreateView):
    model = Course
    form_class = CourseForm
    template_name = "crud/form.html"
    success_url = reverse_lazy("course_list")


class CourseUpdateView(UpdateView):
    model = Course
    form_class = CourseForm
    template_name = "crud/form.html"
    success_url = reverse_lazy("course_list")


class CourseDeleteView(DeleteView):
    model = Course
    template_name = "crud/delete_confirm.html"
    success_url = reverse_lazy("course_list")


class TeacherListView(ListView):
    model = Teacher
    template_name = "crud/teacher_list.html"
    context_object_name = "items"


class TeacherCreateView(CreateView):
    model = Teacher
    form_class = TeacherForm
    template_name = "crud/form.html"
    success_url = reverse_lazy("teacher_list")


class TeacherUpdateView(UpdateView):
    model = Teacher
    form_class = TeacherForm
    template_name = "crud/form.html"
    success_url = reverse_lazy("teacher_list")


class TeacherDeleteView(DeleteView):
    model = Teacher
    template_name = "crud/delete_confirm.html"
    success_url = reverse_lazy("teacher_list")


class StudentListView(ListView):
    model = StudentProfile
    template_name = "crud/student_list.html"
    context_object_name = "items"


class StudentCreateView(CreateView):
    model = StudentProfile
    form_class = StudentForm
    template_name = "crud/form.html"
    success_url = reverse_lazy("student_list")


class StudentUpdateView(UpdateView):
    model = StudentProfile
    form_class = StudentForm
    template_name = "crud/form.html"
    success_url = reverse_lazy("student_list")


class StudentDeleteView(DeleteView):
    model = StudentProfile
    template_name = "crud/delete_confirm.html"
    success_url = reverse_lazy("student_list")


class ClassroomListView(ListView):
    model = Classroom
    template_name = "crud/classroom_list.html"
    context_object_name = "items"


class ClassroomCreateView(CreateView):
    model = Classroom
    form_class = ClassroomForm
    template_name = "crud/form.html"
    success_url = reverse_lazy("classroom_list")


class ClassroomUpdateView(UpdateView):
    model = Classroom
    form_class = ClassroomForm
    template_name = "crud/form.html"
    success_url = reverse_lazy("classroom_list")


class ClassroomDeleteView(DeleteView):
    model = Classroom
    template_name = "crud/delete_confirm.html"
    success_url = reverse_lazy("classroom_list")


class StudyPlanListView(ListView):
    model = StudyPlan
    template_name = "crud/study_plan_list.html"
    context_object_name = "items"
