from django.core.exceptions import ValidationError
from django.db import models


class Campus(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Faculty(models.Model):
    name = models.CharField(max_length=100)
    campus = models.ForeignKey(
        Campus,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="faculties",
    )

    def __str__(self):
        return self.name


class AcademicProgram(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True, blank=True, null=True)
    faculty = models.ForeignKey(
        Faculty,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="programs",
    )
    campus = models.ForeignKey(
        Campus,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="programs",
    )

    def __str__(self):
        return self.name


class AcademicTerm(models.Model):
    name = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField()
    active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_date__gt=models.F("start_date")),
                name="academic_term_dates_valid",
            ),
            models.UniqueConstraint(
                fields=["active"],
                condition=models.Q(active=True),
                name="only_one_active_academic_term",
            ),
        ]

    def clean(self):
        super().clean()
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValidationError(
                {"end_date": "La fecha final debe ser posterior a la fecha inicial."}
            )
        if self.active:
            active_terms = AcademicTerm.objects.filter(active=True)
            if self.pk:
                active_terms = active_terms.exclude(pk=self.pk)
            if active_terms.exists():
                raise ValidationError(
                    {"active": "Solo puede existir un periodo academico activo."}
                )

    def __str__(self):
        return self.name


class StudyPlan(models.Model):
    program = models.ForeignKey(
        AcademicProgram, on_delete=models.CASCADE, related_name="study_plans"
    )
    version = models.CharField(max_length=20)
    description = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["program", "version"],
                name="unique_study_plan_version_per_program",
            )
        ]

    def __str__(self):
        return f"{self.program} - Plan {self.version}"


class CourseComponent(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Course(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    credits = models.IntegerField(default=0)
    semester = models.PositiveIntegerField(default=1)
    component = models.ForeignKey(
        CourseComponent,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="courses",
    )
    study_plan = models.ForeignKey(
        StudyPlan, on_delete=models.CASCADE, related_name="courses"
    )

    def __str__(self):
        return f"{self.code} - {self.name}"


class CurriculumCourseGroup(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="groups")
    term = models.ForeignKey(
        AcademicTerm,
        on_delete=models.CASCADE,
        related_name="academic_course_groups",  # ← evita el choque
    )
    group_number = models.IntegerField()
    capacity = models.IntegerField(default=30)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["course", "term", "group_number"],
                name="unique_curriculum_group_per_term",
            ),
            models.CheckConstraint(
                condition=models.Q(capacity__gt=0),
                name="curriculum_group_capacity_positive",
            ),
        ]

    def __str__(self):
        return f"{self.course} - Group {self.group_number} ({self.term})"
