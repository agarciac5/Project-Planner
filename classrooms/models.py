from django.db import models

class ClassroomManagement(models.Model):
    classroom_id = models.CharField(max_length=20, unique=True)
    capacity = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)


class TimeSlot(models.Model):
    day = models.CharField(max_length=10)
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.day} {self.start_time} - {self.end_time}"