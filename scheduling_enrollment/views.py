from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import models
from django.contrib.auth.decorators import login_required
from access_support.role_access import (
    DIRECTOR_ROLES,
    SCHEDULE_MANAGEMENT_ROLES,
    SCHEDULE_READ_ROLES,
    roles_required,
    user_has_any_role,
)

from access_support.models import StudentProfile
from teaching.models import Teacher
from classrooms.models import Classroom
from academic_core.models import AcademicTerm, Course

from .models import (
    CourseGroup,
    Enrollment,
    EnrollmentQueue,
    ProposedSchedule,
    ScheduleSession,
    SemesterScheduleOption,
    SemesterScheduleRun,
    TeacherActivity,
)
from .services.scheduling_service import (
    apply_semester_schedule_run,
    generate_semester_schedule_options,
    get_run_assignment_summary,
    publish_semester_schedule_run,
    revert_semester_schedule_option,
)
from .services.enrollment_service import (
    assign_waiting_students_to_groups,
    get_active_term,
    get_student_available_courses,
    request_student_enrollment,
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
STUDENT_CALENDAR_START = 6 * 60
STUDENT_CALENDAR_END = 22 * 60
STUDENT_CALENDAR_SLOT = 30

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
    run.has_applied_option = run.options.filter(applied=True).exists()
    run.assignment_summary = get_run_assignment_summary(run)

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


def _term_options(selected_term_id=None):
    terms = AcademicTerm.objects.order_by("-start_date")
    selected_term = None

    if selected_term_id:
        selected_term = terms.filter(id=selected_term_id).first()

    if selected_term is None:
        selected_term = terms.first()

    return terms, selected_term


def _teacher_schedule_rows(teacher, term):
    schedule_qs = (
        ProposedSchedule.objects.filter(teacher=teacher, term=term)
        .order_by(
            models.Case(
                models.When(status="approved", then=0),
                models.When(status="draft", then=1),
                models.When(status="rejected", then=2),
                default=3,
                output_field=models.IntegerField(),
            ),
            "rank",
            "-created_at",
        )
    )
    schedules = list(schedule_qs)
    selected_schedule = schedules[0] if schedules else None

    class_rows = []
    if selected_schedule:
        sessions = (
            selected_schedule.sessions.select_related("group__course", "classroom")
            .prefetch_related("group__enrollments")
            .order_by("day", "start_time")
        )
        for session in sessions:
            class_rows.append(
                {
                    "kind": "Clase",
                    "kind_class": "kind-class",
                    "course_code": session.group.course.code,
                    "course_name": session.group.course.name,
                    "section": session.group.nrc or f"Grupo {session.group.id}",
                    "day_key": session.day,
                    "day": DAYS_ES.get(session.day, session.day),
                    "day_order": DAYS_ORDER.index(session.day) if session.day in DAYS_ORDER else 99,
                    "start_time": session.start_time.strftime("%H:%M"),
                    "end_time": session.end_time.strftime("%H:%M"),
                    "location": session.classroom.classroom_id if session.classroom else "Virtual",
                    "status": selected_schedule.get_status_display(),
                    "notes": "Sesion academica asignada.",
                    "student_count": sum(
                        enrollment.status == "active"
                        for enrollment in session.group.enrollments.all()
                    ),
                }
            )

    activity_rows = []
    for activity in (
        TeacherActivity.objects.filter(teacher=teacher, term=term)
        .order_by("day", "start_time")
    ):
        activity_rows.append(
            {
                "kind": "Actividad",
                "kind_class": "kind-activity",
                "course_code": "",
                "course_name": activity.get_activity_type_display(),
                "section": "-",
                "day_key": activity.day,
                "day": DAYS_ES.get(activity.day, activity.day),
                "day_order": DAYS_ORDER.index(activity.day) if activity.day in DAYS_ORDER else 99,
                "start_time": activity.start_time.strftime("%H:%M"),
                "end_time": activity.end_time.strftime("%H:%M"),
                "location": "Sin aula",
                "status": "Registrada",
                "notes": f"Carga adicional de {activity.duration_hours}h.",
                "student_count": "-",
            }
        )

    rows = sorted(
        class_rows + activity_rows,
        key=lambda row: (row["day_order"], row["start_time"], row["kind"] != "Clase"),
    )

    return {
        "selected_schedule": selected_schedule,
        "rows": rows,
        "class_count": len(class_rows),
        "activity_count": len(activity_rows),
        **_teacher_calendar_context(rows),
    }


def _teacher_calendar_context(rows):
    calendar_days = [
        {
            "key": day,
            "label": DAYS_ES[day],
            "column": index + 2,
        }
        for index, day in enumerate(DAYS_ORDER)
    ]
    calendar_times = [
        {
            "label": _clock_label(minutes),
            "grid_row": index + 2,
        }
        for index, minutes in enumerate(
            range(
                STUDENT_CALENDAR_START,
                STUDENT_CALENDAR_END,
                STUDENT_CALENDAR_SLOT,
            )
        )
    ]

    calendar_events = []
    for row in rows:
        day_key = row.get("day_key")
        if day_key not in DAYS_ORDER:
            continue
        try:
            start_hour, start_minute = map(int, row["start_time"].split(":"))
            end_hour, end_minute = map(int, row["end_time"].split(":"))
        except (AttributeError, TypeError, ValueError):
            continue

        start = max(
            STUDENT_CALENDAR_START,
            start_hour * 60 + start_minute,
        )
        end = min(
            STUDENT_CALENDAR_END,
            end_hour * 60 + end_minute,
        )
        if end <= start:
            continue

        event = dict(row)
        event["day_column"] = DAYS_ORDER.index(day_key) + 2
        event["grid_row"] = (
            (start - STUDENT_CALENDAR_START) // STUDENT_CALENDAR_SLOT
        ) + 2
        event["grid_span"] = max(
            1,
            (end - start + STUDENT_CALENDAR_SLOT - 1)
            // STUDENT_CALENDAR_SLOT,
        )
        event["color_index"] = (
            0
            if row["kind"] == "Actividad"
            else (sum(ord(character) for character in row["course_code"]) % 5)
            + 1
        )
        calendar_events.append(event)

    return {
        "calendar_days": calendar_days,
        "calendar_times": calendar_times,
        "calendar_events": calendar_events,
    }


def _published_teacher_schedule_context(teacher, term, groups):
    class_rows = []
    for group in groups:
        student_count = sum(
            enrollment.status == "active"
            for enrollment in group.enrollments.all()
        )
        for session in group.sessions.all():
            class_rows.append(
                {
                    "kind": "Clase",
                    "kind_class": "kind-class",
                    "course_code": group.course.code,
                    "course_name": group.course.name,
                    "section": group.nrc or f"Grupo {group.id}",
                    "day_key": session.day,
                    "day": DAYS_ES.get(session.day, session.day),
                    "day_order": (
                        DAYS_ORDER.index(session.day)
                        if session.day in DAYS_ORDER
                        else 99
                    ),
                    "start_time": session.start_time.strftime("%H:%M"),
                    "end_time": session.end_time.strftime("%H:%M"),
                    "location": (
                        session.classroom.classroom_id
                        if session.classroom
                        else "Virtual"
                    ),
                    "status": "Publicado",
                    "notes": "Horario oficial publicado.",
                    "student_count": student_count,
                }
            )

    activity_rows = [
        {
            "kind": "Actividad",
            "kind_class": "kind-activity",
            "course_code": "",
            "course_name": activity.get_activity_type_display(),
            "section": "-",
            "day_key": activity.day,
            "day": DAYS_ES.get(activity.day, activity.day),
            "day_order": (
                DAYS_ORDER.index(activity.day)
                if activity.day in DAYS_ORDER
                else 99
            ),
            "start_time": activity.start_time.strftime("%H:%M"),
            "end_time": activity.end_time.strftime("%H:%M"),
            "location": "Sin aula",
            "status": "Registrada",
            "notes": f"Carga adicional de {activity.duration_hours}h.",
            "student_count": "-",
        }
        for activity in TeacherActivity.objects.filter(
            teacher=teacher,
            term=term,
        ).order_by("day", "start_time")
    ]
    rows = sorted(
        class_rows + activity_rows,
        key=lambda row: (
            row["day_order"],
            row["start_time"],
            row["kind"] != "Clase",
        ),
    )
    return {
        "rows": rows,
        "class_count": len(class_rows),
        "activity_count": len(activity_rows),
        **_teacher_calendar_context(rows),
    }


def _student_schedule_rows(student_profile, term):
    enrollments = list(
        EnrollmentQueue.objects.filter(
            student=student_profile.user,
            term=term,
            status="enrolled",
        )
        .select_related("course", "course_group__teacher")
        .order_by("course__code")
    )

    rows = []
    for enrollment in enrollments:
        selected_group = enrollment.course_group

        if not selected_group:
            rows.append(
                {
                    "course_code": enrollment.course.code,
                    "course_name": enrollment.course.name,
                    "section": "Sin grupo asignado",
                    "teacher": "Pendiente",
                    "day_key": None,
                    "day": "-",
                    "day_order": 99,
                    "start_time": "-",
                    "end_time": "-",
                    "location": "-",
                    "status": "Inscrito",
                    "notes": "El curso esta inscrito, pero aun no tiene grupo asignado para el periodo.",
                }
            )
            continue

        sessions = list(
            selected_group.sessions.select_related("classroom", "schedule").all()
        )

        if not sessions:
            rows.append(
                {
                    "course_code": enrollment.course.code,
                    "course_name": enrollment.course.name,
                    "section": selected_group.nrc or f"Grupo {selected_group.id}",
                    "teacher": str(selected_group.teacher) if selected_group.teacher else "Pendiente",
                    "day_key": None,
                    "day": "-",
                    "day_order": 99,
                    "start_time": "-",
                    "end_time": "-",
                    "location": "-",
                    "status": "Inscrito",
                    "notes": "El grupo existe, pero todavia no tiene sesiones programadas.",
                }
            )
            continue

        for session in sessions:
            rows.append(
                {
                    "course_code": enrollment.course.code,
                    "course_name": enrollment.course.name,
                    "section": selected_group.nrc or f"Grupo {selected_group.id}",
                    "teacher": str(selected_group.teacher) if selected_group.teacher else "Pendiente",
                    "day_key": session.day,
                    "day": DAYS_ES.get(session.day, session.day),
                    "day_order": DAYS_ORDER.index(session.day) if session.day in DAYS_ORDER else 99,
                    "start_time": session.start_time.strftime("%H:%M"),
                    "end_time": session.end_time.strftime("%H:%M"),
                    "location": session.classroom.classroom_id if session.classroom else "Virtual",
                    "status": "Inscrito",
                    "notes": "Sesion asociada a la matricula del estudiante.",
                }
            )

    rows = sorted(
        rows,
        key=lambda row: (row["day_order"], row["start_time"], row["course_code"]),
    )
    return {
        "rows": rows,
        "course_count": len(enrollments),
        "session_count": len([row for row in rows if row["day"] != "-"]),
        **_student_calendar_context(rows),
    }


def _clock_label(total_minutes):
    hour, minute = divmod(total_minutes, 60)
    suffix = "am" if hour < 12 else "pm"
    display_hour = hour % 12 or 12
    return f"{display_hour}:{minute:02d} {suffix}"


def _student_calendar_context(rows):
    calendar_days = [
        {
            "key": day,
            "label": DAYS_ES[day],
            "column": index + 2,
        }
        for index, day in enumerate(DAYS_ORDER)
    ]
    calendar_times = [
        {
            "label": _clock_label(minutes),
            "grid_row": index + 2,
        }
        for index, minutes in enumerate(
            range(
                STUDENT_CALENDAR_START,
                STUDENT_CALENDAR_END,
                STUDENT_CALENDAR_SLOT,
            )
        )
    ]

    calendar_events = []
    for row in rows:
        day_key = row.get("day_key")
        if day_key not in DAYS_ORDER:
            continue
        try:
            start_hour, start_minute = map(int, row["start_time"].split(":"))
            end_hour, end_minute = map(int, row["end_time"].split(":"))
        except (AttributeError, TypeError, ValueError):
            continue

        start = max(
            STUDENT_CALENDAR_START,
            start_hour * 60 + start_minute,
        )
        end = min(
            STUDENT_CALENDAR_END,
            end_hour * 60 + end_minute,
        )
        if end <= start:
            continue

        event = dict(row)
        event["day_column"] = DAYS_ORDER.index(day_key) + 2
        event["grid_row"] = (
            (start - STUDENT_CALENDAR_START) // STUDENT_CALENDAR_SLOT
        ) + 2
        event["grid_span"] = max(
            1,
            (end - start + STUDENT_CALENDAR_SLOT - 1)
            // STUDENT_CALENDAR_SLOT,
        )
        event["color_index"] = (
            sum(ord(character) for character in row["course_code"]) % 5
        ) + 1
        calendar_events.append(event)

    return {
        "calendar_days": calendar_days,
        "calendar_times": calendar_times,
        "calendar_events": calendar_events,
        "calendar_slot_count": len(calendar_times),
    }


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


@roles_required(*SCHEDULE_MANAGEMENT_ROLES)
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


@roles_required(*SCHEDULE_READ_ROLES)
def teacher_complete_schedule_view(request):
    teachers = Teacher.objects.filter(is_active=True).order_by("last_name", "first_name")
    selected_teacher_id = request.GET.get("teacher_id")
    selected_term_id = request.GET.get("term_id")

    selected_teacher = None
    if selected_teacher_id:
        selected_teacher = teachers.filter(id=selected_teacher_id).first()
    if selected_teacher is None:
        selected_teacher = teachers.first()

    terms, selected_term = _term_options(selected_term_id)

    schedule_context = {
        "selected_schedule": None,
        "rows": [],
        "class_count": 0,
        "activity_count": 0,
    }

    if selected_teacher and selected_term:
        schedule_context = _teacher_schedule_rows(selected_teacher, selected_term)

    return render(
        request,
        "scheduling/teacher_complete_schedule.html",
        {
            "teachers": teachers,
            "terms": terms,
            "selected_teacher": selected_teacher,
            "selected_term": selected_term,
            **schedule_context,
        },
    )


@roles_required(*SCHEDULE_READ_ROLES)
def student_complete_schedule_view(request):
    students = (
        StudentProfile.objects.select_related("user")
        .order_by("full_name", "student_code")
    )
    selected_student_id = request.GET.get("student_id")
    selected_term_id = request.GET.get("term_id")

    selected_student = None
    if selected_student_id:
        selected_student = students.filter(id=selected_student_id).first()
    if selected_student is None:
        selected_student = students.first()

    terms, selected_term = _term_options(selected_term_id)

    schedule_context = {
        "rows": [],
        "course_count": 0,
        "session_count": 0,
    }
    if selected_student and selected_term:
        schedule_context = _student_schedule_rows(selected_student, selected_term)

    return render(
        request,
        "scheduling/student_complete_schedule.html",
        {
            "students": students,
            "terms": terms,
            "selected_student": selected_student,
            "selected_term": selected_term,
            **schedule_context,
        },
    )


@login_required
def enrollment_view(request):
    if request.user.role != "student":
        messages.warning(request, "Este apartado de matricula esta disponible solo para estudiantes.")
        return redirect("home")

    student_profile = (
        StudentProfile.objects.select_related("program", "user")
        .filter(user=request.user)
        .first()
    )
    if not student_profile:
        messages.warning(request, "Tu usuario no tiene perfil estudiantil configurado. Debes crear o importar el StudentProfile antes de usar matricula.")
        return redirect("home")
    active_term = get_active_term()
    if not active_term:
        messages.warning(request, "No existe un periodo academico activo para realizar matriculas.")
        return redirect("home")

    if request.method == "POST":
        course = get_object_or_404(
            get_student_available_courses(student_profile),
            id=request.POST.get("course_id"),
        )
        enrollment, outcome = request_student_enrollment(request.user, course, active_term)
        if outcome == "existing":
            if enrollment.status == "enrolled":
                messages.info(request, "Ya tienes esta materia matriculada en el periodo activo.")
            else:
                messages.info(request, "Ya tienes esta materia en lista de espera.")
        else:
            messages.success(
                request,
                "La solicitud fue registrada. Esta materia se tendra en cuenta cuando se procese el plan semestral del periodo.",
            )
        return redirect("enrollment")

    available_courses = list(get_student_available_courses(student_profile))
    existing_enrollments = {
        enrollment.course_id: enrollment
        for enrollment in EnrollmentQueue.objects.filter(
            student=request.user,
            term=active_term,
        ).select_related("course_group")
    }

    course_rows = []
    for course in available_courses:
        enrollment = existing_enrollments.get(course.id)
        waiting_count = EnrollmentQueue.objects.filter(
            course=course,
            term=active_term,
            status="waiting",
        ).count()
        available_groups = []
        for group in CourseGroup.objects.filter(course=course, term=active_term).annotate(
            enrolled_count=models.Count(
                "student_enrollments",
                filter=models.Q(student_enrollments__status="enrolled"),
            )
        ):
            available_groups.append(group.capacity - group.enrolled_count)

        course_rows.append(
            {
                "id": course.id,
                "code": course.code,
                "name": course.name,
                "semester": course.semester,
                "status": enrollment.get_status_display() if enrollment else "Disponible",
                "group_label": enrollment.course_group.nrc if enrollment and enrollment.course_group else "-",
                "waiting_count": waiting_count,
                "has_capacity": any(space > 0 for space in available_groups),
                "can_request": enrollment is None,
            }
        )

    return render(
        request,
        "scheduling/enrollment.html",
        {
            "student_profile": student_profile,
            "active_term": active_term,
            "course_rows": course_rows,
        },
    )


@login_required
def my_student_schedule_view(request):
    if request.user.role != "student":
        messages.warning(request, "Este apartado de horario esta disponible solo para estudiantes.")
        return redirect("home")

    student_profile = (
        StudentProfile.objects.select_related("user")
        .filter(user=request.user)
        .first()
    )
    if not student_profile:
        messages.warning(request, "Tu usuario no tiene perfil estudiantil configurado. Debes crear o importar el StudentProfile antes de consultar tu horario.")
        return redirect("home")
    active_term = get_active_term()
    enrollments = []
    schedule_rows = []
    if active_term:
        enrollments = (
            Enrollment.objects.filter(
                student=request.user,
                term=active_term,
                status="active",
                course_group__semester_assignments__option__run__status="published",
            )
            .select_related("course_group__course", "course_group__teacher")
            .prefetch_related("course_group__sessions__classroom")
            .distinct()
            .order_by("course_group__course__code")
        )
        for enrollment in enrollments:
            group = enrollment.course_group
            for session in group.sessions.all():
                schedule_rows.append(
                    {
                        "course_code": group.course.code,
                        "course_name": group.course.name,
                        "section": group.nrc or f"Grupo {group.id}",
                        "teacher": (
                            str(group.teacher)
                            if group.teacher
                            else "Pendiente"
                        ),
                        "day_key": session.day,
                        "day": DAYS_ES.get(session.day, session.day),
                        "day_order": (
                            DAYS_ORDER.index(session.day)
                            if session.day in DAYS_ORDER
                            else 99
                        ),
                        "start_time": session.start_time.strftime("%H:%M"),
                        "end_time": session.end_time.strftime("%H:%M"),
                        "location": (
                            session.classroom.classroom_id
                            if session.classroom
                            else "Virtual"
                        ),
                        "status": "Publicado",
                        "notes": "Horario oficial publicado.",
                    }
                )
        schedule_rows.sort(
            key=lambda row: (
                row["day_order"],
                row["start_time"],
                row["course_code"],
            )
        )

    return render(
        request,
        "scheduling/my_student_schedule.html",
        {
            "student_profile": student_profile,
            "active_term": active_term,
            "enrollments": enrollments,
            "rows": schedule_rows,
            "course_count": len(enrollments),
            "session_count": len(schedule_rows),
            **_student_calendar_context(schedule_rows),
        },
    )


@login_required
def my_teacher_schedule_view(request):
    if request.user.role != "teacher":
        messages.warning(request, "Este apartado de horario esta disponible solo para docentes.")
        return redirect("home")

    teacher = getattr(request.user, "teacher_profile", None)
    if not teacher:
        messages.warning(request, "Tu usuario no esta vinculado a un perfil docente.")
        return redirect("home")

    active_term = get_active_term()
    groups = []
    schedule_context = {
        "rows": [],
        "class_count": 0,
        "activity_count": 0,
        **_teacher_calendar_context([]),
    }
    if active_term:
        groups = list(
            CourseGroup.objects.filter(
                teacher=teacher,
                term=active_term,
                semester_assignments__option__run__status="published",
            )
            .select_related("course")
            .prefetch_related("sessions__classroom", "enrollments__student")
            .distinct()
            .order_by("course__code")
        )
        schedule_context = _published_teacher_schedule_context(
            teacher,
            active_term,
            groups,
        )

    return render(
        request,
        "scheduling/my_teacher_schedule.html",
        {
            "teacher": teacher,
            "active_term": active_term,
            "groups": groups,
            **schedule_context,
        },
    )


# ---------------------------------------------------------------------------
# NUEVO ALGORITMO (STUDENTS) - SIN ROMPER EL VIEJO
# ---------------------------------------------------------------------------
@roles_required(*SCHEDULE_MANAGEMENT_ROLES)
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
@roles_required(*SCHEDULE_READ_ROLES)
def schedule_list_view(request):
    schedules = ProposedSchedule.objects.select_related(
        "teacher", "term"
    ).order_by("-created_at")

    return render(request, "scheduling/schedule_list.html", {"schedules": schedules})


@roles_required(*SCHEDULE_READ_ROLES)
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
        if not user_has_any_role(request.user, SCHEDULE_MANAGEMENT_ROLES):
            messages.warning(request, "No tienes permisos para aprobar o rechazar horarios.")
            return redirect("schedule_detail", schedule_id=schedule.id)
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


@roles_required(*SCHEDULE_MANAGEMENT_ROLES)
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

    selected_term = get_object_or_404(AcademicTerm, id=term_id)
    waiting_count = EnrollmentQueue.objects.filter(
        term=selected_term,
        status="waiting",
    ).count()
    if waiting_count == 0:
        messages.warning(
            request,
            f"No hay solicitudes pendientes para el periodo {selected_term}. "
            "El plan semestral solo se genera con matriculas en lista de espera.",
        )
        return render(request, "scheduling/semester_planner.html", context)

    try:
        run = generate_semester_schedule_options(
            term_id=int(term_id),
            auto_apply_best=False,
        )
    except ValueError as exc:
        messages.warning(request, str(exc))
        return render(request, "scheduling/semester_planner.html", context)
    if not run:
        messages.warning(
            request,
            "No se pudo generar el plan. Revisa que exista demanda suficiente, docentes calificados y aulas disponibles.",
        )
        return render(request, "scheduling/semester_planner.html", context)

    run, options = _build_semester_run_context(run)
    messages.success(request, "Se genero el top 3 de opciones para el semestre. Ahora puedes elegir manualmente una.")
    unschedulable_courses = options[0]["summary"].get("unschedulable_courses", []) if options else []
    if unschedulable_courses:
        course_labels = ", ".join(course["code"] for course in unschedulable_courses[:5])
        if len(unschedulable_courses) > 5:
            course_labels = f"{course_labels} y {len(unschedulable_courses) - 5} mas"
        messages.warning(
            request,
            f"Se genero un plan parcial. Quedaron cursos sin programar: {course_labels}.",
        )

    context["run"] = run
    context["options"] = options
    return render(request, "scheduling/semester_planner.html", context)


@roles_required(*SCHEDULE_MANAGEMENT_ROLES)
def save_semester_run_view(request, run_id):
    run = get_object_or_404(SemesterScheduleRun, id=run_id)
    if request.method == "POST" and run.status == "draft":
        run.status = "saved"
        run.save(update_fields=["status"])
        messages.success(request, "El plan semestral fue guardado correctamente.")
    return redirect("saved_semester_run_detail", run_id=run.id)


@roles_required(*SCHEDULE_MANAGEMENT_ROLES)
def select_semester_option_view(request, option_id):
    option = get_object_or_404(
        SemesterScheduleOption.objects.select_related("run"),
        id=option_id,
    )
    if request.method == "POST":
        option.run.options.exclude(id=option.id).update(selected=False)
        option.selected = True
        option.save(update_fields=["selected"])
        if option.run.status in ["draft", "saved"]:
            option.run.status = "saved"
            option.run.save(update_fields=["status"])
        messages.success(request, "La opcion fue fijada como seleccionada.")
    return redirect("saved_semester_run_detail", run_id=option.run.id)


@roles_required(*SCHEDULE_MANAGEMENT_ROLES)
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


@roles_required(*SCHEDULE_MANAGEMENT_ROLES)
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
        try:
            apply_semester_schedule_run(option.run, option=option)
        except ValueError as exc:
            messages.warning(request, str(exc))
            return redirect("saved_semester_run_detail", run_id=option.run.id)
        option.run.refresh_from_db()
        if option.run.status == "ready_to_publish":
            messages.success(request, "La opcion seleccionada fue aplicada. Los horarios estan listos para ser emitidos.")
        else:
            messages.warning(request, "La opcion fue aplicada, pero aun quedan estudiantes pendientes por ubicar antes de emitir los horarios.")
    return redirect("saved_semester_run_detail", run_id=option.run.id)


@roles_required(*DIRECTOR_ROLES)
def revert_semester_option_view(request, option_id):
    option = get_object_or_404(
        SemesterScheduleOption.objects.select_related("run"),
        id=option_id,
    )
    if request.method == "POST":
        try:
            revert_semester_schedule_option(option)
            messages.success(request, "La aplicacion de la opcion fue revertida y los grupos creados fueron eliminados.")
        except ValueError as exc:
            messages.warning(request, str(exc))
    return redirect("saved_semester_run_detail", run_id=option.run.id)


@roles_required(*DIRECTOR_ROLES)
def publish_semester_run_view(request, run_id):
    run = get_object_or_404(SemesterScheduleRun, id=run_id)
    if request.method == "POST":
        try:
            publish_semester_schedule_run(run)
            messages.success(request, "Los horarios fueron publicados para docentes y estudiantes.")
        except ValueError as exc:
            messages.warning(request, str(exc))
    return redirect("saved_semester_run_detail", run_id=run.id)


@roles_required(*DIRECTOR_ROLES)
def delete_semester_run_view(request, run_id):
    run = get_object_or_404(SemesterScheduleRun, id=run_id)
    if request.method == "POST":
        if run.status == "published":
            messages.warning(
                request,
                "Un plan publicado no se puede eliminar. Debe conservarse como evidencia.",
            )
            return redirect("saved_semester_run_detail", run_id=run.id)
        applied_option = run.options.filter(applied=True).first()
        if applied_option:
            revert_semester_schedule_option(applied_option)
        run.delete()
        messages.success(request, "El plan semestral fue eliminado.")
    return redirect("saved_semester_runs")


@roles_required(*SCHEDULE_READ_ROLES)
def saved_semester_runs_view(request):
    runs = list(
        SemesterScheduleRun.objects.filter(status__in=["saved", "ready_to_publish", "published"])
        .prefetch_related("options")
        .select_related("term")
        .order_by("-created_at")
    )
    for run in runs:
        run.assignment_summary = get_run_assignment_summary(run)
    return render(
        request,
        "scheduling/saved_semester_runs.html",
        {"runs": runs},
    )


@roles_required(*SCHEDULE_READ_ROLES)
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
