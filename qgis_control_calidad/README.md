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

## Excepciones DT y operador (1.2.5)

La revisión se diligencia en Excel. No se genera la ventana «Revisión de hallazgos
por registro» ni se muestra el botón «Revisar hallazgos». Se conservan **Guardar
revisión en Excel** y **Recuperar revisión**.

Todos los reportes incluyen una hoja **Revisión** con cada hallazgo y estos campos:

| Campo | Valor inicial | Condición |
|---|---|---|
| Excepción DT | No | Sí exige Observación DT válida. |
| Observación DT | Vacío | Edición libre, antes o después de la marca. |
| Excepción operador | No | Dominio Sí/No; no corresponde revisar si DT es Sí. |
| Observación operador | Vacío | Edición libre; la fila oscura indica exclusión por DT. |

En los paquetes por componente, diligencie los cuatro campos en la hoja de
cada regla, por hallazgo. La hoja **Revisión** consolida automáticamente esas
marcas y observaciones mediante búsquedas por `clave_caso`; sus campos están
protegidos para evitar dos fuentes de edición. La clave se conserva oculta en
las hojas de detalle. Cambiar el orden de las filas no altera el cruce.

Las columnas de excepción se muestran en verde para **Sí** y rojo para **No**.
Cuando DT es Sí, solo los valores de los dos campos del operador quedan
visualmente ocultos; las columnas de DT y los datos conservan sus colores. En reportes sin hojas de regla (archivo ejecutivo o Guardar revisión en
Excel), el seguimiento se diligencia directamente en **Revisión**.

Al recuperar un paquete, el plugin obtiene las marcas desde las hojas de regla
por su clave, sin depender de los valores de fórmula almacenados por Excel.
También verifica que los datos originales de la hoja no se hayan alterado. Las
fórmulas se usan solo para mostrar el consolidado en Excel, no para ejecutar
código ni decidir coincidencias. El consolidado de un paquete corresponde a ese
mismo archivo; no modifica otros archivos Excel externos abiertos o guardados.
Para actualizar un archivo de revisión separado, recupere el paquete en QGIS y
use **Guardar revisión en Excel**.

Los campos de excepción tienen dominio **Sí / No**, mediante listas desplegables
siempre disponibles. Las observaciones no tienen validaciones de entrada ni
exigen un orden de diligenciamiento: se puede seleccionar Sí y luego escribir
la nota. En las hojas de regla, las cuatro celdas del seguimiento están
desbloqueadas; los datos originales siguen protegidos.

Cuando **Excepción DT = Sí**, se ocultan visualmente solo los valores de
**Excepción operador** y **Observación operador** de esa fila, usando texto y
fondo blancos. El resto de la fila permanece visible; la marca DT conserva su
verde y las otras marcas su rojo/verde. Al cambiar DT a No, los valores del
operador vuelven a verse. Este efecto no borra datos ni oculta físicamente las
columnas: en Excel una columna oculta afecta a toda la hoja, no a un solo caso.
El contenido sigue existiendo y puede verse en la barra de fórmulas; no es una
medida de seguridad. No se añaden macros ni ventanas de edición.

La recuperación sigue verificando la justificación y la prioridad de DT:
flexibilizar la edición no convierte una marca incompleta en una excepción
validada. Si DT es Sí con justificación, el seguimiento del operador no se
incorpora para ese caso.

**Recuperar revisión** solo reutiliza coincidencias únicas con los mismos datos
y criterio. Si una excepción carece de su observación, la convierte a No e
informa. Si DT es Sí, descarta cualquier excepción u observación del operador y
lo informa. El seguimiento existente en la ejecución actual nunca se sobrescribe
silenciosamente. Los campos de revisión de la versión 1.1 se conservan ocultos
por compatibilidad; una antigua revisión genérica no se atribuye automáticamente
a DT ni al operador.

**Guardar revisión en Excel** incluye todas las filas de la ejecución y el
resultado automático de cada regla, sin aplicar filtros del archivo. Conserva los
identificadores como texto y la hoja oculta de identidades para cruzar futuras
ejecuciones. Las revisiones recuperadas se pueden volver a guardar o incorporar
a los reportes detallados. Los cambios sin guardar se advierten al cerrar o al
iniciar otra ejecución.

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
La columna `recuperable` y el resumen de importación informan sobre los casos que no se pueden cruzar. No se intentan
coincidencias aproximadas por predio, por orden ni por descripción.

