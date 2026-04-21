import random
from datetime import date, time

from django.contrib.auth import get_user_model
from django.test import TestCase

from academic_core.models import AcademicProgram, AcademicTerm, Campus, Course, Faculty, StudyPlan
from classrooms.models import Classroom, TimeSlot
from scheduling_enrollment.models import CourseGroup, EnrollmentQueue, ScheduleSession
from scheduling_enrollment.services.scheduling_service import generate_semester_schedule_options
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
        self.assertEqual(run.status, "applied")
        self.assertGreaterEqual(run.options.count(), 1)

        best_option = run.options.get(is_best=True)
        self.assertTrue(best_option.applied)
        self.assertGreater(best_option.score, 0)
        self.assertGreater(best_option.assignments.count(), 0)
        self.assertGreater(CourseGroup.objects.count(), 0)
        self.assertGreater(ScheduleSession.objects.count(), 0)
