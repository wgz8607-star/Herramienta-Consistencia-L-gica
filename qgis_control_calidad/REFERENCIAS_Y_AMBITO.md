# Referencias y ámbito territorial

En Modelo Interno/XTF y CICA, el botón **Filtro avanzado…** debajo de Esquema a validar permite seleccionar Todos, Urbano (01), Rural (00) o Centro poblado (>01). Por defecto se valida todo. El botón se habilita al seleccionar un esquema listado o cargar la fuente de predios CICA. Se interpreta el código de dos dígitos en las posiciones 6 y 7 del número predial. El filtro se aplica tanto a las validaciones del modelo como a Cargue SNC.

Opcionalmente puede leer los códigos de manzana/vereda de la fuente seleccionada y marcar uno o varios prefijos NPN de exactamente 13 dígitos. Sin códigos marcados no se restringe por manzana/vereda. El ámbito y los códigos se combinan; una selección incompatible se informa antes de aplicarla. Cancelar conserva el filtro previo. Cambiar de modelo o esquema, o reemplazar la fuente CICA, elimina los códigos seleccionados para evitar trasladarlos a otra fuente.

La misma selección filtra Modelo Interno/CICA y R1/R2 antes de ejecutar las reglas y el reporte general. Las tablas del modelo (cica_ o ilc_) que contienen numero_predial o numero_predial_nacional se consultan mediante vistas temporales filtradas; las tablas auxiliares sin NPN conservan sus datos y se relacionan mediante los JOIN de cada sentencia. Un ámbito específico excluye NPN vacíos o con código territorial no válido. Todos conserva los datos completos para sus controles de integridad.

R1/R2 pueden provenir de archivos temporales o de R1 y R2 Vigente en sentencias.r1_r2. En Vigente se muestra municipio, DIVIPOLA, fecha y nombres de las tablas. Se toma la fecha más reciente del municipio, sin combinar referencias de fechas diferentes. Las referencias se copian a la sesión temporal de validación; las tablas originales no se modifican.

El ámbito queda registrado en los datos de ejecución y en la identidad de las revisiones. Las revisiones de ámbitos diferentes no se trasladan automáticamente. El filtro no transforma ni modifica el SQL almacenado en el repositorio.
