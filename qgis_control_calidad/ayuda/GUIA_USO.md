# Guía de uso — Validador Consistencia Lógica Alfanumérica

Guía de la versión **2.0.0**. Las opciones descritas pueden no estar disponibles en paquetes anteriores.

## Contenido

1. [Instalación y requisitos](#1-instalación-y-requisitos)
2. [Preparar una validación](#2-preparar-una-validación)
3. [Conectar la base de datos](#3-conectar-la-base-de-datos)
4. [Referencias R1 y R2](#4-referencias-r1-y-r2)
5. [Seleccionar y ejecutar controles](#5-seleccionar-y-ejecutar-controles)
6. [Interpretar las estadísticas](#6-interpretar-las-estadísticas)
7. [Generar y diligenciar reportes](#7-generar-y-diligenciar-reportes)
8. [Recuperar y gestionar detalles](#8-recuperar-y-gestionar-detalles)
9. [Conservar los detalles y repetir la validación](#9-conservar-los-detalles-y-repetir-la-validación)
10. [Problemas frecuentes](#10-problemas-frecuentes)
11. [Administración del repositorio de sentencias](#11-administración-del-repositorio-de-sentencias)

## 1. Instalación y requisitos

- QGIS **3.28 o superior**. Las pruebas automatizadas de desarrollo se ejecutan con QGIS 3.40; esto no equivale a probar todas las versiones o equipos.
- Instale el ZIP **del plugin**, no el ZIP completo del repositorio. No necesita descomprimirlo.
- En QGIS: **Complementos → Administrar e instalar complementos → Instalar desde ZIP**. Seleccione el paquete y active **Validador Consistencia Lógica Alfanumérica**.
- Reinicie QGIS después de actualizar. Abra la herramienta desde **Base de datos** o su icono en la barra de herramientas.
- Se requieren `openpyxl` para Excel y `psycopg2` para PostgreSQL, disponibles en el Python que utiliza QGIS. Instalar bibliotecas en otro Python no las incorpora automáticamente a QGIS.
- El equipo debe poder llegar al servidor PostgreSQL/PostGIS y al repositorio de sentencias. La instalación del plugin no configura la red ni una VPN.
- La cuenta de datos necesita acceso a la base y permisos de consulta sobre el esquema y sus tablas. Para referencias temporales también necesita permiso **TEMP** sobre la base.

La herramienta usa dos conexiones distintas: una al **repositorio de sentencias** y otra a la **base de datos que se validará**. Que una funcione no confirma la otra.

## 2. Preparar una validación

1. En **Conexión**, seleccione **Modelo Interno de Levantamiento 1.0** o **CICA**. XTF se considera parte del Modelo Interno; no aparece como modelo separado.
2. Seleccione un ambiente:
   - **Validaciones del modelo**: busque y seleccione la versión SQL publicada correspondiente.
   - **Validaciones para cargue a SNC**: se carga automáticamente su única versión publicada con reglas activas. El selector manual se deshabilita.
3. Configure la conexión de datos y seleccione el esquema que se evaluará.
4. Si las reglas lo requieren, prepare R1/R2 en la pestaña de referencias.
5. Abra **Seleccionar grupos**, compruebe los controles marcados y pulse **Ejecutar validación**, debajo de las pestañas.

**Reseleccionar el modelo limpia el ambiente y la versión SQL.** Vuelva a elegirlos antes de ejecutar. Los resultados de una ejecución previa conservan su propio contexto hasta que inicie otra ejecución.

Sin sentencias activas y ejecutables no se habilita la ejecución. El plugin no sustituye una consulta fallida al repositorio por reglas locales.

## 3. Conectar la base de datos

### Conexión guardada en QGIS

1. Seleccione **Conexión guardada en QGIS**.
2. Pulse **Actualizar** si agregó o cambió conexiones en QGIS.
3. Elija la conexión. Debajo se muestra su base de datos y servidor.
4. Pulse **Listar Esquemas** y seleccione **Esquema a validar**.

Se reutilizan las credenciales guardadas en la conexión o en el gestor de autenticación de QGIS. Si QGIS conecta pero el plugin no, revise cómo está configurada la autenticación y copie el mensaje de error completo.

### Conexión manual a PostgreSQL

1. Seleccione **Conexión manual a PostgreSQL**.
2. El servidor preestablecido es **172.19.3.225** y no es editable.
3. Revise el puerto —por defecto **5432**— e ingrese base de datos, usuario y contraseña de la cuenta de datos.
4. Pulse **Listar Esquemas** y seleccione el esquema.

La contraseña de datos no se muestra y se usa durante la sesión. No debe confundirse con el acceso interno al repositorio de sentencias.

## 4. Referencias R1 y R2

Estas opciones están en la pestaña **Referencias R1/R2**, junto a **Conexión**.

### A. Archivos R1 y R2 temporales

1. Elija **Archivos R1 y R2 temporales** y pulse **Cargar R1 / R2…**.
2. Seleccione un Excel R1. Puede seleccionar también un Excel R2; R2 es opcional.
3. Pulse **Preparar referencias temporales** y después **Aceptar**.
4. Compruebe los nombres y cantidades de registros preparados.

Se lee la hoja activa del Excel. La primera fila debe contener los encabezados. Se admiten columnas adicionales; no deben quedar encabezados duplicados al normalizarlos.

| Referencia | Columnas requeridas |
|---|---|
| R1 | `NUMERO_PREDIAL`, `DESTINO_ECONOMICO`, `AREA_TERRENO`, `AREA_CONSTRUIDA`, `AVALUO`, `VIGENCIA` |
| R2 | `NUMERO_PREDIAL`, `MATRICULA_INMOBILIARIA`, `AREA_TERRENO_1`, `AREA_CONSTRUIDA_1`, `VIGENCIA` |

Los encabezados se normalizan a minúsculas, sin tildes y con separadores convertidos en guiones bajos. Mantenga los identificadores como **texto desde el archivo original**: Excel puede perder precisión en números largos y no se pueden reconstruir dígitos que ya se perdieron.

**Duración de los datos:**

- Preparar los archivos crea una copia local temporal; todavía no los publica en PostgreSQL.
- Al validar, se crean tablas **TEMP** en `pg_temp` dentro de la misma conexión que ejecuta las reglas.
- Las tablas temporales desaparecen al cerrar esa conexión, tanto al terminar como al fallar.
- La copia local permite repetir una ejecución con el mismo contenido. Se elimina automáticamente al reemplazar la referencia o cerrar la herramienta.
- El archivo original no se modifica. Este modo evita guardar tablas permanentes, pero los datos sí se envían al servidor durante la validación.

Los TXT de ancho fijo no están implementados. Una regla que requiera R2 dará un error si no se preparó R2.

### B. R1 existente en public

Elija **R1 existente en public**, pulse **Actualizar listado** y seleccione una tabla accesible en la conexión de datos actual. El listado busca nombres de tablas R1; no supone que cualquier tabla tenga la estructura requerida.

La herramienta consulta la tabla seleccionada: **no la elimina ni sobrescribe**. Esta opción no utiliza el R2 temporal. Las tablas permanentes de versiones anteriores no se borran automáticamente.

### C. Consulta de R1 por municipio

**Consulta de R1 por municipio (próximamente)** está visible pero deshabilitada. El catálogo centralizado y sus consultas todavía no están desarrollados.

## 5. Seleccionar y ejecutar controles

**Controles a ejecutar** ocupa una sola línea. **Seleccionar grupos** abre la lista con casillas y conteos; puede seleccionar varios grupos. También dispone de **Seleccionar todos** y **Desmarcar todos**.

- Se ofrecen los grupos que tienen SQL ejecutable en la versión cargada.
- En SNC solo se ofrece **+ Cargue SNC**; se selecciona cuando se carga su versión válida.
- Sin grupos seleccionados, durante una ejecución o sin reglas válidas, el botón de ejecución permanece deshabilitado.
- Durante la ejecución no se permite sustituir las referencias que está utilizando el proceso.
- **Minimizar (−)** conserva el estado. Al abrir otra vez el plugin desde QGIS se restaura la ventana.

Las reglas se ejecutan tal como están publicadas. Si una falla, se registra un error técnico y se intenta continuar con las siguientes. Un estado automático **Correcta** indica que la consulta se ejecutó correctamente; no significa que devolviera cero hallazgos.

## 6. Interpretar las estadísticas

| Columna | Significado |
|---|---|
| Componente | Grupo al que pertenecen las reglas ejecutadas. |
| Reglas ejecutadas | Número de reglas procesadas en ese componente. |
| Hallazgos | Filas de inconsistencia devueltas por las validaciones. No necesariamente son predios distintos. |
| Excepciones DT | Hallazgos con excepción DT reconocida y observación válida. |
| Excepciones operador | Marcas justificadas del operador. Se muestran separadas y no descuentan errores. |
| Errores | **Hallazgos − Excepciones DT**. |
| Errores técnicos | Fallos de conexión, SQL u otros fallos técnicos; son independientes de las excepciones. |

**Solo las excepciones validadas y marcadas por DT descuentan errores.**

Ejemplo: 100 hallazgos, 10 excepciones DT y 8 del operador dejan **90 errores**, no 82. Un caso puede conservar ambas marcas y aparecer en los conteos de ambos roles. Solo su marca DT descuenta el hallazgo, una única vez.

La estadística se actualiza al cargar, recargar o descartar revisiones. No borra ni cambia el resultado automático original.

## 7. Generar y diligenciar reportes

Pulse **Generar reporte detallado** y elija una carpeta. Se genera un archivo ejecutivo y archivos `detalle_<componente>_….xlsx` para los componentes con hallazgos. El nombre exacto incluye fecha y hora.

### ¿Dónde editar?

En un **detalle por componente**, abra la hoja de la regla que desea revisar y diligencie los campos por hallazgo:

| Campo | Uso |
|---|---|
| Excepción DT | Dominio desplegable **Sí / No**. DT debe validar el caso antes de marcar Sí. |
| Observación DT | Justificación de DT. |
| Excepción operador | Dominio **Sí / No** para la propuesta del operador. |
| Observación operador | Justificación o comentario del operador. |

Las observaciones se pueden escribir antes o después de la marca. No están condicionadas por un orden de edición. Para **recuperar una excepción como válida** debe existir una observación con texto: vacíos, espacios o caracteres invisibles no bastan.

- **No**: relleno rojo tenue (`#FFC7CE`) y texto rojo oscuro (`#9C0006`).
- **Sí**: relleno verde tenue (`#C6EFCE`) y texto verde oscuro (`#006100`).
- **DT = Sí**: los valores de los dos campos del operador se ocultan visualmente en esa fila. No se oculta toda la columna ni se borran los datos. No es un mecanismo de seguridad: el contenido puede verse en la barra de fórmulas.

Dentro de cada detalle, la hoja **Revisión** refleja los valores por clave y sirve para recuperarlos. No se editan sus campos: se alimentan desde las hojas de reglas del mismo archivo. Esta hoja interna no es un archivo de revisión consolidada separado. El reporte ejecutivo contiene únicamente estadísticas y no se usa para cargar excepciones.

Conserve las claves, las columnas de datos originales y las hojas ocultas. No copie únicamente una hoja suelta a otro libro si luego desea recuperar el seguimiento. La protección evita ediciones accidentales; no es una barrera de seguridad.

Las listas aparecen al seleccionar una **celda de excepción**, no su encabezado. Los reportes antiguos no se actualizan al instalar un plugin nuevo: deben regenerarse para incorporar nuevos dominios y formatos.

## 8. Recuperar y gestionar detalles

1. Reciba el Excel diligenciado y la información fuente que haya ajustado el operador.
2. Ejecute las nuevas validaciones sobre el esquema correspondiente.
3. En **Gestión de Excepciones**, use **Cargar** en la fila del componente correspondiente.
4. Seleccione su archivo `.xlsx` y revise el resumen de importación.
5. Repita con los demás componentes. Sus revisiones se acumulan en la misma ejecución.

| Estado o acción | Significado |
|---|---|
| No cargado | No hay un archivo asociado a ese detalle. |
| Cargado | Se leyó el archivo y se encontraron casos del detalle. No significa que todas las filas sean excepciones. |
| Cargado con observaciones | Hay advertencias, casos no coincidentes, ambiguos o conflictos. Consulte el resumen. |
| Sin coincidencias | El archivo se leyó, pero no se encontraron casos coincidentes. |
| Error de carga | No pudo cargarse. Una carga anterior válida se conserva. |
| Recargar | Reemplaza explícitamente el seguimiento importado de ese mismo detalle. |

Sitúe el puntero sobre el archivo o estado para ver su ruta y mensajes completos. Los archivos no quedan abiertos después de leerse: puede editarlos en Excel, guardarlos y **Recargar**. No es necesario cerrar ni liberar el archivo desde el plugin. Para quitar una marca, cámbiela a No en el Excel, guarde y recargue el mismo detalle. Se conservan las ediciones posteriores que no sea seguro retirar.

La gestión se hace exclusivamente por detalle. No hay botones para guardar o recuperar una revisión consolidada. Recargue cada archivo que haya cambiado; el seguimiento de los otros componentes se conserva.

### ¿Qué significa el resumen de recuperación?

El mensaje separa **DT**, **Operador** e **Incidencias de carga**.

| Contador | Interpretación |
|---|---|
| DT — Incorporadas | Excepciones DT con observación válida que se incorporaron al caso actual. Incluye las propuestas del operador aprobadas por DT. |
| DT — Descartadas sin observación | Marcas DT en Sí sin texto válido en su observación; no se aceptan como excepción. |
| Operador — Incorporadas | Marcas justificadas del operador incorporadas, incluso si DT también está en Sí. No descuentan errores. |
| Operador — Descartadas sin observación | Marcas del operador en Sí sin texto válido en su observación. |
| Operador — Aprobadas por DT | Casos incorporados que llegan con ambas marcas en Sí y ambas observaciones válidas. Son un subconjunto de las incorporadas por DT; no son excepciones adicionales. El plugin reconoce lo diligenciado, no verifica la identidad del evaluador ni aprueba casos por sí mismo. |
| Sin coincidencia | La clave del archivo no aparece en la ejecución actual. Puede cambiar por datos, SQL, contexto o referencias; no prueba por sí solo que el error esté corregido. |
| Coincidencias ambiguas | No existe una coincidencia única y segura; no se asigna automáticamente. |
| Conflictos | Se conservó seguimiento actual diferente, sin sobrescribirlo. |
| Registros no recuperables | Total de filas con identidad insuficiente o que no superaron la verificación de datos. |
| Por identidad insuficiente | Desglose del total anterior: no hay identificación recuperable suficiente. |
| Por datos o identidad alterados | Desglose del total anterior: los datos, la clave o las referencias de las hojas no superaron la verificación. |

Las cifras describen la carga actual, no se acumulan cada vez que recarga el
mismo archivo. Las incorporadas cuentan solo excepciones efectivamente
transferidas, no observaciones sin marca ni casos rechazados por conflicto.
No sume todas las líneas: las aprobadas por DT están incluidas en ambos roles y los dos últimos contadores son
desgloses. La estadística de errores se calcula por separado y descuenta solo DT.

### ¿Cuándo se recupera una excepción?

La columna `clave_caso` identifica cada hallazgo, no la regla completa. Combina contexto de origen, modelo y ambiente, componente y regla, huella del SQL e identificadores y valores devueltos por el caso. Puede usar NPN, documento, identificador del objeto o matrícula/FMI, según el resultado. No depende del número de fila ni del archivo.

Solo se recupera el seguimiento de una coincidencia única que siga igual. Si cambia el SQL, el caso o la referencia relevante, puede cambiar su clave. No se hacen cruces aproximados por NPN o por orden. Los casos duplicados o sin identificación suficiente no se asignan automáticamente.

Si la regla no devuelve los datos que determinan la inconsistencia, el reporte no puede detectar cambios en esos datos no expuestos. La regla 1.12 por matrícula, por ejemplo, identifica el grupo con matrícula y conteo; no entrega la lista de predios integrantes.

Una excepción sin observación válida se descarta como excepción y se informa. El seguimiento actual no se sobrescribe silenciosamente en un conflicto. Si DT es Sí con justificación, se conserva el seguimiento del operador y solo se oculta visualmente en el detalle. No se borra al recuperar ni al generar otra entrega.

**Un hallazgo ausente no queda automáticamente certificado como corregido.** Compruebe que se ejecutó correctamente la misma validación, con el mismo alcance de datos. Los archivos anteriores sirven como historial.

## 9. Conservar los detalles y repetir la validación

Los **detalles por componente son la fuente principal del seguimiento**. Guarde
las marcas y observaciones directamente en las hojas de reglas de cada Excel.
Después de editarlos, pulse **Recargar** en el componente correspondiente para
que el plugin lea los cambios y recalcule las estadísticas.

No se generan archivos adicionales de revisión consolidada ni se sincronizan
archivos automáticamente. La asociación de los detalles y la estadística viven
en memoria durante la sesión. Al cerrar o iniciar otra ejecución con revisión
cargada, puede cancelar o descartar ese estado de sesión; los Excel originales
no se modifican. No se ofrece guardar un consolidado. Minimizar conserva el
estado de la ventana.

Para otra ejecución, cargue los detalles revisados sobre los resultados nuevos.
Conserve por separado los reportes de cada entrega para mantener el historial.
No hay una base central automática de excepciones. **Generar reporte detallado**
produce una nueva entrega con los datos y seguimiento actuales de la ejecución;
antes de generarla, recargue los archivos que hayan sido editados.

## 10. Problemas frecuentes

| Situación | Qué revisar |
|---|---|
| No aparece el complemento | Busque su nombre completo, active la casilla y compruebe el resultado de Instalar desde ZIP. Reinicie QGIS tras actualizar. |
| `No module named openpyxl` o `psycopg2` | Instale la dependencia en el Python de QGIS; consulte al administrador de su instalación. |
| `no password supplied` | Distinga si falla el repositorio de sentencias o la conexión de datos. Revise las credenciales de esa conexión y su autenticación en QGIS. |
| `connection refused` o tiempo agotado | Revise servidor, puerto, disponibilidad y acceso de red. No es un fallo que se resuelva cambiando las excepciones. |
| Ejecutar validación está deshabilitado | Seleccione modelo y ambiente, cargue reglas activas y marque al menos un grupo. |
| SNC no carga automáticamente | Debe existir exactamente una versión publicada con reglas activas para el modelo. Cero o varias versiones bloquean la ejecución. |
| R1/R2 temporal no carga | Revise los encabezados, el archivo Excel y el permiso TEMP de la cuenta de datos. |
| Una regla exige R1/R2 | Prepare la referencia correspondiente o seleccione el R1 de public; no se sustituye por otra tabla automáticamente. |
| No aparece Sí/No | Seleccione una celda en la hoja de la regla. Use un reporte generado con una versión reciente, no solo un plugin actualizado. |
| Cero revisiones incorporadas | Consulte los conteos: sin correspondencia, ambiguas, datos alterados o identidad insuficiente. Compruebe que eligió el componente, versión y esquema correctos. |
| No se puede abrir la ayuda | Reinstale el ZIP completo para recuperar la guía local incluida. La ayuda interna no requiere Internet. |

Si necesita soporte, conserve versión de QGIS, versión del plugin, modelo, ambiente, versión SQL, componente, código de regla y mensaje completo. No incluya contraseñas. Si comparte un Excel para diagnóstico, use datos autorizados para compartir.

## 11. Administración del repositorio de sentencias

Esta sección corresponde al administrador del repositorio, no al operador que diligencia reportes.

- Las reglas individuales usan `activa`: solo se cargan las activas.
- Las tablas de versiones en `public` usan `descripcion_version` y `version_publicada`. El plugin lee ambos valores del primer registro de cada versión según `orden NULLS LAST`, `componente` y `codigo_regla`, incluyendo reglas inactivas.
- `version_publicada = FALSE` retira la versión del selector sin borrar las reglas. Mantenga estables el orden y la fila que contiene los metadatos.
- Una versión publicada debe tener reglas activas. Retirarla no revoca automáticamente las sentencias ya cargadas en otras sesiones.
- SNC consulta `public.reglas_cargue_snc_cica` o `public.reglas_cargue_snc_xtf`, según el modelo. Debe mantener una única versión publicada con reglas activas.
- Las referencias temporales necesitan marcadores como `{esquema_r1}.{tabla_r1}` y su equivalente R2. También se admiten las variantes con `{punto}` y sin separador. Un nombre permanente escrito literalmente en el SQL no se convierte automáticamente en una referencia temporal.
- Publique únicamente SQL revisado y compatible con el modelo, el esquema y los permisos de las cuentas que validan.

El script `sql/agregar_metadatos_version.sql` incluido en el paquete prepara las columnas de metadatos en las tablas existentes. No se ejecuta automáticamente desde la ayuda ni al instalar el plugin.

## Consultar esta guía dentro del plugin

El botón **Ayuda** abre la pestaña principal **Ayuda** de la misma ventana.
La guía se lee del paquete instalado y no necesita navegador ni conexión a
Internet. Use el índice o el buscador para localizar una sección y vuelva a
**Validación** para continuar trabajando.

## Mejoras de presentación y seguimiento en 2.0.0

- La pantalla muestra indicadores de hallazgos, excepciones DT y errores pendientes, además de una fila TOTAL por ejecución. Las excepciones del operador se muestran por separado; solo las de DT descuentan errores.
- Cada detalle muestra su archivo, última carga (hora de Colombia) y estado. Las incidencias de la última carga pueden desplegarse sin ocupar permanentemente el área de resultados.
- Si un detalle cargado cambia o deja de estar disponible, aparece un aviso y se bloquea la generación de reportes hasta volver a cargarlo. Se comprueba periódicamente mientras la ventana está visible y se verifica su contenido antes de exportar. Solo se detectan cambios guardados en el archivo; guarde primero en Excel.
- Los campos de observación se ensanchan según el contenido hasta el límite de Excel (255 caracteres de ancho); los textos extensos se ajustan en varias líneas. Las observaciones que comienzan con = se conservan como texto.
- Antes de ejecutar, se comprueba que existan las referencias R1/R2 requeridas por las sentencias seleccionadas.
- Los reportes incluyen identificador y fecha de ejecución, versión del plugin, modelo, ambiente, versión SQL, base y esquema. Estos datos de trazabilidad no modifican la clave estable de cada caso ni incluyen contraseñas.
- Las marcas y observaciones del operador se conservan cuando DT aprueba una excepción; su ocultación visual en el detalle no elimina esos datos.
