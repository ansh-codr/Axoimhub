"""
Axiom Design Engine - UI-Optimized Prompt Templates
Pre-configured prompts for generating high-quality UI/UX assets
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class AssetCategory(str, Enum):
    """Categories of UI assets."""
    HERO = "hero"
    ICON = "icon"
    BACKGROUND = "background"
    BUTTON = "button"
    CARD = "card"
    ILLUSTRATION = "illustration"
    PATTERN = "pattern"
    AVATAR = "avatar"
    LOGO = "logo"
    SCENE = "scene"


class AnimationStyle(str, Enum):
    """Animation styles for video generation."""
    SUBTLE = "subtle"
    DYNAMIC = "dynamic"
    CINEMATIC = "cinematic"
    LOOP = "loop"
    TRANSITION = "transition"


class Model3DStyle(str, Enum):
    """Styles for 3D model generation."""
    MINIMAL = "minimal"
    DETAILED = "detailed"
    CARTOON = "cartoon"
    REALISTIC = "realistic"
    ISOMETRIC = "isometric"


@dataclass
class PromptTemplate:
    """A reusable prompt template."""
    name: str
    category: str
    base_prompt: str
    negative_prompt: str
    recommended_params: dict[str, Any]
    description: str


# =============================================================================
# IMAGE GENERATION TEMPLATES (SDXL)
# =============================================================================

IMAGE_TEMPLATES: dict[str, PromptTemplate] = {
    # Hero Sections
    "hero_gradient_abstract": PromptTemplate(
        name="Abstract Gradient Hero",
        category="hero",
        base_prompt=(
            "abstract gradient background, smooth color transitions, "
            "soft flowing shapes, modern minimalist design, "
            "high resolution, 8k quality, suitable for website hero section"
        ),
        negative_prompt=(
            "text, watermark, logo, busy, cluttered, "
            "low quality, pixelated, noisy, jpeg artifacts"
        ),
        recommended_params={
            "width": 1920,
            "height": 1080,
            "steps": 30,
            "cfg_scale": 7.0,
        },
        description="Clean abstract gradients perfect for hero sections",
    ),
    
    "hero_3d_shapes": PromptTemplate(
        name="3D Geometric Hero",
        category="hero",
        base_prompt=(
            "3D geometric shapes floating in space, soft shadows, "
            "glass morphism effect, pastel colors, "
            "modern UI design, depth of field, ray tracing, 8k"
        ),
        negative_prompt=(
            "flat, 2d, text, watermark, noisy, "
            "low quality, blurry, distorted"
        ),
        recommended_params={
            "width": 1920,
            "height": 1080,
            "steps": 35,
            "cfg_scale": 7.5,
        },
        description="3D geometric shapes with glass morphism for modern UIs",
    ),
    
    "hero_nature_blur": PromptTemplate(
        name="Nature Bokeh Hero",
        category="hero",
        base_prompt=(
            "soft bokeh background, natural lighting, "
            "blurred nature scene, dreamy atmosphere, "
            "professional photography, shallow depth of field"
        ),
        negative_prompt=(
            "sharp foreground elements, text, watermark, "
            "oversaturated, artificial looking"
        ),
        recommended_params={
            "width": 1920,
            "height": 1080,
            "steps": 25,
            "cfg_scale": 6.5,
        },
        description="Soft nature backgrounds with beautiful bokeh",
    ),

    # Icons
    "icon_3d_simple": PromptTemplate(
        name="Simple 3D Icon",
        category="icon",
        base_prompt=(
            "3D render of a simple {subject}, clean white background, "
            "soft studio lighting, minimal design, isometric view, "
            "suitable for app icon, high detail, centered composition"
        ),
        negative_prompt=(
            "complex background, multiple objects, text, "
            "blurry, low quality, distorted proportions"
        ),
        recommended_params={
            "width": 512,
            "height": 512,
            "steps": 30,
            "cfg_scale": 7.5,
        },
        description="Clean 3D icons on white background - perfect for apps",
    ),
    
    "icon_flat_modern": PromptTemplate(
        name="Flat Modern Icon",
        category="icon",
        base_prompt=(
            "flat design icon of {subject}, minimal geometric shapes, "
            "bold colors, clean edges, material design style, "
            "vector art quality, centered, app icon style"
        ),
        negative_prompt=(
            "3d, shadows, gradients, photorealistic, "
            "complex details, text"
        ),
        recommended_params={
            "width": 512,
            "height": 512,
            "steps": 25,
            "cfg_scale": 8.0,
        },
        description="Flat design icons in material design style",
    ),
    
    "icon_glassmorphism": PromptTemplate(
        name="Glassmorphism Icon",
        category="icon",
        base_prompt=(
            "glassmorphism icon of {subject}, frosted glass effect, "
            "soft blur, subtle glow, transparent layers, "
            "modern iOS style, premium quality, centered"
        ),
        negative_prompt=(
            "opaque, flat, dull, pixelated, "
            "low quality, busy background"
        ),
        recommended_params={
            "width": 512,
            "height": 512,
            "steps": 30,
            "cfg_scale": 7.0,
        },
        description="Glassmorphism icons with frosted glass effect",
    ),

    # Backgrounds
    "background_mesh_gradient": PromptTemplate(
        name="Mesh Gradient",
        category="background",
        base_prompt=(
            "mesh gradient background, smooth color blending, "
            "vibrant but not harsh colors, abstract fluid shapes, "
            "high resolution, seamless edges"
        ),
        negative_prompt=(
            "text, patterns, objects, harsh edges, "
            "banding, low quality"
        ),
        recommended_params={
            "width": 1920,
            "height": 1080,
            "steps": 25,
            "cfg_scale": 6.0,
        },
        description="Smooth mesh gradients for website backgrounds",
    ),
    
    "background_particles": PromptTemplate(
        name="Particle Field",
        category="background",
        base_prompt=(
            "abstract particle field, glowing dots, "
            "dark background with light particles, "
            "tech aesthetic, network visualization, "
            "depth effect, high resolution"
        ),
        negative_prompt=(
            "bright background, cluttered, text, "
            "realistic objects, noisy"
        ),
        recommended_params={
            "width": 1920,
            "height": 1080,
            "steps": 30,
            "cfg_scale": 7.0,
        },
        description="Tech-style particle backgrounds",
    ),

    # Illustrations
    "illustration_isometric": PromptTemplate(
        name="Isometric Scene",
        category="illustration",
        base_prompt=(
            "isometric illustration of {subject}, "
            "cute minimal style, soft pastel colors, "
            "clean lines, digital art, "
            "suitable for website illustration"
        ),
        negative_prompt=(
            "realistic, photograph, messy, "
            "dark colors, complex details"
        ),
        recommended_params={
            "width": 1024,
            "height": 1024,
            "steps": 30,
            "cfg_scale": 7.5,
        },
        description="Cute isometric illustrations for websites",
    ),

    # Patterns
    "pattern_geometric": PromptTemplate(
        name="Geometric Pattern",
        category="pattern",
        base_prompt=(
            "seamless geometric pattern, repeating shapes, "
            "clean minimal design, {color_scheme} colors, "
            "tileable, high resolution"
        ),
        negative_prompt=(
            "non-repeating, irregular, photorealistic, "
            "text, watermark"
        ),
        recommended_params={
            "width": 512,
            "height": 512,
            "steps": 25,
            "cfg_scale": 8.0,
        },
        description="Seamless geometric patterns for backgrounds",
    ),
}


# =============================================================================
# VIDEO GENERATION TEMPLATES (SVD)
# =============================================================================

VIDEO_TEMPLATES: dict[str, PromptTemplate] = {
    "video_hero_subtle": PromptTemplate(
        name="Subtle Hero Animation",
        category="hero",
        base_prompt=(
            "subtle motion, gentle floating particles, "
            "slow smooth movement, ambient animation, "
            "perfect loop, professional quality"
        ),
        negative_prompt=(
            "fast motion, jarring, flickering, "
            "low framerate, artifacts"
        ),
        recommended_params={
            "motion_bucket_id": 40,  # Lower = more subtle
            "fps": 24,
            "frames": 25,
            "decode_chunk_size": 8,
        },
        description="Subtle ambient motion for hero backgrounds",
    ),
    
    "video_hero_dynamic": PromptTemplate(
        name="Dynamic Hero Animation",
        category="hero",
        base_prompt=(
            "dynamic flowing motion, energetic movement, "
            "smooth transitions, cinematic quality, "
            "professional video production"
        ),
        negative_prompt=(
            "static, choppy, flickering, "
            "low quality, blurry"
        ),
        recommended_params={
            "motion_bucket_id": 127,  # Higher = more motion
            "fps": 30,
            "frames": 25,
            "decode_chunk_size": 8,
        },
        description="Dynamic motion for energetic hero sections",
    ),
    
    "video_background_loop": PromptTemplate(
        name="Seamless Background Loop",
        category="background",
        base_prompt=(
            "seamless loop, continuous motion, "
            "ambient background animation, "
            "smooth transitions, no jarring cuts"
        ),
        negative_prompt=(
            "visible seam, jump cut, flickering, "
            "inconsistent motion"
        ),
        recommended_params={
            "motion_bucket_id": 60,
            "fps": 24,
            "frames": 48,  # Longer for smooth loop
            "decode_chunk_size": 8,
        },
        description="Seamless looping backgrounds",
    ),
    
    "video_transition": PromptTemplate(
        name="UI Transition Effect",
        category="transition",
        base_prompt=(
            "smooth transition effect, morphing shapes, "
            "fluid motion, modern UI animation, "
            "professional quality"
        ),
        negative_prompt=(
            "static, abrupt, choppy, "
            "low framerate"
        ),
        recommended_params={
            "motion_bucket_id": 80,
            "fps": 30,
            "frames": 15,  # Short for transitions
            "decode_chunk_size": 8,
        },
        description="Smooth transitions for UI animations",
    ),
}


# =============================================================================
# 3D MODEL TEMPLATES (TripoSR)
# =============================================================================

MODEL3D_TEMPLATES: dict[str, PromptTemplate] = {
    "3d_icon_minimal": PromptTemplate(
        name="Minimal 3D Icon",
        category="icon",
        base_prompt=(
            "3D render of a simple geometric {subject}, "
            "clean white background, soft studio lighting, "
            "minimal design, isometric view, "
            "suitable for UI icon, high detail"
        ),
        negative_prompt=(
            "complex background, multiple objects, "
            "blurry, low quality, distorted"
        ),
        recommended_params={
            "resolution": 256,
            "threshold": 0.5,
            "remove_background": True,
            "steps": 30,
            "cfg_scale": 7.5,
        },
        description="Clean minimal 3D icons for UI",
    ),
    
    "3d_icon_detailed": PromptTemplate(
        name="Detailed 3D Icon",
        category="icon",
        base_prompt=(
            "detailed 3D render of {subject}, "
            "photorealistic materials, studio lighting, "
            "clean white background, centered composition, "
            "high polygon, ray tracing"
        ),
        negative_prompt=(
            "cartoon, flat, low detail, "
            "blurry, noisy background"
        ),
        recommended_params={
            "resolution": 512,
            "threshold": 0.4,
            "remove_background": True,
            "steps": 40,
            "cfg_scale": 8.0,
        },
        description="Detailed photorealistic 3D icons",
    ),
    
    "3d_object_isometric": PromptTemplate(
        name="Isometric 3D Object",
        category="scene",
        base_prompt=(
            "isometric 3D render of {subject}, "
            "soft pastel colors, clean geometric style, "
            "white background, minimal shadows, "
            "suitable for infographic"
        ),
        negative_prompt=(
            "perspective view, photorealistic, "
            "complex textures, dark"
        ),
        recommended_params={
            "resolution": 256,
            "threshold": 0.5,
            "remove_background": True,
            "steps": 30,
            "cfg_scale": 7.0,
        },
        description="Isometric objects for infographics and illustrations",
    ),
    
    "3d_character_simple": PromptTemplate(
        name="Simple 3D Character",
        category="avatar",
        base_prompt=(
            "cute 3D character of {subject}, "
            "cartoon style, simple shapes, "
            "friendly expression, clean design, "
            "white background, centered"
        ),
        negative_prompt=(
            "realistic, scary, complex, "
            "multiple characters, busy background"
        ),
        recommended_params={
            "resolution": 256,
            "threshold": 0.5,
            "remove_background": True,
            "steps": 35,
            "cfg_scale": 7.5,
        },
        description="Simple cute 3D characters for avatars",
    ),
    
    "3d_product_showcase": PromptTemplate(
        name="Product Showcase",
        category="scene",
        base_prompt=(
            "product photography style 3D render of {subject}, "
            "professional studio lighting, reflective surface, "
            "clean white background, commercial quality, "
            "high detail"
        ),
        negative_prompt=(
            "cartoon, low quality, distorted, "
            "busy background, poor lighting"
        ),
        recommended_params={
            "resolution": 512,
            "threshold": 0.4,
            "remove_background": True,
            "steps": 40,
            "cfg_scale": 8.0,
        },
        description="Product-style 3D renders for showcases",
    ),
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_template(template_id: str) -> PromptTemplate | None:
    """Get a template by ID from any category."""
    return (
        IMAGE_TEMPLATES.get(template_id) or
        VIDEO_TEMPLATES.get(template_id) or
        MODEL3D_TEMPLATES.get(template_id)
    )


def list_templates(category: str | None = None) -> dict[str, list[str]]:
    """List all available templates, optionally filtered by category."""
    result = {
        "image": [],
        "video": [],
        "model3d": [],
    }
    
    for tid, template in IMAGE_TEMPLATES.items():
        if category is None or template.category == category:
            result["image"].append(tid)
    
    for tid, template in VIDEO_TEMPLATES.items():
        if category is None or template.category == category:
            result["video"].append(tid)
    
    for tid, template in MODEL3D_TEMPLATES.items():
        if category is None or template.category == category:
            result["model3d"].append(tid)
    
    return result


def apply_template(
    template_id: str,
    variables: dict[str, str] | None = None,
) -> dict[str, Any]:
    """
    Apply a template and return generation parameters.
    
    Args:
        template_id: The template to use
        variables: Variables to substitute in the prompt (e.g., {subject})
        
    Returns:
        Dict with prompt, negative_prompt, and recommended_params
    """
    template = get_template(template_id)
    if not template:
        raise ValueError(f"Template not found: {template_id}")
    
    variables = variables or {}
    
    # Substitute variables in prompts
    prompt = template.base_prompt
    negative_prompt = template.negative_prompt
    
    for key, value in variables.items():
        prompt = prompt.replace(f"{{{key}}}", value)
        negative_prompt = negative_prompt.replace(f"{{{key}}}", value)
    
    return {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "parameters": template.recommended_params.copy(),
    }


def enhance_prompt(base_prompt: str, asset_type: str) -> str:
    """
    Enhance a user's prompt with quality modifiers.
    
    Args:
        base_prompt: User's original prompt
        asset_type: Type of asset (image, video, model3d)
        
    Returns:
        Enhanced prompt with quality modifiers
    """
    quality_suffixes = {
        "image": ", high quality, professional, 8k resolution, detailed",
        "video": ", smooth motion, professional quality, cinematic",
        "model3d": ", clean geometry, detailed, suitable for real-time rendering",
    }
    
    suffix = quality_suffixes.get(asset_type, "")
    return f"{base_prompt.rstrip(', ')}{suffix}"


def get_default_negative_prompt(asset_type: str) -> str:
    """Get default negative prompt for an asset type."""
    negatives = {
        "image": (
            "blurry, low quality, pixelated, noisy, "
            "watermark, text, jpeg artifacts, distorted"
        ),
        "video": (
            "flickering, choppy, low framerate, artifacts, "
            "blurry, inconsistent, jarring motion"
        ),
        "model3d": (
            "low poly, distorted, broken geometry, "
            "floating artifacts, holes, non-manifold"
        ),
    }
    return negatives.get(asset_type, "low quality, blurry")
