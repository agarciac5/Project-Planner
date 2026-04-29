from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.db import transaction
from django.utils.crypto import get_random_string

from academic_core.models import Campus, Faculty, AcademicProgram, Course, StudyPlan
from teaching.models import Teacher
from classrooms.models import Classroom
from .models import StudentProfile, User
from .role_access import AcademicManagementRequiredMixin
from .forms import (
    CampusForm,
    FacultyForm,
    AcademicProgramForm,
    CourseForm,
    TeacherForm,
    ClassroomForm,
    StudentForm,
)


class CampusListView(AcademicManagementRequiredMixin, ListView):
    model = Campus
    template_name = "dashboard/campuses.html"
    context_object_name = "items"


class CampusCreateView(AcademicManagementRequiredMixin, CreateView):
    model = Campus
    form_class = CampusForm
    template_name = "crud/form.html"
    success_url = reverse_lazy("campus_list")


class CampusUpdateView(AcademicManagementRequiredMixin, UpdateView):
    model = Campus
    form_class = CampusForm
    template_name = "crud/form.html"
    success_url = reverse_lazy("campus_list")


class CampusDeleteView(AcademicManagementRequiredMixin, DeleteView):
    model = Campus
    template_name = "crud/delete_confirm.html"
    success_url = reverse_lazy("campus_list")


class FacultyListView(AcademicManagementRequiredMixin, ListView):
    model = Faculty
    template_name = "dashboard/faculties.html"
    context_object_name = "items"


class FacultyCreateView(AcademicManagementRequiredMixin, CreateView):
    model = Faculty
    form_class = FacultyForm
    template_name = "crud/form.html"
    success_url = reverse_lazy("faculty_list")


class FacultyUpdateView(AcademicManagementRequiredMixin, UpdateView):
    model = Faculty
    form_class = FacultyForm
    template_name = "crud/form.html"
    success_url = reverse_lazy("faculty_list")


class FacultyDeleteView(AcademicManagementRequiredMixin, DeleteView):
    model = Faculty
    template_name = "crud/delete_confirm.html"
    success_url = reverse_lazy("faculty_list")


class ProgramListView(AcademicManagementRequiredMixin, ListView):
    model = AcademicProgram
    template_name = "crud/program_list.html"
    context_object_name = "items"


class ProgramCreateView(AcademicManagementRequiredMixin, CreateView):
    model = AcademicProgram
    form_class = AcademicProgramForm
    template_name = "crud/form.html"
    success_url = reverse_lazy("program_list")


class ProgramUpdateView(AcademicManagementRequiredMixin, UpdateView):
    model = AcademicProgram
    form_class = AcademicProgramForm
    template_name = "crud/form.html"
    success_url = reverse_lazy("program_list")


class ProgramDeleteView(AcademicManagementRequiredMixin, DeleteView):
    model = AcademicProgram
    template_name = "crud/delete_confirm.html"
    success_url = reverse_lazy("program_list")


class CourseListView(AcademicManagementRequiredMixin, ListView):
    model = Course
    template_name = "dashboard/subjects.html"
    context_object_name = "items"


class CourseCreateView(AcademicManagementRequiredMixin, CreateView):
    model = Course
    form_class = CourseForm
    template_name = "crud/form.html"
    success_url = reverse_lazy("course_list")


class CourseUpdateView(AcademicManagementRequiredMixin, UpdateView):
    model = Course
    form_class = CourseForm
    template_name = "crud/form.html"
    success_url = reverse_lazy("course_list")


class CourseDeleteView(AcademicManagementRequiredMixin, DeleteView):
    model = Course
    template_name = "crud/delete_confirm.html"
    success_url = reverse_lazy("course_list")


class TeacherListView(AcademicManagementRequiredMixin, ListView):
    model = Teacher
    template_name = "crud/teacher_list.html"
    context_object_name = "items"


class TeacherCreateView(AcademicManagementRequiredMixin, CreateView):
    model = Teacher
    form_class = TeacherForm
    template_name = "crud/form.html"
    success_url = reverse_lazy("teacher_list")


class TeacherUpdateView(AcademicManagementRequiredMixin, UpdateView):
    model = Teacher
    form_class = TeacherForm
    template_name = "crud/form.html"
    success_url = reverse_lazy("teacher_list")


class TeacherDeleteView(AcademicManagementRequiredMixin, DeleteView):
    model = Teacher
    template_name = "crud/delete_confirm.html"
    success_url = reverse_lazy("teacher_list")


class StudentListView(AcademicManagementRequiredMixin, ListView):
    model = StudentProfile
    template_name = "crud/student_list.html"
    context_object_name = "items"


class StudentCreateView(AcademicManagementRequiredMixin, CreateView):
    model = StudentProfile
    form_class = StudentForm
    template_name = "crud/form.html"
    success_url = reverse_lazy("student_list")

    def form_valid(self, form):
        profile_preview = form.save(commit=False)
        email_base = (
            profile_preview.document_number
            or profile_preview.student_code
            or get_random_string(8)
        )
        email_base = str(email_base).strip().lower().replace(" ", "")
        if not email_base:
            email_base = get_random_string(8).lower()
        email = f"student.{email_base}@autogen.local"
        suffix = 1
        while User.objects.filter(email=email).exists():
            suffix += 1
            email = f"student.{email_base}.{suffix}@autogen.local"
        raw_password = get_random_string(12)

        with transaction.atomic():
            user = User.objects.create_user(
                email=email,
                password=raw_password,
                role="student",
            )
            self.object = form.save(commit=False)
            self.object.user = user
            if self.object.program and not self.object.faculty:
                self.object.faculty = self.object.program.faculty
            if self.object.program and not self.object.campus:
                self.object.campus = self.object.program.campus
            self.object.save()

        messages.success(
            self.request,
            f"Estudiante creado correctamente. Usuario interno: {email}",
        )
        return HttpResponseRedirect(self.get_success_url())


class StudentUpdateView(AcademicManagementRequiredMixin, UpdateView):
    model = StudentProfile
    form_class = StudentForm
    template_name = "crud/form.html"
    success_url = reverse_lazy("student_list")


class StudentDeleteView(AcademicManagementRequiredMixin, DeleteView):
    model = StudentProfile
    template_name = "crud/delete_confirm.html"
    success_url = reverse_lazy("student_list")


class ClassroomListView(AcademicManagementRequiredMixin, ListView):
    model = Classroom
    template_name = "crud/classroom_list.html"
    context_object_name = "items"


class ClassroomCreateView(AcademicManagementRequiredMixin, CreateView):
    model = Classroom
    form_class = ClassroomForm
    template_name = "crud/form.html"
    success_url = reverse_lazy("classroom_list")


class ClassroomUpdateView(AcademicManagementRequiredMixin, UpdateView):
    model = Classroom
    form_class = ClassroomForm
    template_name = "crud/form.html"
    success_url = reverse_lazy("classroom_list")


class ClassroomDeleteView(AcademicManagementRequiredMixin, DeleteView):
    model = Classroom
    template_name = "crud/delete_confirm.html"
    success_url = reverse_lazy("classroom_list")


class StudyPlanListView(AcademicManagementRequiredMixin, ListView):
    model = StudyPlan
    template_name = "crud/study_plan_list.html"
    context_object_name = "items"
