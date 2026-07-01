# Guion breve de demostración

Duración recomendada: 8 a 10 minutos.

## Preparación

```powershell
python manage.py migrate
python manage.py create_demo_role_accounts
python manage.py runserver
```

Las credenciales están en `docs/credenciales_demo_roles.md`.

## Recorrido

1. Ingresar como estudiante y mostrar las materias disponibles y la solicitud
   de matrícula.
2. Ingresar como administrador y mostrar estudiantes, docentes, aulas y datos
   académicos.
3. Generar el plan para el periodo `2026-2 Demo`.
4. Comparar las alternativas, seleccionar una y aplicarla.
5. Ingresar como director académico y publicar el horario.
6. Volver a ingresar como estudiante o docente para mostrar el horario
   publicado.

## Mensaje principal

Project Planner reúne matrícula, disponibilidad docente, capacidad de aulas y
planificación semestral en un solo flujo con permisos separados por rol.

## Antes de presentar

- Usar solamente información ficticia.
- Abrir previamente las pantallas que se mostrarán.
- Conservar `db.sqlite3.bak` como copia del estado inicial de la demostración.
- No usar estas contraseñas fuera del entorno local.
