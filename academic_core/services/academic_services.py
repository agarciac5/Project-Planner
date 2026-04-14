from academic_core.models import AcademicProgram, Faculty, Campus, StudyPlan


def get_programs():
    return AcademicProgram.objects.all().order_by("id")


def get_faculties():
    return Faculty.objects.select_related("campus").all()


def get_campuses():
    return Campus.objects.all()


def get_study_plans():
    return StudyPlan.objects.prefetch_related("courses").all()