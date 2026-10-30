# Validador Consistencia Lógica Alfanumérica

Plugin para QGIS 3.28 o superior. Ejecuta las reglas SQL para **Modelo Interno de Levantamiento 1.0** y **CICA** contra PostgreSQL/PostGIS, muestra el resultado de cada regla y permite exportar un CSV.

## Formas de conexión

- **Conexión guardada en QGIS:** reutiliza una conexión PostgreSQL registrada en el perfil actual de QGIS. Soporta las credenciales guardadas o configuradas mediante el gestor de autenticación de QGIS.
- **Conexión manual a PostgreSQL:** permite ingresar servidor, puerto, base de datos, usuario y contraseña para la sesión actual.

Tras usar **Listar Esquemas**, el plugin lista los esquemas disponibles y permite seleccionar el que se validará.

## Cargue archivos CICA

Al seleccionar CICA aparece **Cargue archivos CICA**. Permite elegir los CSV individualmente y una geodatabase `.gdb` o ZIP. Se preparan copias temporales para validar durante la sesión, sin nuevo esquema de destino y sin modificar los originales. Consulte la guía para las condiciones de las sentencias y las vistas materializadas.

## Referencias R1 y R2

Para ambos modelos, la sección inferior **Referencias R1 y R2** valida los archivos Excel del catastro vigente y sus columnas requeridas. La lectura de los TXT de ancho fijo queda pendiente hasta disponer de su diccionario de posiciones.


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
Las marcas del operador permanecen visibles aunque DT marque Sí. En reportes sin hojas de regla (archivo ejecutivo o Guardar revisión en
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

Las marcas y observaciones de DT y operador permanecen visibles y editables,
aunque ambas excepciones sean Sí. Cada rol requiere su propia justificación;
solo DT descuenta errores. La recuperación y la generación conservan ambos
seguimientos.

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
**Componente · Reglas ejecutadas · Hallazgos · Excepciones DT · Excepciones operador · Errores · Errores técnicos**.
Las excepciones DT y operador se muestran por separado, con observación válida.
**Errores = Hallazgos − Excepciones DT**. Las marcas del operador no descuentan
errores; los errores técnicos se muestran aparte. DT tiene prioridad y un hallazgo
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

En la conexión manual, el servidor preestablecido es `172.19.3.225`. El campo
Servidor es de solo lectura y la conexión usa esa misma constante, incluso si
el texto se altera por código. Puerto, base de datos y credenciales de la
conexión manual conservan sus campos de configuración.

## Referencias R1/R2 y filtro avanzado (2.3.1)

La pestaña **Referencias R1/R2** ofrece dos opciones:

1. **Archivos R1 y R2 cargados por usuario**: prepare las referencias Excel como copias locales de trabajo. Durante la validación se cargan únicamente en la sesión temporal de PostgreSQL.
2. **R1 y R2 Vigente**: consulta el esquema `r1_r2` de la base de sentencias, identifica los municipios por DIVIPOLA y muestra la fecha y las tablas disponibles. Se usa la fecha más reciente del municipio, sin mezclar R1/R2 de fechas distintas. Las referencias requeridas se copian a la sesión temporal de validación.

**Filtro avanzado…**, debajo de **Esquema a validar**, se habilita al seleccionar un esquema o cargar la base catastral CICA a validar. Aplica al Modelo Interno/XTF, CICA y sus referencias R1/R2. Por defecto incluye Todos. Permite elegir Urbano (01), Rural (00) o Centro poblado (>01) según las posiciones 6–7 del NPN y seleccionar opcionalmente manzanas/veredas por las posiciones 1–17, leyendo los códigos de la base catastral a validar. Consulte [Referencias y alcance](REFERENCIAS_Y_AMBITO.md).

En el modo temporal, al iniciar la validación, el worker crea `reference_r1` y
`reference_r2` como **TEMP TABLE** y carga sus datos con COPY en la misma conexión
PostgreSQL que ejecuta las reglas y el reporte general. Usa el esquema especial
`pg_temp`, no un esquema de resultados permanente. El usuario de base requiere
permiso TEMP. Se confirma la preparación una vez para que el rollback de una
regla fallida no elimine las tablas necesarias para las siguientes.

La conexión se cierra explícitamente al finalizar, tanto si termina correctamente
como si falla; PostgreSQL elimina sus tablas temporales. Las copias locales se
conservan para repetir una ejecución con los mismos archivos y se eliminan al
liberarlas, reemplazarlas o cerrar el diálogo principal. No se borran las tablas
R1/R2 de `public` que existían de versiones anteriores. Los archivos originales
no se modifican. Los datos temporales sí se envían al servidor al validar; este
modo evita persistirlos, no implica procesarlos exclusivamente en el equipo.

Se admiten los marcadores `{esquema_r1}.{tabla_r1}`,
`{esquema_r1}{punto}{tabla_r1}`, `{esquema_r1}{tabla_r1}` y sus equivalentes R2.
Se resuelven antes de los marcadores del esquema de datos. Una regla que solicite
una referencia no cargada informa un error; no recurre silenciosamente a otra
tabla permanente. Las sentencias SQL con nombres de referencias escritos
literalmente deben adaptarse en el repositorio para utilizar estos marcadores.

La identidad de revisión incorpora la huella del contenido de las referencias
temporales, sin depender del nombre del archivo ni del directorio temporal.
Cambiar los datos de la referencia invalida conservadoramente la recuperación
automática de revisiones de aquella ejecución. La opción de R1 público conserva
el identificador de referencia anterior para no invalidar por este cambio de UI
las revisiones existentes.

Desde 1.4.0 la estadística descuenta exclusivamente las excepciones DT. Las
excepciones del operador siguen visibles como seguimiento separado, pero no
cierran hallazgos ni se restan del total de errores.

## Pestaña de referencias (1.4.1)

El panel izquierdo contiene las pestañas **Conexión** y **Referencias R1/R2**.
La segunda reúne la carga temporal, la selección del R1 de public y la futura
consulta municipal. Ya no se coloca al pie de la ventana, para que siga
accesible en pantallas pequeñas sin ocultarse debajo de los resultados.

El botón **Ejecutar validación** se encuentra debajo de las pestañas del panel
izquierdo, fuera de su área desplazable, y permanece visible en ambas. Conserva
las condiciones de habilitación según las reglas cargadas y seleccionadas.

## Versión única para cargue SNC (1.4.3)

Al seleccionar **Validaciones para cargue a SNC**, el selector manual de
versiones queda deshabilitado. El plugin consulta y carga automáticamente la
única versión publicada con reglas activas de la tabla SNC del modelo elegido,
sin abrir la ventana de versiones. Se mantiene visible la versión cargada.
Si no existe ninguna, hay más de una o falla la consulta, no se habilita la
ejecución ni se elige una versión arbitrariamente. Para las validaciones
habituales del modelo se conserva la selección manual de versiones.

## Controles compactos y Gestión de Excepciones (1.5.0)

**Controles a ejecutar** ocupa una sola línea. **Seleccionar grupos** abre una
lista desplegable con casillas independientes, conteos de reglas y las acciones
Seleccionar todos / Desmarcar todos. Se mantienen las condiciones de
habilitación: solo se ofrecen los grupos de las sentencias cargadas; para SNC,
solo Cargue SNC. No se muestran tarjetas permanentes de grupos.

**Gestión de Excepciones** dispone de más espacio y muestra una tabla de detalle,
archivo, acciones Cargar/Recargar y Liberar, y estado de cada carga. Los nombres
de archivos y los mensajes completos se pueden consultar en los textos de ayuda
al situar el puntero sobre la celda. Los botones Guardar revisión en Excel y
Cargar revisión consolidada se agrupan bajo esa tabla. Las pestañas de conexión
y referencias permanecen a la izquierda, con Ejecutar validación debajo.

En 1.5.1, la altura del formulario de conexión se recalcula después de aplicar
el estilo y completar la distribución de Qt al cambiar entre conexión manual
y guardada. Se considera la altura mínima real del formulario y su ancho para
evitar recortar Listar Esquemas y Esquema a validar.

## Minimizar y aviso de excepciones (1.5.2)

La ventana tiene habilitado el botón nativo **Minimizar (−)**. Minimizar no cierra
la herramienta ni libera las referencias o revisiones cargadas. Al abrirla desde
el menú o el icono de QGIS se restaura si estaba minimizada.

Al cargar o recargar un detalle y al cargar una revisión consolidada, el mensaje
de resultado recuerda que solo cuentan para descontar errores las excepciones
validadas por DT y marcadas en **Excepción DT = Sí**, con observación válida.
La marca del operador no basta. Gestión de Excepciones conserva también este
aviso visible, sin alterar las estadísticas ni agregar aprobaciones automáticas.

En 1.5.3 los campos de excepción del detalle se exportan con relleno inicial
rojo tenue (`FFC7CE`) para No y verde tenue (`C6EFCE`) para Sí. Se conserva el
formato condicional para actualizar el color al editar la marca en Excel.
La ocultación visual de los campos del operador sigue teniendo prioridad cuando
DT es Sí. El aviso de carga se unifica en: «Solo las excepciones validadas y
marcadas por DT descuentan errores».

## Ayuda de uso (1.5.4)

[Guía completa del plugin](ayuda/GUIA_USO.md). El botón **Ayuda** del encabezado
abre esa guía en GitHub mediante el navegador del usuario. El texto también
se incluye dentro de `ayuda/GUIA_USO.md` en el ZIP para consulta local.

## Flujo sin botones Liberar (1.5.5)

Se omiten los botones Liberar de Gestión de Excepciones y de Referencias R1/R2.
Para modificar revisiones, edite y guarde el Excel y pulse Recargar. Para quitar
marcas, cámbielas a No en el archivo y recargue. La recarga ya sustituye lo
aportado por ese mismo detalle y conserva los otros componentes. La limpieza
de referencias temporales se mantiene internamente al sustituirlas o cerrar.

## Gestión exclusivamente por detalle (1.5.6)

Se retiran Guardar revisión en Excel y Cargar revisión consolidada. El usuario
diligencia cada detalle, guarda ese mismo Excel y lo recarga desde la fila de su
componente. El reporte ejecutivo mantiene estadísticas, pero ya no incluye un
archivo de seguimiento editable o recuperable. Cada detalle conserva su hoja
interna Revisión y sus metadatos de identidad para el cruce seguro. El aviso de
cierre permite cancelar o descartar el estado de sesión, sin ofrecer guardar
un consolidado ni modificar los archivos originales.

## Ayuda integrada (1.5.9)

El botón Ayuda cambia a una pestaña de la misma ventana con la guía local, índice
y buscador. No abre el navegador ni necesita conexión a Internet. Incluye la
explicación de todos los contadores del resumen de recuperación de detalles.

## Resumen de carga por rol (1.6.0)

El mensaje agrupa los resultados en DT, Operador e Incidencias de carga. Cuenta
por separado las excepciones incorporadas y las descartadas sin observación de
cada rol. Aprobadas por DT exige ambas marcas en Sí con sus observaciones válidas
y una incorporación efectiva: no equivale a encontrar cualquier comentario del
operador en una fila DT. Las aprobadas son un subconjunto de DT, no se descuentan
dos veces. Los contadores se recalculan al recargar el archivo y los conflictos
no incrementan las excepciones incorporadas.

### Conservación de las marcas del operador (1.6.1)

La prioridad de DT no borra la marca ni la observación del operador. Ambas se
conservan al importar y al generar otra entrega. La ocultación en Excel es solo
visual; al cambiar DT a No, los valores del operador vuelven a verse. Los
conteos por rol pueden incluir el mismo caso, pero solo DT descuenta errores
y lo hace una sola vez. Se retira además la línea de seguimientos omitidos del
resumen de carga, incluido en la versión 1.6.1.

## Versión 2.0.0

Interfaz compacta con indicadores y totales, seguimiento de archivos modificados, fecha de carga por detalle, incidencias desplegables y observaciones de ancho adaptable. Consulte la guía integrada en la pestaña Ayuda.

## Versión 2.1.0

- Excepciones del operador visibles aun cuando DT marque Sí.
- Carga independiente de CSV CICA en tablas temporales de la conexión de validación; sin escritura en tablas persistentes.
- Descarga local de los formatos homologados originales para CICA V2 y Modelo interno V2 después de validar la versión correspondiente.

Consulte la guía integrada para los tipos de datos de los CSV, la consulta de tablas no seleccionadas y las condiciones de habilitación de los formatos.

La geodatabase también se utiliza temporalmente, conservando atributos, geometría y EPSG. Sus tablas de trabajo desaparecen al finalizar la ejecución.

## Administración externa de reglas

La carga de sentencias se realiza con el complemento independiente de QGIS [Administrador de Reglas SQL](../administrador_reglas_qgis/README.md), usando una conexión guardada en QGIS o los parámetros del administrador. El código del plugin ya no incluye la pestaña Administrar reglas; consulta y ejecuta las sentencias publicadas. La versión 2.3.0 incluye esta separación; el paquete 2.2.0 conserva la función antigua.

## Filtro avanzado con estadísticas (2.4.0)

Alcance permite combinar Urbano, Rural y Centro poblado mediante casillas. El filtro muestra estadísticas de la base catastral a validar y de R1 por separado, con cantidad y porcentaje incluidos. La lista de códigos NPN de 17 dígitos muestra registros de la base catastral a validar y de R1 y permite seleccionar o deseleccionar todos los códigos visibles. Consulte [Referencias y alcance](REFERENCIAS_Y_AMBITO.md) para conocer el conteo y los estados de carga.

## Filtro avanzado como pestaña (2.5.0)

La pestaña **Estadística y filtro avanzado**, después de **Referencias R1/R2**, requiere seleccionar tanto la base catastral a validar como el origen de R1. Contiene el editor integrado y muestra exclusivamente estadísticas de R1 por NPN completo único, con duplicados no sumados y filas sin NPN excluidas. **Aplicar filtro** guarda la selección; **Restablecer** vuelve a la selección aplicada. El filtro sigue actuando sobre el modelo y las referencias. Consulte [Referencias y alcance](REFERENCIAS_Y_AMBITO.md).

## Presentación del filtro avanzado (2.6.0)

La pestaña presenta un resumen general por alcance con estadísticas de CICA/Modelo Interno y R1 separadas. El botón **Ver estadísticas y seleccionar filtros…** abre una ventana independiente y ampliable para consultar detalles y editar alcances y códigos de 17 dígitos. R1 conserva el conteo único por NPN completo. Cancelar conserva el filtro anterior; Aplicar filtro guarda la selección para la validación.

## Presentación y terminología (2.7.0)

La pestaña **Estadística y filtro avanzado** presenta tarjetas y estadísticas con verde para **Base catastral a validar** y azul para **R1**. El selector se denomina **Alcance** y las referencias propias se seleccionan como **Archivos R1 y R2 cargados por usuario**. El resumen agrega predios activos y cancelados de la base; R1 mantiene el conteo de NPN únicos. Los estados no determinables se muestran como no disponibles. La ventana de selección conserva la aplicación o cancelación de filtros.

## Orden de resultados del modelo

En **Validaciones del modelo**, los componentes disponibles se presentan en este orden y con su número: 0 Estructura, 1 Administrativas, 2 Jurídicas, 3 Físicas, 4 Económicas, 5 Novedades y 9 Étnico. TOTAL permanece al final. El resumen ejecutivo Excel conserva el mismo orden. El cambio es de presentación y no modifica las reglas ni los conteos.

## Identificadores y hojas de los reportes

Los reportes generados presentan una sola columna **Numero_Predial_Nacional**, conservada como texto. Se unifican Predio, numero_predial_nacional, numero_predial y npn; los datos originales continúan en los metadatos de identidad para recuperar revisiones sin alterar las claves. Un cambio del identificador visible impide recuperar la revisión.

Las hojas de reglas toman el identificador definido en las sentencias: regla_1_1 se presenta como **1_1** y regla_1_52 como **1_52**. Se ordenan numéricamente, conservando saltos y sufijos definidos en los códigos. Cada reporte por componente conserva su propio espacio de nombres; no se crean hojas para controles sin hallazgos.

## Reportes Excel (2.8.0)

- En Validaciones del modelo, los resultados y su resumen siguen el orden 0 Estructura, 1 Administrativas, 2 Jurídicas, 3 Físicas, 4 Económicas, 5 Novedades, 9 Étnico y TOTAL.
- Una sola columna Numero_Predial_Nacional, como texto, sin duplicar identificadores. Los metadatos originales de los casos se conservan para recuperar revisiones.
- Hojas de reglas con el identificador de las sentencias y orden numérico: 1_1, 1_2, …, 1_10, …, 1_52. Hoja de detalle ofrece vínculos internos azules subrayados.
- Se elimina Sheet vacía, Contexto, Contexto de validación e Identificador de entrega. Revisión permanece oculta y automática.
- Reglas & Componente sustituye Ejecución automática, sin Resultado automático, con encabezados y filas formateados.
- Reportes protegidos con anchos de columna ajustables, primera columna y encabezados inmovilizados. Se mantienen editables excepciones y observaciones.
- Descargas de formatos: fo_gct_pc01_07_v2.xlsx y cons_log_cica_v2.xlsx.

## Detalle de validación y hojas de regla (2.9.0)

La hoja de navegación se denomina **Detalle Validación** y presenta arriba los metadatos de la ejecución: componente, fecha, modelo, ambiente, versión SQL, alcance, manzanas/veredas, base de datos, esquema y ubicación territorial. R1/R2 vigente se muestra cuando corresponde. Los filtros y vínculos internos de las reglas aparecen debajo. La versión del plugin se informa únicamente al pie de **Resumen ejecutivo**, en resumen_control_calidad.

Las hojas de regla muestran únicamente título de regla, descripción, ubicación territorial y cinco columnas visibles: Resultado de la condición, Excepción DT, Observación DT, Excepción operador y Observación operador. Si la consulta no devuelve campos cond_, el resultado se presenta como Incumple, pues cada fila corresponde a un hallazgo del control. Si devuelve varias condiciones, se reúnen con sus nombres en la misma celda. Los identificadores y atributos originales se mantienen en metadatos ocultos para preservar las claves de recuperación, sin mostrarlos como columnas del detalle. Cambiar el resultado visible invalida la recuperación de esa revisión.

## Resultado completo de la sentencia y confirmación

Las hojas de regla vuelven a mostrar todas las columnas devueltas por la sentencia SQL, en su orden original, seguidas de las excepciones y observaciones. El identificador predial conserva el encabezado unificado Numero_Predial_Nacional. Se mantienen título, descripción y ubicación territorial, protección, inmovilización y recuperación segura del seguimiento.

Antes de iniciar una validación se solicita confirmar los metadatos seleccionados. Cancelar conserva resultados y seguimientos de la ejecución anterior.

## Flujo operativo y reportes completos (2.10.0)

Resumen ejecutivo incorpora los metadatos de la validación sobre la tabla de resultados. Las hojas de reglas muestran de nuevo las columnas devueltas por SQL, en su orden original y con el identificador predial unificado, además de las excepciones y observaciones. Se conserva la recuperación de revisiones anteriores, incluidos los detalles compactos.

Ejecutar validación presenta los metadatos seleccionados para confirmar antes de iniciar controles o descartar resultados anteriores. Cancelar conserva los resultados y seguimientos existentes. La ayuda se reorganiza como una guía operativa por función, sin historial de cambios ni administración del repositorio.

## Confirmación de parámetros (2.10.1)

El cuadro previo a la ejecución indica «Revise los parámetros antes de ejecutar la validación». Se retiran de ese cuadro Reporte general y el bloque de referencias R1/R2, sin cambiar su uso por las reglas. Cancelar conserva los resultados y seguimientos anteriores.

## Reportes sin estadística duplicada (2.10.2)

Se elimina la hoja Estadística de revisión de los archivos de detalle. Las estadísticas se mantienen en los resultados del plugin y en el resumen ejecutivo. La hoja Revisión permanece oculta para recuperar excepciones.

### Versión 2.11.0

Selección de fuente CICA desde CSV/GDB o copia temporal de las siete tablas de `sentencias.snc_cica_copy`. Resumen de activos y cancelados. Fecha de marca desde `snc_cica_crudo._control`. Seguimiento CICA publicado en tabla; las gráficas de los bocetos siguen como propuesta visual.

### Versión 2.12.0

Copia base CICA muestra fecha y hora desde `snc_cica_crudo._control.fecha_marca` y oculta los campos CSV. Incluye consulta de municipios por DIVIPOLA y selección múltiple de etapas, con opción de todos los municipios. Las copias se leen filtradas y se valida la GDB sobre los mismos predios. Las referencias se restringen al municipio, manteniendo las condiciones originales de las reglas. Cambiar la selección exige volver a leer la copia. Los parámetros seleccionados forman parte de la confirmación y de la identidad de revisión.
