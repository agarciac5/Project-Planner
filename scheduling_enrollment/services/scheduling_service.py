import math
from datetime import time

from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone

from academic_core.models import AcademicTerm, Course
from classrooms.models import Classroom, TimeSlot
from scheduling_enrollment.algorithms.genetic_scheduler import (
    ClassroomResource,
    DemandCourse,
    TeacherResource,
    TimeSlotResource,
    _build_feasible_candidates,
    run_semester_planner,
)
from scheduling_enrollment.models import (
    CourseGroup,
    Enrollment,
    EnrollmentQueue,
    ProposedSchedule,
    ScheduleSession,
    TeacherActivity,
    SemesterScheduleAssignment,
    SemesterScheduleOption,
    SemesterScheduleRun,
)
from teaching.models import Teacher


# ── Timeslots por defecto ──────────────────────────────────────────────────────
# Deben coincidir exactamente con los definidos en seed_data.py y en la tabla
# classrooms_timeslot.  Se agregaron franjas nocturnas para martes, jueves y
# viernes de modo que los docentes de contrato Cátedra (disponibilidad 18-21 h)
# siempre tengan slots válidos incluso si la BD está vacía.
DEFAULT_TIMESLOTS = [
    # Lunes
    ("Monday",    time(7,  0), time(8,  30)),
    ("Monday",    time(8,  30), time(10, 0)),
    ("Monday",    time(10, 0), time(11, 30)),
    ("Monday",    time(14, 0), time(15, 30)),
    ("Monday",    time(15, 30), time(17, 0)),
    # Martes
    ("Tuesday",   time(7,  0), time(8,  30)),
    ("Tuesday",   time(8,  30), time(10, 0)),
    ("Tuesday",   time(10, 0), time(11, 30)),
    ("Tuesday",   time(14, 0), time(15, 30)),
    ("Tuesday",   time(15, 30), time(17, 0)),
    ("Tuesday",   time(18, 0), time(19, 30)),   # ← nocturno
    ("Tuesday",   time(19, 30), time(21, 0)),   # ← nocturno
    # Miércoles
    ("Wednesday", time(7,  0), time(8,  30)),
    ("Wednesday", time(8,  30), time(10, 0)),
    ("Wednesday", time(10, 0), time(11, 30)),
    ("Wednesday", time(14, 0), time(15, 30)),
    ("Wednesday", time(15, 30), time(17, 0)),
    # Jueves
    ("Thursday",  time(7,  0), time(8,  30)),
    ("Thursday",  time(8,  30), time(10, 0)),
    ("Thursday",  time(10, 0), time(11, 30)),
    ("Thursday",  time(14, 0), time(15, 30)),
    ("Thursday",  time(15, 30), time(17, 0)),
    ("Thursday",  time(18, 0), time(19, 30)),   # ← nocturno
    ("Thursday",  time(19, 30), time(21, 0)),   # ← nocturno
    # Viernes
    ("Friday",    time(7,  0), time(8,  30)),
    ("Friday",    time(8,  30), time(10, 0)),
    ("Friday",    time(10, 0), time(11, 30)),
    ("Friday",    time(14, 0), time(15, 30)),
    ("Friday",    time(18, 0), time(19, 30)),   # ← nocturno
    ("Friday",    time(19, 30), time(21, 0)),   # ← nocturno
    # Sábado
    ("Saturday",  time(8,  0), time(9,  30)),
    ("Saturday",  time(9,  30), time(11, 0)),
]


def _get_term(term_id: int) -> AcademicTerm:
    return AcademicTerm.objects.get(id=term_id)


