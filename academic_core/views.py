from django.contrib import messages
from django.db import IntegrityError
from django.shortcuts import redirect, render

from access_support.role_access import ACADEMIC_MANAGEMENT_ROLES, roles_required
from access_support.views import _base_context
from classrooms.views import get_classrooms
from teaching.models import Teacher

from .models import AcademicProgram, Campus, Course, Faculty, StudyPlan
from .services.academic_services import get_programs


@roles_required(*ACADEMIC_MANAGEMENT_ROLES)
def subjects_view(request):
    context = _base_context(request)
    context["items"] = Course.objects.select_related("study_plan", "study_plan__program").order_by("id")
    return render(request, "dashboard/subjects.html", context)


@roles_required(*ACADEMIC_MANAGEMENT_ROLES)
def create_subject_view(request):
    context = _base_context(request)
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
        credits_clean = form_data["creditos"].strip()

        if not name or not code or not program_id or not credits_clean:
            context["error_message"] = "Debes completar todos los campos obligatorios"
        elif any(ch.isspace() for ch in code):
            context["error_message"] = "El codigo no puede tener espacios"
        elif Course.objects.filter(code__iexact=code).exists():
            context["error_message"] = f"Ya existe una materia con codigo '{code}'"
        else:
            program = AcademicProgram.objects.filter(id=program_id).first()
            study_plan = (
                StudyPlan.objects.filter(program=program).order_by("-version", "-id").first()
                if program else None
            )
            if not program:
                context["error_message"] = "Programa no existe"
            elif not study_plan:
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
                    return redirect("course_list")
                except ValueError:
                    context["error_message"] = "Creditos deben ser numero positivo"
                except IntegrityError:
                    context["error_message"] = "Error: codigo duplicado"

    context["form_data"] = form_data
    return render(request, "dashboard/create_subject.html", context)


@roles_required(*ACADEMIC_MANAGEMENT_ROLES)
def subject_detail_view(request):
    return render(request, "dashboard/subject_detail.html", _base_context(request))


@roles_required(*ACADEMIC_MANAGEMENT_ROLES)
def campuses_view(request):
    context = _base_context(request)
    context["items"] = Campus.objects.all().order_by("id")
    return render(request, "dashboard/campuses.html", context)


@roles_required(*ACADEMIC_MANAGEMENT_ROLES)
def faculties_view(request):
    context = _base_context(request)
    context["items"] = Faculty.objects.all().order_by("id")
    return render(request, "dashboard/faculties.html", context)


@roles_required(*ACADEMIC_MANAGEMENT_ROLES)
def added_success_view(request):
    return render(request, "dashboard/success.html", _base_context(request))


@roles_required(*ACADEMIC_MANAGEMENT_ROLES)
def programs_view(request):
    context = _base_context(request)
    context["items"] = get_programs()
    return render(request, "dashboard/programs.html", context)


@roles_required("student", "teacher", *ACADEMIC_MANAGEMENT_ROLES)
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
        courses_by_semester = {}
        for course in plan.courses.all().order_by("semester", "name"):
            courses_by_semester.setdefault(course.semester, []).append(course.name)

        semesters = [
            {"numero": semester_number, "materias": course_names}
            for semester_number, course_names in courses_by_semester.items()
        ]
        filtered_plans.append({"programa": plan.program.name, "semestres": semesters})

    context["selected_program"] = selected_program
    context["programs"] = programs
    context["filtered_plans"] = filtered_plans
    context["items"] = StudyPlan.objects.all().order_by("id")
    return render(request, "dashboard/study_plan.html", context)
