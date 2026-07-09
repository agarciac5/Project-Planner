from django import forms
from academic_core.models import Campus, Faculty, AcademicProgram, Course, StudyPlan
from teaching.models import Teacher
from classrooms.models import Classroom
from .models import StudentProfile, User

INSTITUTIONAL_EMAIL_DOMAIN = "@uniminuto.edu.co"


class CampusForm(forms.ModelForm):
    class Meta:
        model = Campus
        fields = ["name"]


class FacultyForm(forms.ModelForm):
    class Meta:
        model = Faculty
        fields = ["name", "campus"]


class AcademicProgramForm(forms.ModelForm):
    class Meta:
        model = AcademicProgram
        fields = ["name", "code", "faculty", "campus"]


class StudyPlanForm(forms.ModelForm):
    class Meta:
        model = StudyPlan
        fields = ["program", "version", "description"]


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ["name", "code", "credits", "semester", "study_plan"]


class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = [
            "teacher_id",
            "first_name",
            "last_name",
            "address",
            "program",
            "faculty",
            "campus",
            "contract",        # reemplaza type_of_contract
            "qualified_courses",
            "is_active",
        ]


class ClassroomForm(forms.ModelForm):
    class Meta:
        model = Classroom
        fields = [
            "classroom_id",
            "name",
            "block",
            "campus",
            "capacity",
            "classroom_type",
            "is_active",
        ]
        labels = {
            "classroom_id": "Código aula",
            "name": "Nombre",
            "block": "Bloque",
            "campus": "Sede",
            "capacity": "Capacidad",
            "classroom_type": "Tipo de aula",
            "is_active": "Activo",
        }


class StudentForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = [
            "full_name",
            "document_type",
            "document_number",
            "student_code",
            "address",
            "program",
            "faculty",
            "campus",
            "level",
            "jornada",
        ]
        labels = {
            "level": "Pregrado",
        }


class StudentSelfProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ["address"]
        labels = {
            "address": "Direccion",
        }


class StudentSelfProfileCreateForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = [
            "full_name",
            "document_type",
            "document_number",
            "program",
            "faculty",
            "campus",
            "level",
            "jornada",
            "address",
        ]
        labels = {
            "full_name": "Nombre completo",
            "document_type": "Tipo de documento",
            "document_number": "Numero de documento",
            "program": "Programa",
            "faculty": "Facultad",
            "campus": "Sede",
            "level": "Pregrado",
            "jornada": "Jornada",
            "address": "Direccion",
        }


class StudentSelfReadonlyForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = [
            "full_name",
            "document_type",
            "document_number",
            "program",
            "faculty",
            "campus",
            "level",
            "jornada",
        ]
        labels = {
            "full_name": "Nombre completo",
            "document_type": "Tipo de documento",
            "document_number": "Numero de documento",
            "address": "Direccion",
            "program": "Programa",
            "faculty": "Facultad",
            "campus": "Sede",
            "level": "Pregrado",
            "jornada": "Jornada",
        }


class TeacherSelfProfileForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = ["address"]
        labels = {
            "address": "Direccion",
        }


class TeacherSelfReadonlyForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = [
            "teacher_id",
            "first_name",
            "last_name",
            "program",
            "faculty",
            "campus",
            "contract",
            "is_active",
        ]
        labels = {
            "teacher_id": "Codigo docente",
            "first_name": "Nombres",
            "last_name": "Apellidos",
            "program": "Programa",
            "faculty": "Facultad",
            "campus": "Sede",
            "contract": "Contrato",
            "is_active": "Activo",
        }


class UserRoleSearchForm(forms.Form):
    email_query = forms.CharField(
        required=False,
        label="Correo institucional del usuario",
        widget=forms.TextInput(
            attrs={
                "class": "search-input",
                "placeholder": "Ej. ana@uniminuto.edu.co o solo ana",
            }
        ),
    )

    def clean_email_query(self):
        return self.cleaned_data["email_query"].strip().lower()


class UserRoleAssignmentForm(forms.Form):
    user_id = forms.IntegerField(widget=forms.HiddenInput)
    search = forms.CharField(required=False, widget=forms.HiddenInput)
    role = forms.ChoiceField(
        choices=User.ROLE_CHOICES,
        label="Rol",
        widget=forms.Select(attrs={"class": "search-input"}),
    )

    def __init__(self, *args, actor=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.actor = actor
        actor_can_manage_coordinators = bool(
            actor
            and actor.is_authenticated
            and (actor.is_superuser or actor.role == "coordinator")
        )
        if not actor_can_manage_coordinators and not self.is_bound:
            self.fields["role"].choices = [
                choice
                for choice in User.ROLE_CHOICES
                if choice[0] != "coordinator"
            ]

    def clean_user_id(self):
        user_id = self.cleaned_data["user_id"]
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist as exc:
            raise forms.ValidationError("El usuario seleccionado ya no existe.") from exc
        if not user.email.lower().endswith(INSTITUTIONAL_EMAIL_DOMAIN):
            raise forms.ValidationError(
                "Solo se pueden gestionar cuentas institucionales (@uniminuto.edu.co)."
            )
        if user.is_superuser and not getattr(self.actor, "is_superuser", False):
            raise forms.ValidationError(
                "Solo otro superusuario puede modificar esta cuenta."
            )
        if (
            user.role == "coordinator"
            and not getattr(self.actor, "is_superuser", False)
            and getattr(self.actor, "role", None) != "coordinator"
        ):
            raise forms.ValidationError(
                "Solo un director academico puede modificar a otro director."
            )
        return user

    def clean_role(self):
        role = self.cleaned_data["role"]
        allowed_roles = {value for value, _ in User.ROLE_CHOICES}
        if role not in allowed_roles:
            raise forms.ValidationError("Selecciona un rol valido.")
        if (
            role == "coordinator"
            and not getattr(self.actor, "is_superuser", False)
            and getattr(self.actor, "role", None) != "coordinator"
        ):
            raise forms.ValidationError(
                "Solo un director academico puede asignar el rol de director."
            )
        return role

    def get_user(self):
        return self.cleaned_data["user_id"]
