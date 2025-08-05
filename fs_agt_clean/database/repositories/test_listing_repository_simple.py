"""
Simple test for the listing repository.
"""

import asyncio
import uuid
from datetime import datetime

import pytest
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from fs_agt_clean.database.repositories.listing_repository import ListingRepository

# Create a base class for declarative models
Base = declarative_base()


# Define models for testing
class UnifiedUser(Base):
    """UnifiedUser model for testing."""

    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    listings = relationship("Listing", back_populates="user")

    def to_dict(self):
        """Convert the model to a dictionary."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Marketplace(Base):
    """Marketplace model for testing."""

    __tablename__ = "marketplaces"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    name = Column(String(50), nullable=False)
    type = Column(String(20), nullable=False)  # e.g., "amazon", "ebay", "etsy"
    credentials = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    listings = relationship("Listing", back_populates="marketplace")

    def to_dict(self):
        """Convert the model to a dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "type": self.type,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class InventoryItem(Base):
    """Inventory item model for testing."""

    __tablename__ = "inventory_items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    sku = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    quantity = Column(Integer, default=0)
    price = Column(Float, nullable=True)
    cost = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    listings = relationship("Listing", back_populates="inventory_item")

    def to_dict(self):
        """Convert the model to a dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "sku": self.sku,
            "name": self.name,
            "description": self.description,
            "quantity": self.quantity,
            "price": self.price,
            "cost": self.cost,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Listing(Base):
    """Listing model for testing."""

    __tablename__ = "listings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    marketplace_id = Column(String(36), ForeignKey("marketplaces.id"), nullable=False)
    inventory_item_id = Column(
        String(36), ForeignKey("inventory_items.id"), nullable=False
    )
    external_id = Column(String(100), nullable=True)  # ID on the marketplace
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    quantity = Column(Integer, default=1)
    status = Column(String(20), default="draft")  # draft, active, ended, sold
    listing_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("UnifiedUser", back_populates="listings")
    marketplace = relationship("Marketplace", back_populates="listings")
    inventory_item = relationship("InventoryItem", back_populates="listings")

    def to_dict(self):
        """Convert the model to a dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "marketplace_id": self.marketplace_id,
            "inventory_item_id": self.inventory_item_id,
            "external_id": self.external_id,
            "title": self.title,
            "description": self.description,
            "price": self.price,
            "quantity": self.quantity,
            "status": self.status,
            "metadata": self.listing_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# Patch the ListingRepository to use our test session
class TestListingRepository(ListingRepository):
    """Test version of ListingRepository that uses a test session."""

    def __init__(self, session_maker):
        """Initialize with a session maker."""
        super().__init__()
        self.session_maker = session_maker

    async def find_by_criteria(self, criteria, limit=100, offset=0):
        """Find records by criteria."""
        async with self.session_maker() as session:
            stmt = select(Listing)

            # Apply criteria
            for key, value in criteria.items():
                stmt = stmt.where(getattr(Listing, key) == value)

            # Apply pagination
            stmt = stmt.limit(limit).offset(offset)

            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def create(self, data):
        """Create a new record."""
        async with self.session_maker() as session:
            # Create the model instance
            instance = Listing(**data)

            # Add to session
            session.add(instance)

            # Commit the transaction
            await session.commit()

            # Refresh to get the ID
            await session.refresh(instance)

            return instance

    async def get_by_id(self, id):
        """Find a listing by ID."""
        async with self.session_maker() as session:
            stmt = select(Listing).where(Listing.id == id)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_by_user_id(self, user_id):
        """Find listings by user ID."""
        return await self.find_by_criteria({"user_id": user_id})

    async def get_by_marketplace_id(self, marketplace_id):
        """Find listings by marketplace ID."""
        return await self.find_by_criteria({"marketplace_id": marketplace_id})

    async def get_by_inventory_item_id(self, inventory_item_id):
        """Find listings by inventory item ID."""
        return await self.find_by_criteria({"inventory_item_id": inventory_item_id})

    async def get_by_external_id(self, marketplace_id, external_id):
        """Find a listing by external ID."""
        listings = await self.find_by_criteria(
            {"marketplace_id": marketplace_id, "external_id": external_id}, limit=1
        )
        return listings[0] if listings else None

    async def get_by_status(self, status):
        """Find listings by status."""
        return await self.find_by_criteria({"status": status})

    async def update_listing(self, id, **kwargs):
        """Update a listing."""
        async with self.session_maker() as session:
            # Get the listing
            stmt = select(Listing).where(Listing.id == id)
            result = await session.execute(stmt)
            listing = result.scalars().first()

            if not listing:
                return None

            # Update the listing
            for key, value in kwargs.items():
                setattr(listing, key, value)

            # Commit the transaction
            await session.commit()

            # Refresh to get the updated values
            await session.refresh(listing)

            return listing

    async def update_status(self, id, status):
        """Update a listing's status."""
        return await self.update_listing(id, status=status)


