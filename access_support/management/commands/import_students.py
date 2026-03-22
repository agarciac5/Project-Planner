import pandas as pd
from django.core.management.base import BaseCommand
from access_support.models import User, StudentProfile
import random
import string


def generar_password(longitud=10):
    caracteres = string.ascii_letters + string.digits
    return ''.join(random.sample(caracteres, longitud))


class Command(BaseCommand):
    help = 'Importar estudiantes desde Excel'

    def add_arguments(self, parser):
        parser.add_argument('ruta_excel', type=str)

    def handle(self, *args, **kwargs):
        ruta = kwargs['ruta_excel']
        df = pd.read_excel(ruta)

        emails_procesados = set()

        for _, row in df.iterrows():
            email = str(row['CORREO_ESTUDIANTE']).strip().lower()

            if not email or email == 'nan':
                continue


            if email in emails_procesados:
                continue

            if User.objects.filter(email=email).exists():
                continue

            password = generar_password()

            user = User.objects.create_user(
                email=email,
                password=password,
                role='student'
            )

            StudentProfile.objects.create(
                user=user,
                student_code=str(row['CODIGO']),
                document_type=str(row['TIPO_DOCUMENTO']),
                document_number=str(row['NUM_DOCUMENTO']),
                full_name=str(row['NOMBRES'])
            )

            with open('credenciales_estudiantes.txt', 'a') as f:
                f.write(f"{email},{password}\n")

            emails_procesados.add(email)

            print(f"Usuario creado: {email}")

        print("Importación finalizada")