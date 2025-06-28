#!/usr/bin/env python3
"""
Database Initialization Script for FlipSync Authentication
AGENT_CONTEXT: Initialize authentication database with tables and default data
AGENT_PRIORITY: Create tables, roles, permissions, and admin user
AGENT_PATTERN: Async database operations with proper error handling
"""

import asyncio
import logging
import os
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from fs_agt_clean.database.models.unified_user import UnifiedUnifiedUser, Permission, Role
from fs_agt_clean.database.models.unified_base import Base

# AGENT_INSTRUCTION: Configure logging for database operations
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:1432/flipsync"
)


class DatabaseInitializer:
    """
    AGENT_CONTEXT: Database initialization and setup for authentication system
    AGENT_CAPABILITY: Create tables, seed data, manage database schema
    """

    def __init__(self, database_url: str = DATABASE_URL):
        """Initialize database connection"""
        self.database_url = database_url
        self.engine = create_async_engine(
            database_url, echo=True, future=True  # Log SQL statements
        )
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def create_tables(self) -> None:
        """Create all authentication tables"""
        logger.info("Creating authentication database tables...")

        async with self.engine.begin() as conn:
            # Create all tables defined in Base metadata
            await conn.run_sync(Base.metadata.create_all)

        logger.info("✅ Authentication tables created successfully")

    async def create_default_roles(self) -> None:
        """Create default roles for the system"""
        logger.info("Creating default roles...")

        default_roles = [
            {"name": "admin", "description": "System administrator with full access"},
            {"name": "user", "description": "Regular user with standard access"},
            {"name": "agent", "description": "AI agent with automated access"},
            {"name": "viewer", "description": "Read-only access to system"},
        ]

        async with self.async_session() as session:
            for role_data in default_roles:
                # Check if role already exists
                existing_role = await session.execute(
                    text("SELECT id FROM roles WHERE name = :name"),
                    {"name": role_data["name"]},
                )

                if not existing_role.first():
                    role = Role(
                        name=role_data["name"], description=role_data["description"]
                    )
                    session.add(role)
                    logger.info(f"Created role: {role_data['name']}")
                else:
                    logger.info(f"Role already exists: {role_data['name']}")

            await session.commit()

        logger.info("✅ Default roles created successfully")

    async def create_default_permissions(self) -> None:
        """Create default permissions for the system"""
        logger.info("Creating default permissions...")

        default_permissions = [
            # UnifiedUser management
            {
                "name": "users.read",
                "description": "Read user information",
                "resource": "users",
                "action": "read",
            },
            {
                "name": "users.write",
                "description": "Create and update users",
                "resource": "users",
                "action": "write",
            },
            {
                "name": "users.delete",
                "description": "Delete users",
                "resource": "users",
                "action": "delete",
            },
            # Product management
            {
                "name": "products.read",
                "description": "Read product information",
                "resource": "products",
                "action": "read",
            },
            {
                "name": "products.write",
                "description": "Create and update products",
                "resource": "products",
                "action": "write",
            },
            {
                "name": "products.delete",
                "description": "Delete products",
                "resource": "products",
                "action": "delete",
            },
            # Inventory management
            {
                "name": "inventory.read",
                "description": "Read inventory information",
                "resource": "inventory",
                "action": "read",
            },
            {
                "name": "inventory.write",
                "description": "Update inventory",
                "resource": "inventory",
                "action": "write",
            },
            # Analytics and reports
            {
                "name": "analytics.read",
                "description": "View analytics and reports",
                "resource": "analytics",
                "action": "read",
            },
            # System administration
            {
                "name": "admin.full",
                "description": "Full administrative access",
                "resource": "system",
                "action": "admin",
            },
            # API access
            {
                "name": "api.access",
                "description": "Access to API endpoints",
                "resource": "api",
                "action": "access",
            },
        ]

        async with self.async_session() as session:
            for perm_data in default_permissions:
                # Check if permission already exists
                existing_perm = await session.execute(
                    text("SELECT id FROM permissions WHERE name = :name"),
                    {"name": perm_data["name"]},
                )

                if not existing_perm.first():
                    permission = Permission(
                        name=perm_data["name"],
                        description=perm_data["description"],
                        resource=perm_data["resource"],
                        action=perm_data["action"],
                    )
                    session.add(permission)
                    logger.info(f"Created permission: {perm_data['name']}")
                else:
                    logger.info(f"Permission already exists: {perm_data['name']}")

            await session.commit()

        logger.info("✅ Default permissions created successfully")

    async def assign_role_permissions(self) -> None:
        """Assign permissions to roles"""
        logger.info("Assigning permissions to roles...")

        role_permissions = {
            "admin": [
                "users.read",
                "users.write",
                "users.delete",
                "products.read",
                "products.write",
                "products.delete",
                "inventory.read",
                "inventory.write",
                "analytics.read",
                "admin.full",
                "api.access",
            ],
            "user": ["products.read", "inventory.read", "analytics.read", "api.access"],
            "agent": [
                "products.read",
                "products.write",
                "inventory.read",
                "inventory.write",
                "analytics.read",
                "api.access",
            ],
            "viewer": ["products.read", "inventory.read", "analytics.read"],
        }

        async with self.async_session() as session:
            for role_name, permission_names in role_permissions.items():
                # Get role
                role_result = await session.execute(
                    text("SELECT id FROM roles WHERE name = :name"), {"name": role_name}
                )
                role_row = role_result.first()

                if not role_row:
                    logger.warning(f"Role not found: {role_name}")
                    continue

                role_id = role_row[0]

                for perm_name in permission_names:
                    # Get permission
                    perm_result = await session.execute(
                        text("SELECT id FROM permissions WHERE name = :name"),
                        {"name": perm_name},
                    )
                    perm_row = perm_result.first()

                    if not perm_row:
                        logger.warning(f"Permission not found: {perm_name}")
                        continue

                    perm_id = perm_row[0]

                    # Check if assignment already exists
                    existing = await session.execute(
                        text(
                            "SELECT 1 FROM role_permissions WHERE role_id = :role_id AND permission_id = :perm_id"
                        ),
                        {"role_id": role_id, "perm_id": perm_id},
                    )

                    if not existing.first():
                        # Create assignment
                        await session.execute(
                            text(
                                "INSERT INTO role_permissions (role_id, permission_id) VALUES (:role_id, :perm_id)"
                            ),
                            {"role_id": role_id, "perm_id": perm_id},
                        )
                        logger.info(f"Assigned {perm_name} to {role_name}")

            await session.commit()

        logger.info("✅ Role permissions assigned successfully")

    async def create_admin_user(self) -> None:
        """Create default admin user"""
        logger.info("Creating default admin user...")

        admin_email = "admin@flipsync.com"
        admin_username = "admin"
        admin_password = "FlipSync2024!"  # Change this in production!

        async with self.async_session() as session:
            # Check if admin user already exists
            existing_user = await session.execute(
                text(
                    "SELECT id FROM auth_users WHERE email = :email OR username = :username"
                ),
                {"email": admin_email, "username": admin_username},
            )

            if existing_user.first():
                logger.info("Admin user already exists")
                return

            # Create admin user
            admin_user = UnifiedUnifiedUser(
                email=admin_email,
                username=admin_username,
                password=admin_password,
                first_name="System",
                last_name="Administrator",
                is_active=True,
                is_verified=True,
                is_admin=True,
            )

            session.add(admin_user)
            await session.flush()  # Get the user ID

            # Assign admin role
            admin_role_result = await session.execute(
                text("SELECT id FROM roles WHERE name = 'admin'")
            )
            admin_role_row = admin_role_result.first()

            if admin_role_row:
                await session.execute(
                    text(
                        "INSERT INTO user_roles (user_id, role_id) VALUES (:user_id, :role_id)"
                    ),
                    {"user_id": admin_user.id, "role_id": admin_role_row[0]},
                )

            await session.commit()

            logger.info(f"✅ Admin user created: {admin_email}")
            logger.warning(f"⚠️  Default password: {admin_password}")
            logger.warning("🔒 CHANGE THE DEFAULT PASSWORD IMMEDIATELY!")

    async def initialize_database(self) -> None:
        """Run complete database initialization"""
        logger.info("🚀 Starting FlipSync authentication database initialization...")

        try:
            await self.create_tables()
            await self.create_default_roles()
            await self.create_default_permissions()
            await self.assign_role_permissions()
            await self.create_admin_user()

            logger.info("🎉 Database initialization completed successfully!")

        except Exception as e:
            logger.error(f"❌ Database initialization failed: {str(e)}")
            raise

        finally:
            await self.engine.dispose()

    async def verify_setup(self) -> None:
        """Verify database setup is working"""
        logger.info("🔍 Verifying database setup...")

        async with self.async_session() as session:
            # Count tables
            tables_result = await session.execute(
                text(
                    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name IN ('auth_users', 'roles', 'permissions', 'user_roles', 'user_permissions', 'role_permissions')"
                )
            )
            table_count = tables_result.scalar()

            # Count users
            users_result = await session.execute(
                text("SELECT COUNT(*) FROM auth_users")
            )
            user_count = users_result.scalar()

            # Count roles
            roles_result = await session.execute(text("SELECT COUNT(*) FROM roles"))
            role_count = roles_result.scalar()

            # Count permissions
            perms_result = await session.execute(
                text("SELECT COUNT(*) FROM permissions")
            )
            perm_count = perms_result.scalar()

            logger.info(f"📊 Database verification results:")
            logger.info(f"   Tables: {table_count}/6")
            logger.info(f"   UnifiedUsers: {user_count}")
            logger.info(f"   Roles: {role_count}")
            logger.info(f"   Permissions: {perm_count}")

            if (
                table_count == 6
                and user_count > 0
                and role_count > 0
                and perm_count > 0
            ):
                logger.info("✅ Database setup verification passed!")
            else:
                logger.error("❌ Database setup verification failed!")


async def main():
    """Main initialization function"""
    initializer = DatabaseInitializer()

    try:
        await initializer.initialize_database()
        await initializer.verify_setup()
    except Exception as e:
        logger.error(f"Initialization failed: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    # AGENT_CONTEXT: Standalone database initialization execution
    exit_code = asyncio.run(main())
    exit(exit_code)
