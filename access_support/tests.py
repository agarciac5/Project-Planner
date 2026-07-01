from unittest.mock import patch

import pandas as pd
from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from access_support.models import StudentProfile, User
from academic_core.models import AcademicProgram, Campus, Faculty
from teaching.models import Teacher


class RegisterViewTest(TestCase):
    def test_register_creates_user_with_institutional_email(self):
        response = self.client.post(
            reverse("register"),
            {
                "email": "ana@uniminuto.edu.co",
                "password": "ClaveSegura123",
                "confirm": "ClaveSegura123",
            },
        )

        self.assertRedirects(response, reverse("student_profile_setup"))
        self.assertTrue(User.objects.filter(email="ana@uniminuto.edu.co").exists())
        self.assertIn("_auth_user_id", self.client.session)

    def test_register_rejects_email_outside_institutional_domain(self):
        response = self.client.post(
            reverse("register"),
            {
                "email": "ana@gmail.com",
                "password": "ClaveSegura123",
                "confirm": "ClaveSegura123",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email="ana@gmail.com").exists())
        self.assertContains(response, "Solo se permiten correos institucionales")

    def test_register_rejects_weak_password(self):
        response = self.client.post(
            reverse("register"),
            {
                "email": "ana@uniminuto.edu.co",
                "password": "12345",
                "confirm": "12345",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email="ana@uniminuto.edu.co").exists())
        self.assertContains(response, "too short")


class LoginViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="docente@uniminuto.edu.co",
            password="ClaveSegura123",
        )

    def test_login_authenticates_user_with_valid_credentials(self):
        response = self.client.post(
            reverse("login"),
            {
                "email": "docente@uniminuto.edu.co",
                "password": "ClaveSegura123",
            },
        )

        self.assertRedirects(response, reverse("home"))
        self.assertEqual(str(self.client.session["_auth_user_id"]), str(self.user.pk))

    def test_login_rejects_invalid_credentials(self):
        response = self.client.post(
            reverse("login"),
            {
                "email": "docente@uniminuto.edu.co",
                "password": "incorrecta",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertContains(response, "Credenciales incorrectas")


class StudentProfileSetupViewTest(TestCase):
    def setUp(self):
        self.campus = Campus.objects.create(name="Sede Principal")
        self.faculty = Faculty.objects.create(name="Ingenieria", campus=self.campus)
        self.program = AcademicProgram.objects.create(
            name="Ingenieria de Software",
            code="ISW",
            faculty=self.faculty,
            campus=self.campus,
        )

    def test_student_profile_setup_creates_profile_and_generates_student_code(self):
        user = User.objects.create_user(
            email="student@uniminuto.edu.co",
            password="ClaveSegura123",
            role="student",
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("student_profile_setup"),
            {
                "full_name": "Ana Perez",
                "document_type": "CC",
                "document_number": "123456",
                "address": "Cra 10",
                "program": self.program.id,
                "faculty": "",
                "campus": "",
                "level": "Pregrado",
                "jornada": "Diurna",
            },
        )

        self.assertRedirects(response, reverse("profile"))
        profile = StudentProfile.objects.get(user=user)
        self.assertEqual(profile.program, self.program)
        self.assertEqual(profile.faculty, self.faculty)
        self.assertEqual(profile.campus, self.campus)
        self.assertRegex(profile.student_code, r"^EST-\d{6}$")

    def test_student_profile_setup_redirects_non_student_users(self):
        user = User.objects.create_user(
            email="teacher@uniminuto.edu.co",
            password="ClaveSegura123",
            role="teacher",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("student_profile_setup"))

        self.assertRedirects(response, reverse("profile"))
        self.assertFalse(StudentProfile.objects.filter(user=user).exists())


class ImportViewTest(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            email="admin@uniminuto.edu.co",
            password="ClaveSegura123",
            role="admin",
        )
        self.client.force_login(self.admin_user)

    @patch("access_support.views.pd.read_excel")
    def test_import_creates_student_and_related_catalog_records_for_supported_program(
        self, mock_read_excel
    ):
        mock_read_excel.return_value = pd.DataFrame(
            [
                {
                    "CORREO_ESTUDIANTE": "estudiante1@correo.com",
                    "DESCRIPCION_PROGRAMA": "ingenieria de software",
                    "DESCRIPCION_SEDE": "Sede Principal",
                    "DESCRIPCION_FACULTAD": "Facultad de Ingenieria",
                    "CODIGO": "EST-001",
                    "TIPO_DOCUMENTO": "CC",
                    "NUM_DOCUMENTO": "123456",
                    "NOMBRES": "Ana Perez",
                    "DESCRIPCION_NIVEL": "Pregrado",
                    "JORNADA": "Diurna",
                }
            ]
        )

        response = self.client.post(
            reverse("import"),
            {
                "archivo": SimpleUploadedFile(
                    "estudiantes.xlsx",
                    b"contenido",
                    content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(email="estudiante1@correo.com").exists())
        self.assertTrue(StudentProfile.objects.filter(student_code="EST-001").exists())
        self.assertTrue(Campus.objects.filter(name="Sede Principal").exists())
        self.assertTrue(Faculty.objects.filter(name="Facultad de Ingenieria").exists())
        self.assertTrue(
            AcademicProgram.objects.filter(name="ingenieria de software").exists()
        )

    def test_import_returns_error_when_file_is_missing(self):
        response = self.client.post(reverse("import"), {})
        messages = [message.message for message in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/import.html")
        self.assertIn("No se subio ningun archivo", messages)
        self.assertEqual(User.objects.filter(role="student").count(), 0)
        self.assertEqual(StudentProfile.objects.count(), 0)


class AssignRolesViewTest(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            email="admin.roles@uniminuto.edu.co",
            password="ClaveSegura123",
            role="admin",
        )
        self.target_user = User.objects.create_user(
            email="ana.perez@uniminuto.edu.co",
            password="ClaveSegura123",
            role="student",
        )
        self.target_profile = StudentProfile.objects.create(
            user=self.target_user,
            student_code="EST-900001",
            full_name="Ana Perez",
            address="Cra 10",
        )
        self.other_user = User.objects.create_user(
            email="luis.gomez@uniminuto.edu.co",
            password="ClaveSegura123",
            role="teacher",
        )

    def test_assign_roles_view_allows_coordinator_role(self):
        coordinator_user = User.objects.create_user(
            email="director@uniminuto.edu.co",
            password="ClaveSegura123",
            role="coordinator",
        )
        self.client.force_login(coordinator_user)

        response = self.client.get(reverse("assign_roles"))

        self.assertEqual(response.status_code, 200)

    def test_assign_roles_view_blocks_teacher_role(self):
        teacher_user = User.objects.create_user(
            email="docente.roles@uniminuto.edu.co",
            password="ClaveSegura123",
            role="teacher",
        )
        self.client.force_login(teacher_user)

        response = self.client.get(reverse("assign_roles"))

        self.assertRedirects(response, reverse("home"), fetch_redirect_response=False)

    def test_assign_roles_view_filters_users_by_partial_email(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("assign_roles"), {"email_query": "ana"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ana.perez@uniminuto.edu.co")
        self.assertNotContains(response, "luis.gomez@uniminuto.edu.co")

    def test_admin_cannot_assign_coordinator_role(self):
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse("assign_roles"),
            {
                "user_id": self.target_user.id,
                "role": "coordinator",
                "search": "ana.perez",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.target_user.refresh_from_db()
        self.assertEqual(self.target_user.role, "student")
        self.assertContains(
            response,
            "Solo un director academico puede asignar el rol de director",
        )

    def test_coordinator_can_assign_coordinator_role(self):
        coordinator_user = User.objects.create_user(
            email="director.roles@uniminuto.edu.co",
            password="ClaveSegura123",
            role="coordinator",
        )
        self.client.force_login(coordinator_user)

        response = self.client.post(
            reverse("assign_roles"),
            {
                "user_id": self.target_user.id,
                "role": "coordinator",
                "search": "ana.perez",
            },
        )

        self.assertRedirects(
            response,
            f"{reverse('assign_roles')}?email_query=ana.perez",
        )
        self.target_user.refresh_from_db()
        self.assertEqual(self.target_user.role, "coordinator")

    def test_admin_cannot_modify_existing_coordinator(self):
        coordinator_user = User.objects.create_user(
            email="director.protected@uniminuto.edu.co",
            password="ClaveSegura123",
            role="coordinator",
        )
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse("assign_roles"),
            {
                "user_id": coordinator_user.id,
                "role": "student",
                "search": "director.protected",
            },
        )

        self.assertEqual(response.status_code, 200)
        coordinator_user.refresh_from_db()
        self.assertEqual(coordinator_user.role, "coordinator")
        self.assertContains(
            response,
            "Solo un director academico puede modificar a otro director",
        )

    def test_assigning_teacher_role_creates_teacher_profile(self):
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse("assign_roles"),
            {
                "user_id": self.target_user.id,
                "role": "teacher",
                "search": "ana.perez",
            },
        )

        self.assertRedirects(
            response,
            f"{reverse('assign_roles')}?email_query=ana.perez",
        )
        self.target_user.refresh_from_db()
        teacher_profile = Teacher.objects.get(user=self.target_user)
        self.assertEqual(self.target_user.role, "teacher")
        self.assertEqual(teacher_profile.first_name, "Ana")
        self.assertEqual(teacher_profile.last_name, "Perez")
        self.assertEqual(teacher_profile.address, "Cra 10")

    def test_assigning_student_role_creates_student_profile_and_detaches_teacher_profile(self):
        teacher_user = User.objects.create_user(
            email="docente.cambio@uniminuto.edu.co",
            password="ClaveSegura123",
            role="teacher",
        )
        teacher_profile = Teacher.objects.create(
            user=teacher_user,
            teacher_id="DOC-900",
            first_name="Laura",
            last_name="Gomez",
            address="Av 1",
            is_active=True,
        )
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse("assign_roles"),
            {
                "user_id": teacher_user.id,
                "role": "student",
                "search": "docente.cambio",
            },
        )

        self.assertRedirects(
            response,
            f"{reverse('assign_roles')}?email_query=docente.cambio",
        )
        teacher_user.refresh_from_db()
        teacher_profile.refresh_from_db()
        student_profile = StudentProfile.objects.get(user=teacher_user)
        self.assertEqual(teacher_user.role, "student")
        self.assertEqual(student_profile.full_name, "Laura Gomez")
        self.assertEqual(student_profile.address, "Av 1")
        self.assertIsNone(teacher_profile.user)

    def test_assign_roles_rejects_non_institutional_accounts_posted_manually(self):
        local_user = User.objects.create_user(
            email="student.local@autogen.local",
            password="ClaveSegura123",
            role="student",
        )
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse("assign_roles"),
            {
                "user_id": local_user.id,
                "role": "admin",
                "search": "student.local",
            },
            follow=True,
        )

        local_user.refresh_from_db()
        self.assertEqual(local_user.role, "student")
        self.assertContains(response, "Solo se pueden gestionar cuentas institucionales")

    def test_students_view_excludes_profiles_of_users_without_student_role(self):
        self.target_user.role = "coordinator"
        self.target_user.save(update_fields=["role"])
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("students"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "ana.perez@uniminuto.edu.co")
        self.assertNotContains(response, "Ana Perez")
