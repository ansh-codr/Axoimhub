"""
Axiom Design Engine - GPU Manager
Utilities for GPU device management and memory monitoring
"""

import os
from dataclasses import dataclass
from typing import Any

from workers.config import settings


@dataclass
class GPUInfo:
    """GPU device information."""
    
    available: bool
    device_count: int
    current_device: int
    device_name: str
    vram_total_gb: float
    vram_free_gb: float
    vram_used_gb: float
    cuda_version: str
    driver_version: str


class GPUManager:
    """
    Manager for GPU resources.
    Handles device selection, memory management, and monitoring.
    """

    def __init__(self):
        self._torch_available = False
        self._cuda_available = False
        self._device = None

        # Set CUDA visible devices
        if settings.cuda_visible_devices:
            os.environ["CUDA_VISIBLE_DEVICES"] = settings.cuda_visible_devices

        # Check torch availability
        try:
            import torch
            self._torch_available = True
            self._cuda_available = torch.cuda.is_available()
        except ImportError:
            pass

    def get_gpu_info(self) -> dict[str, Any]:
        """Get current GPU information."""
        if not self._torch_available:
            return {
                "available": False,
                "error": "PyTorch not installed",
            }

        import torch

        if not self._cuda_available:
            # Check for MPS (Apple Silicon)
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                return {
                    "available": True,
                    "backend": "mps",
                    "device_name": "Apple Silicon",
                    "vram_total_gb": 0,  # MPS doesn't report VRAM
                    "vram_free_gb": 0,
                    "vram_used_gb": 0,
                }

            return {
                "available": False,
                "error": "No CUDA devices available",
            }

        device_count = torch.cuda.device_count()
        current_device = torch.cuda.current_device()

        # Get memory info
        mem_info = torch.cuda.mem_get_info(current_device)
        vram_free = mem_info[0] / (1024**3)  # Convert to GB
        vram_total = mem_info[1] / (1024**3)
        vram_used = vram_total - vram_free

        # Get device properties
        props = torch.cuda.get_device_properties(current_device)

        return {
            "available": True,
            "backend": "cuda",
            "device_count": device_count,
            "current_device": current_device,
            "device_name": props.name,
            "vram_total_gb": round(vram_total, 2),
            "vram_free_gb": round(vram_free, 2),
            "vram_used_gb": round(vram_used, 2),
            "cuda_version": torch.version.cuda or "unknown",
            "compute_capability": f"{props.major}.{props.minor}",
            "multi_processor_count": props.multi_processor_count,
        }

    def check_vram_available(self, required_gb: float) -> bool:
        """Check if sufficient VRAM is available."""
        info = self.get_gpu_info()
        if not info.get("available"):
            return False
        return info.get("vram_free_gb", 0) >= required_gb

    def get_device(self):
        """Get the appropriate torch device."""
        if not self._torch_available:
            raise RuntimeError("PyTorch not installed")

        import torch

        if self._device is not None:
            return self._device

        if self._cuda_available:
            self._device = torch.device("cuda")
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            self._device = torch.device("mps")
        else:
            self._device = torch.device("cpu")

        return self._device

    def set_memory_fraction(self, fraction: float) -> None:
        """Set the fraction of GPU memory to use."""
        if not self._cuda_available:
            return

        import torch
        torch.cuda.set_per_process_memory_fraction(
            fraction,
            torch.cuda.current_device(),
        )

    def cleanup(self) -> None:
        """Clean up GPU memory."""
        if not self._torch_available:
            return

        import torch

        if self._cuda_available:
            torch.cuda.empty_cache()
            torch.cuda.synchronize()

        # Clear references
        import gc
        gc.collect()

    def wait_for_memory(
        self,
        required_gb: float,
        timeout_seconds: int = 60,
        poll_interval: float = 1.0,
    ) -> bool:
        """
        Wait for sufficient GPU memory to become available.
        
        Returns:
            True if memory became available, False if timeout
        """
        import time

        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            if self.check_vram_available(required_gb):
                return True
            self.cleanup()
            time.sleep(poll_interval)

        return False

    def get_optimal_batch_size(
        self,
        base_memory_gb: float,
        per_item_memory_gb: float,
        max_batch_size: int = 4,
    ) -> int:
        """
        Calculate optimal batch size based on available memory.
        
        Args:
            base_memory_gb: Base memory required regardless of batch size
            per_item_memory_gb: Additional memory per batch item
            max_batch_size: Maximum allowed batch size
            
        Returns:
            Recommended batch size
        """
        info = self.get_gpu_info()
        if not info.get("available"):
            return 1

        available = info.get("vram_free_gb", 0) * settings.gpu_memory_fraction
        remaining = available - base_memory_gb

        if remaining <= 0:
            return 1

        optimal = int(remaining / per_item_memory_gb)
        return max(1, min(optimal, max_batch_size))


class GPUProfiler:
    """
    Context manager for profiling GPU memory usage.
    """

    def __init__(self, label: str = ""):
        self.label = label
        self.start_memory = 0
        self.peak_memory = 0
        self.end_memory = 0
        self._cuda_available = False

        try:
            import torch
            self._cuda_available = torch.cuda.is_available()
        except ImportError:
            pass

    def __enter__(self):
        if self._cuda_available:
            import torch
            torch.cuda.reset_peak_memory_stats()
            self.start_memory = torch.cuda.memory_allocated()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._cuda_available:
            import torch
            self.end_memory = torch.cuda.memory_allocated()
            self.peak_memory = torch.cuda.max_memory_allocated()

    @property
    def memory_used_gb(self) -> float:
        """Memory used during the profiled section (GB)."""
        return (self.end_memory - self.start_memory) / (1024**3)

    @property
    def peak_memory_gb(self) -> float:
        """Peak memory usage during the profiled section (GB)."""
        return self.peak_memory / (1024**3)

    def report(self) -> dict[str, Any]:
        """Get profiling report."""
        return {
            "label": self.label,
            "start_memory_gb": self.start_memory / (1024**3),
            "end_memory_gb": self.end_memory / (1024**3),
            "peak_memory_gb": self.peak_memory_gb,
            "memory_used_gb": self.memory_used_gb,
        }
