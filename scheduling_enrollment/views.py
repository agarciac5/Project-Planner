from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

from teaching.models import Teacher
from classrooms.models import Classroom
from academic_core.models import AcademicTerm

from .models import CourseGroup, ProposedSchedule, ScheduleSession, TeacherActivity
from .genetic import (
    run_genetic_algorithm,
    GroupInfo, AvailabilitySlot, ClassroomInfo, OccupiedSlot, ActivitySlot,
)

DAYS_ES = {
    "Monday":    "Lunes",
    "Tuesday":   "Martes",
    "Wednesday": "Miércoles",
    "Thursday":  "Jueves",
    "Friday":    "Viernes",
    "Saturday":  "Sábado",
}

DAYS_ORDER = list(DAYS_ES.keys())


def _sessions_display(genes, groups_by_id, classrooms_by_id):
    rows = []
    for gene in genes:
        group    = groups_by_id.get(gene.group_id)
        classroom = classrooms_by_id.get(gene.classroom_id) if gene.classroom_id else None
        if not group:
            continue
        rows.append({
            "course_code": group.course.code,
            "course_name": group.course.name,
            "day":         DAYS_ES.get(gene.day, gene.day),
            "day_order":   DAYS_ORDER.index(gene.day) if gene.day in DAYS_ORDER else 99,
            "start_time":  gene.start_time.strftime("%H:%M"),
            "end_time":    gene.end_time.strftime("%H:%M"),
            "classroom":   classroom.classroom_id if classroom else "Virtual",
        })
    return sorted(rows, key=lambda r: (r["day_order"], r["start_time"]))


def generate_schedule_view(request):
    teachers = Teacher.objects.filter(is_active=True).order_by("last_name", "first_name")
    terms    = AcademicTerm.objects.order_by("-start_date")

    context = {
        "teachers": teachers,
        "terms":    terms,
        "top3":     None,
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
            classroom_id=c.id, code=c.classroom_id,
            capacity=c.capacity, classroom_type=c.classroom_type,
        )
        for c in classrooms_qs
    ]
    classrooms_by_id = {c.id: c for c in classrooms_qs}
    groups_by_id     = {cg.id: cg for cg in course_groups}

    # --- Franjas ocupadas por otros ---
    occupied = [
        OccupiedSlot(
            classroom_id=s.classroom.id,
            day=s.day, start=s.start_time, end=s.end_time,
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
            day=a.day, start=a.start_time, end=a.end_time,
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
            teacher=teacher, term=term,
            fitness_score=round(fitness, 2),
            rank=rank, status="draft",
        )
        for gene in chromosome:
            group     = groups_by_id.get(gene.group_id)
            classroom = classrooms_by_id.get(gene.classroom_id) if gene.classroom_id else None
            if not group:
                continue
            ScheduleSession.objects.create(
                schedule=proposed, group=group, classroom=classroom,
                day=gene.day, start_time=gene.start_time, end_time=gene.end_time,
            )

        top3_display.append({
            "rank":     rank,
            "id":       proposed.id,
            "fitness":  round(fitness, 2),
            "hours":    breakdown.total_teaching_hours,
            "sessions": _sessions_display(chromosome, groups_by_id, classrooms_by_id),
            "breakdown": breakdown.penalty_detail(),
        })

    context["top3"]    = top3_display
    context["teacher"] = str(teacher)
    context["term"]    = str(term)

    messages.success(request, f"Se generaron {len(top3_display)} propuestas de horario.")
    return render(request, "scheduling/generate_schedule.html", context)


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
        ProposedSchedule.objects.select_related("teacher", "term"), id=schedule_id
    )
    sessions = schedule.sessions.select_related(
        "group__course", "classroom"
    ).order_by("day", "start_time")

    sessions_display = [
        {
            "course_code": s.group.course.code,
            "course_name": s.group.course.name,
            "day":         DAYS_ES.get(s.day, s.day),
            "start_time":  s.start_time.strftime("%H:%M"),
            "end_time":    s.end_time.strftime("%H:%M"),
            "classroom":   s.classroom.classroom_id if s.classroom else "Virtual",
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