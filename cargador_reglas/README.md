# Administrador del repositorio de reglas — 1.0.0

Programa independiente para que los administradores carguen sentencias SQL desde Excel al repositorio PostgreSQL. No necesita QGIS y no lleva usuarios ni contraseñas incorporados.

## Inicio en Windows

1. Descomprima **todo el ZIP** en una carpeta local. No ejecute los archivos directamente desde el ZIP.
2. Instale Python 3.11 o superior desde https://www.python.org/downloads/windows/ si no lo tiene, incluido el lanzador `py` y Tkinter. El código admite Python 3.9 o superior.
3. Ejecute `instalar_windows.bat` una sola vez. Crea un entorno `.venv` dentro de esta carpeta e instala las dos dependencias. Este paso necesita Internet.
4. Abra `iniciar_windows.bat` cada vez que vaya a usar el programa.

Esta distribución es un programa Python con lanzador para Windows; no es un `.exe`. No necesita Microsoft Excel instalado para leer el archivo `.xlsx`.

## Uso

1. Indique servidor, puerto, base de datos, usuario administrador y contraseña. La base propuesta es `sentencias`. Pulse **Probar conexión**.
2. Seleccione la tabla de destino del esquema `public`.
3. Use **Guardar plantilla vacía** o **Exportar todas las reglas**. La exportación incluye todas las filas, también las reglas inactivas y las versiones no publicadas.
4. Diligencie la hoja **Reglas**, una fila por regla. La hoja **Ejemplo** no se importa. Puede usar una plantilla anterior si conserva los mismos encabezados.
5. Pulse **Seleccionar Excel y revisar**. Revise las filas, el SQL y la pestaña **Todos los campos**, que muestra también los metadatos de publicación que se guardarán.
6. Pulse **Cargar reglas nuevas**. Confirme el servidor, la base, la tabla y la cantidad que muestra la ventana.

Se incorporan todos los registros nuevos válidos, incluidos los que tengan `activa = No`. Las reglas existentes se conservan; este programa no las actualiza ni elimina. Los errores y el resumen quedan visibles en **Actividad y mensajes**.

## Campos de la plantilla

`version`, `componente`, `codigo_regla`, `tipo`, `sentencia_sql`, `descripcion_regla`, `activa`, `orden`, `descripcion_version` y `version_publicada`.

- Conserve como texto los códigos y las versiones para no perder ceros iniciales.
- Pegue cada consulta completa en una celda de `sentencia_sql`, con sus saltos de línea. No agregue un `INSERT INTO` ni delimitadores `$regla$` alrededor de la consulta.
- Use `{esquema}.tabla` para las reglas que deban consultar las fuentes elegidas por el validador, incluidas las temporales.
- `tipo`: CONTROL o REPORTE_GENERAL. `activa`: Sí o No. `orden`: entero desde cero.
- Las consultas CONTROL deben devolver únicamente las inconsistencias. El cargador las almacena como texto; no ejecuta el SQL ni comprueba su sintaxis.
- La clave de coincidencia es `version + componente + codigo_regla`. Los duplicados dentro del archivo impiden la carga completa. Las reglas ya existentes se muestran en la vista previa, pero no se reemplazan.
- Las versiones existentes mantienen su descripción y publicación actuales. Una versión nueva se guarda sin publicar cuando `version_publicada` queda vacío. Los metadatos repetidos de una versión nueva deben coincidir.
- En SNC solo puede existir una versión publicada con reglas activas. Las versiones pueden identificarse por fecha. Si se declara explícitamente un prefijo V2 o V3, debe corresponder a la tabla de destino.
- Excel admite hasta 32.767 caracteres por celda. El programa rechaza una exportación que exceda ese tamaño para evitar truncar el SQL.

Los diez campos son los definidos para las reglas del validador. El programa no es un importador de cualquier tabla ni crea estructuras. Otros campos técnicos de la tabla, si existen, deben poder completarse con sus valores por defecto.

## Destinos admitidos

- public.reglas_cargue_snc_cica
- public.reglas_cargue_snc_xtf
- public.reglas_cica_v2_29_07_2024
- public.reglas_cica_v3_07_09_2026
- public.reglas_interno_v2_29_07_2024
- public.reglas_interno_v3_07_09_2026

Las tablas deben existir con sus columnas de reglas y metadatos. La cuenta utilizada debe tener permisos para consultar, insertar y bloquear la tabla durante la transacción. El programa no concede permisos ni utiliza las credenciales internas del plugin.

## Operación y credenciales

- El usuario y la contraseña se introducen por sesión. La contraseña aparece oculta y no se guarda en archivos de configuración ni en el Excel.
- La carga se realiza en una transacción: si falla una inserción, se revierte toda la operación.
- Si cambia el Excel, la conexión, el destino o el contenido del repositorio después de revisar, debe repetir la vista previa.
- Las operaciones de red se realizan en segundo plano para mantener operativa la ventana. Se aplican tiempos de espera a la conexión, las consultas y el bloqueo de la tabla.
- Si no logra conectar, compruebe el mensaje en Actividad, la conectividad de su equipo y los permisos de la cuenta. No se ha probado la conexión a su servidor desde el entorno de desarrollo.
- Para usar las reglas nuevas en QGIS, vuelva a consultar su versión en el plugin de validación. No se carga Excel administrativo desde el plugin.

## Otros sistemas

En una terminal, con Python y Tkinter disponibles:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python iniciar.py
```

En Linux, Tkinter puede requerir el paquete `python3-tk` de su distribución. Para SSL `verify-full`, utilice la configuración de certificados de PostgreSQL/libpq de su equipo.
