# Renumeración predial — Máximos R1

Plugin QGIS independiente, versión inicial 0.1.1. No depende del Validador de Consistencia Lógica ni cambia su instalación.

## Alcance

Visualiza los máximos existentes del R1 elegido. No cambia números prediales ni aprueba renumeraciones. Las reglas especiales de condición 8 y 9 quedan para otra fase; los códigos válidos existentes sí forman parte del resumen R1.

- **Por zona:** DIVIPOLA y código de posiciones 6–7; muestra el máximo bloque de manzana y un NPN de referencia.
- **Por prefijo 13:** máximo de manzana dentro del mismo prefijo territorial de 13 dígitos. Esta es la referencia que se usará posteriormente para comprobar una manzana nueva.
- **Por manzana:** prefijo completo de 17 dígitos y máximo de terreno (posiciones 18–21), con su NPN de referencia.
- Los siguientes consecutivos son informativos. 9999 se muestra como agotado.

## Instalación

En QGIS: Complementos → Administrar e instalar complementos → Instalar a partir de ZIP. Instale el paquete `renumeracion_maximos_R1_v0.1.1.zip`. Abra **Renumeración · Máximos R1** desde el menú de base de datos o su icono.

## Uso

1. Elija el origen R1: archivo Excel/TXT, tablas precargadas en `r1_r2`, o una tabla de `public`.
2. Para Excel, seleccione hoja y columna NPN; si hay una hoja `R1`, se propone esa hoja. Para TXT se usa el estándar R1 de 312 caracteres, con NPN en posiciones 1–30.
3. Para PostgreSQL, elija una conexión ya guardada en QGIS y consulte las tablas. Los precargados se consultan en `sentencias.r1_r2` del servidor elegido, muestran el municipio y la última fecha disponible de cada municipio, y actualizan la vigencia en la opción 2. Se reconocen nombres `r1_DIVIPOLA_AAAAMMDD`. En public se listan las tablas/vistas con columna NPN; seleccione la referencia R1 correcta.
4. Pulse **Leer R1 y calcular máximos**.
5. Filtre por municipio, zona o prefijo y consulte las tres pestañas. Los NPN duplicados se cuentan una sola vez. Los inválidos y vacíos se informan; no se reconstruyen ceros ni dígitos faltantes.
6. Exporte los máximos visibles a Excel. El resumen conserva el origen, los filtros y los conteos completos de la lectura.

Las conexiones usan autenticación guardada de QGIS o contraseña suministrada para la sesión. El paquete no contiene credenciales. Todas las consultas PostgreSQL se ejecutan en modo de solo lectura.

No se utiliza como referencia el archivo de resultados de renumeración: los máximos se calculan exclusivamente desde el R1 seleccionado.
