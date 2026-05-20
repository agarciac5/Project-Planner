from django import forms
from django.contrib.auth import authenticate


class EmailLoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"type": "email", "placeholder": "correo@dominio.com"})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Contrasena"})
    )

    error_messages = {
        "invalid_login": "Credenciales incorrectas",
    }

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")

        if email and password:
            user = authenticate(email=email, password=password)
            if user is None:
                raise forms.ValidationError(
                    self.error_messages["invalid_login"],
                    code="invalid_login",
                )
            cleaned_data["user"] = user

        return cleaned_data
