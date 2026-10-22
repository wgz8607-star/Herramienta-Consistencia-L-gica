# Prevalidador MAILC v1.0 - Componente gráfico

Complemento para QGIS 3.28 o superior. Ejecuta reglas de prevalidación del componente gráfico MAILC sobre PostgreSQL/PostGIS, organiza los hallazgos como capas temporales de QGIS y permite exportarlos a GeoPackage y Excel. La fuente nunca se modifica y no se conservan esquemas de resultados en PostgreSQL.

La interfaz funciona como panel acoplable de QGIS. Los microfragmentos pueden excluirse mediante un área y un ancho mínimo reportables, sin ajustar las geometrías fuente.

## Formas de conexión

- **Servidor autorizado:** el complemento solamente permite conexiones al anfitrión PostgreSQL `172.19.3.225`.
- **Conexión guardada en QGIS:** reutiliza una conexión PostgreSQL registrada en el perfil actual de QGIS. Soporta las credenciales guardadas o configuradas mediante el gestor de autenticación de QGIS.
- **Conexión manual a PostgreSQL:** permite ingresar servidor, puerto, base de datos, usuario y contraseña para la sesión actual.

Puede ejecutarse con un usuario de consulta que tenga `CONNECT` y `TEMP` sobre la base, `USAGE` sobre el esquema y `SELECT` sobre las tablas involucradas. No requiere permisos de edición ni de creación de esquemas permanentes.

Tras usar **Listar esquemas**, el complemento consulta los esquemas disponibles y permite seleccionar el que se validará.

## Ingesta CICA

Al seleccionar CICA aparece el botón **Cargar insumos CICA**. Solicita individualmente los siete CSV requeridos y la geodatabase `.gdb` —directa o comprimida en ZIP—, validando su presencia antes de la carga al esquema de destino.

## Referencias R1 y R2

Para ambos modelos, el botón **Cargar referencia R1 y R2** valida los archivos Excel del catastro vigente y sus columnas requeridas. La lectura de los TXT de ancho fijo queda pendiente hasta disponer de su diccionario de posiciones.


## Instalación para pruebas

1. Copie la carpeta `qgis_control_calidad` al directorio de complementos de su perfil de QGIS.
2. En QGIS abra **Complementos > Administrar e instalar complementos**.
3. Active **Control de Calidad Catastral**.
4. Abra el complemento desde el menú **Base de datos** o su botón de barra de herramientas.

Las reglas SQL se incluyen en `resources/sql`. El complemento no guarda la contraseña ni ejecuta instrucciones que modifiquen la base de datos.
