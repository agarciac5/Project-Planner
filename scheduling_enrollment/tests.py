import random
from datetime import date, time

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from academic_core.models import AcademicProgram, AcademicTerm, Campus, Course, Faculty, StudyPlan
from access_support.models import StudentProfile
from classrooms.models import Classroom, TimeSlot
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
from scheduling_enrollment.services.enrollment_service import request_student_enrollment
from scheduling_enrollment.services.scheduling_service import (
    generate_semester_schedule_options,
    get_run_assignment_summary,
)
from teaching.models import Availability, ContractRule, Teacher


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

        run = generate_semester_schedule_options(self.term.id, auto_apply_best=True)

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
        run = generate_semester_schedule_options(self.term.id, auto_apply_best=False)

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

        run = generate_semester_schedule_options(self.term.id, auto_apply_best=True)
        summary = get_run_assignment_summary(run)

        self.assertEqual(run.status, "ready_to_publish")
        self.assertTrue(summary["ready_to_publish"])
        self.assertEqual(summary["waiting_total"], 0)
        self.assertEqual(summary["assigned_total"], 10)
        self.assertGreater(summary["groups_created"], 0)
        self.assertTrue(any(stage["label"] == "Asignacion" and stage["done"] for stage in summary["stages"]))

    def test_assignment_summary_includes_pending_students_detail(self):
        random.seed(7)

        run = generate_semester_schedule_options(self.term.id, auto_apply_best=True)
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
