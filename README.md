# Talento IA SaaS

La API usa NVIDIA NIM en el servidor; la clave `NVIDIA_API_KEY` nunca se envía al navegador. El modelo por defecto es `qwen/qwen3.5-397b-a17b` y puede cambiarse con `NVIDIA_MODEL`.

## Ejecutar con Docker

1. Instala Docker Desktop y copia `.env.example` como `.env` en la raíz. Sustituye todos los valores de ejemplo, especialmente `NVIDIA_API_KEY` y `SECRET_KEY`.
2. Ejecuta `docker compose up --build`.
3. Abre `http://localhost:8080`. En desarrollo la documentación queda en `http://localhost:8080/api/docs`.

El primer arranque crea un MySQL vacío con el esquema de `docker/mysql/init/001-schema.sql`. Si ya tienes datos, importa un respaldo antes de usar el entorno nuevo; los scripts de inicialización de MySQL no se reaplican sobre un volumen ya creado.

## Verificaciones locales

Desde `backend`, ejecuta `python -m unittest discover -s tests -v`. La prueba simula NVIDIA y comprueba modelo, parámetros y manejo seguro de la clave, por lo que no consume créditos.

## Producción

Antes de publicar, usa HTTPS mediante un proxy administrado, guarda secretos en un gestor de secretos, restringe `ALLOWED_ORIGINS`, realiza respaldos del volumen MySQL y de `uploads`, y configura observabilidad. Las evaluaciones IA deben ser asistencia para reclutadores, con revisión humana, trazabilidad y una política de privacidad para los datos personales de candidatos.

## Seguridad y aislamiento de datos

Este proyecto usa MySQL 8.4. MySQL no tiene Row-Level Security (RLS) nativo, así que no se puede activar `CREATE POLICY` como en PostgreSQL. El aislamiento se aplica en la API: las operaciones de reclutadores filtran por su cuenta, los endpoints administrativos validan el rol y los CV solo salen por endpoints autenticados con comprobación de propietario. No se debe montar `uploads` como directorio web público.

En despliegues públicos establece `APP_ENV=production`, configura `ALLOWED_ORIGINS` con los dominios reales y usa HTTPS en el proxy. `SECRET_KEY` debe ser aleatoria y tener al menos 32 caracteres; las contraseñas nuevas requieren 12 caracteres como mínimo. El API se mantiene dentro de la red Docker y solo el frontend publica el puerto web.

La aplicación todavía usa una sola cuenta MySQL. Para producción, limita esa cuenta a permisos DML en las tablas necesarias y ejecuta los cambios de esquema con una cuenta de migraciones separada. No uses credenciales de desarrollo ni la cuenta `root` en la aplicación.
