import random
from datetime import date, time

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from academic_core.models import AcademicProgram, AcademicTerm, Campus, Course, Faculty, StudyPlan
from access_support.models import StudentProfile
from classrooms.models import Classroom, TimeSlot
from scheduling_enrollment.algorithms.genetic_scheduler import (
    AssignmentResult,
    ClassroomResource,
    DemandCourse,
    FitnessResult,
    PotentialSection,
    SectionGene,
    TeacherResource,
    TimeSlotResource,
    _build_feasible_candidates,
    _select_diverse_results,
    evaluate_semester_schedule,
)
from scheduling_enrollment.models import (
    CourseGroup,
    Enrollment,
    EnrollmentQueue,
    ProposedSchedule,
    ScheduleSession,
    SemesterScheduleAssignment,
    SemesterScheduleOption,
    SemesterScheduleRun,
)
from scheduling_enrollment.services.enrollment_service import (
    assign_waiting_students_to_groups,
    request_student_enrollment,
)
from scheduling_enrollment.services.scheduling_service import (
    generate_semester_schedule_options,
    get_run_assignment_summary,
    revert_semester_schedule_option,
)
from teaching.models import Availability, ContractRule, Teacher


class GeneticPlannerResourceTests(TestCase):
    def setUp(self):
        self.course = DemandCourse(
            course_id=1,
            code="SW101",
            name="Algoritmos",
            demand=10,
            min_sections=1,
            max_sections=1,
            campus_id=1,
        )
        self.teacher = TeacherResource(
            teacher_id=1,
            label="Ana Ruiz",
            qualified_course_ids=frozenset({1}),
            availability=(("Monday", time(8, 0), time(12, 0)),),
            activities=(),
            max_teaching_hours=12,
            min_teaching_hours=0,
            campus_id=1,
        )
        self.slot = TimeSlotResource(
            index=1,
            day="Monday",
            start_time=time(8, 0),
            end_time=time(9, 30),
        )

    def test_candidates_reject_classroom_from_another_campus(self):
        classroom = ClassroomResource(
            classroom_id=1,
            label="B101",
            capacity=20,
            classroom_type="SALON",
            campus_id=2,
        )

        candidates = _build_feasible_candidates(
            {1: self.course},
            {1: self.teacher},
            {1: classroom},
            {1: self.slot},
        )

        self.assertEqual(candidates[1], [])

    def test_uncovered_demand_uses_real_classroom_capacity(self):
        classroom = ClassroomResource(
            classroom_id=1,
            label="A101",
            capacity=5,
            classroom_type="SALON",
            campus_id=1,
        )
        result = evaluate_semester_schedule(
            [SectionGene(True, 1, 1, 1)],
            [PotentialSection(0, 1, "SW101", "Algoritmos", 1)],
            {1: self.course},
            {1: self.teacher},
            {1: classroom},
            {1: self.slot},
        )

        self.assertEqual(result.summary["demand_covered"], 5)
        self.assertEqual(result.summary["uncovered_students"], 5)

    def test_alternatives_prioritize_different_scores(self):
        def build_result(score, course_id):
            return FitnessResult(
                score=score,
                summary={},
                assignments=[
                    AssignmentResult(
                        course_id=course_id,
                        course_code=f"SW{course_id}",
                        course_name="Materia",
                        section_number=1,
                        teacher_id=course_id,
                        classroom_id=course_id,
                        timeslot_index=course_id,
                        students_assigned=10,
                        capacity=20,
                    )
                ],
            )

        selected = _select_diverse_results(
            [
                build_result(96, 1),
                build_result(96, 2),
                build_result(92, 3),
            ],
            options_limit=2,
        )

        self.assertEqual([item.score for item in selected], [96, 92])


class SemesterPlannerServiceTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.campus = Campus.objects.create(name="Principal")
        self.faculty = Faculty.objects.create(name="Ingenieria", campus=self.campus)
        self.program = AcademicProgram.objects.create(
            name="Software",
            code="SW",
            faculty=self.faculty,
            campus=self.campus,
        )
        self.study_plan = StudyPlan.objects.create(program=self.program, version="2026")
        self.course = Course.objects.create(
            name="Algoritmos",
            code="SW101",
            credits=3,
            semester=1,
            study_plan=self.study_plan,
        )
        self.term = AcademicTerm.objects.create(
            name="2026-1",
            start_date=date(2026, 1, 15),
            end_date=date(2026, 5, 15),
            active=True,
        )
        self.contract = ContractRule.objects.create(
            contract_type="TC",
            min_teaching_hours=2,
            max_teaching_hours=12,
            max_advisory_hours=2,
            max_research_hours=2,
            max_total_hours=16,
        )
        self.teacher = Teacher.objects.create(
            teacher_id="DOC01",
            first_name="Ana",
            last_name="Ruiz",
            program=self.program,
            faculty=self.faculty,
            campus=self.campus,
            contract=self.contract,
            is_active=True,
        )
        self.teacher.qualified_courses.add(self.course)
        Availability.objects.create(
            teacher=self.teacher,
            day="Monday",
            start_time=time(7, 0),
            end_time=time(12, 0),
        )
        Availability.objects.create(
            teacher=self.teacher,
            day="Tuesday",
            start_time=time(7, 0),
            end_time=time(12, 0),
        )
        Classroom.objects.create(
            classroom_id="A101",
            name="Aula 101",
            block=1,
            campus=self.campus,
            capacity=25,
            classroom_type="SALON",
            is_active=True,
        )
        for day, start_hour in [("Monday", 7), ("Monday", 9), ("Tuesday", 7), ("Tuesday", 9)]:
            TimeSlot.objects.create(
                day=day,
                start_time=time(start_hour, 0),
                end_time=time(start_hour + 1, 30),
            )
        for index in range(10):
            student = self.user_model.objects.create_user(
                email=f"student{index}@test.com",
                password="secret123",
                role="student",
            )
            EnrollmentQueue.objects.create(
                student=student,
                course=self.course,
                term=self.term,
                status="waiting",
            )

    def test_generates_semester_run_and_applies_best_option(self):
        random.seed(7)

        run = generate_semester_schedule_options(
            self.term.id,
            auto_apply_best=True,
        )

        self.assertIsNotNone(run)
        self.assertEqual(run.status, "ready_to_publish")
        self.assertGreaterEqual(run.options.count(), 1)

        best_option = run.options.get(is_best=True)
        self.assertTrue(best_option.applied)
        self.assertGreater(best_option.score, 0)
        self.assertGreater(best_option.assignments.count(), 0)
        self.assertGreater(CourseGroup.objects.count(), 0)
        self.assertGreater(ScheduleSession.objects.count(), 0)
        self.assertEqual(Enrollment.objects.filter(term=self.term, status="active").count(), 10)
        self.assertEqual(EnrollmentQueue.objects.filter(term=self.term, status="enrolled").count(), 10)

    def test_generates_partial_plan_when_some_courses_have_no_feasible_resources(self):
        extra_course = Course.objects.create(
            name="Redes",
            code="SW201",
            credits=3,
            semester=2,
            study_plan=self.study_plan,
        )
        for index in range(6):
            student = self.user_model.objects.create_user(
                email=f"extra{index}@test.com",
                password="secret123",
                role="student",
            )
            EnrollmentQueue.objects.create(
                student=student,
                course=extra_course,
                term=self.term,
                status="waiting",
            )

        random.seed(7)
        run = generate_semester_schedule_options(
            self.term.id,
            auto_apply_best=False,
        )

        self.assertIsNotNone(run)
        best_option = run.options.get(is_best=True)
        self.assertEqual(best_option.demand_total, 16)
        self.assertEqual(best_option.demand_covered, 10)
        self.assertEqual(best_option.summary["unschedulable_course_count"], 1)
        self.assertEqual(best_option.summary["unschedulable_demand"], 6)
        self.assertEqual(best_option.summary["uncovered_students"], 6)
        self.assertEqual(best_option.summary["unschedulable_courses"][0]["code"], "SW201")

    def test_student_request_only_registers_demand_until_semester_plan_is_processed(self):
        pending_student = self.user_model.objects.create_user(
            email="newstudent@test.com",
            password="secret123",
            role="student",
        )

        enrollment, outcome = request_student_enrollment(
            pending_student,
            self.course,
            self.term,
        )

        self.assertEqual(outcome, "waiting")
        self.assertEqual(enrollment.status, "waiting")
        self.assertEqual(CourseGroup.objects.count(), 0)
        self.assertEqual(Enrollment.objects.count(), 0)

    def test_assignment_summary_reports_ready_to_publish_when_everyone_is_assigned(self):
        random.seed(7)

        run = generate_semester_schedule_options(
            self.term.id,
            auto_apply_best=True,
        )
        summary = get_run_assignment_summary(run)

        self.assertEqual(run.status, "ready_to_publish")
        self.assertTrue(summary["ready_to_publish"])
        self.assertEqual(summary["waiting_total"], 0)
        self.assertEqual(summary["assigned_total"], 10)
        self.assertGreater(summary["groups_created"], 0)
        self.assertTrue(any(stage["label"] == "Asignacion" and stage["done"] for stage in summary["stages"]))

    def test_assignment_summary_includes_pending_students_detail(self):
        random.seed(7)

        run = generate_semester_schedule_options(
            self.term.id,
            auto_apply_best=True,
        )
        late_student = self.user_model.objects.create_user(
            email="late@test.com",
            password="secret123",
            role="student",
        )
        EnrollmentQueue.objects.create(
            student=late_student,
            course=self.course,
            term=self.term,
            status="waiting",
        )

        summary = get_run_assignment_summary(run)

        self.assertEqual(summary["waiting_total"], 1)
        self.assertEqual(len(summary["pending_by_student"]), 1)
        self.assertEqual(summary["pending_by_student"][0]["student_email"], "late@test.com")

    def test_published_option_cannot_be_reverted(self):
        run = SemesterScheduleRun.objects.create(
            term=self.term,
            status="published",
        )
        option = SemesterScheduleOption.objects.create(
            run=run,
            rank=1,
            applied=True,
        )

        with self.assertRaisesMessage(
            ValueError,
            "Un plan publicado no se puede revertir",
        ):
            revert_semester_schedule_option(option)

    def test_only_one_option_per_run_can_be_selected(self):
        run = SemesterScheduleRun.objects.create(term=self.term)
        SemesterScheduleOption.objects.create(
            run=run,
            rank=1,
            selected=True,
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            SemesterScheduleOption.objects.create(
                run=run,
                rank=2,
                selected=True,
            )

    def test_nrc_must_be_unique_within_term(self):
        CourseGroup.objects.create(
            course=self.course,
            teacher=self.teacher,
            term=self.term,
            nrc="12345",
            capacity=20,
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            CourseGroup.objects.create(
                course=self.course,
                teacher=self.teacher,
                term=self.term,
                nrc="12345",
                capacity=20,
            )


class EnrollmentViewTest(TestCase):
    def setUp(self):
        self.campus = Campus.objects.create(name="Principal")
        self.faculty = Faculty.objects.create(name="Ingenieria", campus=self.campus)
        self.program = AcademicProgram.objects.create(
            name="Software",
            code="SW",
            faculty=self.faculty,
            campus=self.campus,
        )
        self.study_plan = StudyPlan.objects.create(program=self.program, version="2026")
        self.course = Course.objects.create(
            name="Algoritmos",
            code="SW101",
            credits=3,
            semester=1,
            study_plan=self.study_plan,
        )
        self.term = AcademicTerm.objects.create(
            name="2026-1",
            start_date=date(2026, 1, 15),
            end_date=date(2026, 5, 15),
            active=True,
        )
        self.student = get_user_model().objects.create_user(
            email="student-enrollment@test.com",
            password="secret123",
            role="student",
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.student,
            student_code="EST-000001",
            full_name="Ana Perez",
            program=self.program,
            faculty=self.faculty,
            campus=self.campus,
        )

    def test_enrollment_view_creates_waiting_request_for_student(self):
        self.client.force_login(self.student)

        get_response = self.client.get(reverse("enrollment"))
        post_response = self.client.post(
            reverse("enrollment"),
            {"course_id": self.course.id},
        )

        self.assertEqual(get_response.status_code, 200)
        self.assertRedirects(post_response, reverse("enrollment"))
        self.assertTrue(
            EnrollmentQueue.objects.filter(
                student=self.student,
                course=self.course,
                term=self.term,
                status="waiting",
            ).exists()
        )

    def test_enrollment_view_does_not_duplicate_existing_request(self):
        EnrollmentQueue.objects.create(
            student=self.student,
            course=self.course,
            term=self.term,
            status="waiting",
        )
        self.client.force_login(self.student)

        response = self.client.post(
            reverse("enrollment"),
            {"course_id": self.course.id},
        )

        self.assertRedirects(response, reverse("enrollment"))
        self.assertEqual(
            EnrollmentQueue.objects.filter(
                student=self.student,
                course=self.course,
                term=self.term,
            ).count(),
            1,
        )

    def test_database_rejects_duplicate_enrollment_request(self):
        EnrollmentQueue.objects.create(
            student=self.student,
            course=self.course,
            term=self.term,
            status="waiting",
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            EnrollmentQueue.objects.create(
                student=self.student,
                course=self.course,
                term=self.term,
                status="waiting",
            )

    def test_assignment_keeps_student_waiting_when_schedule_conflicts(self):
        second_course = Course.objects.create(
            name="Bases de Datos",
            code="SW102",
            credits=3,
            semester=1,
            study_plan=self.study_plan,
        )
        teacher = Teacher.objects.create(
            teacher_id="DOC-CONFLICT",
            first_name="Ana",
            last_name="Ruiz",
            campus=self.campus,
        )
        classroom = Classroom.objects.create(
            classroom_id="A-CONFLICT",
            block=1,
            campus=self.campus,
            capacity=30,
        )
        first_group = CourseGroup.objects.create(
            course=self.course,
            teacher=teacher,
            term=self.term,
            nrc="10001",
            capacity=30,
        )
        first_schedule = ProposedSchedule.objects.create(
            teacher=teacher,
            term=self.term,
        )
        ScheduleSession.objects.create(
            schedule=first_schedule,
            group=first_group,
            classroom=classroom,
            day="Monday",
            start_time=time(8, 0),
            end_time=time(10, 0),
        )
        Enrollment.objects.create(
            student=self.student,
            course_group=first_group,
            term=self.term,
        )
        conflicting_group = CourseGroup.objects.create(
            course=second_course,
            teacher=teacher,
            term=self.term,
            nrc="10002",
            capacity=30,
        )
        conflicting_schedule = ProposedSchedule.objects.create(
            teacher=teacher,
            term=self.term,
        )
        ScheduleSession.objects.create(
            schedule=conflicting_schedule,
            group=conflicting_group,
            classroom=classroom,
            day="Monday",
            start_time=time(9, 0),
            end_time=time(11, 0),
        )
        request = EnrollmentQueue.objects.create(
            student=self.student,
            course=second_course,
            term=self.term,
            status="waiting",
        )

        assigned = assign_waiting_students_to_groups(
            self.term,
            course=second_course,
        )

        request.refresh_from_db()
        self.assertEqual(assigned, 0)
        self.assertEqual(request.status, "waiting")

    def test_enrollment_view_rejects_course_outside_student_study_plan(self):
        other_program = AcademicProgram.objects.create(
            name="Industrial",
            code="IND",
            faculty=self.faculty,
            campus=self.campus,
        )
        other_plan = StudyPlan.objects.create(program=other_program, version="2026")
        unauthorized_course = Course.objects.create(
            name="Procesos",
            code="IND101",
            credits=3,
            semester=1,
            study_plan=other_plan,
        )
        self.client.force_login(self.student)

        response = self.client.post(
            reverse("enrollment"),
            {"course_id": unauthorized_course.id},
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(
            EnrollmentQueue.objects.filter(
                student=self.student,
                course=unauthorized_course,
                term=self.term,
            ).exists()
        )

    def test_admin_cannot_publish_semester_plan(self):
        admin_user = get_user_model().objects.create_user(
            email="admin-schedule@uniminuto.edu.co",
            password="ClaveSegura123",
            role="admin",
        )
        run = SemesterScheduleRun.objects.create(
            term=self.term,
            status="ready_to_publish",
        )
        SemesterScheduleOption.objects.create(
            run=run,
            rank=1,
            applied=True,
        )
        self.client.force_login(admin_user)

        response = self.client.post(
            reverse("publish_semester_run", args=[run.id]),
        )

        self.assertRedirects(response, reverse("home"))
        run.refresh_from_db()
        self.assertEqual(run.status, "ready_to_publish")

    def test_coordinator_cannot_delete_published_semester_plan(self):
        coordinator = get_user_model().objects.create_user(
            email="director-schedule@uniminuto.edu.co",
            password="ClaveSegura123",
            role="coordinator",
        )
        run = SemesterScheduleRun.objects.create(
            term=self.term,
            status="published",
        )
        self.client.force_login(coordinator)

        response = self.client.post(
            reverse("delete_semester_run", args=[run.id]),
        )

        self.assertRedirects(
            response,
            reverse("saved_semester_run_detail", args=[run.id]),
        )
        self.assertTrue(SemesterScheduleRun.objects.filter(id=run.id).exists())


class PersonalScheduleViewTest(TestCase):
    def setUp(self):
        self.campus = Campus.objects.create(name="Principal")
        self.faculty = Faculty.objects.create(name="Ingenieria", campus=self.campus)
        self.program = AcademicProgram.objects.create(
            name="Software",
            code="SW",
            faculty=self.faculty,
            campus=self.campus,
        )
        self.study_plan = StudyPlan.objects.create(program=self.program, version="2026")
        self.course = Course.objects.create(
            name="Algoritmos",
            code="SW101",
            credits=3,
            semester=1,
            study_plan=self.study_plan,
        )
        self.term = AcademicTerm.objects.create(
            name="2026-1",
            start_date=date(2026, 1, 15),
            end_date=date(2026, 5, 15),
            active=True,
        )
        self.classroom = Classroom.objects.create(
            classroom_id="A101",
            name="Aula 101",
            block=1,
            campus=self.campus,
            capacity=30,
            classroom_type="SALON",
            is_active=True,
        )
        self.teacher_user = get_user_model().objects.create_user(
            email="teacher-schedule@test.com",
            password="secret123",
            role="teacher",
        )
        self.teacher = Teacher.objects.create(
            user=self.teacher_user,
            teacher_id="DOC01",
            first_name="Laura",
            last_name="Gomez",
            program=self.program,
            faculty=self.faculty,
            campus=self.campus,
            is_active=True,
        )
        self.student = get_user_model().objects.create_user(
            email="student-schedule@test.com",
            password="secret123",
            role="student",
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.student,
            student_code="EST-000001",
            full_name="Ana Perez",
            program=self.program,
            faculty=self.faculty,
            campus=self.campus,
        )
        self.run = SemesterScheduleRun.objects.create(
            term=self.term,
            status="published",
        )
        self.option = SemesterScheduleOption.objects.create(
            run=self.run,
            rank=1,
            score=95,
            is_best=True,
            selected=True,
            applied=True,
        )
        self.group = CourseGroup.objects.create(
            course=self.course,
            teacher=self.teacher,
            term=self.term,
            nrc="9001",
            capacity=30,
        )
        self.schedule = ProposedSchedule.objects.create(
            teacher=self.teacher,
            term=self.term,
            status="approved",
            fitness_score=95,
            rank=1,
        )
        ScheduleSession.objects.create(
            schedule=self.schedule,
            group=self.group,
            classroom=self.classroom,
            day="Monday",
            start_time=time(7, 0),
            end_time=time(8, 30),
        )
        SemesterScheduleAssignment.objects.create(
            option=self.option,
            course=self.course,
            teacher=self.teacher,
            classroom=self.classroom,
            generated_group=self.group,
            generated_schedule=self.schedule,
            section_number=1,
            nrc="9001",
            day="Monday",
            start_time=time(7, 0),
            end_time=time(8, 30),
            students_assigned=1,
            capacity=30,
        )
        Enrollment.objects.create(
            student=self.student,
            course_group=self.group,
            term=self.term,
            status="active",
        )

    def test_my_student_schedule_view_shows_published_enrollments(self):
        self.client.force_login(self.student)

        response = self.client.get(reverse("my_student_schedule"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "SW101")
        self.assertContains(response, "Algoritmos")
        self.assertContains(response, "A101")

    def test_my_student_schedule_view_redirects_student_without_profile(self):
        student_without_profile = get_user_model().objects.create_user(
            email="student-noprofile@test.com",
            password="secret123",
            role="student",
        )
        self.client.force_login(student_without_profile)

        response = self.client.get(reverse("my_student_schedule"))

        self.assertRedirects(response, reverse("home"))

    def test_my_teacher_schedule_view_shows_published_groups(self):
        self.client.force_login(self.teacher_user)

        response = self.client.get(reverse("my_teacher_schedule"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "SW101")
        self.assertContains(response, "student-schedule@test.com")
        self.assertContains(response, "A101")

    def test_my_teacher_schedule_view_redirects_teacher_without_profile(self):
        teacher_without_profile = get_user_model().objects.create_user(
            email="teacher-noprofile@test.com",
            password="secret123",
            role="teacher",
        )
        self.client.force_login(teacher_without_profile)

        response = self.client.get(reverse("my_teacher_schedule"))

        self.assertRedirects(response, reverse("home"))
