from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    username = None  # remove username
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email


class StudentProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    student_code = models.CharField(max_length=20, unique=True)
    document_type = models.CharField(max_length=20)
    document_number = models.CharField(max_length=30)

    program = models.ForeignKey(
        'academic_core.AcademicProgram',
        on_delete=models.SET_NULL,
        null=True
    )

    level = models.CharField(max_length=20, null=True, blank=True)
    jornada = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return f"{self.student_code} - {self.user.email}"