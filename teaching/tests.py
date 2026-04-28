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
