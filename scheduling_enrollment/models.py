from django.db import models


class CourseGroup(models.Model):
    course = models.ForeignKey("academic_core.Course", on_delete=models.CASCADE)
    teacher = models.ForeignKey(
        "teaching.Teacher", on_delete=models.SET_NULL, null=True, blank=True
    )
    term = models.ForeignKey(
        "academic_core.AcademicTerm", on_delete=models.SET_NULL, null=True
    )
    nrc = models.CharField(max_length=10, blank=True)
    capacity = models.IntegerField(default=40)
    is_virtual = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Grupo de horario"
        verbose_name_plural = "Grupos de horario"

    def __str__(self):
        return f"{self.course.code} - NRC {self.nrc}"


class TeacherActivity(models.Model):
    """Actividad extra del profesor: asesoría o investigación. Sin aula."""
    ACTIVITY_TYPES = [
        ("asesoria",      "Asesoría"),
        ("investigacion", "Investigación"),
    ]
    DAYS = [
        ("Monday",    "Lunes"),
        ("Tuesday",   "Martes"),
        ("Wednesday", "Miércoles"),
        ("Thursday",  "Jueves"),
        ("Friday",    "Viernes"),
        ("Saturday",  "Sábado"),
    ]
    teacher = models.ForeignKey(
        "teaching.Teacher", on_delete=models.CASCADE, related_name="activities"
    )
    term = models.ForeignKey(
        "academic_core.AcademicTerm", on_delete=models.SET_NULL, null=True
    )
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    day = models.CharField(max_length=10, choices=DAYS)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        verbose_name = "Actividad docente"
        verbose_name_plural = "Actividades docentes"

    @property
    def duration_hours(self):
        from datetime import datetime
        s = datetime.combine(datetime.today(), self.start_time)
        e = datetime.combine(datetime.today(), self.end_time)
        return round((e - s).total_seconds() / 3600, 2)

    def __str__(self):
        return (f"{self.teacher} — {self.get_activity_type_display()} "
                f"{self.get_day_display()} {self.start_time:%H:%M}-{self.end_time:%H:%M}")


class ProposedSchedule(models.Model):
    STATUS_CHOICES = [
        ("draft",    "Borrador"),
        ("approved", "Aprobado"),
        ("rejected", "Rechazado"),
    ]
    teacher = models.ForeignKey(
        "teaching.Teacher", on_delete=models.CASCADE, related_name="proposed_schedules"
    )
    term = models.ForeignKey(
        "academic_core.AcademicTerm", on_delete=models.SET_NULL, null=True
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    fitness_score = models.FloatField(default=0.0)
    rank = models.PositiveSmallIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Horario #{self.rank} {self.teacher} - {self.term} ({self.status})"


class ScheduleSession(models.Model):
    DAYS = [
        ("Monday",    "Lunes"),
        ("Tuesday",   "Martes"),
        ("Wednesday", "Miércoles"),
        ("Thursday",  "Jueves"),
        ("Friday",    "Viernes"),
        ("Saturday",  "Sábado"),
    ]
    schedule = models.ForeignKey(
        ProposedSchedule, on_delete=models.CASCADE, related_name="sessions"
    )
    group = models.ForeignKey(
        CourseGroup, on_delete=models.CASCADE, related_name="sessions"
    )
    classroom = models.ForeignKey(
        "classrooms.Classroom", on_delete=models.SET_NULL, null=True, blank=True
    )
    day = models.CharField(max_length=10, choices=DAYS)
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.group} - {self.day} {self.start_time}-{self.end_time}"


class EnrollmentQueue(models.Model):
    student = models.ForeignKey("access_support.User", on_delete=models.CASCADE)
    course = models.ForeignKey("academic_core.Course", on_delete=models.CASCADE)
    course_group = models.ForeignKey(
        "scheduling_enrollment.CourseGroup",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="student_enrollments",
    )
    term = models.ForeignKey(
        "academic_core.AcademicTerm",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="enrollment_requests",
    )
    request_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[("waiting", "Waiting"), ("enrolled", "Enrolled")],
        default="waiting",
    )

    def __str__(self):
        return f"{self.student} waiting for {self.course}"


class SemesterScheduleRun(models.Model):
    STATUS_CHOICES = [
        ("draft", "Borrador"),
        ("saved", "Guardado"),
        ("applied", "Aplicado"),
    ]

    term = models.ForeignKey(
        "academic_core.AcademicTerm",
        on_delete=models.CASCADE,
        related_name="semester_schedule_runs",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Plan semestral {self.term} - {self.created_at:%Y-%m-%d %H:%M}"


class SemesterScheduleOption(models.Model):
    run = models.ForeignKey(
        SemesterScheduleRun,
        on_delete=models.CASCADE,
        related_name="options",
    )
    rank = models.PositiveSmallIntegerField(default=1)
    score = models.FloatField(default=0.0)
    demand_covered = models.PositiveIntegerField(default=0)
    demand_total = models.PositiveIntegerField(default=0)
    sections_opened = models.PositiveIntegerField(default=0)
    is_best = models.BooleanField(default=False)
    selected = models.BooleanField(default=False)
    applied = models.BooleanField(default=False)
    summary = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["rank", "-score"]
        unique_together = ("run", "rank")

    def __str__(self):
        return f"Opcion {self.rank} - {self.run.term} ({self.score:.2f})"


class SemesterScheduleAssignment(models.Model):
    option = models.ForeignKey(
        SemesterScheduleOption,
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    course = models.ForeignKey("academic_core.Course", on_delete=models.CASCADE)
    teacher = models.ForeignKey(
        "teaching.Teacher",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    classroom = models.ForeignKey(
        "classrooms.Classroom",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    generated_group = models.ForeignKey(
        CourseGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="semester_assignments",
    )
    generated_schedule = models.ForeignKey(
        ProposedSchedule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="semester_assignments",
    )
    section_number = models.PositiveSmallIntegerField(default=1)
    nrc = models.CharField(max_length=20, blank=True)
    day = models.CharField(max_length=10, choices=ScheduleSession.DAYS)
    start_time = models.TimeField()
    end_time = models.TimeField()
    students_assigned = models.PositiveSmallIntegerField(default=0)
    capacity = models.PositiveSmallIntegerField(default=20)

    class Meta:
        ordering = ["course__code", "section_number"]

    def __str__(self):
        return (
            f"{self.course.code} - Sec {self.section_number} "
            f"{self.day} {self.start_time}-{self.end_time}"
        )
