# Administrador de Reglas SQL — QGIS 1.0.1

Complemento independiente para administrar las sentencias del repositorio desde Excel. No forma parte del Validador de Consistencia Lógica y no necesita el programa externo en Python ni sus archivos BAT.

## Instalación

1. En QGIS, abra **Complementos → Administrar e instalar complementos → Instalar desde ZIP**.
2. Seleccione `administrador_reglas_qgis_v1.0.1.zip` sin descomprimirlo.
3. Active **Administrador de Reglas SQL**.
4. Ábralo desde **Base de datos → Administrador de Reglas SQL** o desde su icono en la barra de herramientas.

Se requiere QGIS 3.28 o superior y las bibliotecas `openpyxl` y `psycopg2` en el Python de QGIS, las mismas utilizadas por el validador para Excel y PostgreSQL. El complemento usa el perfil de QGIS y no incorpora credenciales ni concede permisos de base de datos.

## Conexión y destino

- **Conexión guardada en QGIS:** seleccione una conexión PostgreSQL del perfil actual. Se reutilizan sus parámetros, servicio, SSL y autenticación de QGIS. Si la configuración está protegida, QGIS puede pedir su contraseña maestra. El complemento no muestra ni escribe en archivos las contraseñas guardadas.
- **Parámetros de conexión:** introduzca servidor, puerto, base, usuario, contraseña y modo SSL. Estos datos solo se usan en la sesión. Si la conexión guardada no dispone de una contraseña utilizable, puede introducir sus credenciales mediante esta opción.

Pulse **Conectar y listar esquemas**, seleccione el esquema y elija la tabla. Solo se muestran tablas existentes con los diez campos de la plantilla y permiso de consulta para el usuario conectado. Una tabla sin permiso INSERT se marca **solo lectura**: puede exportarla y revisar el Excel, pero no cargar registros.

El esquema no está restringido a `public`. El usuario debe elegir la base, el esquema y la tabla correctos. Para utilizar las reglas en el validador, seleccione el destino configurado para ese modelo; cargar otro esquema no modifica la configuración del validador.

## Plantilla, exportación y carga

1. Use **Guardar plantilla Excel** para obtener un libro vacío, o **Exportar todas las reglas** para exportar todos los registros, incluidas reglas inactivas y versiones no publicadas.
2. Diligencie **Reglas**, una fila por regla. Los campos son `version`, `componente`, `codigo_regla`, `tipo`, `sentencia_sql`, `descripcion_regla`, `activa`, `orden`, `descripcion_version` y `version_publicada`.
3. Pegue cada consulta SQL completa en una sola celda, con sus saltos de línea y referencias `{esquema}.tabla`. No la envuelva en `INSERT INTO` ni en `$regla$`. No utilice fórmulas de Excel.
4. Pulse **Seleccionar Excel y revisar**. La vista previa distingue registros nuevos, existentes y existentes con diferencias. En **Todos los campos** puede revisar los metadatos de publicación que se guardarán.
5. Pulse **Cargar y reemplazar reglas**. La confirmación indica filas nuevas, filas que se reemplazarán y filas sin cambios. En sus detalles se muestran los códigos, el SQL que se incorporará y las diferencias anteriores/nuevas de los reemplazos. Confirme el destino y la operación completa. Las sentencias se almacenan como texto: no se ejecutan durante la carga.

Las plantillas anteriores siguen siendo compatibles si conservan los mismos encabezados. La hoja Ejemplo no se importa. Mantenga versiones y códigos como texto para conservar ceros iniciales. Los campos técnicos adicionales de la tabla, si existen, deben admitir valores por defecto; el cargador no crea ni altera estructuras.

## Reglas de incorporación

- La coincidencia para reemplazar es **version + componente + orden**, dentro de la tabla seleccionada. El mismo orden en otra versión o componente corresponde a un caso distinto. Un orden nuevo inserta una fila; el mismo orden dentro de esa versión y componente reemplaza la fila mediante UPDATE y conserva su identificador técnico.
- Los órdenes repetidos dentro de la misma versión y componente en el Excel se rechazan. Si un orden coincide con varias filas de la tabla, se informa la ambigüedad y no se prepara la carga. Un código ya utilizado en otro orden de la misma versión y componente también se rechaza para evitar sustituir una regla distinta.
- Una fila idéntica se marca **Sin cambios** y no se vuelve a escribir. El resultado final informa nuevas, reemplazadas y sin cambios.
- Las filas nuevas de una versión existente heredan sus metadatos de publicación. Al reemplazar una fila, los metadatos diligenciados en el Excel sustituyen los de esa fila; los campos de metadatos vacíos conservan los anteriores. La publicación de una versión se determina por su primera fila según orden, componente y código, igual que en el validador. Los cambios de publicación se indican en la confirmación.
- Una versión nueva queda sin publicar si no se indica lo contrario. Los metadatos repetidos de una versión nueva deben coincidir.
- Las versiones identificadas por fecha, como `29_10_2026`, son válidas. Si se indica explícitamente un prefijo V2 o V3, debe coincidir con la tabla de destino. Las tablas `reglas_cargue_snc_*` permiten una sola versión publicada con reglas activas.
- El SQL no se ejecuta ni se comprueba sintácticamente durante la carga. En las reglas CONTROL, la consulta debe devolver únicamente los hallazgos; se comprobará al ejecutar las validaciones.
- La carga utiliza una transacción para las inserciones y los reemplazos juntos. Un error revierte toda la operación. Si cambia el Excel, la conexión, el destino o el contenido del repositorio después de la revisión, debe repetir la vista previa.
- Se respetan los permisos reales de la conexión. La inserción también requiere que el usuario pueda bloquear la tabla durante la transacción. La herramienta no utiliza usuarios internos, no concede permisos y no crea tablas.
- Las operaciones se ejecutan en segundo plano y los errores quedan visibles en **Actividad y mensajes**. Espere a que termine la operación antes de cerrar; el bloqueo tiene un tiempo de espera limitado.

## Después de cargar

En el validador, vuelva a consultar la versión de sentencias para utilizar las reglas incorporadas. Este complemento administra reglas; no carga datos catastrales ni cambia la información que se valida.

La interfaz y la lógica se comprobaron con QGIS 3.40. La conexión a su servidor y sus permisos deben verificarse desde su equipo mediante **Conectar y listar esquemas**.