La identidad protege los datos expuestos por la regla: para recuperar con
seguridad, cada SQL debe devolver los identificadores y atributos que determinan
su inconsistencia. Cambios en datos auxiliares que el SQL no devuelve ni
versiona no pueden detectarse desde el reporte. No se cambian las reglas SQL
existentes durante esta implementación.

La recuperación preserva el seguimiento solo en coincidencias únicas. Nunca sobrescribe seguimiento ya editado en la ejecución actual. Una
excepción DT u operador importada sin observación se convierte a **No** y se
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

Desde 1.2.4 el dominio Sí/No se incluye directamente en cada validación de lista,
sin referencias a rangos nombrados u hojas ocultas. La flecha de desplegable se
muestra al seleccionar una celda de excepción en la hoja de la regla. En los
paquetes, Revisión es el consolidado de fórmulas y no se edita allí. Los archivos
Excel creados con versiones anteriores deben regenerarse para incorporar el
nuevo dominio.

## Carga visible e independiente de detalles (1.3.0)

Después de ejecutar las reglas, cada componente con hallazgos muestra su propio
botón **Cargar detalle**, el estado **No cargado**, y **Liberar**. Al cargar,
se muestra el nombre del archivo y el resultado: **Cargado**, **Cargado con
observaciones**, **Sin coincidencias** o **Error de carga**. Los cinco detalles,
si existen, se cargan independientemente y sus revisiones se acumulan.

**Liberar** pide confirmación y retira exclusivamente lo aportado por ese archivo
a la ejecución actual; no modifica el Excel ni elimina revisiones de otros
detalles. Si el seguimiento cambió posteriormente, lo conserva en lugar de
borrarlo. El archivo no queda abierto después de importarlo y puede editarse
en Excel; tras guardarlo, use **Recargar detalle** o vuelva a cargarlo después
de Liberar. La recarga reemplaza explícitamente la revisión anterior de ese
mismo detalle, incluso cuando se quitó una marca; un archivo ilegible o de otro
componente no destruye una carga anterior válida.

**Cargar revisión consolidada** distribuye los componentes entre esas mismas
filas. Si un componente ya está cargado, solicita reemplazarlo mediante su
control individual. No se permiten sustituciones silenciosas entre archivos.
Los estados, rutas y la procedencia de cada detalle viven en memoria durante
la ejecución. **Guardar revisión en Excel** conserva el seguimiento consolidado
en la carpeta elegida; no se escribe en PostgreSQL ni se mantienen conexiones
a los archivos. Iniciar otra ejecución restablece los estados de carga.

La regla 1.12 del modelo interno devuelve grupos por matrícula, no predios
individuales. La identificación reconoce ahora matrícula/FMI además de NPN,
documentos y los demás identificadores: la clave incluye la matrícula, el conteo,
los datos retornados, el SQL y el contexto. Se admiten reportes anteriores que
marcaron estos grupos como no recuperables por no reconocer la matrícula,
siempre que la ejecución actual confirme una coincidencia única e idéntica.
La lectura del consolidado no depende de cómo Excel reescriba sus fórmulas:
se leen las celdas de la regla por clave, sin ejecutar las fórmulas. El resumen
distingue identidad insuficiente de datos/identidad alterados.

## Estadística actualizada al recuperar detalles (1.3.1)

La tabla y el resumen se recalculan al cargar una revisión consolidada, cargar,
recargar o liberar un detalle, y al descartar cambios. Muestran por componente:
**Componente · Reglas ejecutadas · Hallazgos · Excepciones · Errores · Errores técnicos**.
Excepciones suma las reconocidas de DT y operador con observación válida.
Errores es Hallazgos menos Excepciones; los errores técnicos se muestran aparte. DT tiene prioridad y un hallazgo
no se descuenta dos veces. Las observaciones sin una marca Sí no descuentan
hallazgos, ni lo hacen las excepciones sin justificación.

Los resultados automáticos y errores técnicos no se alteran ni se borran por la
revisión humana. Liberar un detalle devuelve a Errores los casos que dejan de
estar exceptuados. Los reportes detallados y Guardar revisión en Excel incluyen
una hoja Estadística de revisión con los mismos conteos; el resumen ejecutivo
usa estas mismas columnas, incluyendo un total general.

## Distribución compacta (1.3.2)

La conexión ocupa inicialmente unos 300 px (30 % del área) y los resultados el
70 % restante. El separador permite cambiar esa proporción. Los controles de
conexión se apilan con menor espaciado y desplazamiento vertical cuando hace
falta. El modo de conexión guardada ya no reserva la altura de los campos
manuales ocultos, eliminando el hueco antes de Listar Esquemas.
