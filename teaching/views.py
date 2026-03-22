from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Teacher, Availability
from academic_core.models import AcademicProgram, Faculty, Campus
def add_availability(request, teacher_id):
    if request.method == "POST":
        teacher = get_object_or_404(Teacher, id=teacher_id)
        day = request.POST.get("day")
        start_time = request.POST.get("start_time")
        end_time = request.POST.get("end_time")

        
        Availability.objects.create(
            teacher=teacher,
            day=day,
            start_time=start_time,
            end_time=end_time
        )
    
    return redirect("teacher_list")

def teachers_view(request):
    teachers = Teacher.objects.all().order_by("id")
    return render(request, "dashboard/teachers.html", {"items": teachers})


def teacher_create_view(request):
    programs = AcademicProgram.objects.all()
    faculties = Faculty.objects.all()
    campuses = Campus.objects.all()

    if request.method == "POST":
        teacher_id = request.POST.get("teacher_id")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        address = request.POST.get("address")
        program_id = request.POST.get("program")
        faculty_id = request.POST.get("faculty")
        campus_id = request.POST.get("campus")
        type_of_contract = request.POST.get("type_of_contract")

        program = AcademicProgram.objects.get(id=program_id) if program_id else None
        faculty = Faculty.objects.get(id=faculty_id) if faculty_id else None
        campus = Campus.objects.get(id=campus_id) if campus_id else None

        teacher = Teacher.objects.create(
            teacher_id=teacher_id,
            first_name=first_name,
            last_name=last_name,
            address=address,
            program=program,
            faculty=faculty,
            campus=campus,
            type_of_contract=type_of_contract
        )

        
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
        return redirect("teachers_view")

    return render(request, "dashboard/teacher_create.html", {
        "programs": programs,
        "faculties": faculties,
        "campuses": campuses
    })

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Teacher

def teacher_edit_view(request, teacher_id):
    teacher = get_object_or_404(Teacher, id=teacher_id)
    messages.info(request, f"Función editar docente {teacher_id} no implementada aún.")
    return redirect("teacher_list")

def teacher_delete_view(request, teacher_id):
    teacher = get_object_or_404(Teacher, id=teacher_id)
    teacher.delete()
    messages.success(request, "Docente eliminado correctamente.")
    return redirect("teacher_list")