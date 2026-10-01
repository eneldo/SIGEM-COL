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

Todas las reglas parsean con `promtool check config`. Las dos últimas son placeholders intencionales: no dispararán hasta que existan los exporters correspondientes.

## 4. Validación de configuración

```bash
docker run --rm -v <ruta-del-repo>/infra/monitoring:/etc/prometheus prom/prometheus:latest promtool check config /etc/prometheus/prometheus.yml
```

## 5. Qué falta (documentado, no implementado)

- Endpoint `/metrics` en el backend (agente Backend).
- `postgres_exporter` y `node_exporter` para alertas de saturación de BD y disco.
- Canal de notificación (Alertmanager/correo) — sin él, las alertas solo se ven en la UI.
- Grafana / dashboards.
