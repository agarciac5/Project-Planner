# Project Planner

Sistema Django para matrícula, planificación semestral y publicación de
horarios académicos con separación por roles e integridad de datos.

## Equipo

| Nombre | Rol | Correo |
|---|---|---|
| Carlos David Sanchez Soto | Tester | cdsanchezs@eafit.edu.co |
| Alejandro Garcia Cortes | Developer | agarciac5@eafit.edu.co |
| Dorian Alejandro Guisao Ospina | Scrum Master | daguisaoo@eafit.edu.co |
| Juan Esteban Orrego Gomez | Software Architect | jeorregog1@eafit.edu.co |
| Sebastian Rodriguez | Tester | srodrigub1@eafit.edu.co |

## Ejecución local

Requiere Python 3.12 o superior.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

La configuración se obtiene de variables de entorno. Use `.env.example` como
referencia; Django no carga ese archivo automáticamente.

## Comprobaciones

```powershell
python manage.py check
python manage.py makemigrations --check
python manage.py test
```

## Demostración local

```powershell
python manage.py create_demo_role_accounts
```

Este comando prepara cuentas y datos ficticios. Consulte
`docs/guion_demo_uniminuto.md` para el recorrido de presentación.
La instalación completa y las pruebas manuales están explicadas en
`docs/guia_instalacion_y_pruebas.md`.

Con `DJANGO_DEBUG=False` se deben definir una clave segura en
`DJANGO_SECRET_KEY` y los dominios permitidos en `DJANGO_ALLOWED_HOSTS`.
