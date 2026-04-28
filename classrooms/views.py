from django.shortcuts import render

from access_support.role_access import ACADEMIC_MANAGEMENT_ROLES, roles_required
from .models import Classroom


@roles_required(*ACADEMIC_MANAGEMENT_ROLES)
def classrooms_view(request):
    classrooms = Classroom.objects.select_related("campus").order_by("id")
    return render(request, "dashboard/classrooms.html", {"items": classrooms})


def get_classrooms():
    return Classroom.objects.all().order_by("classroom_id")
