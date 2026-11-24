# Renumeración predial · v0.7.6

Plugin QGIS 3.28 o superior para identificar provisionales, consultar máximos R1, generar una propuesta y compararla con un archivo de renumeración. Todas las consultas de base se realizan en modo de solo lectura. No aplica actualizaciones de NPN.

## Instalación

Complementos → Administrar e instalar complementos → Instalar a partir de ZIP → `renumeracion_maximos_R1_v0.7.6.zip`.

Abra **Renumeración predial** desde el menú de base de datos o el icono. La ventana abre maximizada y permite minimizar y restaurar.

## 1. Fuente y referencia

- **CICA:** consulta fija `sentencias.snc_cica_copy.cica_predio` usando el acceso configurado en el Validador de Consistencia Lógica instalado. No se incluye una copia de su contraseña en el ZIP. Requiere USAGE del esquema y SELECT de la tabla para el usuario efectivo de esa conexión.
- **Modelo Interno de Levantamiento 1.0:** conexión guardada QGIS o directa PostgreSQL y esquema con `ilc_predio`. Reconoce `numero_predial` o `numero_predial_nacional` y nombres de tabla en mayúsculas. La contraseña directa solo se utiliza durante la sesión.
- En CICA pulse **Consultar departamentos y municipios CICA**. Se listan municipios con predios `etapa = VALIDADO` y `estado_control = DESCARGADO_AL_SNC`; la identificación usa las mismas condiciones.
- Después de consultar aparece **Copia base CICA · Fecha y hora del corte**, desde `inicio` del último registro por `id` en `public.copia_cica_progreso`, como en el validador. Si falta permiso para esa tabla se indica fecha no disponible y se permite leer predios.
- **Leer R1 del municipio** consulta automáticamente la última tabla `r1_DIVIPOLA_AAAAMMDD` de `sentencias.r1_r2`. Muestra vigencia y marca Leído. Requiere permiso de lectura de esas referencias.
- **Consultar máximos del R1**, al lado de la referencia, muestra únicamente el municipio seleccionado, sin Todos los municipios. Vistas Por zona–sector (6–9) y Por manzana/vereda (1–17), sin la pestaña redundante Por prefijo 13. El prefijo 13 sigue usándose internamente.
- Los NPN R1 se cuentan sin duplicados. Los valores numéricos Excel o NPN incompletos se informan, sin reconstruir ceros o dígitos.

## 2. Alcance y diagnóstico

Pulse **Identificar predios a renumerar**. CICA identifica 7, 8 o 9 en posición 14 o 18; Modelo Interno, cualquier letra en esas posiciones.

- Arriba: manzanas/veredas nuevas (provisional en posición 14), agrupadas por prefijo 1–9, con detalle desplegable 1–17.
- Abajo: todos los predios identificados, en el mismo resumen desplegable 1–9 → 1–17.
- Urbano y CP se denominan **Manzana**; Rural, **Vereda**.
- El filtro de alcance aparece en este paso, después de identificar la fuente. Muestra solamente los códigos 6–7 con provisionales: Rural 00, Urbano 01 y cada CP 02–99. Se pueden combinar. Cambiarlo actualiza el diagnóstico y limita la propuesta y los resúmenes exportados.
- Se distinguen predios, terrenos distintos (1–21) y manzanas/veredas nuevas: un PH puede contener muchos predios y consumir un solo consecutivo de terreno.

**Ver estadísticas CICA** abre el informe de todas las etapas del municipio: totales, activos/cancelados, reconocimiento y control separados por estado, faltantes para el 100 %, activos sin áreas y resultado final cargados SNC. Incluye filtros independientes de zonas y detalle de NPN paginado. No modifica el alcance de la propuesta.

## 3. Propuesta y comparación

Se habilita **Generar propuesta y comparar archivo** cuando hay R1 del mismo municipio y provisionales seleccionados. Abre una ventana independiente con propuesta, comparación y filas no utilizadas.

### Reglas de generación

1. Se ordenan los provisionales de menor a mayor. Sus saltos no se trasladan al definitivo.
2. Cada manzana/vereda provisional completa (1–17) recibe un consecutivo desde el máximo R1 + 1 del mismo prefijo territorial 1–13. Todos sus predios comparten el nuevo bloque 14–17.
3. Dentro de una manzana/vereda existente, los terrenos se asignan desde su máximo R1 de posiciones 18–21 + 1.
4. En manzanas/veredas nuevas, los grupos de terreno se enumeran desde 0001, en orden de sus provisionales.
5. Un grupo de terreno (1–21) recibe un solo consecutivo. La condición 2 puede compartirlo con un predio base de condición 0, 3, 4, 8 o 9. Los predios de PH (9) y condominio (8) con el mismo prefijo 1–22 comparten el terreno.
6. Se conservan la condición en posición 22 y todo el contenido 23–30.
7. Si falta referencia R1, se agota 9999, se repite un terreno con una combinación no definida, o hay colisión de definitivos, se marca **Pendiente** sin generar NPN para esos registros. No se inventan máximos.

### Archivo de comparación

Cargue Excel `.xlsx`, elija hoja y compare **A = nuevo definitivo; B = provisional**. Se admiten cabeceras o datos desde la primera fila. Los NPN deben estar almacenados como texto para conservar precisión y ceros iniciales.

Se distinguen Coincide, Diferencia, Falta en archivo, Pendiente de generar, provisionales o definitivos duplicados y filas inválidas. Las tablas y exportación de comparación solo incluyen los provisionales de la propuesta; los registros externos se omiten y se informa su cantidad. A = B se trata como Sin cambio fuera del alcance únicamente si no corresponde a un provisional identificado; si sí corresponde se compara con el esperado.

