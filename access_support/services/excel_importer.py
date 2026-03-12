import pandas as pd
import random
import string
from access_support.models import User, StudentProfile
from academic_core.models import AcademicProgram

def generate_random_password(length=8):
    """Genera una contraseña aleatoria"""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def import_excel_users(file):
    df = pd.read_excel(file)

    with open("usuarios_generados.txt", "w") as f:
        for _, row in df.iterrows():
           
            email = row["CORREO_ESTUDIANTE"]
            name = row["NOMBRES"]

           
            user, created = User.objects.get_or_create(
                email=email,
                defaults={"first_name": name}
            )

            if created:
                password = generate_random_password()
                user.set_password(password)
                user.save()
               
                f.write(f"{email} | {row['CODIGO']} | {password}\n")
            else:
                
                password = None

      
            program_code = row["CODIGO_PROGRAMA_1"]
            program_name = row["DESCRIPCION_PROGRAMA"]
            program, _ = AcademicProgram.objects.get_or_create(
                code=program_code,
                defaults={"name": program_name}
            )

       
            StudentProfile.objects.update_or_create(
                user=user,
                defaults={
                    "student_code": row["CODIGO"],
                    "document_type": row["TIPO_DOCUMENTO"],
                    "document_number": row["NUM_DOCUMENTO"],
                    "program": program,
                    "level": row.get("DESCRIPCION_NIVEL", ""),
                    "jornada": row.get("JORNADA", ""),
                }
            )