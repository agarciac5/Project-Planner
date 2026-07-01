from datetime import time

from django.test import TestCase
from django.urls import reverse

from access_support.models import User
from teaching.models import Availability, Teacher


class TeacherViewTest(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            email="admin-teaching@uniminuto.edu.co",
            password="ClaveSegura123",
            role="admin",
        )
        self.client.force_login(self.admin_user)

    def test_teacher_create_creates_teacher_and_initial_availability(self):
        response = self.client.post(
            reverse("teacher_create"),
            {
                "teacher_id": "DOC-001",
                "first_name": "Laura",
                "last_name": "Gomez",
                "address": "Cra 10",
                "is_active": "on",
                "day": "Monday",
                "start_time": "08:00",
                "end_time": "10:00",
            },
        )

        self.assertRedirects(response, reverse("teacher_list"))
        teacher = Teacher.objects.get(teacher_id="DOC-001")
        self.assertEqual(teacher.first_name, "Laura")
        self.assertTrue(
            Availability.objects.filter(
                teacher=teacher,
                day="Monday",
                start_time="08:00",
                end_time="10:00",
            ).exists()
        )

    def test_add_availability_ignores_incomplete_payload(self):
        teacher = Teacher.objects.create(
            teacher_id="DOC-002",
            first_name="Carlos",
            last_name="Lopez",
        )

        response = self.client.post(
            reverse("add_availability", args=[teacher.id]),
            {
                "day": "Tuesday",
                "start_time": "",
                "end_time": "11:00",
            },
        )

        self.assertRedirects(response, reverse("teacher_list"))
        self.assertFalse(Availability.objects.filter(teacher=teacher).exists())

    def test_add_availability_rejects_overlapping_slot(self):
        teacher = Teacher.objects.create(
            teacher_id="DOC-OVERLAP",
            first_name="Ana",
            last_name="Ruiz",
        )
        Availability.objects.create(
            teacher=teacher,
            day="Monday",
            start_time=time(8, 0),
            end_time=time(10, 0),
        )

        response = self.client.post(
            reverse("add_availability", args=[teacher.id]),
            {
                "day": "Monday",
                "start_time": "09:00",
                "end_time": "11:00",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Availability.objects.filter(teacher=teacher).count(), 1)
        self.assertContains(response, "se cruza con otra franja")

    def test_teacher_edit_updates_teacher_fields(self):
        teacher = Teacher.objects.create(
            teacher_id="DOC-003",
            first_name="Ana",
            last_name="Perez",
            address="Direccion antigua",
        )

        response = self.client.post(
            reverse("teacher_edit", args=[teacher.id]),
            {
                "teacher_id": "DOC-003",
                "first_name": "Ana Maria",
                "last_name": "Perez",
                "address": "Direccion nueva",
                "is_active": "on",
            },
        )

        self.assertRedirects(response, reverse("teacher_list"))
        teacher.refresh_from_db()
        self.assertEqual(teacher.first_name, "Ana Maria")
        self.assertEqual(teacher.address, "Direccion nueva")
