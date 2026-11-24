# Renumeración predial · v0.7.0

Plugin QGIS 3.28 o superior para identificar provisionales, consultar máximos R1, generar una propuesta y compararla con un archivo de renumeración. Todas las consultas de base se realizan en modo de solo lectura. No aplica actualizaciones de NPN.

## Instalación

Complementos → Administrar e instalar complementos → Instalar a partir de ZIP → `renumeracion_maximos_R1_v0.7.0.zip`.

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

Se distinguen Coincide, Diferencia, Falta en archivo, Pendiente de generar, provisionales o definitivos duplicados, registros fuera del alcance y filas inválidas. A = B se trata como Sin cambio fuera del alcance únicamente si no corresponde a un provisional identificado; si sí corresponde se compara con el esperado.

**Coincide significa que el archivo coincide con la propuesta calculada; no acredita que el cambio ya haya sido aplicado en la base.** Generado tampoco significa aprobado ni ejecutado. Los casos pendientes conservan su explicación.

Exporte la propuesta y comparación a Excel. La hoja Renumeracion mantiene A nuevo / B provisional; Bases R1 conserva máximos utilizados. El resumen incluye fuente, corte, R1, huella SHA256, zonas, fecha y conteos. No se modifica el archivo cargado ni la base.

## Verificación

`QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 /workspace/.venvs/calidad-qgis/bin/python -m unittest discover -s tests_maximos_r1`

Pruebas de agrupación, deduplicación, aislamiento territorial, máximos y faltantes, orden sin saltos, condición 2, PH/condominio, sufijos, agotamiento, comparación, lectura Excel y exportación. La conectividad institucional debe verificarse en QGIS desde la red de la entidad.
