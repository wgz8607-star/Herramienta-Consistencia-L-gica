# Renumeración predial — Máximos R1

Plugin QGIS independiente, versión inicial 0.6.1. No depende del Validador de Consistencia Lógica ni cambia su instalación.

## Alcance

Visualiza los máximos existentes del R1 elegido. No cambia números prediales ni aprueba renumeraciones. Las reglas especiales de condición 8 y 9 quedan para otra fase; los códigos válidos existentes sí forman parte del resumen R1.

- **Por zona–sector:** DIVIPOLA y código de posiciones 6–9; muestra el máximo bloque de manzana y un NPN de referencia.
- **Por prefijo 13:** máximo de manzana dentro del mismo prefijo territorial de 13 dígitos. Esta es la referencia que se usará posteriormente para comprobar una manzana nueva.
- **Por manzana:** prefijo completo de 17 dígitos y máximo de terreno (posiciones 18–21), con su NPN de referencia.
- Los siguientes consecutivos son informativos. 9999 se muestra como agotado.

## Instalación

En QGIS: Complementos → Administrar e instalar complementos → Instalar a partir de ZIP. Instale el paquete `renumeracion_maximos_R1_v0.6.1.zip`. Abra **Renumeración · Máximos R1** desde el menú de base de datos o su icono.

## Uso

1. Elija el origen R1: archivo Excel/TXT, tablas precargadas en `r1_r2`, o una tabla de `public`.
2. Para Excel, seleccione hoja y columna NPN; si hay una hoja `R1`, se propone esa hoja. Para TXT se usa el estándar R1 de 312 caracteres, con NPN en posiciones 1–30.
3. Para precargados se utiliza el acceso institucional a sentencias. Para public se reutiliza la base seleccionada en la ventana principal; consulte las tablas sin seleccionar otra conexión. Los precargados se consultan en `sentencias.r1_r2` institucional, muestran el municipio y la última fecha disponible de cada municipio, y actualizan la vigencia en la opción 2. Se reconocen nombres `r1_DIVIPOLA_AAAAMMDD`. En public se listan las tablas/vistas con columna NPN; seleccione la referencia R1 correcta.
4. Pulse **Leer R1 y calcular máximos**.
5. Filtre por municipio, zona–sector o prefijo y consulte las tres pestañas. Los NPN duplicados se cuentan una sola vez. Los inválidos y vacíos se informan; no se reconstruyen ceros ni dígitos faltantes.
6. Exporte los máximos visibles a Excel. El resumen conserva el origen, los filtros y los conteos completos de la lectura.

Las conexiones usan autenticación guardada de QGIS o contraseña suministrada para la sesión. El paquete no contiene credenciales. Todas las consultas PostgreSQL se ejecutan en modo de solo lectura.

No se utiliza como referencia el archivo de resultados de renumeración: los máximos se calculan exclusivamente desde el R1 seleccionado.


## Identificar predios a renumerar

Abra **Predios a renumerar · CICA / Modelo Interno**. Elija **CICA** o **Modelo Interno de Levantamiento 1.0**, y una conexión guardada en QGIS o una conexión directa PostgreSQL. Las contraseñas directas solo se usan durante esta ventana. CICA consulta `sentencias.snc_cica_copy.cica_predio`; Modelo Interno permite listar esquemas con `ilc_predio` y seleccionar uno en la base de la conexión. Se reconocen `numero_predial` y `numero_predial_nacional`, incluso con nombres de tabla en mayúsculas. Puede restringir la consulta por DIVIPOLA o consultar todos los municipios.

CICA identifica 7, 8 o 9 en posición 14 o 18; Modelo Interno identifica cualquier letra en esas posiciones. El listado distingue manzana, terreno o ambos, excluye NPN duplicados e informa registros inválidos. CICA incluye únicamente `etapa = VALIDADO` y `estado_control = DESCARGADO_AL_SNC`; el filtro se aplica en PostgreSQL junto a la DIVIPOLA y se registra en el origen exportado. Modelo Interno no filtra etapas ni estados. Las condiciones 8 y 9 en posición 22 se muestran como pendientes de revisión especial. Se exportan listado, procedencia e inválidos a Excel.

Esta fase identifica provisionales actuales. Los máximos siguen calculándose exclusivamente desde el R1. La comparación con el archivo de renumeración y la comprobación de cambios aplicados pertenecen a la siguiente fase.

En CICA se pueden combinar Urbano (01), Rural (00) y Centro poblado (02–99), según posiciones 6–7 del NPN. Las tres zonas se proponen marcadas; se exige al menos una y el alcance se conserva en la exportación.

Al abrir el plugin se muestra primero la selección de fuente CICA / Modelo Interno, conexión y alcance. Desde esa ventana, el botón **Consultar máximos del R1…** abre la consulta de referencias R1.

### Inicio y selección territorial CICA

La ventana inicial es la selección de fuente. En CICA se ocultan las conexiones y se usa la copia fija `sentencias.snc_cica_copy.cica_predio`. Pulse **Consultar departamentos y municipios CICA** y seleccione departamento y municipio. El catálogo incluye municipios con predios VALIDADO / DESCARGADO_AL_SNC. Se reutiliza la configuración de sentencias del Validador de Consistencia Lógica instalado, incluida su contraseña, sin volver a solicitarla. Para CICA debe estar instalado ese validador. El nuevo ZIP no incorpora una copia de la contraseña. Modelo Interno conserva las conexiones guardadas QGIS y la conexión directa PostgreSQL.

