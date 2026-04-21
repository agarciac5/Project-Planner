from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

from teaching.models import Teacher
from classrooms.models import Classroom
from academic_core.models import AcademicTerm

from .models import (
    CourseGroup,
    ProposedSchedule,
    ScheduleSession,
    SemesterScheduleOption,
    SemesterScheduleRun,
    TeacherActivity,
)
from .services.scheduling_service import (
    apply_semester_schedule_run,
    generate_semester_schedule_options,
    revert_semester_schedule_option,
)

from .genetic import (
    run_genetic_algorithm,
    GroupInfo, AvailabilitySlot, ClassroomInfo, OccupiedSlot, ActivitySlot,
)

# IMPORT NUEVO ALGORITMO (SEPARADO)
from . import genetic_students as gs
from collections import defaultdict

# Clase simple para timeslots
class Timeslot:
    def __init__(self, day, start_time, end_time):
        self.day = day
        self.start_time = start_time
        self.end_time = end_time


def _generate_timeslots():
    """Genera timeslots estándar para cada día."""
    from datetime import time
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    slots = []
    start_times = [
        time(7, 0), time(8, 30), time(10, 0), time(11, 30), time(13, 0), time(14, 30), time(16, 0), time(17, 30), time(19, 0), time(20, 30)
    ]
    for day in days:
        for start in start_times:
            # Assume 1.5 hours duration
            end_hour = start.hour + 1
            end_minute = start.minute + 30
            if end_minute >= 60:
                end_hour += 1
                end_minute -= 60
            end = time(end_hour, end_minute)
            if end <= time(22, 0):  # up to 10 PM
                slots.append(Timeslot(day, start, end))
    return slots
DAYS_ES = {
    "Monday":    "Lunes",
    "Tuesday":   "Martes",
    "Wednesday": "Miércoles",
    "Thursday":  "Jueves",
    "Friday":    "Viernes",
    "Saturday":  "Sábado",
}

DAYS_ORDER = list(DAYS_ES.keys())

SEMESTER_PENALTY_LABELS = {
    "uncovered_demand": "Demanda sin cubrir",
    "extra_sections": "Secciones abiertas de mas",
    "missing_resources": "Asignaciones incompletas",
    "qualification": "Docentes no calificados",
    "capacity": "Aulas con capacidad insuficiente",
    "teacher_conflicts": "Choques de docente",
    "classroom_conflicts": "Choques de aula",
    "availability": "Fuera de disponibilidad",
    "activities": "Choques con actividades",
    "below_min_section_size": "Secciones con menos de 5 estudiantes",
    "load_balance": "Desbalance de carga",
    "contract_overload": "Sobrecarga contractual",
    "under_min_hours": "Docentes por debajo del minimo contractual",
}


def _build_semester_run_context(run):
    options = []
    run = SemesterScheduleRun.objects.prefetch_related(
        "options__assignments__course",
        "options__assignments__teacher",
        "options__assignments__classroom",
    ).get(id=run.id)

    for option in run.options.all():
        assignments = []
        for assignment in option.assignments.all():
            assignments.append(
                {
                    "course_code": assignment.course.code,
                    "course_name": assignment.course.name,
                    "section_number": assignment.section_number,
                    "teacher": str(assignment.teacher) if assignment.teacher else "Sin docente",
                    "classroom": assignment.classroom.classroom_id if assignment.classroom else "Sin aula",
                    "day": DAYS_ES.get(assignment.day, assignment.day),
                    "start_time": assignment.start_time.strftime("%H:%M"),
                    "end_time": assignment.end_time.strftime("%H:%M"),
                    "students_assigned": assignment.students_assigned,
                    "nrc": assignment.nrc,
                }
            )

        penalties = []
        for key, value in option.summary.get("penalties", {}).items():
            if not value:
                continue
            penalties.append(
                {
                    "label": SEMESTER_PENALTY_LABELS.get(key, key),
                    "value": value,
                }
            )

        options.append(
            {
                "id": option.id,
                "rank": option.rank,
                "score": option.score,
                "is_best": option.is_best,
                "selected": option.selected,
                "applied": option.applied,
                "demand_covered": option.demand_covered,
                "demand_total": option.demand_total,
                "sections_opened": option.sections_opened,
                "summary": option.summary,
                "penalties": penalties,
                "assignments": assignments,
            }
        )

    return run, options


