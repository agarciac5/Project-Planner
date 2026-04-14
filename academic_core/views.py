
from django.shortcuts import redirect, render
from django.contrib import messages
from .models import Course, AcademicProgram, StudyPlan
from teaching.models import Teacher
from .models import Campus, Faculty
from django.db import IntegrityError
from classrooms.views import get_classrooms
from academic_core.services.academic_services import get_programs
from access_support.views import _base_context


def subjects_view(request):
    context = {}
    context["items"] = Course.objects.all().order_by("id")
    return render(request, "dashboard/subjects.html", context)


def create_subject_view(request):
    context = {}

    context["classrooms_db"] = get_classrooms()
    context["programs_db"] = AcademicProgram.objects.all().order_by("name")
    context["teachers_db"] = Teacher.objects.all().order_by("first_name", "last_name")

    form_data = {}

    if request.method == "POST":
        context["error_message"] = ""

        form_data = {
            "materia": request.POST.get("materia", ""),
            "codigo": request.POST.get("codigo", ""),
            "creditos": request.POST.get("creditos", ""),
            "programa": request.POST.get("programa", ""),
        }

        name = form_data["materia"].strip()
        code = form_data["codigo"].strip()
        program_id = form_data["programa"].strip()
        credits_raw = form_data["creditos"]
        credits_clean = credits_raw.strip()

        
        if not name or not code or not program_id or not credits_clean:
            context["error_message"] = "Debes completar todos los campos obligatorios"

        elif any(ch.isspace() for ch in code):
            context["error_message"] = "El código no puede tener espacios"

        elif Course.objects.filter(code__iexact=code).exists():
            context["error_message"] = f"Ya existe una materia con código '{code}'"

        else:
            program = AcademicProgram.objects.filter(id=program_id).first()

            if not program:
                context["error_message"] = "Programa no existe"

            else:
                study_plan = (
                    StudyPlan.objects.filter(program=program)
                    .order_by("-version", "-id")
                    .first()
                )

                if not study_plan:
                    context["error_message"] = "El programa no tiene plan de estudios"

                else:
                    try:
                        credits = int(credits_clean)

                        if credits < 0:
                            raise ValueError

                        Course.objects.create(
                            name=name,
                            code=code,
                            credits=credits,
                            semester=1,
                            study_plan=study_plan,
                        )

                        messages.success(request, "Materia creada correctamente")

                        # ⚠️ IMPORTANTE: usa el nombre correcto de tu URL
                        return redirect("course_list")

                    except ValueError:
                        context["error_message"] = "Créditos deben ser número positivo"

                    except IntegrityError:
                        context["error_message"] = "Error: código duplicado"

    context["form_data"] = form_data
    return render(request, "dashboard/create_subject.html", context)


def subject_detail_view(request):
    return render(request, "dashboard/subject_detail.html", {})
def campuses_view(request):
    context = {}
    context["items"] = Campus.objects.all().order_by("id")
    return render(request, "dashboard/campuses.html", context)


def faculties_view(request):
    context = {}
    context["items"] = Faculty.objects.all().order_by("id")
    return render(request, "dashboard/faculties.html", context)

def added_success_view(request):
    return render(request, "dashboard/success.html", {})


def programs_view(request):
    context = _base_context(request)
    context["items"] = get_programs()
    return render(request, "dashboard/programs.html", context)
def study_plan_view(request):
    context = _base_context(request)
    selected_program = request.GET.get("program")

    study_plans = (
        StudyPlan.objects.select_related("program")
        .prefetch_related("courses")
        .order_by("program__name", "version")
    )
    programs = AcademicProgram.objects.order_by("name")

    if selected_program:
        study_plans = study_plans.filter(program__name=selected_program)

    filtered_plans = []
    for plan in study_plans:
        semesters = []
        courses_by_semester = {}
        for course in plan.courses.all().order_by("semester", "name"):
            courses_by_semester.setdefault(course.semester, []).append(course.name)

        for semester_number, course_names in courses_by_semester.items():
            semesters.append(
                {
                    "numero": semester_number,
                    "materias": course_names,
                }
            )

        filtered_plans.append(
            {
                "programa": plan.program.name,
                "semestres": semesters,
            }
        )
    context["selected_program"] = selected_program
    context["programs"] = programs
    context["filtered_plans"] = filtered_plans
    context["items"] = StudyPlan.objects.all().order_by("id")
    return render(request, "dashboard/study_plan.html", context)