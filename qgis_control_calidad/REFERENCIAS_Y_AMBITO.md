# Referencias y ámbito territorial

En Modelo Interno/XTF y CICA, el botón **Filtro avanzado…** debajo de Esquema a validar permite seleccionar Todos, Urbano (01), Rural (00) o Centro poblado (>01). Por defecto se valida todo. El botón se habilita al seleccionar un esquema listado o cargar la fuente de predios CICA. Se interpreta el código de dos dígitos en las posiciones 6 y 7 del número predial. El filtro se aplica tanto a las validaciones del modelo como a Cargue SNC.

Opcionalmente puede leer los códigos de manzana/vereda de la fuente seleccionada y marcar uno o varios prefijos NPN de exactamente 17 dígitos. Sin códigos marcados no se restringe por manzana/vereda. El ámbito y los códigos se combinan; una selección incompatible se informa antes de aplicarla. Cancelar conserva el filtro previo. Cambiar de modelo o esquema, o reemplazar la fuente CICA, elimina los códigos seleccionados para evitar trasladarlos a otra fuente.

La misma selección filtra Modelo Interno/CICA y R1/R2 antes de ejecutar las reglas y el reporte general. Las tablas del modelo (cica_ o ilc_) que contienen numero_predial o numero_predial_nacional se consultan mediante vistas temporales filtradas; las tablas auxiliares sin NPN conservan sus datos y se relacionan mediante los JOIN de cada sentencia. Un ámbito específico excluye NPN vacíos o con código territorial no válido. Todos conserva los datos completos para sus controles de integridad.

R1/R2 pueden provenir de archivos temporales o de R1 y R2 Vigente en sentencias.r1_r2. En Vigente se muestra municipio, DIVIPOLA, fecha y nombres de las tablas. Se toma la fecha más reciente del municipio, sin combinar referencias de fechas diferentes. Las referencias se copian a la sesión temporal de validación; las tablas originales no se modifican.

El ámbito queda registrado en los datos de ejecución y en la identidad de las revisiones. Las revisiones de ámbitos diferentes no se trasladan automáticamente. El filtro no transforma ni modifica el SQL almacenado en el repositorio.

## Estadísticas y selección combinada (2.4.0)

El cuadro Ámbito contiene casillas y permite combinar Urbano, Rural y Centro poblado. Todos es el valor inicial e incluye también registros sin ámbito identificable. Marcar los tres ámbitos equivale a Todos. Desmarcar todos impide aplicar el filtro hasta elegir al menos uno.

Al abrir Filtro avanzado se consulta la fuente y el R1 seleccionado. Se muestran por separado sus totales por ámbito, registros sin ámbito identificable y registros incluidos con el filtro (cantidad y porcentaje). Son conteos de registros, incluidos duplicados, previos a las condiciones particulares de las reglas. No representan conteos de NPN únicos ni se suman entre fuentes.

R1 temporal se lee de la copia local preparada; R1 vigente se consulta en la base de sentencias por municipio y fecha seleccionados, en modo de solo lectura. Si falta R1 o falla su consulta, aparece el motivo; no se informa un cero que pueda confundirse con un archivo vacío.

La lista combina los prefijos de 17 dígitos encontrados en la fuente o en R1 y presenta dos columnas de cantidades. Seleccionar todo y Deseleccionar todo actúan sobre los códigos visibles según el ámbito y la búsqueda; las selecciones ocultas se conservan. La búsqueda solo afecta a la lista, no al conteo ni a la validación. Sin códigos marcados se incluyen todos los del ámbito seleccionado.
