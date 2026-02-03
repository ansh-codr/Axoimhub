"""
Axiom Design Engine - Worker CLI
Command-line interface for managing Celery workers
"""

import argparse
import sys
from typing import Literal

from workers.config import settings


def start_worker(
    queues: list[str] | None = None,
    concurrency: int | None = None,
    loglevel: str = "INFO",
    pool: Literal["prefork", "solo", "gevent"] = "prefork",
) -> None:
    """
    Start a Celery worker.
    
    Args:
        queues: List of queues to consume from
        concurrency: Number of worker processes
        loglevel: Log level
        pool: Pool implementation
    """
    from workers.celery_app import celery_app

    # Build arguments
    argv = ["worker"]
    
    # Queues
    if queues:
        argv.extend(["-Q", ",".join(queues)])
    else:
        argv.extend(["-Q", "queue_image,queue_video,queue_3d"])
    
    # Concurrency
    conc = concurrency or settings.worker_concurrency
    argv.extend(["-c", str(conc)])
    
    # Log level
    argv.extend(["--loglevel", loglevel])
    
    # Pool
    argv.extend(["-P", pool])
    
    # Max tasks per child (memory cleanup)
    argv.extend(["--max-tasks-per-child", str(settings.worker_max_tasks_per_child)])
    
    # Start worker
    celery_app.worker_main(argv)


def start_beat() -> None:
    """Start Celery Beat scheduler."""
    from workers.celery_app import celery_app
    
    argv = ["beat", "--loglevel", settings.log_level]
    celery_app.start(argv)


def check_queues() -> None:
    """Check queue status."""
    from workers.dispatcher import JobDispatcher
    
    print("Queue Status")
    print("=" * 40)
    
    queue_lengths = JobDispatcher.get_queue_lengths()
    for queue_name, length in queue_lengths.items():
        print(f"  {queue_name}: {length} pending tasks")


def check_gpu() -> None:
    """Check GPU availability."""
    from workers.utils.gpu import GPUManager
    
    manager = GPUManager()
    info = manager.get_gpu_info()
    
    print("GPU Status")
    print("=" * 40)
    
    if not info.get("available"):
        print(f"  Available: No")
        print(f"  Error: {info.get('error', 'Unknown')}")
        return
    
    print(f"  Available: Yes")
    print(f"  Backend: {info.get('backend', 'unknown')}")
    print(f"  Device: {info.get('device_name', 'unknown')}")
    print(f"  VRAM Total: {info.get('vram_total_gb', 0):.2f} GB")
    print(f"  VRAM Free: {info.get('vram_free_gb', 0):.2f} GB")
    print(f"  VRAM Used: {info.get('vram_used_gb', 0):.2f} GB")


def check_comfyui() -> None:
    """Check ComfyUI connection."""
    from workers.handlers.comfyui import ComfyUIHandler
    
    handler = ComfyUIHandler()
    
    print("ComfyUI Status")
    print("=" * 40)
    print(f"  URL: {handler.base_url}")
    
    if handler.check_health():
        print("  Status: Connected")
        
        try:
            queue_status = handler.get_queue_status()
            running = len(queue_status.get("queue_running", []))
            pending = len(queue_status.get("queue_pending", []))
            print(f"  Running: {running}")
            print(f"  Pending: {pending}")
        except Exception as e:
            print(f"  Queue: Error - {e}")
    else:
        print("  Status: Not connected")


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="axiom-worker",
        description="Axiom Design Engine Worker CLI",
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Start worker command
    worker_parser = subparsers.add_parser("start", help="Start Celery worker")
    worker_parser.add_argument(
        "-Q", "--queues",
        nargs="+",
        help="Queues to consume (default: all)",
    )
    worker_parser.add_argument(
        "-c", "--concurrency",
        type=int,
        help="Number of worker processes",
    )
    worker_parser.add_argument(
        "-l", "--loglevel",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log level",
    )
    worker_parser.add_argument(
        "-P", "--pool",
        default="prefork",
        choices=["prefork", "solo", "gevent"],
        help="Pool implementation",
    )
    
    # Image queue worker
    subparsers.add_parser("start-image", help="Start image generation worker")
    
    # Video queue worker
    subparsers.add_parser("start-video", help="Start video generation worker")
    
    # 3D queue worker
    subparsers.add_parser("start-3d", help="Start 3D model generation worker")
    
    # Beat scheduler
    subparsers.add_parser("beat", help="Start Celery Beat scheduler")
    
    # Status commands
    subparsers.add_parser("status", help="Show worker and queue status")
    subparsers.add_parser("gpu", help="Check GPU status")
    subparsers.add_parser("comfyui", help="Check ComfyUI status")
    
    args = parser.parse_args()
    
    if args.command == "start":
        start_worker(
            queues=args.queues,
            concurrency=args.concurrency,
            loglevel=args.loglevel,
            pool=args.pool,
        )
    elif args.command == "start-image":
        start_worker(queues=["queue_image"], concurrency=1)
    elif args.command == "start-video":
        start_worker(queues=["queue_video"], concurrency=1)
    elif args.command == "start-3d":
        start_worker(queues=["queue_3d"], concurrency=1)
    elif args.command == "beat":
        start_beat()
    elif args.command == "status":
        check_queues()
    elif args.command == "gpu":
        check_gpu()
    elif args.command == "comfyui":
        check_comfyui()
    else:
        parser.print_help()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
