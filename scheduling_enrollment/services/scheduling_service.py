import math
from datetime import time

from django.db import transaction
from django.db.models import Count, Q

from academic_core.models import AcademicTerm, Course
from classrooms.models import Classroom, TimeSlot
from scheduling_enrollment.algorithms.genetic_scheduler import (
    ClassroomResource,
    DemandCourse,
    TeacherResource,
    TimeSlotResource,
    run_semester_planner,
)
from scheduling_enrollment.models import (
    CourseGroup,
    EnrollmentQueue,
    ProposedSchedule,
    ScheduleSession,
    TeacherActivity,
    SemesterScheduleAssignment,
    SemesterScheduleOption,
    SemesterScheduleRun,
)
from teaching.models import Teacher


DEFAULT_TIMESLOTS = [
    ("Monday", time(7, 0), time(8, 30)),
    ("Monday", time(8, 30), time(10, 0)),
    ("Monday", time(10, 0), time(11, 30)),
    ("Monday", time(14, 0), time(15, 30)),
    ("Monday", time(15, 30), time(17, 0)),
    ("Tuesday", time(7, 0), time(8, 30)),
    ("Tuesday", time(8, 30), time(10, 0)),
    ("Tuesday", time(10, 0), time(11, 30)),
    ("Tuesday", time(14, 0), time(15, 30)),
    ("Tuesday", time(15, 30), time(17, 0)),
    ("Wednesday", time(7, 0), time(8, 30)),
    ("Wednesday", time(8, 30), time(10, 0)),
    ("Wednesday", time(10, 0), time(11, 30)),
    ("Wednesday", time(14, 0), time(15, 30)),
    ("Wednesday", time(15, 30), time(17, 0)),
    ("Thursday", time(7, 0), time(8, 30)),
    ("Thursday", time(8, 30), time(10, 0)),
    ("Thursday", time(10, 0), time(11, 30)),
    ("Thursday", time(14, 0), time(15, 30)),
    ("Thursday", time(15, 30), time(17, 0)),
    ("Friday", time(7, 0), time(8, 30)),
    ("Friday", time(8, 30), time(10, 0)),
    ("Friday", time(10, 0), time(11, 30)),
    ("Friday", time(14, 0), time(15, 30)),
    ("Saturday", time(8, 0), time(9, 30)),
    ("Saturday", time(9, 30), time(11, 0)),
]


def _get_term(term_id: int) -> AcademicTerm:
    return AcademicTerm.objects.get(id=term_id)


def _build_demand_courses(term: AcademicTerm) -> list[DemandCourse]:
    waiting = (
        EnrollmentQueue.objects.filter(status="waiting")
        .filter(Q(term=term) | Q(term__isnull=True))
        .values("course")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
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
        if demand < 5:
            continue
        min_sections = math.ceil(demand / 20)
        max_sections = max(min_sections, demand // 5)
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


@transaction.atomic
def generate_semester_schedule_options(term_id: int, auto_apply_best: bool = False) -> SemesterScheduleRun | None:
    term = _get_term(term_id)
    demand_courses = _build_demand_courses(term)
    if not demand_courses:
        return None

    teacher_resources = _build_teacher_resources(
        term,
        demanded_course_ids={course.course_id for course in demand_courses},
    )
    classroom_resources = _build_classroom_resources()
    timeslots = _build_timeslots()
    results = run_semester_planner(
        demand_courses=demand_courses,
        teachers=teacher_resources,
        classrooms=classroom_resources,
        timeslots=timeslots,
    )
    if not results:
        return None

    teacher_map = {teacher.id: teacher for teacher in Teacher.objects.filter(id__in=[t.teacher_id for t in teacher_resources])}
    classroom_map = {classroom.id: classroom for classroom in Classroom.objects.filter(id__in=[c.classroom_id for c in classroom_resources])}
    course_map = {course.id: course for course in Course.objects.filter(id__in=[c.course_id for c in demand_courses])}
    timeslot_map = {slot.index: slot for slot in timeslots}

    run = SemesterScheduleRun.objects.create(term=term)
    for rank, result in enumerate(results, start=1):
        option = SemesterScheduleOption.objects.create(
            run=run,
            rank=rank,
            score=result.score,
            demand_covered=result.summary["demand_covered"],
            demand_total=result.summary["demand_total"],
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
def apply_semester_schedule_run(run: SemesterScheduleRun, option: SemesterScheduleOption | None = None) -> SemesterScheduleOption:
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
        assignment.generated_group = group
        assignment.generated_schedule = schedule
        assignment.nrc = nrc
        assignment.save(update_fields=["generated_group", "generated_schedule", "nrc"])

    run.options.exclude(id=best_option.id).update(selected=False)
    best_option.selected = True
    best_option.applied = True
    best_option.save(update_fields=["selected", "applied"])
    run.status = "applied"
    run.save(update_fields=["status"])
    return best_option


@transaction.atomic
def revert_semester_schedule_option(option: SemesterScheduleOption) -> SemesterScheduleOption:
    assignments = list(
        option.assignments.select_related("generated_group", "generated_schedule")
    )
    group_ids = [assignment.generated_group_id for assignment in assignments if assignment.generated_group_id]
    schedule_ids = [assignment.generated_schedule_id for assignment in assignments if assignment.generated_schedule_id]

    if group_ids:
        CourseGroup.objects.filter(id__in=group_ids).delete()

    if schedule_ids:
        ProposedSchedule.objects.filter(id__in=schedule_ids).delete()

    option.assignments.update(
        generated_group=None,
        generated_schedule=None,
        nrc="",
    )
    option.applied = False
    option.save(update_fields=["applied"])

    run = option.run
    if not run.options.filter(applied=True).exists():
        run.status = "saved" if run.options.filter(selected=True).exists() else "draft"
        run.save(update_fields=["status"])

    return option
