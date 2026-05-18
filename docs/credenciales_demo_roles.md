# Credenciales demo por rol

Estas cuentas son solo para probar las vistas separadas por rol en ambiente local.
No deben usarse en produccion y las contrasenas deben cambiarse antes de una entrega real.

| Rol | Correo | Contrasena |
|---|---|---|
| Estudiante | `estudiante.demo@uniminuto.edu.co` | `Estudiante2026!` |
| Docente | `docente.demo@uniminuto.edu.co` | `Docente2026!` |
| Administrador | `admin.demo@uniminuto.edu.co` | `Admin2026!` |
| Director academico | `director.demo@uniminuto.edu.co` | `Director2026!` |

## Como crearlas en la base local

```bash
python manage.py migrate
python manage.py create_demo_role_accounts
```