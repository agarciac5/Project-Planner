
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Teacher, Availability
from access_support.forms import TeacherForm


def teachers_view(request):
    teachers = Teacher.objects.all().order_by("id")
    return render(request, "dashboard/teachers.html", {"items": teachers})


def teacher_create_view(request):
    if request.method == "POST":
        form = TeacherForm(request.POST)
        if form.is_valid():
            teacher = form.save() 

        
            day = request.POST.get("day")
            start_time = request.POST.get("start_time")
            end_time = request.POST.get("end_time")
            if day and start_time and end_time:
                Availability.objects.create(
                    teacher=teacher,
                    day=day,
                    start_time=start_time,
                    end_time=end_time
                )

            messages.success(request, "Docente creado correctamente con disponibilidad")
            return redirect("teacher_list")
    else:
        form = TeacherForm()

    return render(request, "crud/form.html", {
        "form": form
    })

# Vista para agregar disponibilidad de un docente existente
def add_availability(request, teacher_id):
    if request.method == "POST":
        teacher = get_object_or_404(Teacher, id=teacher_id)
        day = request.POST.get("day")
        start_time = request.POST.get("start_time")
        end_time = request.POST.get("end_time")

        if day and start_time and end_time:
            Availability.objects.create(
                teacher=teacher,
                day=day,
                start_time=start_time,
                end_time=end_time
            )

    return redirect("teacher_list")

# Vista para editar docente (solo mensaje por ahora)
def teacher_edit_view(request, teacher_id):
    teacher = get_object_or_404(Teacher, id=teacher_id)
    messages.info(request, f"Función editar docente {teacher_id} no implementada aún.")
    return redirect("teacher_list")

# Vista para eliminar docente
def teacher_delete_view(request, teacher_id):
    teacher = get_object_or_404(Teacher, id=teacher_id)
    teacher.delete()
    messages.success(request, "Docente eliminado correctamente.")
    return redirect("teacher_list")