def _build_demand_courses(term: AcademicTerm, course_ids: set[int] | None = None) -> list[DemandCourse]:
    waiting = (
        EnrollmentQueue.objects.filter(status="waiting")
        .filter(Q(term=term) | Q(term__isnull=True))
        .values("course")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
    if course_ids:
        waiting = waiting.filter(course__in=course_ids)
    courses = {
        course.id: course
        for course in Course.objects.filter(id__in=[item["course"] for item in waiting])
    }

    demand_courses = []
    for item in waiting:
        course = courses.get(item["course"])
        if not course:
            continue
        demand = item["total"]
        min_sections = max(1, math.ceil(demand / 20))
        max_sections = max(min_sections, max(1, demand // 5))
        demand_courses.append(
            DemandCourse(
                course_id=course.id,
                code=course.code,
                name=course.name,
                demand=demand,
                min_sections=min_sections,
                max_sections=max_sections,
            )
        )
    return demand_courses


def _build_timeslots() -> list[TimeSlotResource]:
    qs = list(TimeSlot.objects.order_by("day", "start_time"))
    source = (
        [(slot.day, slot.start_time, slot.end_time) for slot in qs]
        if qs
        else DEFAULT_TIMESLOTS
    )
    return [
        TimeSlotResource(
            index=index + 1,
            day=day,
            start_time=start_time,
            end_time=end_time,
        )
        for index, (day, start_time, end_time) in enumerate(source)
    ]


def _build_teacher_resources(term: AcademicTerm, demanded_course_ids: set[int]) -> list[TeacherResource]:
    teachers = (
        Teacher.objects.filter(is_active=True, qualified_courses__id__in=demanded_course_ids)
        .prefetch_related("qualified_courses", "availabilities")
        .distinct()
    )
    activities_by_teacher: dict[int, list[tuple[str, time, time]]] = {}
    for activity in TeacherActivity.objects.filter(term=term, teacher__in=teachers):
        activities_by_teacher.setdefault(activity.teacher_id, []).append(
            (activity.day, activity.start_time, activity.end_time)
        )

    resources = []
    for teacher in teachers:
        resources.append(
            TeacherResource(
                teacher_id=teacher.id,
                label=f"{teacher.first_name} {teacher.last_name}",
                qualified_course_ids=frozenset(
                    teacher.qualified_courses.values_list("id", flat=True)
                ),
                availability=tuple(
                    (av.day, av.start_time, av.end_time)
                    for av in teacher.availabilities.all()
                ),
                activities=tuple(activities_by_teacher.get(teacher.id, [])),
                max_teaching_hours=float(
                    teacher.contract.max_teaching_hours if teacher.contract else 20
                ),
                min_teaching_hours=float(
                    teacher.contract.min_teaching_hours if teacher.contract else 0
                ),
                campus_id=teacher.campus_id,
            )
        )
    return resources


def _build_classroom_resources() -> list[ClassroomResource]:
    classrooms = Classroom.objects.filter(is_active=True).exclude(classroom_type="VIRTUAL")
    return [
        ClassroomResource(
            classroom_id=classroom.id,
            label=classroom.classroom_id,
            capacity=classroom.capacity,
            classroom_type=classroom.classroom_type,
            campus_id=classroom.campus_id,
        )
        for classroom in classrooms
    ]


def _split_schedulable_demand_courses(
    demand_courses: list[DemandCourse],
    teacher_resources: list[TeacherResource],
    classroom_resources: list[ClassroomResource],
    timeslots: list[TimeSlotResource],
) -> tuple[list[DemandCourse], list[dict], int]:
    feasible_candidates = _build_feasible_candidates(
        {course.course_id: course       for course in demand_courses},
        {teacher.teacher_id: teacher    for teacher in teacher_resources},
        {classroom.classroom_id: classroom for classroom in classroom_resources},
        {slot.index: slot               for slot in timeslots},
    )

    schedulable_courses:   list[DemandCourse] = []
    unschedulable_courses: list[dict]         = []
    unschedulable_demand = 0

    for course in demand_courses:
        if feasible_candidates.get(course.course_id):
            schedulable_courses.append(course)
            continue

        unschedulable_demand += course.demand
        unschedulable_courses.append(
            {
                "course_id": course.course_id,
                "code":      course.code,
                "name":      course.name,
                "demand":    course.demand,
                "reason":    "Sin combinaciones viables de docente, aula y horario.",
            }
        )

    return schedulable_courses, unschedulable_courses, unschedulable_demand


def get_run_assignment_summary(run: SemesterScheduleRun) -> dict:
    from scheduling_enrollment.services.enrollment_service import summarize_pending_requests

    applied_option = (
        run.options.prefetch_related("assignments__course")
        .filter(applied=True)
        .first()
    )
    selected_option = (
        run.options.prefetch_related("assignments__course")
        .filter(selected=True)
        .first()
    )
    reference_option = applied_option or selected_option or run.options.first()
    planned_course_ids = []
    if reference_option:
        planned_course_ids = list(
            reference_option.assignments.values_list("course_id", flat=True).distinct()
        )

    demand_qs  = EnrollmentQueue.objects.filter(term=run.term)
    if planned_course_ids:
        demand_qs = demand_qs.filter(course_id__in=planned_course_ids)

    waiting_qs     = demand_qs.filter(status="waiting")
    grouped_pending = (
        waiting_qs.values("course__code", "course__name")
        .annotate(total=Count("id"))
        .order_by("-total", "course__code")
    )
    pending_by_course = [
        {
            "code":   row["course__code"],
            "name":   row["course__name"],
            "pending": row["total"],
            "reason": "Sin cupo suficiente o conflicto de horario al asignar estudiantes.",
        }
        for row in grouped_pending
    ]
    pending_by_student = summarize_pending_requests(run.term, option=applied_option)

    assignment_qs = Enrollment.objects.filter(term=run.term, status="active")
    if planned_course_ids:
        assignment_qs = assignment_qs.filter(course_group__course_id__in=planned_course_ids)
    if applied_option:
        assignment_qs = assignment_qs.filter(
            course_group__semester_assignments__option=applied_option
        )

    assigned_by_course_rows = (
        assignment_qs.values("course_group__course__code", "course_group__course__name")
        .annotate(total=Count("id"))
        .order_by("course_group__course__code")
    )
    assigned_by_course = [
        {
            "code":     row["course_group__course__code"],
            "name":     row["course_group__course__name"],
            "assigned": row["total"],
        }
        for row in assigned_by_course_rows
    ]

    groups_qs   = CourseGroup.objects.filter(term=run.term)
    sessions_qs = ScheduleSession.objects.filter(schedule__term=run.term)
    if applied_option:
        groups_qs   = groups_qs.filter(semester_assignments__option=applied_option)
        sessions_qs = sessions_qs.filter(group__semester_assignments__option=applied_option)
    elif planned_course_ids:
        groups_qs   = groups_qs.filter(course_id__in=planned_course_ids)
        sessions_qs = sessions_qs.filter(group__course_id__in=planned_course_ids)

    demand_total   = demand_qs.count()
    waiting_total  = waiting_qs.count()
    assigned_total = assignment_qs.count()
    groups_created   = groups_qs.distinct().count()
    sessions_created = sessions_qs.distinct().count()
    ready_to_publish = bool(applied_option) and waiting_total == 0

    blockers = []
    if not applied_option:
        blockers.append("Debes aplicar una opcion antes de emitir horarios.")
    if waiting_total:
        blockers.append(
            f"Quedan {waiting_total} solicitudes pendientes por ubicar antes de publicar."
        )

    stages = [
        {
            "label":       "Solicitudes",
            "description": "Estudiantes eligen materias y se registra la demanda.",
            "done":        demand_total > 0,
            "current":     demand_total > 0 and not run.options.exists(),
        },
        {
            "label":       "Opciones",
            "description": "El algoritmo genetico genera escenarios de apertura.",
            "done":        run.options.exists(),
            "current":     run.options.exists() and not reference_option,
        },
        {
            "label":       "Seleccion",
            "description": "Se fija una opcion para convertirla en grupos reales.",
            "done":        bool(reference_option and reference_option.selected),
            "current":     run.options.exists() and not bool(reference_option and reference_option.selected),
        },
        {
            "label":       "Asignacion",
            "description": "Los estudiantes se distribuyen en grupos sin sobrecargar cupos.",
            "done":        bool(applied_option) and waiting_total == 0,
            "current":     bool(applied_option) and waiting_total > 0,
        },
        {
            "label":       "Emision",
            "description": "Se publican los horarios finales para estudiantes y docentes.",
            "done":        run.status == "published",
            "current":     run.status == "ready_to_publish",
        },
    ]

    return {
        "demand_total":      demand_total,
        "assigned_total":    assigned_total,
        "waiting_total":     waiting_total,
        "groups_created":    groups_created,
        "sessions_created":  sessions_created,
        "ready_to_publish":  ready_to_publish,
        "pending_by_course": pending_by_course,
        "pending_by_student":pending_by_student,
        "assigned_by_course":assigned_by_course,
        "blockers":          blockers,
        "stages":            stages,
    }


@transaction.atomic
def generate_semester_schedule_options(
    term_id: int,
    auto_apply_best: bool = False,
    course_ids: set[int] | None = None,
) -> SemesterScheduleRun | None:
    term = _get_term(term_id)
    demand_courses = _build_demand_courses(term, course_ids=course_ids)
    if not demand_courses:
        return None
    total_demand = sum(course.demand for course in demand_courses)

    teacher_resources   = _build_teacher_resources(
        term, demanded_course_ids={course.course_id for course in demand_courses},
    )
    classroom_resources = _build_classroom_resources()
    timeslots           = _build_timeslots()

    schedulable_courses, unschedulable_courses, unschedulable_demand = (
        _split_schedulable_demand_courses(
            demand_courses, teacher_resources, classroom_resources, timeslots,
        )
    )
    if not schedulable_courses:
        return None

    results = run_semester_planner(
        demand_courses=schedulable_courses,
        teachers=teacher_resources,
        classrooms=classroom_resources,
        timeslots=timeslots,
    )
    if not results:
        return None

    teacher_map   = {teacher.id: teacher     for teacher in Teacher.objects.filter(id__in=[t.teacher_id for t in teacher_resources])}
    classroom_map = {classroom.id: classroom for classroom in Classroom.objects.filter(id__in=[c.classroom_id for c in classroom_resources])}
    course_map    = {course.id: course       for course in Course.objects.filter(id__in=[c.course_id for c in schedulable_courses])}
    timeslot_map  = {slot.index: slot        for slot in timeslots}

    run = SemesterScheduleRun.objects.create(term=term)
    for rank, result in enumerate(results, start=1):
        result.summary["unschedulable_courses"]       = unschedulable_courses
        result.summary["unschedulable_course_count"]  = len(unschedulable_courses)
        result.summary["unschedulable_demand"]        = unschedulable_demand
        result.summary["schedulable_demand_total"]    = result.summary["demand_total"]
        result.summary["demand_total"]                = total_demand
        result.summary["uncovered_students"]         += unschedulable_demand
        option = SemesterScheduleOption.objects.create(
            run=run,
            rank=rank,
            score=result.score,
            demand_covered=result.summary["demand_covered"],
            demand_total=total_demand,
            sections_opened=result.summary["sections_opened"],
            is_best=rank == 1,
            selected=False,
            summary=result.summary,
        )
        for assignment in result.assignments:
            slot = timeslot_map[assignment.timeslot_index]
            SemesterScheduleAssignment.objects.create(
                option=option,
                course=course_map[assignment.course_id],
                teacher=teacher_map.get(assignment.teacher_id),
                classroom=classroom_map.get(assignment.classroom_id),
                section_number=assignment.section_number,
                day=slot.day,
                start_time=slot.start_time,
                end_time=slot.end_time,
                students_assigned=assignment.students_assigned,
                capacity=assignment.capacity,
            )

    if auto_apply_best:
        apply_semester_schedule_run(run)
    return run


@transaction.atomic
def apply_semester_schedule_run(
    run: SemesterScheduleRun,
    option: SemesterScheduleOption | None = None,
) -> SemesterScheduleOption:
    from scheduling_enrollment.services.enrollment_service import assign_waiting_students_to_groups

    best_option = option or run.options.prefetch_related(
        "assignments__course", "assignments__teacher", "assignments__classroom"
    ).filter(is_best=True).first()
    if not best_option:
        raise ValueError("No existe una opcion marcada como mejor para este plan.")
    if best_option.applied:
        return best_option

    term = run.term
    schedules_by_teacher: dict[int, ProposedSchedule] = {}

    for assignment in best_option.assignments.all():
        if not assignment.teacher:
            continue
        schedule = schedules_by_teacher.get(assignment.teacher_id)
        if schedule is None:
            schedule = ProposedSchedule.objects.create(
                teacher=assignment.teacher,
                term=term,
                status="approved",
                fitness_score=best_option.score,
                rank=1,
            )
            schedules_by_teacher[assignment.teacher_id] = schedule

        nrc = f"{term.id}{assignment.course_id}{assignment.section_number}".zfill(10)[:10]
        group = CourseGroup.objects.create(
            course=assignment.course,
            teacher=assignment.teacher,
            term=term,
            nrc=nrc,
            capacity=assignment.capacity,
            is_virtual=False,
        )
        ScheduleSession.objects.create(
            schedule=schedule,
            group=group,
            classroom=assignment.classroom,
            day=assignment.day,
            start_time=assignment.start_time,
            end_time=assignment.end_time,
        )
        assignment.generated_group    = group
        assignment.generated_schedule = schedule
        assignment.nrc                = nrc
        assignment.save(update_fields=["generated_group", "generated_schedule", "nrc"])

    run.options.exclude(id=best_option.id).update(selected=False)
    best_option.selected = True
    best_option.applied  = True
    best_option.save(update_fields=["selected", "applied"])

    assign_waiting_students_to_groups(term, option=best_option)

    pending_requests = EnrollmentQueue.objects.filter(
        term=term,
        status="waiting",
        course_id__in=best_option.assignments.values_list("course_id", flat=True).distinct(),
    ).exists()
    run.status = "saved" if pending_requests else "ready_to_publish"
    run.save(update_fields=["status"])
    return best_option


@transaction.atomic
def revert_semester_schedule_option(option: SemesterScheduleOption) -> SemesterScheduleOption:
    assignments  = list(option.assignments.select_related("generated_group", "generated_schedule"))
    group_ids    = [a.generated_group_id    for a in assignments if a.generated_group_id]
    schedule_ids = [a.generated_schedule_id for a in assignments if a.generated_schedule_id]

    if group_ids:
        Enrollment.objects.filter(course_group_id__in=group_ids).delete()
        EnrollmentQueue.objects.filter(course_group_id__in=group_ids).update(
            status="waiting", course_group=None,
        )
        CourseGroup.objects.filter(id__in=group_ids).delete()

    if schedule_ids:
        ProposedSchedule.objects.filter(id__in=schedule_ids).delete()

    option.assignments.update(generated_group=None, generated_schedule=None, nrc="")
    option.applied = False
    option.save(update_fields=["applied"])

    run = option.run
    if not run.options.filter(applied=True).exists():
        run.status     = "saved" if run.options.filter(selected=True).exists() else "draft"
        run.published_at = None
        run.save(update_fields=["status", "published_at"])

    return option


@transaction.atomic
def publish_semester_schedule_run(run: SemesterScheduleRun) -> SemesterScheduleRun:
    if not run.options.filter(applied=True).exists():
        raise ValueError("No existe una opcion aplicada para publicar.")
    if run.status != "ready_to_publish":
        raise ValueError(
            "Este plan aun no esta listo para emitirse porque quedan "
            "estudiantes pendientes o ajustes por resolver."
        )
    run.status       = "published"
    run.published_at = timezone.now()
    run.save(update_fields=["status", "published_at"])
    return run
