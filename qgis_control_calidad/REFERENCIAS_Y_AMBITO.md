# Referencias R1/R2 y filtro avanzado — 2.6.0

La pestaña **Filtro avanzado** se encuentra después de **Referencias R1/R2**. Se habilita únicamente al seleccionar la fuente de datos (esquema de Modelo Interno/XTF o CICA, o fuente temporal cica_predio) y la fuente de R1 (archivo temporal preparado o municipio con R1 vigente disponible). Elegir solo el modo de referencia no es suficiente.

## Ámbito y manzanas/veredas

El cuadro Ámbito contiene casillas para combinar Urbano (01), Rural (00) y Centro poblado (>01), usando las posiciones 6–7 del NPN. Todos es el valor inicial e incluye registros sin ámbito identificable. Marcar los tres ámbitos equivale a Todos. No se permite aplicar sin seleccionar al menos uno.

La lista presenta códigos de manzana/vereda de 17 dígitos (posiciones 1–17 del NPN) encontrados en la fuente o en R1. La columna de cantidades muestra exclusivamente predios únicos de R1. Seleccionar todo y Deseleccionar todo actúan sobre los códigos visibles según el ámbito y la búsqueda; las selecciones ocultas se conservan. La búsqueda solo afecta a la lista, no al conteo ni a la validación. Sin códigos marcados se incluyen todos los del ámbito elegido.

La pestaña muestra un resumen general por ámbito con columnas separadas para la fuente de validación y R1. El botón **Ver estadísticas y seleccionar filtros…** abre una ventana independiente, ampliable y con desplazamiento, donde se revisan cantidades por código y se seleccionan los filtros. **Aplicar filtro** guarda la selección antes de ejecutar; **Cancelar** conserva la selección aplicada. El resumen de la pestaña muestra el filtro aplicado. Al cambiar de fuente se eliminan códigos seleccionados y estadísticas anteriores; al entrar en la pestaña se consultan los datos nuevos. **Actualizar datos de la fuente** permite consultar nuevamente el mismo origen.

## Estadísticas de la fuente y de R1

Se muestran por separado las estadísticas de la fuente de validación y de R1: totales y distribución por ámbito. La ventana independiente agrega cantidades por código de manzana/vereda e incluidos en el filtro (cantidad y porcentaje). La fuente cuenta registros, incluidos duplicados; R1 cuenta NPN únicos. No se presentan cantidades de R2 ni se suman las fuentes.

Cada NPN completo se cuenta una sola vez, incluso si aparece repetido con atributos diferentes. Dos NPN distintos dentro de una misma manzana/vereda siguen contando como dos predios. Se conservan ceros iniciales y se ignoran espacios exteriores. Se excluyen filas sin NPN y se informa su cantidad, junto con los duplicados no sumados. La deduplicación se aplica solo a estadísticas; no elimina filas de las referencias usadas por las reglas. Los conteos son previos a las condiciones particulares de cada regla.

R1 temporal se lee de la copia local preparada. R1 vigente se consulta en sentencias.r1_r2 para el municipio y fecha seleccionados, en modo de solo lectura. Si falta R1 o falla la consulta, se indica el motivo y se muestran cantidades sin dato; no se informa cero como si fuera un archivo vacío.

## Aplicación del filtro

El filtro se aplica al Modelo Interno/XTF, CICA y a R1/R2, antes de ejecutar las reglas y el reporte general. Se utilizan vistas temporales de las tablas con numero_predial o numero_predial_nacional; las tablas auxiliares sin NPN mantienen sus datos y se relacionan mediante los JOIN de las sentencias. No se modifican las tablas originales. El ámbito y los códigos quedan registrados en la ejecución y en la identidad de las revisiones.

Las referencias pueden provenir de archivos temporales o de R1 y R2 Vigente. El catálogo vigente muestra municipio, DIVIPOLA, fecha y tablas disponibles; elige la fecha más reciente sin combinar referencias de fechas distintas. Las referencias requeridas se copian a la sesión temporal de validación.
