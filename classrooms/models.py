# classrooms/models.py

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from academic_core.models import Campus


class Classroom(models.Model):
    CLASSROOM_TYPES = [
        ("SALON", "Salón"),
        ("SISTEMAS", "Aula de Sistemas"),
        ("LAB", "Laboratorio"),
        ("AUDITORIO", "Auditorio"),
        ("VIRTUAL", "Virtual"),
    ]

    classroom_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100, blank=True)
    block = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="bloque"
    )
    campus = models.ForeignKey(
        Campus, on_delete=models.SET_NULL, null=True, blank=True
    )
    capacity = models.PositiveSmallIntegerField(default=40)
    classroom_type = models.CharField(
        max_length=20, choices=CLASSROOM_TYPES, default="SALON"
    )
    is_active = models.BooleanField(default=True, verbose_name="activo")

    def __str__(self):
        return f"{self.classroom_id} ({self.get_classroom_type_display()})"


class TimeSlot(models.Model):
    """Franja horaria predefinida institucional."""
    DAYS = [
        ("Monday", "Lunes"),
        ("Tuesday", "Martes"),
        ("Wednesday", "Miércoles"),
        ("Thursday", "Jueves"),
        ("Friday", "Viernes"),
        ("Saturday", "Sábado"),
    ]

    day = models.CharField(max_length=10, choices=DAYS)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        unique_together = ("day", "start_time", "end_time")
        ordering = ["day", "start_time"]

    def __str__(self):
        return f"{self.get_day_display()} {self.start_time}-{self.end_time}"