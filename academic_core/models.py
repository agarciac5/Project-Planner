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

    def __str__(self):
        return self.name


class StudyPlan(models.Model):
    program = models.ForeignKey(
        AcademicProgram, on_delete=models.CASCADE, related_name="study_plans"
    )
    version = models.CharField(max_length=20)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.program} - Plan {self.version}"


class Course(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    credits = models.IntegerField(default=0)
    semester = models.PositiveIntegerField(default=1)

    study_plan = models.ForeignKey(
        StudyPlan, on_delete=models.CASCADE, related_name="courses"
    )

    def __str__(self):
        return f"{self.code} - {self.name}"


class CourseGroup(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="groups")
    term = models.ForeignKey(AcademicTerm, on_delete=models.CASCADE)
    group_number = models.IntegerField()
    capacity = models.IntegerField(default=30)

    def __str__(self):
        return f"{self.course} - Group {self.group_number} ({self.term})"
