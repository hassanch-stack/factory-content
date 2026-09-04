"""Tareas periódicas (celery beat)."""
BEAT_SCHEDULE: dict = {
    "poll-and-publish-due-posts": {
        "task": "workers.publish.poll_and_publish",
        "schedule": 15.0,  # segundos — spec 22: 'poll schedules every few seconds'
    },
    "collect-due-metrics": {
        "task": "workers.analytics.collect_due_metrics",
        "schedule": 300.0,  # cada 5 min revisa qué posts tocan recolección (15m/1h/6h/24h/48h)
    },
}
