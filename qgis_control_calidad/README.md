# Validador Consistencia Lógica Alfanumérica

Plugin para QGIS 3.28 o superior. Ejecuta las reglas SQL para **Modelo Interno de Levantamiento 1.0** y **CICA** contra PostgreSQL/PostGIS, muestra el resultado de cada regla y permite exportar un CSV.

## Formas de conexión

- **Conexión guardada en QGIS:** reutiliza una conexión PostgreSQL registrada en el perfil actual de QGIS. Soporta las credenciales guardadas o configuradas mediante el gestor de autenticación de QGIS.
- **Conexión manual a PostgreSQL:** permite ingresar servidor, puerto, base de datos, usuario y contraseña para la sesión actual.

Tras usar **Listar Esquemas**, el plugin lista los esquemas disponibles y permite seleccionar el que se validará.

## Ingesta CICA

Al seleccionar CICA aparece el botón **Cargar insumos CICA**. Solicita individualmente los siete CSV requeridos y la geodatabase `.gdb` —directa o comprimida en ZIP—, validando su presencia antes de la carga al esquema de destino.

## Referencias R1 y R2

Para ambos modelos, el botón **Cargar referencia R1 y R2** valida los archivos Excel del catastro vigente y sus columnas requeridas. La lectura de los TXT de ancho fijo queda pendiente hasta disponer de su diccionario de posiciones.


## Instalación para pruebas

1. Copie la carpeta `qgis_control_calidad` al directorio de complementos de su perfil de QGIS.
2. En QGIS abra **Complementos > Administrar e instalar complementos**.
3. Active **Validador Consistencia Lógica Alfanumérica**.
4. Abra el complemento desde el menú **Base de datos** o su botón de barra de herramientas.

Las reglas SQL se incluyen en `resources/sql`. El complemento no guarda la contraseña ni ejecuta instrucciones que modifiquen la base de datos.

## Base de esta distribución

Versión 1.0.2 basada en el archivo `control_calidad_catastral_qgis.zip` (versión original 0.3.3). Se conserva la lógica y las reglas SQL de esa base; se actualiza la identificación del complemento.

## Ambiente de cargue a SNC

CICA y Modelo Interno de Levantamiento 1.0 muestran el ambiente **Validaciones para cargue a SNC** y el control
opcional **+ Cargue SNC**. Este control permanece desactivado hasta cargar una versión con reglas SNC.
Al seleccionar esa versión en el ambiente SNC de CICA o Modelo Interno de Levantamiento 1.0, solo se muestra y
selecciona **+ Cargue SNC**. Mientras no estén conectadas las reglas correspondientes,
permanece inhabilitado. Las reglas SNC se incorporarán desde dos tablas de
`public`, una por modelo; se usan `public.reglas_cargue_snc_cica` y `public.reglas_cargue_snc_xtf`,
con las columnas `version`, `componente`, `codigo_regla`, `tipo`,
`sentencia_sql`, `descripcion_regla`, `activa` y `orden`. No se requiere
`fecha_actualizacion` para estas tablas. Los controles SNC de la versión
seleccionada se agrupan bajo **+ Cargue SNC**.
El ambiente SNC no reutiliza las reglas de validación ordinarias de CICA ni de
otros modelos. XTF corresponde al Modelo Interno de Levantamiento 1.0 y no
aparece como modelo separado. El ambiente SNC de este modelo usa
`public.reglas_cargue_snc_xtf`; sus validaciones habituales mantienen sus
tablas originales. No se incorpora lectura de archivos XTF.

## Disponibilidad de ejecución

Ejecutar controles permanece deshabilitado hasta cargar una versión del repositorio con controles activos y seleccionar un grupo. Un fallo o cancelación al recargar la versión elimina la selección anterior. No se usan las reglas SQL locales como alternativa ante fallos de conexión.

## Acceso a sentencias

El repositorio usa la base `sentencias` y el usuario `admin_ant`. Al buscar una versión se solicita la contraseña con entrada enmascarada; se conserva únicamente en memoria durante la sesión del complemento. Cancelar bloquea la consulta y la ejecución. No se incluye una contraseña en el código ni en el ZIP.

Los grupos disponibles y seleccionados se calculan a partir de los controles activos con SQL no vacío de la versión seleccionada. Los grupos ausentes de esa versión no se muestran. Al cambiar de versión se reemplaza la selección completa.