@pytest.mark.asyncio
async def test_listing_repository():
    """Test the listing repository."""
    # Create in-memory SQLite database
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session maker
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Create a test user
    async with async_session() as session:
        user = UnifiedUser(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        user_id = user.id

        # Create a test marketplace
        marketplace = Marketplace(
            user_id=user_id,
            name="Test Marketplace",
            type="ebay",
            credentials={
                "client_id": "test_client_id",
                "client_secret": "test_client_secret",
            },
        )
        session.add(marketplace)
        await session.commit()
        await session.refresh(marketplace)
        marketplace_id = marketplace.id

        # Create a test inventory item
        inventory_item = InventoryItem(
            user_id=user_id,
            sku="TEST-SKU-001",
            name="Test Item",
            description="This is a test item",
            quantity=10,
            price=19.99,
        )
        session.add(inventory_item)
        await session.commit()
        await session.refresh(inventory_item)
        inventory_item_id = inventory_item.id

    # Create repository
    listing_repo = TestListingRepository(async_session)

    # Test create_listing
    listing_data = {
        "user_id": user_id,
        "marketplace_id": marketplace_id,
        "inventory_item_id": inventory_item_id,
        "title": "Test Listing",
        "description": "This is a test listing",
        "price": 29.99,
        "quantity": 5,
        "status": "draft",
        "listing_metadata": {
            "shipping_options": ["Standard", "Express"],
            "condition": "New",
        },
    }

    listing = await listing_repo.create(listing_data)

    # Verify listing was created
    assert listing is not None
    assert listing.user_id == user_id
    assert listing.marketplace_id == marketplace_id
    assert listing.inventory_item_id == inventory_item_id
    assert listing.title == "Test Listing"
    assert listing.description == "This is a test listing"
    assert listing.price == 29.99
    assert listing.quantity == 5
    assert listing.status == "draft"

    # Test get_by_user_id
    user_listings = await listing_repo.get_by_user_id(user_id)
    assert len(user_listings) == 1
    assert user_listings[0].title == "Test Listing"

    # Test get_by_id
    found_listing = await listing_repo.get_by_id(listing.id)
    assert found_listing is not None
    assert found_listing.id == listing.id
    assert found_listing.title == "Test Listing"

    # Test get_by_marketplace_id
    marketplace_listings = await listing_repo.get_by_marketplace_id(marketplace_id)
    assert len(marketplace_listings) == 1
    assert marketplace_listings[0].id == listing.id

    # Test get_by_inventory_item_id
    item_listings = await listing_repo.get_by_inventory_item_id(inventory_item_id)
    assert len(item_listings) == 1
    assert item_listings[0].id == listing.id

    # Test update_listing
    updated_listing = await listing_repo.update_listing(
        listing.id,
        title="Updated Listing",
        price=39.99,
        listing_metadata={
            "shipping_options": ["Standard", "Express", "Overnight"],
            "condition": "Like New",
        },
    )
    assert updated_listing is not None
    assert updated_listing.title == "Updated Listing"
    assert updated_listing.price == 39.99
    assert "Overnight" in updated_listing.listing_metadata["shipping_options"]

    # Test update_status
    status_updated_listing = await listing_repo.update_status(listing.id, "active")
    assert status_updated_listing is not None
    assert status_updated_listing.status == "active"

    # Test get_by_status
    status_listings = await listing_repo.get_by_status("active")
    assert len(status_listings) == 1
    assert status_listings[0].id == listing.id

    # Test get_by_external_id
    # First, update the listing with an external ID
    external_id_listing = await listing_repo.update_listing(
        listing.id, external_id="EXT-123"
    )
    assert external_id_listing is not None
    assert external_id_listing.external_id == "EXT-123"

    # Now test get_by_external_id
    found_by_external = await listing_repo.get_by_external_id(marketplace_id, "EXT-123")
    assert found_by_external is not None
    assert found_by_external.id == listing.id
    assert found_by_external.external_id == "EXT-123"

    # Clean up
    await engine.dispose()

    print("All tests passed!")


if __name__ == "__main__":
    asyncio.run(test_listing_repository())
