from django.core.exceptions import ValidationError
from django.db import models
from academic_core.models import AcademicProgram, Faculty, Campus


class ContractRule(models.Model):
    """Define los límites de horas por tipo de contrato sin hardcodear."""
    contract_type = models.CharField(max_length=20, unique=True)
    min_teaching_hours = models.PositiveSmallIntegerField()
    max_teaching_hours = models.PositiveSmallIntegerField()
    max_advisory_hours = models.PositiveSmallIntegerField(default=0)
    max_research_hours = models.PositiveSmallIntegerField(default=0)
    max_total_hours = models.PositiveSmallIntegerField()

    def __str__(self):
        return self.contract_type


class Teacher(models.Model):
    user = models.OneToOneField(
        "access_support.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="teacher_profile",
    )
    teacher_id = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    address = models.CharField(max_length=200, blank=True)
    program = models.ForeignKey(
        AcademicProgram, on_delete=models.SET_NULL, null=True, blank=True
    )
    faculty = models.ForeignKey(
        Faculty, on_delete=models.SET_NULL, null=True, blank=True
    )
    campus = models.ForeignKey(
        Campus, on_delete=models.SET_NULL, null=True, blank=True
    )
    contract = models.ForeignKey(
        ContractRule, on_delete=models.SET_NULL, null=True, blank=True
    )
    qualified_courses = models.ManyToManyField(
        "academic_core.Course",
        blank=True,
        related_name="qualified_teachers"
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.teacher_id} - {self.first_name} {self.last_name}"


class Availability(models.Model):
    DAYS_OF_WEEK = [
        ("Monday", "Lunes"),
        ("Tuesday", "Martes"),
        ("Wednesday", "Miércoles"),
        ("Thursday", "Jueves"),
        ("Friday", "Viernes"),
        ("Saturday", "Sábado"),
        ("Sunday", "Domingo"),
    ]

    teacher = models.ForeignKey(
        Teacher, on_delete=models.CASCADE, related_name="availabilities"
    )
    day = models.CharField(max_length=10, choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        unique_together = ("teacher", "day", "start_time", "end_time")
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_time__gt=models.F("start_time")),
                name="availability_end_after_start",
            )
        ]

    def clean(self):
        super().clean()
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError(
                {"end_time": "La hora final debe ser posterior a la hora inicial."}
            )
        if self.teacher_id and self.day and self.start_time and self.end_time:
            overlaps = Availability.objects.filter(
                teacher_id=self.teacher_id,
                day=self.day,
                start_time__lt=self.end_time,
                end_time__gt=self.start_time,
            )
            if self.pk:
                overlaps = overlaps.exclude(pk=self.pk)
            if overlaps.exists():
                raise ValidationError(
                    "La disponibilidad se cruza con otra franja del docente."
                )

    def __str__(self):
        return f"{self.teacher} - {self.day} ({self.start_time}-{self.end_time})"
