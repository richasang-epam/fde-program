"""
Database connection and session management.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from typing import AsyncGenerator
import logging

from .config import settings

logger = logging.getLogger(__name__)

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    poolclass=NullPool,  # Disable connection pooling for serverless
)

# Create async session factory
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database session."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database tables."""
    from sqlalchemy import text

    async with engine.begin() as conn:
        # Create tables if they don't exist
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS onboarding_instances (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                employee_id VARCHAR(50) NOT NULL UNIQUE,
                hire_date DATE NOT NULL,
                employment_type VARCHAR(20) NOT NULL,
                jurisdiction VARCHAR(50) NOT NULL,
                department VARCHAR(100),
                job_level VARCHAR(20),
                status VARCHAR(20) NOT NULL DEFAULT 'NEW_HIRE',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                completed_at TIMESTAMP WITH TIME ZONE,
                sla_violations INTEGER DEFAULT 0,
                last_state_change TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """))

        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS tasks (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                onboarding_instance_id UUID NOT NULL REFERENCES onboarding_instances(id),
                task_type VARCHAR(50) NOT NULL,
                system_source VARCHAR(50) NOT NULL,
                assigned_to VARCHAR(50) NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
                due_date TIMESTAMP WITH TIME ZONE,
                completed_at TIMESTAMP WITH TIME ZONE,
                output JSONB,
                retry_count INTEGER DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """))

        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS escalations (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                task_id UUID NOT NULL REFERENCES tasks(id),
                escalation_type VARCHAR(50) NOT NULL,
                description TEXT,
                context JSONB DEFAULT '{}',
                options_considered JSONB DEFAULT '[]',
                recommended_action TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                resolved_at TIMESTAMP WITH TIME ZONE,
                resolution TEXT,
                resolved_by VARCHAR(100)
            );
        """))

        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS task_dependencies (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                task_type VARCHAR(50) NOT NULL,
                depends_on VARCHAR(50) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """))

        logger.info("Database tables initialized")


async def close_db():
    """Close database connections."""
    await engine.dispose()
    logger.info("Database connections closed")