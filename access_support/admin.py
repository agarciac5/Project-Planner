from django.contrib import admin
from .models import StudentProfile, User

admin.site.register(User)
admin.site.register(StudentProfile)