def _sessions_display(genes, groups_by_id, classrooms_by_id):
    rows = []
    for gene in genes:
        group = groups_by_id.get(gene.group_id)
        classroom = classrooms_by_id.get(gene.classroom_id) if gene.classroom_id else None
        if not group:
            continue
        rows.append(
            {
                "course_code": group.course.code,
                "course_name": group.course.name,
                "day": DAYS_ES.get(gene.day, gene.day),
                "day_order": DAYS_ORDER.index(gene.day) if gene.day in DAYS_ORDER else 99,
                "start_time": gene.start_time.strftime("%H:%M"),
                "end_time": gene.end_time.strftime("%H:%M"),
                "classroom": classroom.classroom_id if classroom else "Virtual",
            }
        )
    return sorted(rows, key=lambda row: (row["day_order"], row["start_time"]))


def _sessions_display_students(genes, classrooms_by_id):
    rows = []
    for gene in genes:
        group = gene["group"]
        classroom = gene["classroom"]
        ts = gene["timeslot"]
        rows.append({
            "course_code": group.course.code,
            "course_name": group.course.name,
            "day": DAYS_ES.get(ts.day, ts.day),
            "day_order": DAYS_ORDER.index(ts.day) if ts.day in DAYS_ORDER else 99,
            "start_time": ts.start_time.strftime("%H:%M"),
            "end_time": ts.end_time.strftime("%H:%M"),
            "classroom": classroom.classroom_id if classroom else "Virtual",
        })
    return sorted(rows, key=lambda r: (r["day_order"], r["start_time"]))


def _unique_individuals(individuals):
    seen = set()
    unique = []

    for individual in individuals:
        signature = tuple(
            (
                gene["group"].id,
                gene["classroom"].id if gene["classroom"] else None,
                gene["timeslot"].day,
                gene["timeslot"].start_time,
                gene["timeslot"].end_time,
            )
            for gene in individual.genes
        )

        if signature not in seen:
            seen.add(signature)
            unique.append(individual)

    return unique