**Coincide significa que el archivo coincide con la propuesta calculada; no acredita que el cambio ya haya sido aplicado en la base.** Generado tampoco significa aprobado ni ejecutado. Los casos pendientes conservan su explicación.

Exporte la propuesta y comparación a Excel. La hoja Renumeracion mantiene A nuevo / B provisional; Bases R1 conserva máximos utilizados. El resumen incluye fuente, corte, R1, huella SHA256, zonas, fecha y conteos. No se modifica el archivo cargado ni la base.

## Verificación

`QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 /workspace/.venvs/calidad-qgis/bin/python -m unittest discover -s tests_maximos_r1`

Pruebas de agrupación, deduplicación, aislamiento territorial, máximos y faltantes, orden sin saltos, condición 2, PH/condominio, sufijos, agotamiento, comparación, lectura Excel y exportación. La conectividad institucional debe verificarse en QGIS desde la red de la entidad.

## Agrupación y filtros en propuesta y comparación

Ambas tablas muestran dos niveles: **prefijo 1–9 → código 10–13**, con los provisionales individuales desplegables debajo. Los encabezados territoriales se mantienen al filtrar. Cada subgrupo usa el prefijo completo 1–13 para mostrar **máximo manzana/vereda R1** e **inicio (máximo + 1)**. Si un grupo 1–9 contiene varios subgrupos con referencias distintas, se indica Ver subgrupos 10–13 para evitar presentar un único inicio incorrecto. El máximo e inicio de terreno se presentan por cada manzana/vereda en las filas individuales. Agotados y referencias ausentes se muestran explícitamente.

Pulse cualquier encabezado **▾** para filtrar esa columna por texto o uno de los valores sugeridos. Los filtros de varias columnas se combinan con la búsqueda y el filtro de resultado. **Limpiar filtros de columnas** restablece los encabezados. El selector **Desagregación de la vista** controla el árbol.

El Excel conserva la hoja A nuevo / B provisional, exporta las filas visibles según los filtros y añade **Grupos y maximos R1** con claves 1–9, 10–13, referencia completa e inicios de cada subgrupo. Conserva en Resumen los filtros empleados y la cantidad de filas externas omitidas.


## Terrenos 090x del R1 con condición 9

En Propuesta y comparación aparece **Tomar terrenos 090x (0900–0909), condición 9, como máximos R1**, desmarcado por defecto. Solo afecta a posiciones 18–21 y condición 9 en posición 22; no modifica máximos de manzana/vereda ni excluye terrenos de otras condiciones o códigos fuera de 0900–0909.

- Sin marcar: el inicio usa el mayor terreno elegible de la misma manzana/vereda, excluyendo esos registros PH.
- Marcado: el cálculo considera también esos terrenos del R1.
- Cambiar la opción regenera la propuesta y recalcula una comparación ya cargada. Los NPN originales del R1 y de la fuente permanecen intactos.
- Si no queda ningún terreno elegible, el caso queda Pendiente con motivo específico; no se supone máximo cero. Un definitivo ya existente en el R1 también queda Pendiente, sin saltar automáticamente números.
- La elección se registra en Resumen del Excel; Bases R1 refleja los máximos efectivos usados. Para recalcular sin volver a consultar el servidor se conserva en memoria la colección de NPN únicos del R1 leído.

La comparación genera resultados únicamente para provisionales de la propuesta seleccionada. Los no provisionales y otros registros externos del archivo no se incorporan como filas a la tabla ni a la exportación de comparación; se informa su cantidad omitida.


## Vista por sectores en Propuesta y Comparación

Ambas pestañas presentan un árbol como el diagnóstico, con **Prefijo territorial** y **Agrupación** como primeras columnas. El sector muestra el prefijo 1–9; debajo, la subdivisión 10–13 identificada con su prefijo completo 1–13; al desplegar, los provisionales muestran su manzana o vereda 1–17 y el NPN en su columna correspondiente. Los encabezados de grupo se resaltan visualmente.

El selector **Desagregación de la vista** permite alternar entre **Sectores · 1–9**, **Sector y subdivisión · 1–9 → 10–13** (inicial) y **Detalle de provisionales**. Se aplica a las dos pestañas, conserva filtros y no recalcula la numeración ni crea un reporte adicional. También se puede desplegar manualmente cada sector con su flecha.

El paquete configurado puede incluir una configuración local de sentencias, que prevalece sobre la del validador instalado y se aplica a CICA y R1 precargado. Esa configuración se entrega solo en el ZIP privado y no se versiona en el repositorio.


## Selección de esquemas del Modelo Interno

El botón **Consultar esquemas** aparece antes del selector. El desplegable agrupa **Departamento → Municipio (DIVIPOLA) → Esquema**, con conteos por municipio y selección exclusiva de los esquemas. Los nombres sin código reconocido aparecen en Sin ubicación identificada. Al seleccionar uno se consulta el municipio real desde los NPN de ILC_Predio y se muestra en **Municipio a validar**; si solo hay uno se selecciona automáticamente. Si contiene varios, se elige entre los encontrados. No se muestra el antiguo campo manual Municipio · DIVIPOLA. La lectura de provisionales y el R1 utilizan ese municipio real. La ubicación del esquema seleccionado se actualiza en el árbol según los datos consultados.

El ZIP público v0.7.6 se descarga desde GitHub y no contiene contraseñas. Configura sentencias con admin_ant. Reutiliza el acceso del validador solo si coincide con ese usuario y servidor; de lo contrario pide la contraseña una vez por sesión. La configuración local privada continúa teniendo prioridad si existe.
