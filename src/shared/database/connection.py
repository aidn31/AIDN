"""Database connection management for AIDN."""

import asyncpg
import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and operations."""

    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or os.getenv("DATABASE_URL")
        self.pool: Optional[asyncpg.Pool] = None

        if not self.database_url:
            raise ValueError("DATABASE_URL must be provided via parameter or environment variable")

    async def connect(self) -> None:
        """Create database connection pool."""
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            logger.info("Database connection pool created successfully")
        except Exception as e:
            logger.error(f"Failed to create database pool: {e}")
            raise

    async def disconnect(self) -> None:
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")

    async def execute(self, query: str, *args) -> str:
        """Execute a query that doesn't return rows."""
        if not self.pool:
            await self.connect()

        async with self.pool.acquire() as connection:
            return await connection.execute(query, *args)

    async def fetch(self, query: str, *args) -> list:
        """Fetch multiple rows."""
        if not self.pool:
            await self.connect()

        async with self.pool.acquire() as connection:
            return await connection.fetch(query, *args)

    async def fetchrow(self, query: str, *args) -> Optional[asyncpg.Record]:
        """Fetch a single row."""
        if not self.pool:
            await self.connect()

        async with self.pool.acquire() as connection:
            return await connection.fetchrow(query, *args)

    async def fetchval(self, query: str, *args):
        """Fetch a single value."""
        if not self.pool:
            await self.connect()

        async with self.pool.acquire() as connection:
            return await connection.fetchval(query, *args)

    async def initialize_schema(self) -> None:
        """Initialize database schema from schema.sql file."""
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")

        try:
            with open(schema_path, 'r') as f:
                schema_sql = f.read()

            await self.execute(schema_sql)
            logger.info("Database schema initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize schema: {e}")
            raise