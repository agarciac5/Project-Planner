from datetime import time

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from access_support.models import User
from classrooms.models import Classroom, TimeSlot


class ClassroomCrudViewTest(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            email="admin-classrooms@uniminuto.edu.co",
            password="ClaveSegura123",
            role="admin",
        )
        self.client.force_login(self.admin_user)

    def test_classroom_create_persists_valid_classroom(self):
        response = self.client.post(
            reverse("classroom_create"),
            {
                "classroom_id": "A-101",
                "name": "Aula 101",
                "block": 2,
                "capacity": 35,
                "classroom_type": "SALON",
                "is_active": "on",
            },
        )

        self.assertRedirects(
            response,
            reverse("classroom_list"),
            fetch_redirect_response=False,
        )
        self.assertTrue(Classroom.objects.filter(classroom_id="A-101").exists())

    def test_classroom_create_rejects_block_out_of_range(self):
        response = self.client.post(
            reverse("classroom_create"),
            {
                "classroom_id": "A-999",
                "name": "Aula invalida",
                "block": 8,
                "capacity": 20,
                "classroom_type": "SALON",
                "is_active": "on",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Classroom.objects.filter(classroom_id="A-999").exists())
        self.assertFormError(
            response.context["form"],
            "block",
            "Ensure this value is less than or equal to 5.",
        )

    def test_timeslot_end_must_follow_start(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            TimeSlot.objects.create(
                day="Monday",
                start_time=time(10, 0),
                end_time=time(9, 0),
            )
