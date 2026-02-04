"""
Axiom Design Engine - Prompt Enhancer Service
Optional LLM-backed prompt enhancement (e.g., Dolphin via HF Inference endpoint).
"""

from typing import Any

import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.core.prompt_templates import enhance_prompt


class PromptEnhancer:
    """Service for enhancing prompts using rules or an LLM endpoint."""

    def __init__(self) -> None:
        self.logger = get_logger(__name__)

    async def enhance(self, base_prompt: str, asset_type: str) -> str:
        """Enhance a prompt using configured mode."""
        if settings.prompt_enhancer_mode != "hf":
            return enhance_prompt(base_prompt, asset_type)

        endpoint = settings.prompt_enhancer_endpoint.strip()
        if not endpoint:
            self.logger.warning(
                "Prompt enhancer endpoint not set, falling back to rules"
            )
            return enhance_prompt(base_prompt, asset_type)

        payload: dict[str, Any] = {
            "inputs": self._build_instruction(base_prompt, asset_type),
            "parameters": {
                "max_new_tokens": settings.prompt_enhancer_max_new_tokens,
                "temperature": settings.prompt_enhancer_temperature,
                "top_p": settings.prompt_enhancer_top_p,
                "return_full_text": False,
            },
        }

        if settings.prompt_enhancer_model:
            payload["model"] = settings.prompt_enhancer_model

        headers = {"Content-Type": "application/json"}
        if settings.prompt_enhancer_api_key:
            headers["Authorization"] = f"Bearer {settings.prompt_enhancer_api_key}"

        try:
            async with httpx.AsyncClient(
                timeout=settings.prompt_enhancer_timeout_seconds
            ) as client:
                response = await client.post(endpoint, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
        except Exception as exc:  # noqa: BLE001
            self.logger.warning(
                f"Prompt enhancer request failed, falling back to rules: {exc}"
            )
            return enhance_prompt(base_prompt, asset_type)

        enhanced = self._extract_text(data)
        if not enhanced:
            self.logger.warning(
                "Prompt enhancer returned no text, falling back to rules"
            )
            return enhance_prompt(base_prompt, asset_type)

        return enhanced

    def _build_instruction(self, base_prompt: str, asset_type: str) -> str:
        """Build instruction for the LLM."""
        return (
            "You are a prompt engineer for generative media. "
            "Rewrite the user's prompt into a single, detailed prompt optimized "
            f"for {asset_type} generation. Include style, lighting, composition, "
            "and quality modifiers when appropriate. Return only the rewritten prompt.\n\n"
            f"User prompt: {base_prompt.strip()}"
        )

    def _extract_text(self, data: Any) -> str:
        """Extract generated text from common HF/TGI response shapes."""
        if isinstance(data, list) and data:
            first = data[0]
            if isinstance(first, dict) and "generated_text" in first:
                return str(first["generated_text"]).strip()
            if isinstance(first, str):
                return first.strip()

        if isinstance(data, dict):
            if "generated_text" in data:
                return str(data["generated_text"]).strip()
            if "text" in data:
                return str(data["text"]).strip()

        if isinstance(data, str):
            return data.strip()

        return ""
