# Runtime Topology

Status: Phase 0 Iteration 0B.

```text
Browser -> Cloudflare Access -> Cloudflare Tunnel -> FastAPI app
                                                   |        |
                                             Angular bundle  PostgreSQL
                                                            ^
Dedicated worker --------------------------------------------|
       |
configured data root: raw, work, staging, ready, quarantine
```

Production has exactly four Compose services: `app`, `worker`, `postgres`, and
`cloudflared`. The application and worker use one Python/application image and
the same source code, with separate entrypoints. The Angular production bundle
is built into that image and served by FastAPI. PostgreSQL is internal-only;
the worker, package filesystem, and Docker daemon are never publicly exposed.

The worker scheduler runs in the worker process. PostgreSQL row locking, leases,
and heartbeats provide the one-active-run total guarantee; no Redis, RabbitMQ,
Celery, Kafka, or other broker is introduced. There is no microservice split,
separate scheduler, Nginx, or object-storage service in V1.

The browser uses `/api/v1/` for JSON and `/files/` for authenticated binary
downloads. Downloads resolve package IDs through server-side metadata and the
approved ready roots; browser input never selects a filesystem path.
