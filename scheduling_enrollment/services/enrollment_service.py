from django.db import transaction

from academic_core.models import AcademicTerm, Course
from scheduling_enrollment.models import (
    CourseGroup,
    Enrollment,
    EnrollmentQueue,
    SemesterScheduleOption,
)


def _overlaps(start_a, end_a, start_b, end_b):
    return start_a < end_b and start_b < end_a


def _student_has_schedule_conflict(student, term, group):
    candidate_sessions = list(group.sessions.all())
    if not candidate_sessions:
        return False

    existing_enrollments = (
        Enrollment.objects.filter(student=student, term=term, status="active")
        .select_related("course_group")
        .prefetch_related("course_group__sessions")
    )

    for enrollment in existing_enrollments:
        for existing_session in enrollment.course_group.sessions.all():
            for candidate_session in candidate_sessions:
                if existing_session.day != candidate_session.day:
                    continue
                if _overlaps(
                    existing_session.start_time,
                    existing_session.end_time,
                    candidate_session.start_time,
                    candidate_session.end_time,
                ):
                    return True
    return False


def _candidate_groups_for_request(request, term, groups_by_course):
    candidate_groups = groups_by_course.get(request.course_id, [])
    if not candidate_groups:
        return [], "No se abrieron grupos para esta materia."

    load_pairs = []
    full_groups = 0
    conflict_groups = 0
    for group in candidate_groups:
        current_load = Enrollment.objects.filter(course_group=group, status="active").count()
        if current_load >= group.capacity:
            full_groups += 1
            continue
        if _student_has_schedule_conflict(request.student, term, group):
            conflict_groups += 1
            continue
        load_pairs.append((current_load, group.id, group))

    if load_pairs:
        return load_pairs, ""
    if full_groups == len(candidate_groups):
        return [], "Todos los grupos disponibles alcanzaron su capacidad maxima."
    if conflict_groups:
        return [], "Los grupos disponibles chocan con el horario ya asignado del estudiante."
    return [], "No hay una combinacion valida para asignar este estudiante en este momento."


def _resolve_groups_by_course(term, option: SemesterScheduleOption | None = None):
    if option is not None:
        assignments = (
            option.assignments.select_related("generated_group")
            .filter(generated_group__isnull=False)
            .order_by("course__code", "section_number")
        )
        groups_by_course: dict[int, list] = {}
        for assignment in assignments:
            groups_by_course.setdefault(assignment.course_id, []).append(assignment.generated_group)
        return groups_by_course

    groups_by_course = {}
    groups = CourseGroup.objects.filter(term=term).select_related("course").order_by(
        "course__code", "id"
    )
    for group in groups:
        groups_by_course.setdefault(group.course_id, []).append(group)
    return groups_by_course


def get_active_term():
    return (
        AcademicTerm.objects.filter(active=True).order_by("-start_date").first()
        or AcademicTerm.objects.order_by("-start_date").first()
    )


def get_student_available_courses(student_profile):
    if not student_profile.program_id:
        return Course.objects.none()

    study_plan = student_profile.program.study_plans.order_by("-version", "-id").first()
    if not study_plan:
        return Course.objects.none()

    return study_plan.courses.order_by("semester", "code")


@transaction.atomic
def assign_waiting_students_to_groups(term, course=None, option: SemesterScheduleOption | None = None):
    groups_by_course = _resolve_groups_by_course(term, option=option)

    assigned = 0
    requested_courses = [course.id] if course is not None else list(groups_by_course.keys())
    waiting_requests = list(
        EnrollmentQueue.objects.filter(term=term, status="waiting", course_id__in=requested_courses)
        .select_related("course", "student")
        .order_by("request_date", "id")
    )
    if not waiting_requests:
        return assigned

    prioritized_requests = []
    for request in waiting_requests:
        load_pairs, _ = _candidate_groups_for_request(request, term, groups_by_course)
        prioritized_requests.append((len(load_pairs), request.request_date, request.id, request))
    prioritized_requests.sort(key=lambda item: (item[0], item[1], item[2]))

    for _, _, _, request in prioritized_requests:
        load_pairs, _ = _candidate_groups_for_request(request, term, groups_by_course)
        if not load_pairs:
            continue

        _, _, selected_group = min(load_pairs, key=lambda item: (item[0], item[1]))
        Enrollment.objects.create(
            request=request,
            student=request.student,
            course_group=selected_group,
            term=term,
            status="active",
        )
        request.status = "enrolled"
        request.course_group = selected_group
        request.save(update_fields=["status", "course_group"])
        assigned += 1

    return assigned


def summarize_pending_requests(term, option: SemesterScheduleOption | None = None):
    groups_by_course = _resolve_groups_by_course(term, option=option)
    requested_courses = list(groups_by_course.keys())
    waiting_qs = EnrollmentQueue.objects.filter(term=term, status="waiting").select_related(
        "course",
        "student",
    )
    if requested_courses:
        waiting_qs = waiting_qs.filter(course_id__in=requested_courses)

    pending = []
    for request in waiting_qs.order_by("course__code", "request_date", "id"):
        _, reason = _candidate_groups_for_request(request, term, groups_by_course)
        pending.append(
            {
                "student_email": request.student.email,
                "course_code": request.course.code,
                "course_name": request.course.name,
                "reason": reason or "Pendiente de una nueva ronda de asignacion.",
            }
        )
    return pending


@transaction.atomic
def request_student_enrollment(student, course, term):
    enrollment, created = EnrollmentQueue.objects.get_or_create(
        student=student,
        course=course,
        term=term,
        defaults={"status": "waiting"},
    )
    return enrollment, "waiting" if created else "existing"
