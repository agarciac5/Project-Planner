from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El correo es obligatorio")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("El superusuario debe tener is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("El superusuario debe tener is_superuser=True")

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)

    ROLE_CHOICES = (
        ('student', 'Estudiante'),
        ('teacher', 'Docente'),
        ('admin', 'Administrador'),
        ('coordinator', 'Coordinador'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email









class StudentProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )
    student_code = models.CharField(max_length=20, unique=True)
    document_type = models.CharField(max_length=20, blank=True, null=True)
    document_number = models.CharField(max_length=30, blank=True, null=True)
    full_name = models.CharField(max_length=120, blank=True)
    address = models.CharField(max_length=200, blank=True)

    program = models.ForeignKey(
        'academic_core.AcademicProgram',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    faculty = models.ForeignKey(
        'academic_core.Faculty',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    campus = models.ForeignKey(
        'academic_core.Campus',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    level = models.CharField(max_length=20, null=True, blank=True)
    jornada = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return f"{self.student_code} - {self.full_name or self.user.email}"