def generate_schedule_view(request):
    teachers = Teacher.objects.filter(is_active=True).order_by("last_name", "first_name")
    terms    = AcademicTerm.objects.order_by("-start_date")

    context = {
        "teachers": teachers,
        "terms": terms,
        "top3": None,
    }

    if request.method != "POST":
        return render(request, "scheduling/generate_schedule.html", context)

    teacher_id = request.POST.get("teacher_id")
    term_id    = request.POST.get("term_id")

    if not teacher_id or not term_id:
        messages.error(request, "Debes seleccionar un docente y un periodo.")
        return render(request, "scheduling/generate_schedule.html", context)

    teacher = get_object_or_404(Teacher, id=teacher_id)
    term    = get_object_or_404(AcademicTerm, id=term_id)

    # --- Grupos del profesor ---
    course_groups = CourseGroup.objects.filter(
        teacher=teacher, term=term
    ).select_related("course")

    if not course_groups.exists():
        messages.warning(
            request,
            f"El docente {teacher} no tiene grupos asignados en el periodo {term}."
        )
        return render(request, "scheduling/generate_schedule.html", context)

    groups_info = [
        GroupInfo(
            group_id=cg.id,
            course_code=cg.course.code,
            course_name=cg.course.name,
            credits=cg.course.credits,
            required_classroom_type="VIRTUAL" if cg.is_virtual else "SISTEMAS",
            is_virtual=cg.is_virtual,
        )
        for cg in course_groups
    ]

    # --- Disponibilidad ---
    availability_slots = [
        AvailabilitySlot(day=av.day, start=av.start_time, end=av.end_time)
        for av in teacher.availabilities.all()
    ]
   
    # --- Aulas ---
    classrooms_qs = Classroom.objects.filter(is_active=True)
    if teacher.campus:
        classrooms_qs = classrooms_qs.filter(campus=teacher.campus)

    classrooms_info = [
        ClassroomInfo(
            classroom_id=c.id,
            code=c.classroom_id,
            capacity=c.capacity,
            classroom_type=c.classroom_type,
        )
        for c in classrooms_qs
    ]

    classrooms_by_id = {c.id: c for c in classrooms_qs}
    groups_by_id     = {cg.id: cg for cg in course_groups}

    # --- Franjas ocupadas por otros ---
    occupied = [
        OccupiedSlot(
            classroom_id=s.classroom.id,
            day=s.day,
            start=s.start_time,
            end=s.end_time,
        )
        for s in ScheduleSession.objects.filter(
            schedule__term=term
        ).exclude(
            schedule__teacher=teacher
        ).select_related("classroom")
        if s.classroom
    ]

    # --- Actividades extra del profesor ---
    activities = [
        ActivitySlot(
            activity_type=a.activity_type,
            day=a.day,
            start=a.start_time,
            end=a.end_time,
        )
        for a in TeacherActivity.objects.filter(teacher=teacher, term=term)
    ]

    # --- Contrato ---
    if teacher.contract:
        max_hours = teacher.contract.max_teaching_hours
        min_hours = teacher.contract.min_teaching_hours
    else:
        max_hours, min_hours = 20, 5

    # --- Ejecutar algoritmo ---
    top3_raw = run_genetic_algorithm(
        groups=groups_info,
        availability=availability_slots,
        classrooms=classrooms_info,
        occupied_slots=occupied,
        activities=activities,
        max_teaching_hours=max_hours,
        min_teaching_hours=min_hours,
    )

    if not top3_raw:
        messages.error(request, "El algoritmo no pudo generar ninguna propuesta.")
        return render(request, "scheduling/generate_schedule.html", context)

    # --- Guardar top 3 en BD ---
    ProposedSchedule.objects.filter(
        teacher=teacher, term=term, status="draft"
    ).delete()

    top3_display = []

    for rank, (chromosome, fitness, breakdown) in enumerate(top3_raw, start=1):
        proposed = ProposedSchedule.objects.create(
            teacher=teacher,
            term=term,
            fitness_score=round(fitness, 2),
            rank=rank,
            status="draft",
        )

        for gene in chromosome:
            group = groups_by_id.get(gene.group_id)
            classroom = classrooms_by_id.get(gene.classroom_id) if gene.classroom_id else None

            if not group:
                continue

            ScheduleSession.objects.create(
                schedule=proposed,
                group=group,
                classroom=classroom,
                day=gene.day,
                start_time=gene.start_time,
                end_time=gene.end_time,
            )

        top3_display.append({
            "rank": rank,
            "id": proposed.id,
            "fitness": round(fitness, 2),
            "hours": breakdown.total_teaching_hours,
            "sessions": _sessions_display(chromosome, groups_by_id, classrooms_by_id),
            "breakdown": breakdown.penalty_detail(),
        })

    context["top3"]    = top3_display
    context["teacher"] = str(teacher)
    context["term"]    = str(term)

    messages.success(request, f"Se generaron {len(top3_display)} propuestas de horario.")
    return render(request, "scheduling/generate_schedule.html", context)


