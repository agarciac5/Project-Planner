# Guia compacta - Importacion de estudiantes

## Formato del archivo

- Tipo de archivo: Excel `.xlsx`.
- La primera fila debe contener los nombres exactos de las columnas.
- Cada fila representa un estudiante.
- La columna `CORREO_ESTUDIANTE` se usa para evitar duplicados.

## Columnas requeridas

| Columna | Obligatoria | Ejemplo | Uso en el sistema |
|---|---:|---|---|
| `CORREO_ESTUDIANTE` | Si | `ana.perez@uniminuto.edu.co` | Crea o identifica el usuario estudiante. |
| `DESCRIPCION_PROGRAMA` | Si | `ingenieria de software` | Define el programa academico. |
| `DESCRIPCION_SEDE` | No | `Sede Principal` | Define o crea la sede. |
| `DESCRIPCION_FACULTAD` | No | `Facultad de Ingenieria` | Define o crea la facultad. |
| `CODIGO` | No | `EST-001` | Codigo estudiantil. |
| `TIPO_DOCUMENTO` | No | `CC` | Tipo de documento. |
| `NUM_DOCUMENTO` | No | `123456789` | Numero de documento. |
| `NOMBRES` | No | `Ana Perez` | Nombre completo del estudiante. |
| `DESCRIPCION_NIVEL` | No | `Pregrado` | Nivel academico. |
| `JORNADA` | No | `Diurna` | Jornada del estudiante. |

## Programas aceptados

El importador solo procesa estudiantes cuyo `DESCRIPCION_PROGRAMA` sea uno de estos valores:

| Programa aceptado |
|---|
| `ingenieria de software` |
| `ingenieria industrial` |

El texto se normaliza antes de validar, por lo que mayusculas y tildes no deberian afectar. Ejemplo: `Ingeniería de Software` tambien es valido.

## Reglas importantes

1. Si el correo esta vacio, la fila se omite.
2. Si el programa no es aceptado, la fila se omite.
3. Si el correo ya existe y ya tiene perfil estudiantil, la fila se omite.
4. Si el correo ya existe pero no tiene perfil, se crea el perfil para ese usuario.
5. Si `DESCRIPCION_SEDE` esta vacio, se usa `Sede sin definir`.
6. Si `DESCRIPCION_FACULTAD` esta vacio, se usa `Facultad sin definir`.
7. Si `DESCRIPCION_PROGRAMA` esta vacio, la fila no pasa la validacion de programas.
8. Si `CODIGO` esta vacio, el sistema intenta generar un codigo automaticamente.

## Ejemplo de estructura

| CORREO_ESTUDIANTE | DESCRIPCION_PROGRAMA | DESCRIPCION_SEDE | DESCRIPCION_FACULTAD | CODIGO | TIPO_DOCUMENTO | NUM_DOCUMENTO | NOMBRES | DESCRIPCION_NIVEL | JORNADA |
|---|---|---|---|---|---|---|---|---|---|
| estudiante1@uniminuto.edu.co | ingenieria de software | Sede Principal | Facultad de Ingenieria | EST-001 | CC | 123456789 | Ana Perez | Pregrado | Diurna |

## Como importar

1. Iniciar sesion como **Administrador** o **Director academico**.
2. Ir al menu **Importar**.
3. Seleccionar el archivo Excel `.xlsx`.
4. Presionar **Importar documentos**.
5. Revisar el resumen de creados, omitidos y errores.

