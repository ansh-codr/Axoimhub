"""
Axiom Design Engine - Project Service
Core service for managing projects
"""

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_config import Permission
from app.core.authorization import AuthorizationService
from app.core.exceptions import (
    ProjectNotFoundError,
    AuthorizationError,
    DuplicateError,
)
from app.models.project import Project
from app.models.user import User


class ProjectService:
    """
    Service for managing projects.
    
    Projects are containers for organizing jobs and assets.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Project Creation
    # =========================================================================

    async def create_project(
        self,
        user: User,
        name: str,
        description: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Project:
        """
        Create a new project.
        
        Args:
            user: User creating the project
            name: Project name
            description: Optional description
            metadata: Optional metadata
            
        Returns:
            Created Project instance
        """
        # Check permissions
        AuthorizationService.require_permission_or_raise(
            user, Permission.CREATE_PROJECT
        )

        # Check for duplicate name for this user
        existing = await self.db.execute(
            select(Project).where(
                and_(Project.user_id == user.id, Project.name == name)
            )
        )
        if existing.scalar_one_or_none():
            raise DuplicateError("Project", "name", name)

        project = Project(
            user_id=user.id,
            name=name,
            description=description,
            metadata=metadata or {},
        )

        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)

        return project

    # =========================================================================
    # Project Retrieval
    # =========================================================================

    async def get_project(self, project_id: UUID, user: User) -> Project:
        """
        Get a project by ID.
        
        Args:
            project_id: Project identifier
            user: User requesting the project
            
        Returns:
            Project instance
            
        Raises:
            ProjectNotFoundError: If project doesn't exist
            AuthorizationError: If user can't access project
        """
        project = await self.db.get(Project, project_id)
        
        if project is None:
            raise ProjectNotFoundError(str(project_id))

        # Check access
        if not AuthorizationService.user_can_access_project(user, project.user_id):
            raise AuthorizationError("You don't have access to this project")

        return project

    async def list_projects(
        self,
        user: User,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Project]:
        """
        List projects for a user.
        
        Args:
            user: User requesting projects
            limit: Maximum results
            offset: Pagination offset
            
        Returns:
            List of Project instances
        """
        conditions = []

        # Users see only their projects, admins see all
        if not user.is_admin:
            conditions.append(Project.user_id == user.id)

        query = (
            select(Project)
            .where(and_(*conditions) if conditions else True)
            .order_by(Project.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    # =========================================================================
    # Project Management
    # =========================================================================

    async def update_project(
        self,
        project_id: UUID,
        user: User,
        name: str | None = None,
        description: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Project:
        """
        Update a project.
        
        Args:
            project_id: Project identifier
            user: User requesting update
            name: Optional new name
            description: Optional new description
            metadata: Optional metadata to merge
            
        Returns:
            Updated Project instance
        """
        project = await self.get_project(project_id, user)

        if name is not None:
            project.name = name
        if description is not None:
            project.description = description
        if metadata is not None:
            project.metadata = {**(project.metadata or {}), **metadata}

        project.updated_at = datetime.now(timezone.utc)
        
        await self.db.commit()
        await self.db.refresh(project)

        return project

    async def delete_project(self, project_id: UUID, user: User) -> None:
        """
        Delete a project and all its contents.
        
        Args:
            project_id: Project identifier
            user: User requesting deletion
        """
        project = await self.get_project(project_id, user)

        # Delete project (cascade will handle jobs and assets)
        await self.db.delete(project)
        await self.db.commit()
