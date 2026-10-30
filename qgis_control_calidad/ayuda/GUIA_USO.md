# Ayuda operativa — Validador Consistencia Lógica Alfanumérica

Siga los pasos en orden para preparar la validación, revisar sus resultados y gestionar las excepciones. La ayuda permanece dentro del plugin; use el buscador para localizar una opción.

## Contenido

1. [Abrir el plugin](#1-abrir-el-plugin)
2. [Seleccionar modelo y ambiente](#2-seleccionar-modelo-y-ambiente)
3. [Conectar la Base catastral a validar](#3-conectar-la-base-catastral-a-validar)
4. [Cargar archivos CICA](#4-cargar-archivos-cica)
5. [Seleccionar R1 y R2](#5-seleccionar-r1-y-r2)
6. [Consultar estadísticas y aplicar filtros](#6-consultar-estadísticas-y-aplicar-filtros)
7. [Confirmar y ejecutar la validación](#7-confirmar-y-ejecutar-la-validación)
8. [Interpretar los resultados](#8-interpretar-los-resultados)
9. [Generar y consultar los reportes](#9-generar-y-consultar-los-reportes)
10. [Diligenciar excepciones en Excel](#10-diligenciar-excepciones-en-excel)
11. [Cargar o recargar detalles revisados](#11-cargar-o-recargar-detalles-revisados)
12. [Descargar el formato homologado](#12-descargar-el-formato-homologado)
13. [Resolver situaciones frecuentes](#13-resolver-situaciones-frecuentes)

## 1. Abrir el plugin

1. En QGIS, abra **Base de datos → Validador Consistencia Lógica Alfanumérica**, o pulse su icono.
2. Si todavía no está instalado, vaya a **Complementos → Administrar e instalar complementos → Instalar desde ZIP** y seleccione el ZIP del plugin sin descomprimirlo.
3. Después de actualizar el plugin, reinicie QGIS.

Tenga disponibles la conexión a la Base catastral a validar y los archivos que utilizará. Para Modelo Interno/XTF, la base debe estar previamente preparada en PostgreSQL. Para CICA puede consultar una base existente o utilizar archivos durante la sesión.

## 2. Seleccionar modelo y ambiente

1. En **Conexión**, seleccione **Modelo Interno de Levantamiento 1.0** o **CICA**. Para datos XTF, elija Modelo Interno.
2. Seleccione el ambiente:
   - **Validaciones del modelo:** pulse **Buscar versión de sentencias…** y seleccione la versión publicada que corresponda.
   - **Validaciones para cargue a SNC:** espere la carga de su versión disponible; no requiere escoger otra versión manualmente.
3. Compruebe la versión y la cantidad de sentencias mostradas.

Volver a seleccionar el modelo limpia el ambiente y la versión SQL. Si lo hace, elija nuevamente ambas opciones.

## 3. Conectar la Base catastral a validar

### Conexión guardada en QGIS

1. Elija **Conexión guardada en QGIS**.
2. Pulse **Actualizar** si agregó o cambió conexiones en QGIS.
3. Seleccione la conexión y compruebe la base de datos indicada.
4. Pulse **Listar Esquemas** y elija **Esquema a validar**.

### Conexión manual

1. Elija **Conexión manual a PostgreSQL**.
2. Conserve el servidor establecido y complete puerto, base de datos, usuario y contraseña.
3. Pulse **Listar Esquemas** y seleccione el esquema.

Si la conexión falla, revise los datos de acceso y su conexión de red antes de continuar.

## 4. Cargar archivos CICA

Use esta función únicamente si validará archivos CICA. Si consultará las tablas de una base CICA existente, continúe con R1/R2.

1. Seleccione **CICA** y pulse **Seleccionar fuente de datos…**.
2. Elija **Archivos CSV del usuario** o **sentencias.snc_cica_copy**. Para la segunda opción, pulse **Leer tablas**: se consultan las siete tablas y se muestran sus cantidades. Al seleccionar esta fuente se muestra la última fecha de marca registrada en `snc_cica_crudo.control` (campo `fecha_marca`). Si no se puede consultar, se indica como no disponible. La lectura no modifica el esquema. Para CSV, pulse **Cargar CSV…** junto al tipo de archivo correspondiente: Datos Contacto, Datos Predio - Derecho, Predio, Datos Propietario, Justificación, Seguimiento de Control o Unidad de Construcción.
3. Si utilizará una geodatabase, pulse **Seleccionar geodatabase…** y elija una carpeta `.gdb` o un ZIP que contenga una sola geodatabase.
4. Revise los nombres y cantidades informados. El resumen general muestra los predios activos y cancelados de la fuente seleccionada, sin aplicar filtros. Los otros estados se indican aparte. Para la distribución territorial y los filtros detallados, utilice la pestaña de estadística y filtro avanzado.
5. Pulse **Usar fuente de datos** para aplicar la selección.

Puede reemplazar un archivo sin volver a seleccionar los demás. Si una tabla está tanto en los CSV o en la copia de snc_cica_copy como en la geodatabase, se utilizan los datos tabulares seleccionados. Los archivos no seleccionados se consultan en el esquema elegido.

Los originales no se modifican. Los archivos preparados están disponibles durante la sesión; al cerrar el plugin deberá cargarlos nuevamente. **Cancelar** conserva la selección anterior.

## 5. Seleccionar R1 y R2

Abra **Referencias R1/R2** y elija una opción.

### Archivos R1 y R2 cargados por usuario

1. Pulse **Cargar R1 / R2…**.
2. Seleccione el Excel R1 y el Excel R2 cuando lo requieran las reglas.
3. Pulse **Preparar referencias temporales** y después **Aceptar**.
4. Compruebe los archivos y cantidades que aparecen en la pestaña.

El Excel debe tener los encabezados en la primera fila de la hoja activa. Conserve los identificadores como texto para evitar pérdida de ceros iniciales o dígitos.

| Archivo | Encabezados requeridos |
|---|---|
| R1 | `NUMERO_PREDIAL`, `DESTINO_ECONOMICO`, `AREA_TERRENO`, `AREA_CONSTRUIDA`, `AVALUO`, `VIGENCIA` |
| R2 | `NUMERO_PREDIAL`, `MATRICULA_INMOBILIARIA`, `AREA_TERRENO_1`, `AREA_CONSTRUIDA_1`, `VIGENCIA` |

### R1 y R2 Vigente

1. Elija **R1 y R2 Vigente** y pulse **Consultar R1 y R2 Vigente** si necesita actualizar el listado.
2. Busque y seleccione el municipio por nombre o DIVIPOLA.
3. Verifique la fecha y las tablas R1/R2 disponibles para ese municipio.
4. Compruebe que la selección corresponde a la Base catastral a validar.

Si una referencia requerida no está disponible, selecciónela o cárguela antes de ejecutar.

## 6. Consultar estadísticas y aplicar filtros

La pestaña **Estadística y filtro avanzado** se habilita cuando estén seleccionadas la Base catastral a validar y la referencia R1.

1. Abra la pestaña y revise la distribución de Urbano, Rural y Centro poblado.
2. Identifique los datos por color: **verde para la Base catastral a validar** y **azul para R1**.
3. Revise los predios activos y cancelados de la base, cuando se puedan determinar. En R1 cada NPN completo cuenta una sola vez, aunque esté repetido.
4. Pulse **Ver estadísticas y seleccionar filtros…** para abrir la ventana de selección.
5. En **Alcance**, marque una o varias opciones: Urbano (`01`), Rural (`00`) o Centro poblado (`>01`). **Todos** no restringe el alcance.
6. Opcionalmente, busque y marque manzanas/veredas usando los primeros **17 dígitos del NPN**.
7. Revise la cantidad y el porcentaje incluidos para cada origen.
8. Pulse **Aplicar filtro**. **Cancelar** mantiene la selección anterior.

**Seleccionar todo** y **Deseleccionar todo** actúan sobre los códigos visibles según la búsqueda y el alcance. Las marcas de códigos ocultos se conservan; revise el contador antes de aplicar. Sin códigos marcados se incluyen todos los del alcance elegido.

El filtro se aplica a la Base catastral a validar y a R1/R2. Al cambiar de origen se limpian los códigos seleccionados y las estadísticas anteriores. Use **Actualizar estadísticas** para volver a consultar los datos.

## 7. Confirmar y ejecutar la validación

1. En **Controles a ejecutar**, abra **Seleccionar grupos** y marque los componentes que necesita. Puede usar **Seleccionar todos** o **Desmarcar todos**.
2. Para SNC, compruebe que esté seleccionado **+ Cargue SNC**.
3. Pulse **Ejecutar validación**.
4. Revise el resumen: modelo, ambiente, versión SQL, base, esquema, alcance, manzanas/veredas, archivos CICA y cantidad de reglas por componente.
5. Si algo no corresponde, pulse **Cancelar** y ajuste la selección. Los resultados y revisiones anteriores se conservan.
6. Para iniciar, pulse **Ejecutar validación** dentro de la confirmación y atienda cualquier aviso de revisión pendiente.
7. Espere a que finalice el proceso y revise los resultados.

Puede minimizar la ventana y restaurarla desde el icono del plugin. No cierre QGIS durante la validación o la generación de reportes.

## 8. Interpretar los resultados

| Columna | Qué significa |
|---|---|
| Reglas ejecutadas | Controles procesados por componente. |
| Hallazgos | Inconsistencias encontradas; no necesariamente corresponden a predios distintos. |
| Excepciones DT | Excepciones marcadas por DT con observación válida. |
| Excepciones operador | Propuestas justificadas del operador; no descuentan errores. |
| Errores | Hallazgos menos excepciones DT. |
| Errores técnicos | Controles que no pudieron completarse por un problema técnico. |

**Solo las excepciones validadas y marcadas por DT descuentan errores.** Por ejemplo, 100 hallazgos y 10 excepciones DT dejan 90 errores, aunque existan otras marcas del operador.

Si aparecen errores técnicos, consulte el mensaje antes de considerar completa la validación. La ausencia de hallazgos en una regla que falló no significa que los datos estén correctos.

## 9. Generar y consultar los reportes

1. Al finalizar, pulse **Generar reporte detallado**.
2. Seleccione la carpeta donde guardará los Excel y espere el mensaje de finalización.
3. Abra `resumen_control_calidad_<fecha>.xlsx` para consultar el resumen ejecutivo, los metadatos de la validación, el reporte general, los hallazgos por predio y los errores técnicos. La versión del plugin aparece únicamente en este archivo.
4. Abra `detalle_<componente>_<fecha>.xlsx` para revisar los hallazgos de cada componente.
5. En **Detalle Validación**, compruebe los metadatos superiores y pulse un vínculo azul, por ejemplo **↪ Ir a 1_12**, para abrir la regla en el mismo archivo.
6. Revise las columnas y valores devueltos por la regla. El NPN se presenta como **Numero_Predial_Nacional**, sin duplicar sus alias.
7. Consulte **Reglas & Componente** si necesita ver las reglas, hallazgos, descripciones y mensajes técnicos del componente.

Las hojas de reglas conservan sus identificadores y se ordenan numéricamente. Solo se generan detalles para los componentes con hallazgos.

Los reportes están protegidos. Puede ajustar anchos de columna y utilizar los filtros existentes. La primera columna y los encabezados permanecen fijos. No cambie nombres de hojas, encabezados ni datos automáticos; conserve el archivo completo para recuperar revisiones.

## 10. Diligenciar excepciones en Excel

1. Abra el detalle del componente y entre en la hoja de la regla.
2. Para una excepción validada por DT, marque **Excepción DT = Sí** y diligencie **Observación DT**.
3. Para una propuesta del operador, marque **Excepción operador = Sí** y diligencie **Observación operador**.
4. Para retirar una marca, cambie su valor a **No**.
5. Guarde el archivo Excel.

Las marcas usan el desplegable **Sí / No**: Sí se muestra en verde tenue y No en rojo tenue. Puede escribir la observación antes o después de marcar la excepción, pero una excepción sin justificación válida no se incorporará al cargar el archivo. Los espacios no cuentan como justificación.

Las marcas del operador permanecen visibles cuando DT aprueba el caso. Solo DT descuenta errores. La hoja **Revisión** está oculta y se calcula desde los detalles; no necesita editarla ni mostrarla.

## 11. Cargar o recargar detalles revisados

1. Si ajustaron la Base catastral, ejecute nuevamente las validaciones con la configuración correspondiente.
2. En **Gestión de Excepciones**, pulse **Cargar** en la fila del componente que va a revisar.
3. Seleccione su archivo `detalle_<componente>_….xlsx`. No seleccione el resumen ejecutivo ni un formato homologado.
4. Lea el mensaje de carga: excepciones incorporadas, descartadas y casos sin correspondencia o con conflicto.
5. Repita la carga para cada componente revisado y compruebe las estadísticas actualizadas.
6. Si vuelve a editar un detalle, guárdelo y pulse **Recargar** en su fila.
7. Antes de generar otra entrega, recargue todos los archivos que hayan cambiado.

Las revisiones solo se recuperan para el mismo caso sin cambios relevantes. Un caso nuevo, modificado o ambiguo queda pendiente. Una excepción sin observación no se incorpora como excepción. La carga no sobrescribe silenciosamente una revisión en conflicto.

Puede editar y volver a cargar el Excel; no hay que liberar el archivo desde el plugin. Si figura como no disponible, guárdelo en una ubicación accesible y selecciónelo otra vez con **Recargar**.

Conserve los Excel revisados en su carpeta de trabajo. Después de cerrar el plugin o iniciar una nueva ejecución, cargue nuevamente los detalles sobre los resultados que corresponda. No se guardan automáticamente las revisiones en una base central.

## 12. Descargar el formato homologado

1. Ejecute **Validaciones del modelo** con una versión V2 de CICA o Modelo Interno.
2. Al finalizar, pulse el enlace de descarga del formato correspondiente.
3. Seleccione la carpeta y guarde el Excel:
   - Modelo Interno V2: **fo_gct_pc01_07_v2.xlsx**.
   - CICA V2: **cons_log_cica_v2.xlsx**.

El formato se entrega para diligenciarlo; no se completa automáticamente. El enlace no está disponible para SNC, V3 o una ejecución en la que todas las reglas terminaron con error técnico.

## 13. Resolver situaciones frecuentes

| Situación | Qué hacer |
|---|---|
| No aparecen versiones de reglas | Compruebe el acceso al repositorio y consulte al responsable de publicar las reglas. |
| Ejecutar validación está deshabilitado | Seleccione ambiente, versión con reglas disponibles y al menos un grupo de controles. |
| Estadística y filtro avanzado está deshabilitada | Seleccione la Base catastral a validar y cargue R1, o seleccione un municipio con R1 vigente. |
| No aparecen esquemas | Revise la conexión y pulse Listar Esquemas. |
| Un archivo CICA o R1/R2 no se acepta | Revise que eligió el tipo correcto y que los encabezados y datos cumplen lo indicado en el mensaje. |
| Aparece un error de permisos | Solicite al responsable acceso de consulta y permiso para usar datos temporales en la base. |
| Una estadística figura como no disponible | Actualice los datos y consulte el mensaje del origen; no la interprete como cero. |
| No se reconocen excepciones | Compruebe el componente, los valores Sí/No, las observaciones y que el caso corresponda a la ejecución actual. |
| Un Excel editado no cambia las cifras | Guárdelo y pulse Recargar en el componente correspondiente. |
| No se puede generar el reporte | Revise los avisos, cierre archivos de salida abiertos en Excel y recargue los detalles modificados o no disponibles. |
| La generación termina con error | Consulte Incidencias y entregue el mensaje completo al responsable de soporte. |

En CICA, la ventana de estadística y filtro avanzado también muestra el **Seguimiento CICA por etapas**, consultado en `sentencias.snc_cica_copy.vw_seguimiento_predios_2026`. Incluye los totales por municipio y zona, reconocidos, control de calidad, áreas geográficas, cargados SNC, cancelados, fecha de actualización y códigos NPN existentes. Es el resumen general publicado en la vista; no se recalcula al seleccionar filtros ni equivale necesariamente a los CSV/GDB cargados. Si no hay acceso a la vista, se informa sin impedir el uso de las demás estadísticas y filtros.
