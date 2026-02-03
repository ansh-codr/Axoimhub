"""
Axiom Design Engine - Prompt Sanitization and Validation
Safety checks and content filtering for user prompts
"""

import re
from typing import Optional

from app.core.auth_config import (
    CONTENT_RESTRICTIONS,
    DANGEROUS_PATTERNS,
    PROMPT_SANITIZATION,
)
from app.core.exceptions import ValidationError


class PromptSanitizer:
    """Sanitize and validate user prompts for safety."""

    @staticmethod
    def check_length(prompt: str) -> str:
        """
        Enforce maximum prompt length.

        Args:
            prompt: User's prompt text

        Returns:
            Original prompt if valid

        Raises:
            ValidationError: If prompt exceeds max length
        """
        max_length = PROMPT_SANITIZATION["max_length"]
        if len(prompt) > max_length:
            raise ValidationError(
                f"Prompt exceeds maximum length of {max_length} characters"
            )
        return prompt

    @staticmethod
    def check_executable_code(prompt: str) -> str:
        """
        Check and remove executable code patterns.

        Args:
            prompt: User's prompt text

        Returns:
            Sanitized prompt

        Raises:
            ValidationError: If dangerous code patterns detected
        """
        if not PROMPT_SANITIZATION.get("strip_executable_code"):
            return prompt

        code_patterns = DANGEROUS_PATTERNS.get("code_patterns", [])
        for pattern in code_patterns:
            matches = re.finditer(pattern, prompt, re.IGNORECASE)
            if matches:
                raise ValidationError(
                    "Prompt contains executable code patterns which are not allowed"
                )

        return prompt

    @staticmethod
    def check_filesystem_paths(prompt: str) -> str:
        """
        Reject prompts containing filesystem paths.

        Args:
            prompt: User's prompt text

        Returns:
            Original prompt if valid

        Raises:
            ValidationError: If filesystem paths detected
        """
        if not PROMPT_SANITIZATION.get("reject_filesystem_paths"):
            return prompt

        path_patterns = DANGEROUS_PATTERNS.get("filesystem_paths", [])
        for pattern in path_patterns:
            if re.search(pattern, prompt):
                raise ValidationError(
                    "Prompt contains filesystem paths which are not allowed"
                )

        return prompt

    @staticmethod
    def check_sql_patterns(prompt: str) -> str:
        """
        Reject prompts containing SQL injection patterns.

        Args:
            prompt: User's prompt text

        Returns:
            Original prompt if valid

        Raises:
            ValidationError: If SQL patterns detected
        """
        if not PROMPT_SANITIZATION.get("reject_sql_patterns"):
            return prompt

        sql_patterns = DANGEROUS_PATTERNS.get("sql_patterns", [])
        for pattern in sql_patterns:
            if re.search(pattern, prompt, re.IGNORECASE):
                raise ValidationError(
                    "Prompt contains SQL patterns which are not allowed"
                )

        return prompt

    @staticmethod
    def check_content_restrictions(prompt: str) -> str:
        """
        Check prompt against content restrictions.

        Args:
            prompt: User's prompt text

        Returns:
            Original prompt if valid

        Raises:
            ValidationError: If prohibited content detected
        """
        restrictions = CONTENT_RESTRICTIONS

        # Check for identity impersonation keywords
        if restrictions.get("no_identity_impersonation"):
            impersonation_keywords = [
                r"\b(impersonate|pretend|fake|false identity)\b",
                r"\b(as \w+ would say)\b",
                r"\b(in the style of \w+)\b",
            ]
            for pattern in impersonation_keywords:
                if re.search(pattern, prompt, re.IGNORECASE):
                    raise ValidationError(
                        "Prompts requesting identity impersonation are not allowed"
                    )

        # Check for biometric replication requests
        if restrictions.get("no_biometric_replication"):
            biometric_keywords = [
                r"\b(face|fingerprint|iris|voice|signature)\b",
                r"\b(deepfake|fake face)\b",
                r"\b(replica of|copy of)\s+\w+",
            ]
            for pattern in biometric_keywords:
                if re.search(pattern, prompt, re.IGNORECASE):
                    raise ValidationError(
                        "Prompts requesting biometric replication are not allowed"
                    )

        # Check for explicit content
        if restrictions.get("no_explicit_content"):
            explicit_keywords = [
                r"\b(nude|naked|explicit|adult|sexual|erotic)\b",
                r"\b(xxx|porn)\b",
            ]
            for pattern in explicit_keywords:
                if re.search(pattern, prompt, re.IGNORECASE):
                    raise ValidationError(
                        "Prompts containing explicit content are not allowed"
                    )

        # Check for violence
        if restrictions.get("no_violence"):
            violence_keywords = [
                r"\b(kill|murder|assault|violence|gore|blood)\b",
                r"\b(weapon|gun|knife|bomb)\b",
            ]
            for pattern in violence_keywords:
                if re.search(pattern, prompt, re.IGNORECASE):
                    raise ValidationError(
                        "Prompts containing violent content are not allowed"
                    )

        # Check for hate speech
        if restrictions.get("no_hate_speech"):
            # Generic check - in production, use comprehensive hate speech detector
            hate_keywords = [
                r"\b(hate|racist|sexist|bigot|discrimination)\b",
            ]
            for pattern in hate_keywords:
                if re.search(pattern, prompt, re.IGNORECASE):
                    raise ValidationError(
                        "Prompts containing hate speech are not allowed"
                    )

        return prompt

    @staticmethod
    def normalize_whitespace(prompt: str) -> str:
        """
        Normalize whitespace and remove extra spaces.

        Args:
            prompt: User's prompt text

        Returns:
            Normalized prompt
        """
        # Remove leading/trailing whitespace
        prompt = prompt.strip()

        # Replace multiple spaces with single space
        prompt = re.sub(r"\s+", " ", prompt)

        # Ensure proper spacing around punctuation
        prompt = re.sub(r"\s+([.,!?;:])", r"\1", prompt)

        return prompt

    @classmethod
    def sanitize(cls, prompt: str) -> str:
        """
        Complete prompt sanitization pipeline.

        Args:
            prompt: User's raw prompt text

        Returns:
            Sanitized and validated prompt

        Raises:
            ValidationError: If prompt fails any safety check
        """
        # Normalize first
        prompt = cls.normalize_whitespace(prompt)

        # Run all checks
        prompt = cls.check_length(prompt)
        prompt = cls.check_executable_code(prompt)
        prompt = cls.check_filesystem_paths(prompt)
        prompt = cls.check_sql_patterns(prompt)
        prompt = cls.check_content_restrictions(prompt)

        return prompt


