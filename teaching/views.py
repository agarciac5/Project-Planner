from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from access_support.forms import TeacherForm
from access_support.models import User
from access_support.role_access import ACADEMIC_MANAGEMENT_ROLES, roles_required
from .models import Availability, Teacher


def _build_teacher_email(teacher_id):
    base = "".join(ch.lower() for ch in str(teacher_id).strip() if ch.isalnum())
    if not base:
        base = "sinid"
    candidate = f"teacher.{base}@autogen.local"
    suffix = 1
    while User.objects.filter(email=candidate).exists():
        suffix += 1
        candidate = f"teacher.{base}.{suffix}@autogen.local"
    return candidate


def _ensure_teacher_user(teacher):
    if teacher.user_id:
        return teacher.user

    email = _build_teacher_email(teacher.teacher_id)
    user = User.objects.create_user(email=email, password="CambioObligatorio2026!", role="teacher")
    teacher.user = user
    teacher.save(update_fields=["user"])
    return user


@roles_required(*ACADEMIC_MANAGEMENT_ROLES)
def teachers_view(request):
    teachers = Teacher.objects.select_related("user", "program", "faculty", "campus", "contract").order_by("id")
    return render(request, "dashboard/teachers.html", {"items": teachers})


@roles_required(*ACADEMIC_MANAGEMENT_ROLES)
def teacher_create_view(request):
    if request.method == "POST":
        form = TeacherForm(request.POST)
        if form.is_valid():
            teacher = form.save()
            _ensure_teacher_user(teacher)

            day = request.POST.get("day")
            start_time = request.POST.get("start_time")
            end_time = request.POST.get("end_time")
            if day and start_time and end_time:
                Availability.objects.create(
                    teacher=teacher, day=day, start_time=start_time, end_time=end_time
                )

            messages.success(request, "Docente creado correctamente con disponibilidad")
            return redirect("teacher_list")
    else:
        form = TeacherForm()

    return render(request, "crud/form.html", {"form": form})


@roles_required(*ACADEMIC_MANAGEMENT_ROLES)
def add_availability(request, teacher_id):
    if request.method == "POST":
        teacher = get_object_or_404(Teacher, id=teacher_id)
        day = request.POST.get("day")
        start_time = request.POST.get("start_time")
        end_time = request.POST.get("end_time")

        if day and start_time and end_time:
            Availability.objects.create(
                teacher=teacher, day=day, start_time=start_time, end_time=end_time
            )
            messages.success(request, "Disponibilidad agregada correctamente.")

    return redirect("teacher_list")


@roles_required(*ACADEMIC_MANAGEMENT_ROLES)
def teacher_edit_view(request, teacher_id):
    teacher = get_object_or_404(Teacher, id=teacher_id)
    if request.method == "POST":
        form = TeacherForm(request.POST, instance=teacher)
        if form.is_valid():
            teacher = form.save()
            _ensure_teacher_user(teacher)
            messages.success(request, "Docente actualizado correctamente.")
            return redirect("teacher_list")
    else:
        form = TeacherForm(instance=teacher)

    return render(request, "crud/form.html", {"form": form})


@roles_required(*ACADEMIC_MANAGEMENT_ROLES)
def teacher_delete_view(request, teacher_id):
    teacher = get_object_or_404(Teacher, id=teacher_id)
    teacher.delete()
    messages.success(request, "Docente eliminado correctamente.")
    return redirect("teacher_list")
