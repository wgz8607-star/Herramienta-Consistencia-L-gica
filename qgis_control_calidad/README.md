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

El repositorio usa la base `sentencias` y el usuario `admin_ant`. Por solicitud del propietario, la configuración local incorpora la contraseña y no la solicita ni la muestra en la interfaz. Esta credencial puede extraerse del código distribuido. Este cambio local no se ha publicado en GitHub ni empaquetado en un ZIP. Si se retira la contraseña interna, se conserva la solicitud enmascarada por sesión como alternativa.

Los grupos disponibles y seleccionados se calculan a partir de los controles activos con SQL no vacío de la versión seleccionada. Los grupos ausentes de esa versión no se muestran. Al cambiar de versión se reemplaza la selección completa.

## Metadatos y publicación de versiones

Antes de usar este cambio, ejecutar `sql/agregar_metadatos_version.sql` en
`sentencias`. Añade `descripcion_version` (texto vacío por defecto) y
`version_publicada` (verdadero por defecto para conservar la disponibilidad
existente). La descripción y publicación se leen exclusivamente de la primera
fila de cada versión, ordenada por `orden NULLS LAST, componente, codigo_regla`,
incluyendo reglas inactivas. No se usa el orden físico de las filas.

Para retirar una versión, cambiar `version_publicada` a falso en esa primera
fila; para publicarla de nuevo, cambiarla a verdadero. `activa` sigue siendo
independiente para cada regla. Solo se listan versiones publicadas con alguna
regla activa. Al cargar las reglas se comprueba otra vez la publicación. Esto
no revoca consultas o controles que ya estén cargados en otra sesión.
Si cambia la primera fila por reordenamiento o eliminación de reglas, transferir
sus metadatos a la nueva primera fila. El cambio aplica a las tablas de `public`;
los repositorios antiguos basados en esquema mantienen su tabla `versiones`.

## Revisión humana por registro (1.1.0)

La sección de resultados conserva el resumen automático por componente. El botón
**Revisar hallazgos** abre las filas devueltas por las reglas SQL, sus datos y su
resultado automático. La revisión humana es independiente y tiene tres campos:

- `estado_revision_usuario`: **Revisión pendiente** (inicial), **Excepción** o
  **Solicitar ajuste**.
- `observacion_usuario`, rotulada **Observación** en pantalla.
- `fecha_revision_usuario`: fecha y hora de la última modificación, con zona
  horaria de Colombia (`America/Bogota`).

Los cambios se aplican al cambiar de fila, filtrar, guardar o cerrar; también se
pueden aplicar expresamente con **Aplicar seguimiento**. Una excepción exige
texto visible en Observación: se rechazan campos vacíos, espacios y caracteres
invisibles. Cerrar o iniciar otra ejecución con cambios sin guardar ofrece
Guardar, Descartar o Cancelar.

**Guardar revisión en Excel** guarda todos los hallazgos de la ejecución, sin
aplicar los filtros del visor, y una hoja con la ejecución automática completa
(incluidas reglas sin hallazgos y errores técnicos). Incluye el reporte general
cuando existe. Los identificadores y demás datos se escriben como texto para
conservar ceros iniciales y evitar interpretar los valores como fórmulas. La
escritura es atómica: un fallo no reemplaza el último archivo guardado. Si un dato
supera el límite de Excel se informa, sin truncarlo silenciosamente.

Después de otra ejecución, **Recuperar revisión** carga un Excel creado por este
botón. No es posible recuperar con seguridad los antiguos reportes, que no
contenían claves de casos. Los reportes detallados existentes también muestran
los tres campos de seguimiento, pero para recuperar debe usarse el archivo de
**Guardar revisión en Excel**. La hoja oculta `_Identidades` forma parte del
formato y debe conservarse. Las columnas `dato:*` no son campos de revisión:
si se editan, el registro se rechaza al recuperar.

### Clave estable y política de coincidencia

La clave es SHA-256 de una representación canónica con tipos que contiene:

1. Origen de ejecución: modelo, ambiente, servidor, puerto, base, esquema,
   referencia R1 y origen de sentencias. Así no se mezclan municipios, bases,
   modelos ni ambientes.
2. Componente y código de la validación. Un mismo predio puede incumplir reglas
   distintas y cada incumplimiento requiere su propio seguimiento.
3. Huella del SQL efectivamente ejecutado, después de sustituir esquema y R1.
   Cualquier cambio del SQL, incluso de formato, invalida la recuperación de
   forma conservadora; no se reutilizan excepciones de un criterio diferente.
4. Todos los campos devueltos para el hallazgo, incluidos sus identificadores
   (por ejemplo `numero_predial`, `numero_predial_nacional`, `npn`, `t_id`,
   `t_ili_tid`, documento o código) y sus valores evaluados y condiciones
   `cond_*`. Incluir todo el contenido evita trasladar una revisión si cambió
   un valor relevante. Se preservan los tipos, los textos y los ceros iniciales.

No intervienen la fila del Excel, el orden del resultado ni el nombre del archivo.
Los nombres de columnas se ordenan antes de calcular la clave. Campos
explícitamente posicionales como `row_number`, `row_num`, `rownum`, `numero_fila`,
`nro_fila` y `fila_reporte` quedan fuera de ella. Cambiar de versión sin cambiar
el SQL, su origen ni los datos permite conservar el seguimiento.

Se exige un identificador reconocible del objeto. Si falta, si el SQL devuelve
columnas duplicadas, si la consulta genera ordinales con `row_number`, `rank` o
`dense_rank` (política conservadora), si hay tipos no compatibles o si una misma clave aparece
más de una vez en cualquiera de las ejecuciones, no se recupera automáticamente.
El visor indica identidad insuficiente o caso duplicado. No se intentan
coincidencias aproximadas por predio, por orden ni por descripción.

La identidad protege los datos expuestos por la regla: para recuperar con
seguridad, cada SQL debe devolver los identificadores y atributos que determinan
su inconsistencia. Cambios en datos auxiliares que el SQL no devuelve ni
versiona no pueden detectarse desde el reporte. No se cambian las reglas SQL
existentes durante esta implementación.

La recuperación preserva estados, observaciones y fechas solo en coincidencias
únicas. Nunca sobrescribe seguimiento ya editado en la ejecución actual. Una
excepción importada sin observación se convierte a **Revisión pendiente** y se
informa. El resumen muestra incorporadas, sin correspondencia, ambiguas,
conflictos y datos inválidos. Las revisiones recuperadas deben guardarse en el
nuevo Excel.

### Comprobación

Con el Python de QGIS y openpyxl:

```bash
QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 \
/workspace/.venvs/calidad-qgis/bin/python -m unittest discover -s tests -v
```

La selección o reselección de modelo restablece **Seleccione un ambiente…**,
borra la versión SQL y bloquea la ejecución hasta elegir reglas válidas. Los
resultados ya ejecutados mantienen su contexto original para revisarlos y
exportarlos aunque se preparen otras opciones de ejecución.
