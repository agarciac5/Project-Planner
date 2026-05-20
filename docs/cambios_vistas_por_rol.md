# Cambios implementados: vistas por rol

## Objetivo
Separar las vistas de Project Planner para que cada usuario vea solamente los módulos que necesita según su rol funcional.

## Roles usados

| Rol interno | Rol funcional | Qué ve principalmente |
|---|---|---|
| `student` | Estudiante | Matrícula, mi horario, plan de estudios y perfil estudiantil. |
| `teacher` | Docente | Mi horario docente, plan de estudios y perfil. |
| `admin` | Administrador | Gestión académica base: estudiantes, docentes, programas, materias, sedes, facultades, aulas e importación. |
| `coordinator` | Director académico | Plan semestral, generación de horarios, publicación de planes y consulta de horarios. |

## Archivos principales modificados

- `access_support/role_access.py`: reglas centralizadas de roles, permisos, navegación y templates por rol.
- `access_support/context_processors.py`: expone al navbar el rol actual y los enlaces permitidos.
- `templates/base/navbar.html`: ya no muestra todos los módulos a todos los usuarios.
- `templates/dashboard/roles/*.html`: home separado para estudiante, docente, administrador y director.
- `access_support/views.py`: el dashboard redirige/renderiza según rol y las vistas administrativas tienen control de permisos.
- `academic_core/views.py`, `teaching/views.py`, `classrooms/views.py`, `scheduling_enrollment/views.py`: se agregaron restricciones por rol.
- `access_support/management/commands/create_demo_role_accounts.py`: comando para crear una cuenta demo por cada rol.
- `docs/credenciales_demo_roles.md`: credenciales de prueba.

## Cómo probar

```bash
python manage.py migrate
python manage.py create_demo_role_accounts
python manage.py runserver
```

Después entra con cada correo de `docs/credenciales_demo_roles.md` y valida que el menú cambie según el rol.
