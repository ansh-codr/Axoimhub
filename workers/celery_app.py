"""
Axiom Design Engine - Celery Application Configuration
Main Celery app setup with task routing and Redis broker
"""

from celery import Celery
from kombu import Exchange, Queue

from workers.config import settings

# Create Celery application
celery_app = Celery(
    "axiom_workers",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "workers.tasks.image",
        "workers.tasks.video",
        "workers.tasks.model3d",
        "workers.tasks.callbacks",
    ],
)

# =============================================================================
# Celery Configuration
# =============================================================================

celery_app.conf.update(
    # Task serialization
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    
    # Timezone
    timezone="UTC",
    enable_utc=True,
    
    # Task execution settings
    task_acks_late=True,  # Acknowledge after task completes (reliability)
    task_reject_on_worker_lost=True,  # Requeue if worker dies
    task_acks_on_failure_or_timeout=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,  # One task at a time (GPU memory)
    worker_concurrency=settings.worker_concurrency,
    worker_max_tasks_per_child=settings.worker_max_tasks_per_child,
    
    # Task time limits
    task_soft_time_limit=settings.job_timeout_seconds - 60,  # Soft limit
    task_time_limit=settings.job_timeout_seconds,  # Hard limit
    
    # Result backend settings
    result_expires=86400,  # Results expire after 24 hours
    result_extended=True,
    
    # Task retry settings
    task_default_retry_delay=settings.job_retry_delay_seconds,
    task_max_retries=settings.job_max_retries,
    
    # Broker connection settings
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=10,
    
    # Task tracking
    task_track_started=True,
    task_send_sent_event=True,
    worker_send_task_events=True,
)

# =============================================================================
# Queue Configuration
# =============================================================================

# Define exchanges
default_exchange = Exchange("axiom", type="direct")

# Define queues with routing
celery_app.conf.task_queues = (
    Queue(
        "queue_image",
        exchange=default_exchange,
        routing_key="image",
        queue_arguments={"x-max-priority": 10},
    ),
    Queue(
        "queue_video",
        exchange=default_exchange,
        routing_key="video",
        queue_arguments={"x-max-priority": 10},
    ),
    Queue(
        "queue_3d",
        exchange=default_exchange,
        routing_key="model3d",
        queue_arguments={"x-max-priority": 10},
    ),
    Queue(
        "queue_callbacks",
        exchange=default_exchange,
        routing_key="callback",
    ),
)

# Task routing rules
celery_app.conf.task_routes = {
    "workers.tasks.image.*": {"queue": "queue_image", "routing_key": "image"},
    "workers.tasks.video.*": {"queue": "queue_video", "routing_key": "video"},
    "workers.tasks.model3d.*": {"queue": "queue_3d", "routing_key": "model3d"},
    "workers.tasks.callbacks.*": {"queue": "queue_callbacks", "routing_key": "callback"},
}

# Default queue
celery_app.conf.task_default_queue = "queue_image"
celery_app.conf.task_default_exchange = "axiom"
celery_app.conf.task_default_routing_key = "image"
