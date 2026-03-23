from django.db import models


class CourseGroup(models.Model):
    course = models.ForeignKey("academic_core.Course", on_delete=models.CASCADE)
    teacher = models.ForeignKey(
        "teaching.Teacher", on_delete=models.SET_NULL, null=True
    )
    classroom = models.ForeignKey(
        "classrooms.Classroom", on_delete=models.SET_NULL, null=True
    )
    timeslot = models.ForeignKey(
        "classrooms.TimeSlot", on_delete=models.SET_NULL, null=True
    )

    capacity = models.IntegerField(default=30)

    def __str__(self):
        return f"{self.course} - Group {self.id}"


class EnrollmentQueue(models.Model):

    student = models.ForeignKey("access_support.User", on_delete=models.CASCADE)

    course = models.ForeignKey("academic_core.Course", on_delete=models.CASCADE)

    request_date = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
        max_length=20,
        choices=[("waiting", "Waiting"), ("enrolled", "Enrolled")],
        default="waiting",
    )

    def __str__(self):
        return f"{self.student} waiting for {self.course}"


class Schedule(models.Model):

    group = models.ForeignKey(CourseGroup, on_delete=models.CASCADE)

    published = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Schedule for {self.group}"
