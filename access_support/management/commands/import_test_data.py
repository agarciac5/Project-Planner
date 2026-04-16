"""
Management command para importar datos de prueba desde el Excel generado.

Uso:
    python manage.py import_test_data ruta/al/archivo.xlsx

Carga en orden:
    1. Campus
    2. Facultades
    3. Contratos
    4. Aulas
    5. Periodos académicos
    6. Profesores
    7. Disponibilidad
    8. Grupos de horario (scheduling_enrollment)
    9. Profesores extremos
   10. Disponibilidad extremos
   11. Grupos extremos
"""

import pandas as pd
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "Importar datos de prueba desde Excel para el algoritmo genético"

    def add_arguments(self, parser):
        parser.add_argument("ruta_excel", type=str, help="Ruta al archivo Excel")

    def handle(self, *args, **kwargs):
        ruta = kwargs["ruta_excel"]
        self.stdout.write(f"\n Leyendo archivo: {ruta}\n")

        xl = pd.ExcelFile(ruta)
        available_sheets = xl.sheet_names

        def read_sheet(name):
            if name not in available_sheets:
                self.stdout.write(self.style.WARNING(f"  Hoja '{name}' no encontrada — omitida"))
                return None
            return pd.read_excel(xl, sheet_name=name)

        try:
            with transaction.atomic():
                # --- Hojas base ---
                self._import_campus(read_sheet("campus"))
                self._import_faculties(read_sheet("facultades"))
                self._import_contracts(read_sheet("contratos"))
                self._import_classrooms(read_sheet("aulas"))
                self._import_terms(read_sheet("periodos"))
                self._import_teachers(read_sheet("profesores"))
                self._import_availability(read_sheet("disponibilidad"))
                self._import_course_groups(read_sheet("grupos_horario"))

                # --- Hojas de casos extremos ---
                self.stdout.write("\n Casos extremos:")
                self._import_teachers(read_sheet("profesores_extremos"), label="Profesores extremos")
                self._import_availability(read_sheet("disponibilidad_extremos"), label="Disponib. extremos")
                self._import_course_groups(read_sheet("grupos_extremos"), label="Grupos extremos")

        except Exception as e:
            self.stderr.write(f"\n Error durante la importación: {e}")
            raise

        self.stdout.write(self.style.SUCCESS("\n mportación completada correctamente.\n"))

    # ------------------------------------------------------------------
    # 1. Campus
    # ------------------------------------------------------------------
    def _import_campus(self, df):
        if df is None:
            return
        from academic_core.models import Campus
        count = 0
        for _, row in df.iterrows():
            _, created = Campus.objects.get_or_create(name=str(row["NOMBRE"]).strip())
            if created:
                count += 1
        self.stdout.write(f"  Campus:      {count} creados")

    # ------------------------------------------------------------------
    # 2. Facultades
    # ------------------------------------------------------------------
    def _import_faculties(self, df):
        if df is None:
            return
        from academic_core.models import Faculty, Campus
        count = 0
        for _, row in df.iterrows():
            campus = Campus.objects.filter(name=str(row["CAMPUS"]).strip()).first()
            _, created = Faculty.objects.get_or_create(
                name=str(row["NOMBRE"]).strip(),
                campus=campus,
            )
            if created:
                count += 1
        self.stdout.write(f"  Facultades:  {count} creadas")

    # ------------------------------------------------------------------
    # 3. Contratos
    # ------------------------------------------------------------------
    def _import_contracts(self, df):
        if df is None:
            return
        from teaching.models import ContractRule
        count = 0
        for _, row in df.iterrows():
            _, created = ContractRule.objects.update_or_create(
                contract_type=str(row["TIPO_CONTRATO"]).strip(),
                defaults={
                    "min_teaching_hours": int(row["MIN_HORAS_CLASE"]),
                    "max_teaching_hours": int(row["MAX_HORAS_CLASE"]),
                    "max_advisory_hours": int(row["MAX_HORAS_ASESORIA"]),
                    "max_research_hours": int(row["MAX_HORAS_INVESTIGACION"]),
                    "max_total_hours":    int(row["MAX_HORAS_TOTAL"]),
                },
            )
            if created:
                count += 1
        self.stdout.write(f"  Contratos:   {count} creados")

    # ------------------------------------------------------------------
    # 4. Aulas
    # ------------------------------------------------------------------
    def _import_classrooms(self, df):
        if df is None:
            return
        from classrooms.models import Classroom
        from academic_core.models import Campus
        count = 0
        for _, row in df.iterrows():
            campus = Campus.objects.filter(name=str(row["CAMPUS"]).strip()).first()
            _, created = Classroom.objects.update_or_create(
                classroom_id=str(row["CODIGO_AULA"]).strip(),
                defaults={
                    "name":           str(row["NOMBRE"]).strip(),
                    "block":          int(row["BLOQUE"]),
                    "campus":         campus,
                    "capacity":       int(row["CAPACIDAD"]),
                    "classroom_type": str(row["TIPO"]).strip(),
                    "is_active":      bool(row["ACTIVO"]),
                },
            )
            if created:
                count += 1
        self.stdout.write(f"  Aulas:       {count} creadas")

    # ------------------------------------------------------------------
    # 5. Periodos académicos
    # ------------------------------------------------------------------
    def _import_terms(self, df):
        if df is None:
            return
        from academic_core.models import AcademicTerm
        count = 0
        for _, row in df.iterrows():
            _, created = AcademicTerm.objects.update_or_create(
                name=str(row["NOMBRE"]).strip(),
                defaults={
                    "start_date": pd.to_datetime(row["FECHA_INICIO"]).date(),
                    "end_date":   pd.to_datetime(row["FECHA_FIN"]).date(),
                    "active":     bool(row["ACTIVO"]),
                },
            )
            if created:
                count += 1
        self.stdout.write(f"  Periodos:    {count} creados")

    # ------------------------------------------------------------------
    # 6 & 9. Profesores (base y extremos comparten la misma lógica)
    # ------------------------------------------------------------------
    def _import_teachers(self, df, label="Profesores"):
        if df is None:
            return
        from teaching.models import Teacher, ContractRule
        from academic_core.models import Campus
        count = 0
        for _, row in df.iterrows():
            campus   = Campus.objects.filter(name=str(row["CAMPUS"]).strip()).first()
            contract = ContractRule.objects.filter(
                contract_type=str(row["TIPO_CONTRATO"]).strip()
            ).first()

            _, created = Teacher.objects.update_or_create(
                teacher_id=str(row["ID_PROFESOR"]).strip(),
                defaults={
                    "first_name": str(row["NOMBRES"]).strip(),
                    "last_name":  str(row["APELLIDOS"]).strip(),
                    "address":    str(row["DIRECCION"]).strip(),
                    "contract":   contract,
                    "campus":     campus,
                    "is_active":  bool(row["ACTIVO"]),
                },
            )
            if created:
                count += 1
        self.stdout.write(f"  {label}:  {count} creados")

    # ------------------------------------------------------------------
    # 7 & 10. Disponibilidad (base y extremos comparten la misma lógica)
    # ------------------------------------------------------------------
    def _import_availability(self, df, label="Disponib."):
        if df is None:
            return
        from teaching.models import Teacher, Availability
        from datetime import time

        def parse_time(val):
            parts = str(val).strip().split(":")
            return time(int(parts[0]), int(parts[1]))

        count = 0
        skipped = 0
        for _, row in df.iterrows():
            teacher = Teacher.objects.filter(
                teacher_id=str(row["ID_PROFESOR"]).strip()
            ).first()
            if not teacher:
                skipped += 1
                continue

            start = parse_time(row["HORA_INICIO"])
            end   = parse_time(row["HORA_FIN"])
            day   = str(row["DIA"]).strip()

            _, created = Availability.objects.get_or_create(
                teacher=teacher,
                day=day,
                start_time=start,
                end_time=end,
            )
            if created:
                count += 1

        self.stdout.write(f"  {label}:   {count} franjas creadas  ({skipped} omitidas)")

    # ------------------------------------------------------------------
    # 8 & 11. Grupos de horario (base y extremos comparten la misma lógica)
    # ------------------------------------------------------------------
    def _import_course_groups(self, df, label="Grupos"):
        if df is None:
            return
        from scheduling_enrollment.models import CourseGroup
        from academic_core.models import Course, AcademicTerm
        from teaching.models import Teacher

        count = 0
        skipped = 0
        for _, row in df.iterrows():
            course = Course.objects.filter(
                code=str(row["CODIGO_MATERIA"]).strip()
            ).first()
            teacher = Teacher.objects.filter(
                teacher_id=str(row["ID_PROFESOR"]).strip()
            ).first()
            term = AcademicTerm.objects.filter(
                name=str(row["PERIODO"]).strip()
            ).first()

            if not course:
                self.stderr.write(
                    f"     Materia no encontrada: {row['CODIGO_MATERIA']}"
                )
                skipped += 1
                continue
            if not teacher:
                self.stderr.write(
                    f"     Profesor no encontrado: {row['ID_PROFESOR']}"
                )
                skipped += 1
                continue
            if not term:
                self.stderr.write(
                    f"     Periodo no encontrado: {row['PERIODO']}"
                )
                skipped += 1
                continue

            _, created = CourseGroup.objects.get_or_create(
                nrc=str(row["NRC"]).strip(),
                defaults={
                    "course":     course,
                    "teacher":    teacher,
                    "term":       term,
                    "capacity":   int(row["CAPACIDAD"]),
                    "is_virtual": bool(row["ES_VIRTUAL"]),
                },
            )
            if created:
                count += 1

        self.stdout.write(
            f"  {label}:      {count} creados  ({skipped} omitidos por datos faltantes)"
        )