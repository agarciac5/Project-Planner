# Guía de instalación y pruebas de Project Planner

Esta guía parte de un computador Windows sin el proyecto instalado.

## 1. Programas necesarios

Instale:

- Git para Windows: <https://git-scm.com/download/win>
- Python 3.12 de 64 bits: <https://www.python.org/downloads/>

Durante la instalación de Python marque la opción **Add Python to PATH**.

Abra PowerShell y verifique:

```powershell
git --version
python --version
```

Si `python` no se reconoce, cierre PowerShell, reinstale Python marcando
**Add Python to PATH** y vuelva a abrir la terminal. En instalaciones que
incluyen el lanzador de Windows también puede usar `py -3.12`.

## 2. Descargar el proyecto

```powershell
cd $HOME\Desktop
git clone https://github.com/agarciac5/Project-Planner.git
cd Project-Planner
```

Si ya tiene la carpeta del proyecto, abra PowerShell dentro de ella y omita
este paso.

## 3. Crear el entorno e instalar los requisitos

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip check
```

El inicio de la línea debe mostrar `(.venv)`. `pip check` debe responder
`No broken requirements found`.

## 4. Crear la base y los datos de demostración

```powershell
python manage.py migrate
python manage.py create_demo_role_accounts
python manage.py check
```

Resultados esperados:

- Todas las migraciones terminan en `OK`.
- Se crean cuentas y datos demo.
- La última comprobación indica `System check identified no issues`.

## 5. Ejecutar la aplicación

```powershell
python manage.py runserver
```

Abra <http://127.0.0.1:8000/>. Mantenga PowerShell abierto mientras utiliza
la aplicación. Para detenerla presione `Ctrl+C`.

## 6. Cuentas de prueba

| Rol | Correo | Contraseña |
|---|---|---|
| Estudiante | `estudiante.demo@uniminuto.edu.co` | `Estudiante2026!` |
| Docente | `docente.demo@uniminuto.edu.co` | `Docente2026!` |
| Administrador | `admin.demo@uniminuto.edu.co` | `Admin2026!` |
| Director académico | `director.demo@uniminuto.edu.co` | `Director2026!` |

Estas cuentas son exclusivamente locales.

## 7. Prueba completa del planificador

1. Ingrese como administrador o director académico.
2. Abra **Plan semestral**.
3. Seleccione `2026-2 Demo`.
4. Pulse **Generar plan semestral**.
5. Compruebe que aparecen tres alternativas, 16 de 16 solicitudes cubiertas,
   dos grupos y cero conflictos duros.
6. En la mejor alternativa pulse **Elegir esta opción** y confirme.
7. Pulse **Aplicar esta opción** y confirme.
8. Compruebe que aparecen 16 estudiantes asignados, cero pendientes y el
   estado `Listo para emitir`.
9. Ingrese como director académico y pulse **Publicar horarios**.
10. Ingrese como estudiante y revise **Mi horario**.
11. Ingrese como docente y revise **Mi horario docente**.

## 8. Qué comprobar en cada rol

### Estudiante

- El inicio muestra su nombre, programa y materias.
- Puede abrir Matrícula, Mi horario, Plan de estudios y Perfil estudiantil.
- No aparecen opciones administrativas.

### Docente

- El inicio muestra su perfil docente.
- Puede consultar Mi horario docente, Plan de estudios y Perfil.
- No puede administrar usuarios ni publicar planes.

### Administrador

- Puede consultar materias, docentes, estudiantes, programas, aulas e
  importación.
- Puede gestionar roles, pero no asignar el rol de director académico.
- Puede generar, seleccionar y aplicar un plan.

### Director académico

- Puede generar, aplicar, revertir y publicar planes.
- Puede consultar horarios docentes y estudiantiles.
- Un plan publicado no puede eliminarse ni revertirse.

## 9. Probar la importación de Excel

El archivo debe ser `.xlsx` y contener estas columnas:

```text
CORREO_ESTUDIANTE
DESCRIPCION_PROGRAMA
DESCRIPCION_SEDE
DESCRIPCION_FACULTAD
CODIGO
TIPO_DOCUMENTO
NUM_DOCUMENTO
NOMBRES
DESCRIPCION_NIVEL
JORNADA
```

Use correos terminados en `@uniminuto.edu.co`. Pruebe también subir un `.csv`
o un Excel sin columnas obligatorias: la aplicación debe rechazarlo sin crear
estudiantes.

## 10. Ejecutar todas las pruebas automáticas

Detenga el servidor con `Ctrl+C` y ejecute:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

El resultado esperado actualmente es:

```text
Found 56 test(s).
Ran 56 tests
OK
```

## 11. Reiniciar solamente la demostración local

Esto borra la base local. No lo haga sobre una base con información real.

```powershell
Copy-Item .\db.sqlite3 .\db.sqlite3.antes-del-reinicio.bak
Remove-Item .\db.sqlite3
python manage.py migrate
python manage.py create_demo_role_accounts
```

## 12. Problemas frecuentes

### `python` no se reconoce

Reinstale Python 3.12 y marque **Add Python to PATH**. Cierre y vuelva a abrir
PowerShell. Si `py -3.12 --version` funciona, puede sustituir `python` por
`py -3.12` solamente al crear el entorno.

### PowerShell no permite activar el entorno

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### El puerto 8000 está ocupado

```powershell
python manage.py runserver 8001
```

Luego abra <http://127.0.0.1:8001/>.

### Aparece una migración pendiente

```powershell
python manage.py migrate
```

### No puede iniciar sesión después de varios intentos fallidos

Espere 15 minutos o reinicie el servidor local. El bloqueo protege contra
intentos repetidos.

### Restaurar la copia inicial preparada

Con el servidor detenido:

```powershell
Copy-Item .\db.sqlite3.bak .\db.sqlite3 -Force
```

## 13. Importante

Este procedimiento deja el proyecto listo para desarrollo y demostración
local. Una instalación institucional requiere HTTPS, secretos propios,
dominio autorizado, respaldo administrado y revisión de infraestructura por
UNIMINUTO.
