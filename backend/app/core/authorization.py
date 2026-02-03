"""
Axiom Design Engine - Authorization Module
Role-Based Access Control (RBAC) enforcement
"""

from typing import Callable
from uuid import UUID

from fastapi import Depends, HTTPException, status

from app.core.auth_config import ROLE_PERMISSIONS, Permission
from app.core.dependencies import CurrentUser
from app.models.user import User, UserRole


def require_permission(permission: Permission) -> Callable:
    """
    Factory for permission-based access control dependency.

    Args:
        permission: Required permission

    Returns:
        Dependency function that validates user has permission

    Example:
        @router.post("/jobs")
        async def create_job(
            user: Annotated[User, Depends(require_permission(Permission.CREATE_JOB))]
        ):
            ...
    """

    async def permission_checker(user: CurrentUser) -> User:
        # Get permissions for user's role
        user_permissions = ROLE_PERMISSIONS.get(user.role.value, [])

        # Check if user has required permission
        if permission not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission.value}' required",
            )

        return user

    return permission_checker


def require_role(required_role: UserRole) -> Callable:
    """
    Factory for role-based access control dependency.

    Args:
        required_role: Minimum required role

    Returns:
        Dependency function that validates user role

    Example:
        @router.post("/admin/users")
        async def manage_users(
            user: Annotated[User, Depends(require_role(UserRole.ADMIN))]
        ):
            ...
    """

    async def role_checker(user: CurrentUser) -> User:
        # Define role hierarchy
        role_hierarchy = {
            UserRole.USER: 0,
            UserRole.ADMIN: 1,
        }

        user_level = role_hierarchy.get(user.role, 0)
        required_level = role_hierarchy.get(required_role, 0)

        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role.value}' required",
            )

        return user

    return role_checker


class AuthorizationService:
    """Service for authorization checks."""

    @staticmethod
    def user_can_access_asset(user: User, asset_owner_id: UUID) -> bool:
        """
        Check if user can access an asset.

        Args:
            user: Current user
            asset_owner_id: ID of asset owner

        Returns:
            True if user can access, False otherwise
        """
        # User can access own assets
        if user.id == asset_owner_id:
            return True

        # Admins can access all assets
        if user.is_admin:
            return True

        return False

    @staticmethod
    def user_can_access_project(user: User, project_owner_id: UUID) -> bool:
        """
        Check if user can access a project.

        Args:
            user: Current user
            project_owner_id: ID of project owner

        Returns:
            True if user can access, False otherwise
        """
        # User can access own projects
        if user.id == project_owner_id:
            return True

        # Admins can access all projects
        if user.is_admin:
            return True

        return False

    @staticmethod
    def user_can_access_job(user: User, job_owner_id: UUID) -> bool:
        """
        Check if user can access a job.

        Args:
            user: Current user
            job_owner_id: ID of job owner

        Returns:
            True if user can access, False otherwise
        """
        # User can access own jobs
        if user.id == job_owner_id:
            return True

        # Admins can access all jobs
        if user.is_admin:
            return True

        return False

    @staticmethod
    def has_permission(user: User, permission: Permission) -> bool:
        """
        Check if user has a specific permission.

        Args:
            user: Current user
            permission: Required permission

        Returns:
            True if user has permission, False otherwise
        """
        user_permissions = ROLE_PERMISSIONS.get(user.role.value, [])
        return permission in user_permissions

    @staticmethod
    def require_permission_or_raise(user: User, permission: Permission) -> None:
        """
        Raise HTTPException if user doesn't have permission.

        Args:
            user: Current user
            permission: Required permission

        Raises:
            HTTPException: If user doesn't have permission
        """
        if not AuthorizationService.has_permission(user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission.value}' required",
            )