class PromptValidator:
    """Validate prompt parameters and structure."""

    @staticmethod
    def validate_image_prompt(
        subject: str,
        context: str,
        negative_prompt: Optional[str] = None,
        style: Optional[str] = None,
    ) -> dict:
        """
        Validate image generation prompt.

        Args:
            subject: What to generate
            context: Design context (UI, illustration, etc)
            negative_prompt: What to avoid
            style: Visual style

        Returns:
            Validated prompt components

        Raises:
            ValidationError: If prompt invalid
        """
        sanitizer = PromptSanitizer()

        return {
            "subject": sanitizer.sanitize(subject),
            "context": sanitizer.sanitize(context),
            "negative_prompt": (
                sanitizer.sanitize(negative_prompt) if negative_prompt else ""
            ),
            "style": sanitizer.sanitize(style) if style else "modern minimal",
        }

    @staticmethod
    def validate_video_prompt(
        subject: str,
        motion_type: str,
        duration: Optional[int] = None,
    ) -> dict:
        """
        Validate video generation prompt.

        Args:
            subject: What to animate
            motion_type: Type of motion
            duration: Video duration in seconds (max 6)

        Returns:
            Validated prompt components

        Raises:
            ValidationError: If prompt invalid
        """
        sanitizer = PromptSanitizer()

        # Validate duration
        max_duration = PROMPT_SANITIZATION.get("max_length", 6)
        if duration and duration > max_duration:
            raise ValidationError(
                f"Video duration must not exceed {max_duration} seconds"
            )

        return {
            "subject": sanitizer.sanitize(subject),
            "motion_type": sanitizer.sanitize(motion_type),
            "duration": duration or 3,
        }

    @staticmethod
    def validate_model3d_prompt(
        subject: str,
        style: Optional[str] = None,
        detail_level: Optional[str] = None,
    ) -> dict:
        """
        Validate 3D model generation prompt.

        Args:
            subject: What to generate
            style: Visual style
            detail_level: Level of detail (low, medium, high)

        Returns:
            Validated prompt components

        Raises:
            ValidationError: If prompt invalid
        """
        sanitizer = PromptSanitizer()

        valid_detail_levels = ["low", "medium", "high"]
        if detail_level and detail_level.lower() not in valid_detail_levels:
            raise ValidationError(
                f"Detail level must be one of: {', '.join(valid_detail_levels)}"
            )

        return {
            "subject": sanitizer.sanitize(subject),
            "style": sanitizer.sanitize(style) if style else "clean modern",
            "detail_level": detail_level or "medium",
        }
