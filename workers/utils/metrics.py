"""
Axiom Design Engine - Worker Metrics
Prometheus metrics for worker observability
"""

import functools
import time
from typing import Any, Callable

from workers.config import settings

# Lazy import prometheus_client
_metrics_initialized = False
_registry = None

# Metric definitions (initialized lazily)
JOB_EXECUTION_TIME = None
JOB_COUNTER = None
GPU_MEMORY_USAGE = None
ACTIVE_JOBS = None
JOB_QUEUE_SIZE = None


def _init_metrics():
    """Initialize Prometheus metrics."""
    global _metrics_initialized, _registry
    global JOB_EXECUTION_TIME, JOB_COUNTER, GPU_MEMORY_USAGE, ACTIVE_JOBS, JOB_QUEUE_SIZE

    if _metrics_initialized:
        return

    try:
        from prometheus_client import (
            Counter,
            Gauge,
            Histogram,
            CollectorRegistry,
            REGISTRY,
        )

        _registry = REGISTRY

        # Job execution time histogram
        JOB_EXECUTION_TIME = Histogram(
            "axiom_job_execution_seconds",
            "Job execution time in seconds",
            ["job_type", "model", "status"],
            buckets=(1, 5, 10, 30, 60, 120, 300, 600, 1200, 1800),
        )

        # Job counter
        JOB_COUNTER = Counter(
            "axiom_jobs_total",
            "Total number of jobs processed",
            ["job_type", "status"],
        )

        # GPU memory usage gauge
        GPU_MEMORY_USAGE = Gauge(
            "axiom_gpu_memory_bytes",
            "GPU memory usage in bytes",
            ["device", "type"],  # type: used, free, total
        )

        # Active jobs gauge
        ACTIVE_JOBS = Gauge(
            "axiom_active_jobs",
            "Number of currently active jobs",
            ["job_type", "worker"],
        )

        # Queue size gauge
        JOB_QUEUE_SIZE = Gauge(
            "axiom_queue_size",
            "Number of jobs in queue",
            ["queue_name"],
        )

        _metrics_initialized = True

    except ImportError:
        pass


def track_job_execution(
    job_type: str,
    model: str = "unknown",
) -> Callable:
    """
    Decorator to track job execution metrics.
    
    Usage:
        @track_job_execution("image", "sdxl")
        def generate_image(...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            if not settings.enable_metrics:
                return func(*args, **kwargs)

            _init_metrics()

            if ACTIVE_JOBS is not None:
                worker_id = kwargs.get("self", {})
                if hasattr(worker_id, "request"):
                    worker_id = worker_id.request.hostname or "unknown"
                else:
                    worker_id = "unknown"
                ACTIVE_JOBS.labels(job_type=job_type, worker=worker_id).inc()

            start_time = time.time()
            status = "success"

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "failure"
                raise
            finally:
                execution_time = time.time() - start_time

                if JOB_EXECUTION_TIME is not None:
                    JOB_EXECUTION_TIME.labels(
                        job_type=job_type,
                        model=model,
                        status=status,
                    ).observe(execution_time)

                if JOB_COUNTER is not None:
                    JOB_COUNTER.labels(
                        job_type=job_type,
                        status=status,
                    ).inc()

                if ACTIVE_JOBS is not None:
                    ACTIVE_JOBS.labels(
                        job_type=job_type,
                        worker=worker_id,
                    ).dec()

        return wrapper
    return decorator


def update_gpu_metrics(device: int = 0) -> None:
    """Update GPU memory metrics."""
    if not settings.enable_metrics:
        return

    _init_metrics()

    if GPU_MEMORY_USAGE is None:
        return

    try:
        import torch

        if not torch.cuda.is_available():
            return

        mem_info = torch.cuda.mem_get_info(device)
        free_memory = mem_info[0]
        total_memory = mem_info[1]
        used_memory = total_memory - free_memory

        device_name = f"cuda:{device}"
        GPU_MEMORY_USAGE.labels(device=device_name, type="used").set(used_memory)
        GPU_MEMORY_USAGE.labels(device=device_name, type="free").set(free_memory)
        GPU_MEMORY_USAGE.labels(device=device_name, type="total").set(total_memory)

    except Exception:
        pass


def update_queue_metrics(queue_sizes: dict[str, int]) -> None:
    """Update queue size metrics."""
    if not settings.enable_metrics:
        return

    _init_metrics()

    if JOB_QUEUE_SIZE is None:
        return

    for queue_name, size in queue_sizes.items():
        JOB_QUEUE_SIZE.labels(queue_name=queue_name).set(size)


def start_metrics_server(port: int | None = None) -> None:
    """Start Prometheus metrics HTTP server."""
    if not settings.enable_metrics:
        return

    _init_metrics()

    try:
        from prometheus_client import start_http_server
        
        port = port or settings.metrics_port
        start_http_server(port)

    except ImportError:
        pass


class MetricsCollector:
    """
    Collector for custom metrics from Celery workers.
    """

    def __init__(self):
        self._init_metrics()

    def _init_metrics(self):
        """Ensure metrics are initialized."""
        _init_metrics()

    def record_job_start(self, job_id: str, job_type: str, worker_id: str) -> None:
        """Record job start."""
        if ACTIVE_JOBS is not None:
            ACTIVE_JOBS.labels(job_type=job_type, worker=worker_id).inc()

    def record_job_end(
        self,
        job_id: str,
        job_type: str,
        worker_id: str,
        model: str,
        execution_time: float,
        success: bool,
    ) -> None:
        """Record job completion."""
        status = "success" if success else "failure"

        if JOB_EXECUTION_TIME is not None:
            JOB_EXECUTION_TIME.labels(
                job_type=job_type,
                model=model,
                status=status,
            ).observe(execution_time)

        if JOB_COUNTER is not None:
            JOB_COUNTER.labels(
                job_type=job_type,
                status=status,
            ).inc()

        if ACTIVE_JOBS is not None:
            ACTIVE_JOBS.labels(job_type=job_type, worker=worker_id).dec()

    def record_gpu_usage(self, device: int = 0) -> None:
        """Record current GPU usage."""
        update_gpu_metrics(device)
