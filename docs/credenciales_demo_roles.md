# Credenciales demo por rol

Estas cuentas son solo para probar las vistas separadas por rol en ambiente local. No deben usarse en producción y las contraseñas deben cambiarse antes de una entrega real.

| Rol | Correo | Contraseña |
|---|---|---|
| Estudiante | `estudiante.demo@uniminuto.edu.co` | `Estudiante2026!` |
| Docente | `docente.demo@uniminuto.edu.co` | `Docente2026!` |
| Administrador | `admin.demo@uniminuto.edu.co` | `Admin2026!` |
| Director académico | `director.demo@uniminuto.edu.co` | `Director2026!` |

## Cómo crearlas en la base local

```bash
python manage.py migrate
python manage.py create_demo_role_accounts
```
