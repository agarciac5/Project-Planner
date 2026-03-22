from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from academic_core.models import Campus


class Classroom(models.Model):
    classroom_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100, blank=True)
    block = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="bloque"
    )
    campus = models.ForeignKey(
        Campus,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    is_active = models.BooleanField(default=True, verbose_name="activo")

    def __str__(self):
        return self.classroom_id


class TimeSlot(models.Model):
    day = models.CharField(max_length=10)
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.day} {self.start_time} - {self.end_time}"