El botón **Comprobar acceso a copia CICA** informa base, servidor, usuario de sesión, usuario efectivo y permisos USAGE/SELECT en la conexión real. La misma comprobación se realiza antes de leer la copia. No muestra contraseñas.


### Interfaz CICA y estadísticas

La interfaz inicial utiliza tarjetas claras y botones azules, con controles deshabilitados en gris. En CICA se ocultan conexiones, esquema y controles/textos de Modelo Interno; se muestra la fecha de copia desde el último registro (id descendente) de `public.copia_cica_progreso.inicio`. Si el usuario de lectura no tiene permiso sobre esa tabla, se muestra fecha no disponible sin bloquear los predios. Ya no se presenta el botón de diagnóstico; se conserva la comprobación de permisos al consultar.

Al seleccionar municipio se consultan únicamente sus zonas con predios `VALIDADO` y `DESCARGADO_AL_SNC`. Las zonas ausentes se ocultan y no quedan seleccionadas.

**Ver estadísticas CICA…** abre el informe de avance del municipio para todas las etapas: totales, activos y cancelados; reconocimiento y control separados por estado con faltantes al 100%; activos sin área geográfica; resultado final cargados SNC. Los selectores de zonas se pueden combinar. El detalle incluye tabla por etapa y códigos NPN paginados. Las estadísticas no modifican el filtro de identificación de provisionales. Fórmulas equivalentes a las del validador: reconocimiento excluye SIN_ASIGNAR/PRE_ASIGNADO/ASIGNADO/PARA_DISPOSITIVO/EN_DISPOSITIVO; control incluye CONTROL_CALIDAD_GENERAL/CONTROL_CALIDAD_GRUPO/DEVUELTO/RECHAZADO/VALIDADO; SNC requiere VALIDADO y DESCARGADO_AL_SNC.

### Máximos por zona–sector

La agrupación del resumen y el filtro usan posiciones 6–9 (cuatro dígitos): zona (6–7) más sector (8–9). La clasificación Urbano/Rural/CP sigue dependiendo de 6–7. Los máximos base de manzana se mantienen por prefijo 1–13, y los de terreno por manzana 1–17. La exportación conserva los códigos como texto. La consulta de máximos no muestra conexiones QGIS: precargados usa sentencias; Public reutiliza la base de la fuente principal.

En opción 2 el catálogo se consulta automáticamente cuando hay municipio seleccionado en la fuente, y se propone su R1 de última vigencia. CICA transmite el municipio elegido; Modelo Interno usa la DIVIPOLA indicada o un código inequívoco en el esquema. Si el municipio no tiene R1 precargado, se informa y no se selecciona por defecto otro municipio.

La pestaña y hoja Excel **Por prefijo 13** se omiten para evitar una vista redundante. Se conservan los cálculos internos por prefijo territorial de 13 dígitos y las vistas Por zona–sector y Por manzana.

La ventana de máximos solo incluye lectura, consulta y exportación de R1; se retira el botón para abrir predios a renumerar. Esta función permanece en la ventana principal.

### Lectura R1 en ventana principal

La sección R1 precargado aparece después del municipio. **Leer R1 del municipio** se habilita con un municipio válido y consulta su última vigencia en sentencias.r1_r2. Al lado de la referencia y vigencia se encuentra **Consultar máximos del R1**, habilitado tras una lectura correcta. Esa ventana muestra únicamente los resultados, filtros y exportación; no pide de nuevo origen ni conexión. Al cambiar de municipio se descarta la referencia anterior.

### Resumen de predios identificados

El resultado muestra únicamente estadísticas: prefijo 1–9 (municipio + zona–sector), desplegable a manzana–vereda completa 1–17. Se cuentan NPN únicos, manzanas–veredas, terrenos distintos por prefijo 1–21 y condiciones 8/9 pendientes. No se muestran filas individuales de NPN en esa tabla. El Excel exporta Por zona-sector y Por manzana-vereda. La selección Zonas CICA se retira de la ventana principal: la identificación incluye todas las zonas del municipio, conservando VALIDADO / DESCARGADO_AL_SNC. El informe de avance conserva sus propios filtros de zonas.

### Dos secciones de identificación

La sección 2 se denomina **Manzanas - Veredas nuevas y predios a renumerar**. Arriba se agrupan por 1–17 únicamente las manzanas/veredas con provisional en posición 14. Abajo se conserva el resumen de todos los predios identificados por 1–9, desplegable a 1–17. Urbano y CP se denominan Manzana; Rural se denomina Vereda. El Excel incluye la hoja Manzanas-Veredas nuevas además de los resúmenes previos.

En Máximos, el municipio seleccionado en la fuente se transmite a la lectura del R1 y se muestra como única opción, sin Todos los municipios. Se conservan los cálculos internos por prefijo 13. Estos cambios son de identificación y consulta: la comprobación de consecutivos contra el archivo de renumeración continúa pendiente de implementación.

La ventana principal abre maximizada y permite minimizar/restaurar/maximizar. Las manzanas o veredas nuevas se resumen por prefijo 1–9 con detalle desplegable 1–17; los botones Desagrupar detalle y Agrupar por zona–sector permiten expandir o contraer todo. Excel incluye resumen de nuevas por zona-sector y su detalle por manzana/vereda.
