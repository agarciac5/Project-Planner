from datetime import date

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from access_support.models import User
from academic_core.models import (
    AcademicProgram,
    AcademicTerm,
    Campus,
    Course,
    Faculty,
    StudyPlan,
)


class AcademicDataIntegrityTest(TestCase):
    def test_only_one_academic_term_can_be_active(self):
        AcademicTerm.objects.create(
            name="2026-1",
            start_date=date(2026, 1, 15),
            end_date=date(2026, 5, 15),
            active=True,
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            AcademicTerm.objects.create(
                name="2026-2",
                start_date=date(2026, 7, 15),
                end_date=date(2026, 11, 15),
                active=True,
            )

    def test_academic_term_end_date_must_follow_start_date(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            AcademicTerm.objects.create(
                name="Invalido",
                start_date=date(2026, 5, 15),
                end_date=date(2026, 1, 15),
                active=False,
            )


class CourseCrudViewTest(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            email="admin-core@uniminuto.edu.co",
            password="ClaveSegura123",
            role="admin",
        )
        self.client.force_login(self.admin_user)
        self.campus = Campus.objects.create(name="Sede Principal")
        self.faculty = Faculty.objects.create(name="Ingenieria", campus=self.campus)
        self.program = AcademicProgram.objects.create(
            name="Ingenieria de Software",
            code="ISW",
            faculty=self.faculty,
            campus=self.campus,
        )
        self.study_plan = StudyPlan.objects.create(
            program=self.program,
            version="2026-1",
            description="Plan base",
        )

    def test_course_create_persists_valid_course(self):
        response = self.client.post(
            reverse("course_create"),
            {
                "name": "Bases de Datos",
                "code": "BD101",
                "credits": 3,
                "semester": 2,
                "study_plan": self.study_plan.id,
            },
        )

        self.assertRedirects(response, reverse("course_list"))
        self.assertTrue(Course.objects.filter(code="BD101").exists())

    def test_course_create_rejects_duplicate_code(self):
        Course.objects.create(
            name="Curso existente",
            code="BD101",
            credits=2,
            semester=1,
            study_plan=self.study_plan,
        )

        response = self.client.post(
            reverse("course_create"),
            {
                "name": "Bases de Datos II",
                "code": "BD101",
                "credits": 4,
                "semester": 3,
                "study_plan": self.study_plan.id,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Course.objects.filter(code="BD101").count(), 1)
        self.assertFormError(
            response.context["form"],
            "code",
            "Course with this Code already exists.",
        )


class StudyPlanViewTest(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            email="admin-plan@uniminuto.edu.co",
            password="ClaveSegura123",
            role="admin",
        )
        self.client.force_login(self.admin_user)
        self.campus = Campus.objects.create(name="Sede Principal")
        self.faculty = Faculty.objects.create(name="Ingenieria", campus=self.campus)

        self.program_one = AcademicProgram.objects.create(
            name="Ingenieria de Software",
            code="ISW",
            faculty=self.faculty,
            campus=self.campus,
        )
        self.plan_one = StudyPlan.objects.create(
            program=self.program_one,
            version="2026-1",
            description="Plan de software",
        )
        Course.objects.create(
            name="Programacion I",
            code="PRG101",
            credits=3,
            semester=1,
            study_plan=self.plan_one,
        )

        self.program_two = AcademicProgram.objects.create(
            name="Ingenieria Industrial",
            code="IIN",
            faculty=self.faculty,
            campus=self.campus,
        )
        self.plan_two = StudyPlan.objects.create(
            program=self.program_two,
            version="2026-1",
            description="Plan industrial",
        )
        Course.objects.create(
            name="Procesos",
            code="IND101",
            credits=3,
            semester=1,
            study_plan=self.plan_two,
        )

    def test_study_plan_view_filters_by_selected_program(self):
        response = self.client.get(
            reverse("study_plan"),
            {"program": "Ingenieria de Software"},
        )

        self.assertEqual(response.status_code, 200)
        filtered_plans = response.context["filtered_plans"]
        self.assertEqual(len(filtered_plans), 1)
        self.assertEqual(filtered_plans[0]["programa"], "Ingenieria de Software")
        self.assertContains(response, "Programacion I")
        self.assertNotContains(response, "Procesos")

    def test_study_plan_view_returns_empty_state_for_unknown_program(self):
        response = self.client.get(
            reverse("study_plan"),
            {"program": "Programa inexistente"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["filtered_plans"], [])
        self.assertContains(response, "No hay resultados para el programa seleccionado.")