# ---------------------------------------------------------------------------
# NUEVO ALGORITMO (STUDENTS) - SIN ROMPER EL VIEJO
# ---------------------------------------------------------------------------
def generate_schedule_view_students(request):
    teachers = Teacher.objects.filter(is_active=True).order_by("last_name", "first_name")
    terms    = AcademicTerm.objects.order_by("-start_date")

    context = {
        "teachers": teachers,
        "terms": terms,
        "top3": None,
    }

    if request.method != "POST":
        return render(request, "scheduling/student_schedule.html", context)

    teacher_id = request.POST.get("teacher_id")
    term_id    = request.POST.get("term_id")

    if not teacher_id or not term_id:
        messages.error(request, "Debes seleccionar un docente y un periodo.")
        return render(request, "scheduling/student_schedule.html", context)

    teacher = get_object_or_404(Teacher, id=teacher_id)
    term    = get_object_or_404(AcademicTerm, id=term_id)

    # --- Grupos del profesor ---
    course_groups = CourseGroup.objects.filter(
        teacher=teacher, term=term
    ).select_related("course")

    if not course_groups.exists():
        messages.warning(
            request,
            f"El docente {teacher} no tiene grupos asignados en el periodo {term}."
        )
        return render(request, "scheduling/student_schedule.html", context)

    groups = [
    type("Group", (), {
        "id": cg.id,
        "course": cg.course,
        "teacher": teacher,
        "capacity": cg.capacity,
        "is_virtual": cg.is_virtual,
    })()
    for cg in course_groups
]

    # --- Aulas ---
    classrooms_qs = Classroom.objects.filter(is_active=True)
    classrooms_by_id = {c.id: c for c in classrooms_qs}

    # --- Timeslots ---
    timeslots = _generate_timeslots()

    # --- Actividades y disponibilidad agrupadas por profesor ---
    teacher_activities = defaultdict(list)
    for act in TeacherActivity.objects.filter(teacher=teacher, term=term):
        teacher_activities[teacher.id].append(act)

    teacher_availability = {teacher.id: list(teacher.availabilities.all())}

    # --- Ejecutar algoritmo NUEVO ---
    top3_raw = gs.run_genetic_algorithm(
        groups=groups,
        classrooms=list(classrooms_qs),
        timeslots=timeslots,
        teacher_activities=teacher_activities,
        teacher_availability=teacher_availability,
    )

    top3_display = []
    unique_individuals = _unique_individuals(top3_raw)

    for rank, individual in enumerate(unique_individuals[:3], start=1):
        chromosome = individual.genes
        fitness = individual.fitness
        sessions = _sessions_display_students(chromosome, classrooms_by_id)
        breakdown = {}  # Simplificado, sin detalles de penalización

        top3_display.append({
            "rank": rank,
            "fitness": fitness,
            "sessions": sessions,
            "breakdown": breakdown,
        })

    context["top3"] = top3_display

    messages.success(request, "Se generaron las propuestas del algoritmo nuevo.")
    return render(request, "scheduling/student_schedule.html", context)


# ---------------------------------------------------------------------------
# Lista y detalle
# ---------------------------------------------------------------------------
def schedule_list_view(request):
    schedules = ProposedSchedule.objects.select_related(
        "teacher", "term"
    ).order_by("-created_at")

    return render(request, "scheduling/schedule_list.html", {"schedules": schedules})


def schedule_detail_view(request, schedule_id):
    schedule = get_object_or_404(
        ProposedSchedule.objects.select_related("teacher", "term"),
        id=schedule_id
    )

    sessions = schedule.sessions.select_related(
        "group__course", "classroom"
    ).order_by("day", "start_time")

    sessions_display = [
        {
            "course_code": s.group.course.code,
            "course_name": s.group.course.name,
            "day": DAYS_ES.get(s.day, s.day),
            "start_time": s.start_time.strftime("%H:%M"),
            "end_time": s.end_time.strftime("%H:%M"),
            "classroom": s.classroom.classroom_id if s.classroom else "Virtual",
        }
        for s in sessions
    ]

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "approve":
            schedule.status = "approved"
            schedule.save()
            messages.success(request, "Horario aprobado.")

        elif action == "reject":
            schedule.status = "rejected"
            schedule.save()
            messages.warning(request, "Horario rechazado.")

        return redirect("schedule_detail", schedule_id=schedule.id)

    return render(request, "scheduling/schedule_detail.html", {
        "schedule": schedule,
        "sessions": sessions_display,
    })


def semester_planner_view(request):
    terms = AcademicTerm.objects.order_by("-start_date")
    context = {
        "terms": terms,
        "run": None,
        "options": [],
        "show_generator": True,
    }

    if request.method != "POST":
        return render(request, "scheduling/semester_planner.html", context)

    term_id = request.POST.get("term_id")
    if not term_id:
        messages.error(request, "Debes seleccionar un periodo academico.")
        return render(request, "scheduling/semester_planner.html", context)

    run = generate_semester_schedule_options(term_id=int(term_id), auto_apply_best=False)
    if not run:
        messages.warning(
            request,
            "No se pudo generar el plan. Revisa que exista demanda suficiente, docentes calificados y aulas disponibles.",
        )
        return render(request, "scheduling/semester_planner.html", context)

    run, options = _build_semester_run_context(run)
    messages.success(request, "Se genero el top 3 de opciones para el semestre. Ahora puedes elegir manualmente una.")

    context["run"] = run
    context["options"] = options
    return render(request, "scheduling/semester_planner.html", context)


