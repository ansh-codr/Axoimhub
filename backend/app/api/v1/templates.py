"""
Axiom Design Engine - Templates Routes
UI-optimized prompt templates for AI generation
"""

from typing import Annotated

from fastapi import APIRouter, Query, status
from pydantic import BaseModel, Field

from app.core.prompt_templates import (
    IMAGE_TEMPLATES,
    VIDEO_TEMPLATES,
    MODEL3D_TEMPLATES,
    get_template,
    list_templates,
    apply_template,
    enhance_prompt,
    get_default_negative_prompt,
)


router = APIRouter(prefix="/templates", tags=["Templates"])


# =============================================================================
# SCHEMAS
# =============================================================================

class TemplateInfo(BaseModel):
    """Template information."""
    id: str
    name: str
    category: str
    description: str
    base_prompt: str
    negative_prompt: str
    recommended_params: dict


class TemplateListResponse(BaseModel):
    """List of templates by asset type."""
    image: list[str]
    video: list[str]
    model3d: list[str]


class ApplyTemplateRequest(BaseModel):
    """Request to apply a template."""
    template_id: str = Field(..., description="ID of the template to apply")
    variables: dict[str, str] | None = Field(
        default=None,
        description="Variables to substitute in the prompt (e.g., {subject})",
    )


class ApplyTemplateResponse(BaseModel):
    """Applied template result."""
    prompt: str
    negative_prompt: str
    parameters: dict


class EnhancePromptRequest(BaseModel):
    """Request to enhance a prompt."""
    prompt: str = Field(..., description="User's base prompt")
    asset_type: str = Field(..., description="Type: image, video, or model3d")


class EnhancePromptResponse(BaseModel):
    """Enhanced prompt result."""
    enhanced_prompt: str
    default_negative_prompt: str


# =============================================================================
# ROUTES
# =============================================================================

@router.get(
    "",
    response_model=TemplateListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Templates",
    description="List all available prompt templates by asset type.",
)
async def get_templates(
    category: Annotated[
        str | None,
        Query(description="Filter by category (hero, icon, background, etc.)"),
    ] = None,
) -> TemplateListResponse:
    """
    Get list of all available template IDs.
    
    Optionally filter by category:
    - hero: Hero section backgrounds
    - icon: App icons
    - background: General backgrounds
    - button: Button graphics
    - card: Card backgrounds
    - illustration: Illustrations
    - pattern: Repeating patterns
    - avatar: Avatar/character graphics
    - scene: Scene compositions
    """
    templates = list_templates(category)
    return TemplateListResponse(**templates)


@router.get(
    "/{template_id}",
    response_model=TemplateInfo,
    status_code=status.HTTP_200_OK,
    summary="Get Template",
    description="Get detailed information about a specific template.",
)
async def get_template_info(template_id: str) -> TemplateInfo:
    """
    Get full details of a template including prompts and recommended parameters.
    """
    template = get_template(template_id)
    if not template:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=404,
            detail=f"Template not found: {template_id}",
        )
    
    return TemplateInfo(
        id=template_id,
        name=template.name,
        category=template.category,
        description=template.description,
        base_prompt=template.base_prompt,
        negative_prompt=template.negative_prompt,
        recommended_params=template.recommended_params,
    )


@router.post(
    "/apply",
    response_model=ApplyTemplateResponse,
    status_code=status.HTTP_200_OK,
    summary="Apply Template",
    description="Apply a template with variable substitution.",
)
async def apply_template_endpoint(request: ApplyTemplateRequest) -> ApplyTemplateResponse:
    """
    Apply a template and get generation-ready prompts.
    
    Variables are substituted using {key} syntax in the template.
    For example, if template has "{subject}", pass {"subject": "coffee mug"}.
    """
    try:
        result = apply_template(request.template_id, request.variables)
        return ApplyTemplateResponse(
            prompt=result["prompt"],
            negative_prompt=result["negative_prompt"],
            parameters=result["parameters"],
        )
    except ValueError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/enhance",
    response_model=EnhancePromptResponse,
    status_code=status.HTTP_200_OK,
    summary="Enhance Prompt",
    description="Add quality modifiers to a user prompt.",
)
async def enhance_prompt_endpoint(request: EnhancePromptRequest) -> EnhancePromptResponse:
    """
    Enhance a user's prompt with quality modifiers.
    
    Adds appropriate quality suffixes based on asset type and returns
    a recommended negative prompt.
    """
    if request.asset_type not in ["image", "video", "model3d"]:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail="asset_type must be one of: image, video, model3d",
        )
    
    enhanced = enhance_prompt(request.prompt, request.asset_type)
    negative = get_default_negative_prompt(request.asset_type)
    
    return EnhancePromptResponse(
        enhanced_prompt=enhanced,
        default_negative_prompt=negative,
    )


@router.get(
    "/categories",
    response_model=list[str],
    status_code=status.HTTP_200_OK,
    summary="List Categories",
    description="List all available template categories.",
)
async def list_categories() -> list[str]:
    """Get list of all template categories."""
    categories = set()
    
    for template in IMAGE_TEMPLATES.values():
        categories.add(template.category)
    for template in VIDEO_TEMPLATES.values():
        categories.add(template.category)
    for template in MODEL3D_TEMPLATES.values():
        categories.add(template.category)
    
    return sorted(categories)


@router.get(
    "/by-category/{category}",
    response_model=list[TemplateInfo],
    status_code=status.HTTP_200_OK,
    summary="Get Templates by Category",
    description="Get all templates in a specific category.",
)
async def get_templates_by_category(category: str) -> list[TemplateInfo]:
    """Get all templates matching a specific category."""
    results = []
    
    for tid, template in IMAGE_TEMPLATES.items():
        if template.category == category:
            results.append(TemplateInfo(
                id=tid,
                name=template.name,
                category=template.category,
                description=template.description,
                base_prompt=template.base_prompt,
                negative_prompt=template.negative_prompt,
                recommended_params=template.recommended_params,
            ))
    
    for tid, template in VIDEO_TEMPLATES.items():
        if template.category == category:
            results.append(TemplateInfo(
                id=tid,
                name=template.name,
                category=template.category,
                description=template.description,
                base_prompt=template.base_prompt,
                negative_prompt=template.negative_prompt,
                recommended_params=template.recommended_params,
            ))
    
    for tid, template in MODEL3D_TEMPLATES.items():
        if template.category == category:
            results.append(TemplateInfo(
                id=tid,
                name=template.name,
                category=template.category,
                description=template.description,
                base_prompt=template.base_prompt,
                negative_prompt=template.negative_prompt,
                recommended_params=template.recommended_params,
            ))
    
    return results
