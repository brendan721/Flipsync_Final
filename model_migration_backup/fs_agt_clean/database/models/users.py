"""SQLAlchemy models for users and accounts."""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Set

from sqlalchemy import Column, DateTime
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .enums import AccountStatus, AccountType, SyncStatus, UserRole


class User(Base):
    """Model representing a user."""

    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    status: Mapped[AccountStatus] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    api_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    quota_multiplier: Mapped[float] = mapped_column(Float, default=1.0)

    accounts: Mapped[list["UserAccount"]] = relationship(back_populates="user")
    dashboards: Mapped[list["DashboardModel"]] = relationship(back_populates="user")
    notifications = relationship("Notification", back_populates="user")


class Account(Base):
    """Model representing an account."""

    __tablename__ = "accounts"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    type: Mapped[AccountType] = mapped_column(String(50))
    status: Mapped[AccountStatus] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    users: Mapped[list["UserAccount"]] = relationship(back_populates="account")
    inventory_syncs: Mapped[list["InventorySync"]] = relationship(
        back_populates="account"
    )
    listing_syncs: Mapped[list["ListingSync"]] = relationship(back_populates="account")
    order_syncs: Mapped[list["OrderSync"]] = relationship(back_populates="account")
    performance_metrics: Mapped[list["PerformanceMetric"]] = relationship(
        back_populates="account"
    )


class UserAccount(Base):
    """Model representing user-account association with role."""

    __tablename__ = "user_accounts"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey("accounts.id"))
    role: Mapped[UserRole] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="accounts")
    account: Mapped["Account"] = relationship(back_populates="users")


class InventorySync(Base):
    """Model representing inventory sync operations."""

    __tablename__ = "inventory_syncs"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey("accounts.id"))
    status: Mapped[SyncStatus] = mapped_column(String(50))
    started_at: Mapped[datetime] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    account: Mapped["Account"] = relationship(back_populates="inventory_syncs")


class ListingSync(Base):
    """Model representing listing sync operations."""

    __tablename__ = "listing_syncs"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey("accounts.id"))
    status: Mapped[SyncStatus] = mapped_column(String(50))
    started_at: Mapped[datetime] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    account: Mapped["Account"] = relationship(back_populates="listing_syncs")


class OrderSync(Base):
    """Model representing order sync operations."""

    __tablename__ = "order_syncs"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey("accounts.id"))
    status: Mapped[SyncStatus] = mapped_column(String(50))
    started_at: Mapped[datetime] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    account: Mapped["Account"] = relationship(back_populates="order_syncs")


class PerformanceMetric(Base):
    """Model representing performance metrics."""

    __tablename__ = "performance_metrics"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey("accounts.id"))
    metric_type: Mapped[str] = mapped_column(String(50))
    value: Mapped[float] = mapped_column(Float)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    account: Mapped["Account"] = relationship(back_populates="performance_metrics")


class MarketUserAccount(Base):
    __tablename__ = "market_user_accounts"
    __table_args__ = {"extend_existing": True}

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    role = Column(SQLAlchemyEnum(UserRole), nullable=False)
    status = Column(SQLAlchemyEnum(AccountStatus), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    last_login = Column(DateTime)
    permissions = Column(String)  # JSON serialized
    api_key = Column(String)
    quota_multiplier = Column(Float, default=1.0)

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
