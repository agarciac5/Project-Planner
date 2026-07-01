# Team Members

| Name                              | Role               | Mail                     |
|-----------------------------------|--------------------|--------------------------|
| Carlos David Sanchez Soto         | Tester             | cdsanchezs@eafit.edu.co  |
| Alejandro Garcia Cortes           | Developer          | agarciac5@eafit.edu.co   |
| Dorian Alejandro Guisao Ospina    | Scrum Master       | daguisaoo@eafit.edu.co   |
| Juan Esteban Orrego Gomez         | Software Architect | jeorregog1@eafit.edu.co  |
| Sebastian Rodriguez               | Tester             | srodrigub1@eafit.edu.co  |

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
referencia; Django no carga archivos `.env` automáticamente.

## Comprobaciones antes de auditar

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test -v 2
```

Para validar una configuración de producción:

```powershell
$env:DJANGO_DEBUG = "False"
$env:DJANGO_SECRET_KEY = "una-clave-secreta-larga-y-aleatoria"
$env:DJANGO_ALLOWED_HOSTS = "planner.example.edu"
$env:DJANGO_CSRF_TRUSTED_ORIGINS = "https://planner.example.edu"
python manage.py check --deploy
```

En producción no se permite iniciar la aplicación sin `DJANGO_SECRET_KEY` y
`DJANGO_ALLOWED_HOSTS`.
