# Celery Task Definitions
from workers.tasks.image import generate_image, generate_image_variation
from workers.tasks.video import generate_video, generate_video_from_image
from workers.tasks.model3d import generate_3d, generate_3d_from_image, generate_3d_from_text
from workers.tasks.callbacks import update_job_status, register_asset, notify_completion

__all__ = [
    # Image tasks
    "generate_image",
    "generate_image_variation",
    # Video tasks
    "generate_video",
    "generate_video_from_image",
    # 3D tasks
    "generate_3d",
    "generate_3d_from_image",
    "generate_3d_from_text",
    # Callback tasks
    "update_job_status",
    "register_asset",
    "notify_completion",
]
