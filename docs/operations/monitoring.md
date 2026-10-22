# Monitoring — Prometheus (perfil `monitoring`)

## 1. Cómo habilitarlo

Prometheus está detrás del perfil `monitoring` de `infra/docker/docker-compose.prod.yml`; por defecto **no levanta**. Para desplegarlo:

```bash
docker compose -f infra/docker/docker-compose.prod.yml -p sigem-prod --profile monitoring up -d
```

Para que el perfil quede activo en todos los comandos (deploy/rollback), exporte antes:

```bash
export COMPOSE_PROFILES=monitoring
```

La UI queda publicada solo en loopback del host: `http://127.0.0.1:9090`. No se expone a Internet; para verla desde otra máquina use un túnel SSH:

```bash
ssh -L 9090:127.0.0.1:9090 usuario@servidor
```

Datos: volumen `prometheus_data`. Config: `infra/monitoring/prometheus.yml` (montado en `/etc/prometheus/prometheus.yml`, solo lectura).

## 2. Qué se raspa

| Job | Target | Path | Intervalo |
|---|---|---|---|
| `sigem-backend` | `backend:8000` | `/metrics` | 15s |
| `prometheus` | `localhost:9090` | `/metrics` | 15s |

- El endpoint `/metrics` del backend está siendo implementado por el agente Backend. Mientras no exista, el scrape devuelve 404 y Prometheus marca el target como caído (`up{job="sigem-backend"} == 0`), por lo que **`BackendTargetDown` se disparará**: es esperado hasta que el endpoint esté entregado.
- Backend está en la red interna; Prometheus se conecta por DNS de servicio de Compose.
- No se añadió Grafana (fuera de alcance de este entregable).

## 3. Reglas de alerta (`infra/monitoring/alerts.yml`)

| Alerta | Sev. | Condición | Estado actual |
|---|---|---|---|
| `BackendTargetDown` | critical | `up{job="sigem-backend"} == 0` por 2m | Activa desde ya |
| `BackendHighErrorRate` | critical | ratio 5xx > 5% en 5m, por 10m | Requiere `http_requests_total` del endpoint /metrics |
| `BackendHighLatencyP95` | warning | p95 (`http_request_duration_seconds_bucket`) > 1s por 10m | Requiere histogramas en /metrics |
| `PostgresConnectionsSaturation` | warning | conexiones > 80% de `max_connections` por 5m | Placeholder: requiere `postgres_exporter` (no desplegado) |
| `DiskSpaceLow` | warning | filesystem < 10% libre por 10m | Placeholder: requiere `node_exporter` (no desplegado) |

Todas las reglas parsean con `promtool check config`. **Las dos últimas alertas fueron retiradas** (2026-10-21, auditoría): referían métricas de exporters inexistentes y nunca podían dispararse; reactivarlas junto con sus exporters (migración 020 del monitoring pendiente).

## 4. Bearer token y Alertmanager (auditoría 2026-10-21)

- **Scrape autenticado:** cuando `METRICS_TOKEN` está configurado, el backend exige `Authorization: Bearer <token>` en `/metrics`. El servicio `prometheus` escribe el token a `/etc/prometheus/metrics_token` en su entrypoint (compose local/prod) y el scrape config lo lee vía `bearer_token_file`. En despliegues sin token, la cabecera extra es ignorada por el backend.
- **Alertmanager:** servicio `alertmanager` (perfil `monitoring`, puertos `127.0.0.1:9093`) con `infra/monitoring/alertmanager.yml`; `prometheus.yml` con bloque `alerting:` → `alertmanager:9093`. ANTES de producción: sustituir los placeholders SMTP del `alertmanager.yml` (Alertmanager no hace sustitución de variables de entorno).
- Los composes local/prod levantan ambos servicios con `--profile monitoring`.

## 5. Validación de configuración

```bash
docker run --rm -v <ruta-del-repo>/infra/monitoring:/etc/prometheus prom/prometheus:latest promtool check config /etc/prometheus/prometheus.yml
```

## 5. Qué falta (documentado, no implementado)

- Endpoint `/metrics` en el backend (agente Backend) — ✅ implementado.
- `postgres_exporter` y `node_exporter` para alertas de saturación de BD y disco (las alertas correspondientes se retiraron hasta que existan los agentes).
- Canales reales en `alertmanager.yml` (placeholders SMTP). — ✅ Alertmanager desplegado (sustituir SMTP).
- Grafana / dashboards.
