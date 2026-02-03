# Database Package
# Note: Import Base separately to avoid circular imports with session
from app.db.base import Base, TimestampMixin, UUIDMixin

__all__ = [
    "Base",
    "TimestampMixin",
    "UUIDMixin",
]

# Lazy imports for session-related items to avoid circular imports
def get_session_maker():
    from app.db.session import async_session_maker
    return async_session_maker

def get_engine():
    from app.db.session import engine
    return engine
