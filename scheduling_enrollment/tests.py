import random
from datetime import date, time

from django.contrib.auth import get_user_model
from django.test import TestCase

from academic_core.models import AcademicProgram, AcademicTerm, Campus, Course, Faculty, StudyPlan
from classrooms.models import Classroom, TimeSlot
from scheduling_enrollment.models import CourseGroup, Enrollment, EnrollmentQueue, ScheduleSession
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
