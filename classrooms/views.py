from django.shortcuts import render
from .models import Classroom


def classrooms_view(request):
    classrooms = Classroom.objects.all().order_by("id")

    context = {
        "items": classrooms
    }

    return render(request, "dashboard/classrooms.html", context)



def get_classrooms():
    return Classroom.objects.all().order_by("classroom_id")