from django.db import models, transaction
from django.db.models import Count

from academic_core.models import AcademicTerm, Course
from scheduling_enrollment.models import CourseGroup, EnrollmentQueue
from scheduling_enrollment.services.scheduling_service import (
    apply_semester_schedule_run,
    generate_semester_schedule_options,
)


def get_active_term():
    return (
        AcademicTerm.objects.filter(active=True).order_by("-start_date").first()
        or AcademicTerm.objects.order_by("-start_date").first()
    )


def get_student_available_courses(student_profile):
    if not student_profile.program_id:
        return Course.objects.none()

    study_plan = (
        student_profile.program.study_plans.order_by("-version", "-id").first()
    )
    if not study_plan:
        return Course.objects.none()

    return study_plan.courses.order_by("semester", "code")
def assign_waiting_students_to_groups(term, course=None):
    waiting_qs = (
        EnrollmentQueue.objects.filter(term=term, status="waiting")
        .select_related("course", "student")
        .order_by("request_date", "id")
    )
    if course is not None:
        waiting_qs = waiting_qs.filter(course=course)

    assigned = 0
    for request in waiting_qs:
        group = (
            CourseGroup.objects.filter(course=request.course, term=term)
            .annotate(
                enrolled_count=Count(
                    "student_enrollments",
                    filter=models.Q(student_enrollments__status="enrolled"),
                )
            )
            .order_by("enrolled_count", "id")
            .first()
        )
        if not group:
            continue
        if group.enrolled_count >= group.capacity:
            continue
        request.status = "enrolled"
        request.course_group = group
        request.save(update_fields=["status", "course_group"])
        assigned += 1
    return assigned


@transaction.atomic
def request_student_enrollment(student, course, term):
    existing = EnrollmentQueue.objects.filter(
        student=student,
        course=course,
        term=term,
    ).first()
    if existing:
        return existing, "existing"

    group = (
        CourseGroup.objects.filter(course=course, term=term)
        .annotate(
            enrolled_count=Count(
                "student_enrollments",
                filter=models.Q(student_enrollments__status="enrolled"),
            )
        )
        .order_by("enrolled_count", "id")
        .first()
    )

    if group and group.enrolled_count < group.capacity:
        enrollment = EnrollmentQueue.objects.create(
            student=student,
            course=course,
            course_group=group,
            term=term,
            status="enrolled",
        )
        return enrollment, "enrolled"

    enrollment = EnrollmentQueue.objects.create(
        student=student,
        course=course,
        term=term,
        status="waiting",
    )

    waiting_count = EnrollmentQueue.objects.filter(
        course=course,
        term=term,
        status="waiting",
    ).count()
    has_group = CourseGroup.objects.filter(course=course, term=term).exists()
    should_generate_group = waiting_count >= 5 or not has_group
    if should_generate_group:
        run = generate_semester_schedule_options(
            term.id,
            auto_apply_best=False,
            course_ids={course.id},
        )
        if run and run.options.filter(selected=True).exists():
            apply_semester_schedule_run(run, option=run.options.get(selected=True))
        elif run:
            best = run.options.filter(is_best=True).first()
            if best:
                best.selected = True
                best.save(update_fields=["selected"])
                apply_semester_schedule_run(run, option=best)
        assign_waiting_students_to_groups(term, course=course)

    return enrollment, "waiting"