def save_semester_run_view(request, run_id):
    run = get_object_or_404(SemesterScheduleRun, id=run_id)
    if request.method == "POST" and run.status == "draft":
        run.status = "saved"
        run.save(update_fields=["status"])
        messages.success(request, "El plan semestral fue guardado correctamente.")
    return redirect("saved_semester_run_detail", run_id=run.id)


def select_semester_option_view(request, option_id):
    option = get_object_or_404(
        SemesterScheduleOption.objects.select_related("run"),
        id=option_id,
    )
    if request.method == "POST":
        option.run.options.exclude(id=option.id).update(selected=False)
        option.selected = True
        option.save(update_fields=["selected"])
        if option.run.status == "draft":
            option.run.status = "saved"
            option.run.save(update_fields=["status"])
        messages.success(request, "La opcion fue fijada como seleccionada.")
    return redirect("saved_semester_run_detail", run_id=option.run.id)


def deselect_semester_option_view(request, option_id):
    option = get_object_or_404(
        SemesterScheduleOption.objects.select_related("run"),
        id=option_id,
    )
    if request.method == "POST":
        if option.applied:
            messages.warning(request, "No puedes deseleccionar una opcion ya aplicada sin revertirla primero.")
            return redirect("saved_semester_run_detail", run_id=option.run.id)
        option.selected = False
        option.save(update_fields=["selected"])
        messages.success(request, "La opcion fue deseleccionada.")
    return redirect("saved_semester_run_detail", run_id=option.run.id)


def apply_semester_option_view(request, option_id):
    option = get_object_or_404(
        SemesterScheduleOption.objects.select_related("run"),
        id=option_id,
    )
    if request.method == "POST":
        if not option.selected:
            messages.warning(request, "Primero debes seleccionar manualmente esta opcion antes de aplicarla.")
            return redirect("saved_semester_run_detail", run_id=option.run.id)
        if option.run.options.exclude(id=option.id).filter(applied=True).exists():
            messages.warning(request, "Ya existe otra opcion aplicada en este plan. Revierte esa aplicacion antes de aplicar una nueva.")
            return redirect("saved_semester_run_detail", run_id=option.run.id)
        apply_semester_schedule_run(option.run, option=option)
        messages.success(request, "La opcion seleccionada fue aplicada y convertida en grupos reales.")
    return redirect("saved_semester_run_detail", run_id=option.run.id)


def revert_semester_option_view(request, option_id):
    option = get_object_or_404(
        SemesterScheduleOption.objects.select_related("run"),
        id=option_id,
    )
    if request.method == "POST":
        revert_semester_schedule_option(option)
        messages.success(request, "La aplicacion de la opcion fue revertida y los grupos creados fueron eliminados.")
    return redirect("saved_semester_run_detail", run_id=option.run.id)


def delete_semester_run_view(request, run_id):
    run = get_object_or_404(SemesterScheduleRun, id=run_id)
    if request.method == "POST":
        run.delete()
        messages.success(request, "El plan semestral fue eliminado.")
    return redirect("saved_semester_runs")


def saved_semester_runs_view(request):
    runs = (
        SemesterScheduleRun.objects.filter(status__in=["saved", "applied"])
        .prefetch_related("options")
        .select_related("term")
        .order_by("-created_at")
    )
    return render(
        request,
        "scheduling/saved_semester_runs.html",
        {"runs": runs},
    )


def saved_semester_run_detail_view(request, run_id):
    run = get_object_or_404(
        SemesterScheduleRun.objects.select_related("term"),
        id=run_id,
    )
    run, options = _build_semester_run_context(run)
    return render(
        request,
        "scheduling/semester_planner.html",
        {
            "terms": AcademicTerm.objects.order_by("-start_date"),
            "run": run,
            "options": options,
            "show_generator": False,
        },
    )
