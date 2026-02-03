# Axiom Design Engine - Workers Package
"""
Celery workers for AI generation tasks.

Usage:
    # Start all workers
    axiom-worker start

    # Start specific queue worker
    axiom-worker start-image
    axiom-worker start-video
    axiom-worker start-3d

    # Check status
    axiom-worker status
    axiom-worker gpu
"""

from workers.celery_app import celery_app
from workers.dispatcher import JobDispatcher
from workers.config import settings

__all__ = [
    "celery_app",
    "JobDispatcher",
    "settings",
]