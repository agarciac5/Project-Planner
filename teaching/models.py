from django.db import models
from classrooms.models import Classroom, TimeSlot
from django.core.validators import MinValueValidator, MaxValueValidator

class Teacher(models.Model):
    CONTRACT_TYPES = [
        ('Full-Time', 'Full-Time'),
        ('Half-Time', 'Half-Time'),
    ]

    HOURS_BY_CONTRACT = {
        'Full-Time': (10,20),
        'Half-Time': (5,10),
    }






    teacher_id = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    type_of_contract = models.CharField(max_length=20 
                                        , choices=CONTRACT_TYPES, default='Full-Time')

    is_active = models.BooleanField(default=True)

    @property
    def min_hours_per_week(self):
        return self.HOURS_BY_CONTRACT[self.type_of_contract][0]
    @property
    def max_hours_per_week(self):
        return self.HOURS_BY_CONTRACT[self.type_of_contract][1]
    def __str__(self):
        return f"{self.teacher_id} - {self.first_name} {self.last_name}"




class Availability(models.Model):
    DAYS_OF_WEEK = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ]

    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='availabilities')
    day = models.CharField(max_length=10, choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:  #Avoid duplicate entries for the same teacher and time slot
        unique_together = ('teacher', 'day', 'start_time', 'end_time') 



    def __str__(self):
        return f"{self.teacher} - {self.day} ({self.start_time}-{self.end_time})"
    

