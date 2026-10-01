# Backups — base de datos y evidencias

**Estado actual:** los respaldos se ejecutan localmente en el volumen Docker `backups` (servicio `backup` de `infra/docker/docker-compose.prod.yml`, imagen `infra/docker/Dockerfile.backup`). **No existe réplica off-site: la copia fuera del servidor debe configurarse** (ver §6).

---

## 1. Componentes

| Archivo | Función |
|---|---|
| `scripts/backup/schedule.sh` | Daemon del contenedor: ejecuta `run_backup.sh` cada día a `BACKUP_TIME` (HH:MM, zona `TZ`, default `America/Bogota`) y vuelve a dormir |
| `scripts/backup/run_backup.sh` | Orquesta: dump de BD + evidencias + retención + `manifest.json` + hook rsync opcional |
| `scripts/backup/backup_db.sh` | `pg_dump -Fc` → `/backups/db_<timestamp>.dump` |
| `scripts/backup/backup_evidencias.sh` | `tar.gz` del volumen de evidencias → `/backups/evidencias_<timestamp>.tar.gz` |
| `scripts/backup/retention.sh` | Borra respaldos con más de `BACKUP_RETENTION_DAYS` (default 14 días) |
| `scripts/backup/restore_db.sh` | Restauración con controles de seguridad (`--yes`, `--force`, `--clean`) |
| `scripts/backup/verify_backup.sh` | Valida checksums SHA-256 contra el manifiesto + `pg_restore --list` |

Variables (todas en `infra/docker/.env.prod`): `BACKUP_DIR=/backups`, `BACKUP_TIME=03:00`, `TZ=America/Bogota`, `BACKUP_RETENTION_DAYS=14`, `EVIDENCIAS_DIR=/data/evidencias`, `BACKUP_RSYNC_TARGET=`.

Conexión a la BD: `DB_HOST`/`DB_PORT`/`DB_USER`/`DB_NAME`/`DB_PASSWORD` (o `POSTGRES_USER`/`POSTGRES_DB`/`POSTGRES_PASSWORD`). El dump corre con el rol superuser `sigem` para incluir todos los objetos.

## 2. Programación y dónde caen los archivos

- Horario: diario a `BACKUP_TIME` en la zona horaria `TZ` (default America/Bogota), calculado por GNU `date` dentro del contenedor.
- Ubicación: volumen Docker `backups` montado en `/backups`.
- Archivos por corrida: `db_YYYYMMDDThhmmssZ.dump`, `evidencias_YYYYMMDDThhmmssZ.tar.gz`, `manifest_YYYYMMDDThhmmssZ.json` (y copia `manifest.json` con el último manifiesto).
- El manifiesto contiene `version` (APP_VERSION/SIGEM_VERSION), `timestamp` UTC y por archivo: `name`, `type`, `sha256`, `size`.
- Logs: `docker compose -f infra/docker/docker-compose.prod.yml -p sigem-prod logs backup`.

## 3. Verificación

```bash
docker compose -f infra/docker/docker-compose.prod.yml -p sigem-prod exec backup /backup/verify_backup.sh
```

Verifica SHA-256 de cada archivo listado en el manifiesto y que `pg_restore --list` pueda leer el dump. También admite `verify_backup.sh <manifest_*.json>` o `verify_backup.sh /backups/db_<ts>.dump`.

**Ejecute la verificación después de cada despliegue crítico y como paso de drill mensual.**

## 4. Restauración (drill)

```bash
docker compose -f infra/docker/docker-compose.prod.yml -p sigem-prod exec backup ls -lt /backups
docker compose -f infra/docker/docker-compose.prod.yml -p sigem-prod exec backup /backup/verify_backup.sh /backups/db_<ts>.dump
```

Drill recomendado (en entorno de pruebas, nunca sobre producción sin copia previa):

1. Detener el stack: `docker compose -f infra/docker/docker-compose.prod.yml -p sigem-prod stop backend nginx`.
2. Restaurar: `docker compose -f infra/docker/docker-compose.prod.yml -p sigem-prod run --rm backup /backup/restore_db.sh /backups/db_<ts>.dump --yes`
   - Rechaza ejecutarse sin `--yes`.
   - Rechaza si hay conexiones activas a la BD distintas de la propia sesión; `--force` lo omite (el stack debe estar detenido de todos modos).
   - `--clean` añade `pg_restore --clean --if-exists` para reconstruir sobre una BD con objetos previos.
3. Restaurar evidencias si corresponde (volumen `evidencias`): detener backend, `run --rm backup tar -xzf /backups/evidencias_<ts>.tar.gz -C /data/...` según corresponda.
4. Verificar: `verify_backup.sh`, luego levantar `backend nginx` y comprobar `/health`.
5. Registrar la fecha del drill en el CHANGELOG del equipo.

Si el dump es anterior a una migración aplicada, el estado de `alembic_version` viaja dentro del dump: después de restaurar, despliegue la imagen del tag correspondiente (o aplique `alembic upgrade head` con el servicio `migrate`) antes de servir tráfico.

## 5. Restauración automática de conexiones activas

`restore_db.sh` consulta `pg_stat_activity` (excluyendo su propio PID). Si el stack sigue corriendo, falle a propósito; no intente `-f` sobre producción con usuarios conectados sin haber confirmado el mantenimiento.

## 6. Off-site (pendiente — obligatorio antes de producción real)

**Hoy el destino de respaldo es únicamente el volumen local `backups` en el mismo host.** Si el disco o el host mueren, se pierden BD y evidencias. Configurar antes de poner en producción:

- Hook incluido: defina `BACKUP_RSYNC_TARGET=user@host:/ruta/respaldos` en `.env.prod`; `run_backup.sh` ejecuta `rsync -a` de los archivos nuevos después de cada corrida (falla la corrida si rsync falla, para que el fallo sea visible).
- Alternativas a evaluar: `rclone` a object storage, réplica a otro host, o copia del volumen con `docker run --rm -v sigem-prod_backups:/b alpine tar ... | ssh`. Ninguna está implementada aún.

## 7. Retención

`retention.sh` elimina `db_*.dump`, `evidencias_*.tar.gz` y `manifest_*.json` con más de `BACKUP_RETENTION_DAYS` días (default 14). Ajuste el valor en `.env.prod` según requisito de retención del municipio; la retención local no sustituye la retención legal en soporte oficial.
