"""Tests for the ListingUnifiedAgent."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from fs_agt_clean.agents.market.specialized.listing_agent import ListingUnifiedAgent
from fs_agt_clean.core.config.config_manager import ConfigManager
from fs_agt_clean.core.monitoring.alerts.manager import AlertManager
from fs_agt_clean.mobile.battery_optimizer import BatteryOptimizer


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    return {
        "api_key": "test_key",
        "marketplace_id": "ebay",
        "rate_limit": 100,
        "timeout": 30,
        "ebay_app_id": "test_app_id",
        "ebay_dev_id": "test_dev_id",
        "ebay_cert_id": "test_cert_id",
        "ebay_token": "test_token",
        "ai_service_url": "http://test-ai-service",
        "paypal_email": "test@example.com",
        "default_policies": {},
        "image_validation_enabled": True,
    }


@pytest.fixture
def mock_config_manager():
    """Mock ConfigManager for testing."""
    manager = MagicMock(spec=ConfigManager)
    return manager


@pytest.fixture
def mock_alert_manager():
    """Mock AlertManager for testing."""
    manager = AsyncMock(spec=AlertManager)
    return manager


@pytest.fixture
def mock_battery_optimizer():
    """Mock BatteryOptimizer for testing."""
    optimizer = MagicMock(spec=BatteryOptimizer)
    return optimizer


@pytest.fixture
def listing_agent(
    mock_config, mock_config_manager, mock_alert_manager, mock_battery_optimizer
):
    """Create ListingUnifiedAgent instance for testing."""
    return ListingUnifiedAgent(
        marketplace="ebay",
        config_manager=mock_config_manager,
        alert_manager=mock_alert_manager,
        battery_optimizer=mock_battery_optimizer,
        config=mock_config,
    )


@pytest.fixture
def sample_product_data():
    """Sample product data for testing."""
    return {
        "title": "Test Product",
        "description": "Test product description",
        "price": 25.99,
        "sku": "TEST-SKU-001",
        "images": ["https://example.com/image1.jpg", "https://example.com/image2.jpg"],
        "condition": "new",
        "category": "electronics",
    }


@pytest.fixture
def sample_market_data():
    """Sample market data for testing."""
    return {
        "average_price": 24.50,
        "competition_level": "medium",
        "trending_keywords": ["test", "product", "electronics"],
        "seasonal_factor": 1.1,
    }


@pytest.fixture
def sample_listing_data():
    """Sample listing data for testing."""
    return {
        "title": "Optimized Test Product - High Quality Electronics",
        "description": "Detailed optimized description...",
        "item_specifics": {"Brand": "TestBrand", "Condition": "New"},
        "category_id": "12345",
        "price": 26.99,
        "images": ["https://example.com/image1.jpg"],
        "sku": "TEST-SKU-001",
        "condition_id": "1000",
        "listing_duration": "GTC",
        "quantity": 1,
        "payment_policy_id": "payment_123",
        "return_policy_id": "return_123",
        "shipping_policy_id": "shipping_123",
    }


class TestListingUnifiedAgent:
    """Test cases for ListingUnifiedAgent."""

    @pytest.mark.asyncio
    async def test_initialization(self, listing_agent):
        """Test agent initialization."""
        assert listing_agent.marketplace == "ebay"
        assert listing_agent.agent_id is not None
        assert listing_agent.request_semaphore._value == 2
        assert listing_agent.max_retries == 3
        assert listing_agent.retry_delay == 1

    @pytest.mark.asyncio
    async def test_required_config_fields(self, listing_agent):
        """Test required configuration fields."""
        required_fields = listing_agent._get_required_config_fields()
        expected_fields = [
            "api_key",
            "marketplace_id",
            "rate_limit",
            "timeout",
            "ebay_app_id",
            "ebay_dev_id",
            "ebay_cert_id",
            "ebay_token",
            "ai_service_url",
            "paypal_email",
            "default_policies",
            "image_validation_enabled",
        ]

        for field in expected_fields:
            assert field in required_fields

    @pytest.mark.asyncio
    async def test_create_optimized_listing_success(
        self, listing_agent, sample_product_data, sample_market_data
    ):
        """Test successful optimized listing creation."""
        with patch.object(listing_agent, "_optimize_title") as mock_title:
            with patch.object(listing_agent, "_generate_description") as mock_desc:
                with patch.object(
                    listing_agent, "_generate_item_specifics"
                ) as mock_specs:
                    with patch.object(
                        listing_agent, "_get_category_id"
                    ) as mock_category:
                        with patch.object(
                            listing_agent, "_optimize_pricing"
                        ) as mock_pricing:
                            with patch.object(
                                listing_agent, "_process_images"
                            ) as mock_images:
                                with patch.object(
                                    listing_agent, "_determine_condition"
                                ) as mock_condition:
                                    with patch.object(
                                        listing_agent, "_get_payment_policy"
                                    ) as mock_payment:
                                        with patch.object(
                                            listing_agent, "_get_return_policy"
                                        ) as mock_return:
                                            with patch.object(
                                                listing_agent, "_get_shipping_policy"
                                            ) as mock_shipping:
                                                with patch.object(
                                                    listing_agent, "_validate_listing"
                                                ) as mock_validate:
                                                    # Setup mocks
                                                    mock_title.return_value = (
                                                        "Optimized Title"
                                                    )
                                                    mock_desc.return_value = (
                                                        "Optimized Description"
                                                    )
                                                    mock_specs.return_value = {
                                                        "Brand": "TestBrand"
                                                    }
                                                    mock_category.return_value = "12345"
                                                    mock_pricing.return_value = {
                                                        "recommended_price": 26.99
                                                    }
                                                    mock_images.return_value = [
                                                        "https://example.com/image1.jpg"
                                                    ]
                                                    mock_condition.return_value = "1000"
                                                    mock_payment.return_value = (
                                                        "payment_123"
                                                    )
                                                    mock_return.return_value = (
                                                        "return_123"
                                                    )
                                                    mock_shipping.return_value = (
                                                        "shipping_123"
                                                    )
                                                    mock_validate.return_value = True

                                                    result = await listing_agent.create_optimized_listing(
                                                        sample_product_data,
                                                        sample_market_data,
                                                    )

                                                    assert result is not None
                                                    assert (
                                                        result["title"]
                                                        == "Optimized Title"
                                                    )
                                                    assert result["price"] == 26.99
                                                    assert (
                                                        result["category_id"] == "12345"
                                                    )

    @pytest.mark.asyncio
    async def test_create_optimized_listing_validation_failure(
        self, listing_agent, sample_product_data, sample_market_data
    ):
        """Test listing creation with validation failure."""
        with patch.object(listing_agent, "_optimize_title") as mock_title:
            with patch.object(listing_agent, "_generate_description") as mock_desc:
                with patch.object(
                    listing_agent, "_generate_item_specifics"
                ) as mock_specs:
                    with patch.object(
                        listing_agent, "_get_category_id"
                    ) as mock_category:
                        with patch.object(
                            listing_agent, "_optimize_pricing"
                        ) as mock_pricing:
                            with patch.object(
                                listing_agent, "_process_images"
                            ) as mock_images:
                                with patch.object(
                                    listing_agent, "_determine_condition"
                                ) as mock_condition:
                                    with patch.object(
                                        listing_agent, "_get_payment_policy"
                                    ) as mock_payment:
                                        with patch.object(
                                            listing_agent, "_get_return_policy"
                                        ) as mock_return:
                                            with patch.object(
                                                listing_agent, "_get_shipping_policy"
                                            ) as mock_shipping:
                                                with patch.object(
                                                    listing_agent, "_validate_listing"
                                                ) as mock_validate:
                                                    # Setup mocks
                                                    mock_title.return_value = "Title"
                                                    mock_desc.return_value = (
                                                        "Description"
                                                    )
                                                    mock_specs.return_value = {}
                                                    mock_category.return_value = "12345"
                                                    mock_pricing.return_value = {
                                                        "recommended_price": 26.99
                                                    }
                                                    mock_images.return_value = []
                                                    mock_condition.return_value = "1000"
                                                    mock_payment.return_value = (
                                                        "payment_123"
                                                    )
                                                    mock_return.return_value = (
                                                        "return_123"
                                                    )
                                                    mock_shipping.return_value = (
                                                        "shipping_123"
                                                    )
                                                    mock_validate.return_value = (
                                                        False  # Validation fails
                                                    )

                                                    result = await listing_agent.create_optimized_listing(
                                                        sample_product_data,
                                                        sample_market_data,
                                                    )

                                                    assert result is None

    @pytest.mark.asyncio
    async def test_publish_listing_success(self, listing_agent, sample_listing_data):
        """Test successful listing publication."""
        with patch.object(listing_agent, "_execute_with_retry") as mock_retry:
            mock_retry.return_value = {
                "Ack": "Success",
                "ItemID": "item_123456789",
                "Warnings": [],
            }

            result = await listing_agent.publish_listing(sample_listing_data)

            assert result["success"] is True
            assert result["listing_id"] == "item_123456789"
            assert result["warnings"] == []

    @pytest.mark.asyncio
    async def test_publish_listing_with_warnings(
        self, listing_agent, sample_listing_data
    ):
        """Test listing publication with warnings."""
        with patch.object(listing_agent, "_execute_with_retry") as mock_retry:
            mock_retry.return_value = {
                "Ack": "Warning",
                "ItemID": "item_123456789",
                "Warnings": ["Image quality could be improved"],
            }

            result = await listing_agent.publish_listing(sample_listing_data)

            assert result["success"] is True
            assert result["listing_id"] == "item_123456789"
            assert len(result["warnings"]) == 1

    @pytest.mark.asyncio
    async def test_publish_listing_failure(self, listing_agent, sample_listing_data):
        """Test listing publication failure."""
        with patch.object(listing_agent, "_execute_with_retry") as mock_retry:
            mock_retry.return_value = {
                "Ack": "Failure",
                "Errors": ["Invalid category ID"],
            }

            result = await listing_agent.publish_listing(sample_listing_data)

            assert result["success"] is False
            assert "error" in result

    @pytest.mark.asyncio
    async def test_process_images_valid(self, listing_agent):
        """Test processing valid images."""
        images = [
            "https://example.com/image1.jpg",
            "https://example.com/image2.jpg",
            "https://example.com/image3.jpg",
        ]

        with patch.object(listing_agent, "_validate_image") as mock_validate:
            mock_validate.return_value = True

            result = await listing_agent._process_images(images)

            assert len(result) == 3
            assert all(img in result for img in images)

    @pytest.mark.asyncio
    async def test_process_images_some_invalid(self, listing_agent):
        """Test processing images with some invalid ones."""
        images = [
            "https://example.com/image1.jpg",
            "invalid_url",
            "https://example.com/image3.jpg",
        ]

        with patch.object(listing_agent, "_validate_image") as mock_validate:

            def validate_side_effect(url):
                return url.startswith("https://")

            mock_validate.side_effect = validate_side_effect

            result = await listing_agent._process_images(images)

            assert len(result) == 2
            assert "https://example.com/image1.jpg" in result
            assert "https://example.com/image3.jpg" in result
            assert "invalid_url" not in result

    @pytest.mark.asyncio
    async def test_process_images_limit(self, listing_agent):
        """Test image processing respects eBay's 12 image limit."""
        images = [f"https://example.com/image{i}.jpg" for i in range(15)]

        with patch.object(listing_agent, "_validate_image") as mock_validate:
            mock_validate.return_value = True

            result = await listing_agent._process_images(images)

            assert len(result) == 12  # eBay limit

    @pytest.mark.asyncio
    async def test_validate_listing_success(self, listing_agent, sample_listing_data):
        """Test successful listing validation."""
        result = await listing_agent._validate_listing(sample_listing_data)
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_listing_missing_field(
        self, listing_agent, sample_listing_data
    ):
        """Test listing validation with missing required field."""
        del sample_listing_data["title"]

        result = await listing_agent._validate_listing(sample_listing_data)
        assert result is False

    @pytest.mark.asyncio
    async def test_validate_listing_title_too_long(
        self, listing_agent, sample_listing_data
    ):
        """Test listing validation with title too long."""
        sample_listing_data["title"] = "x" * 100  # Exceeds 80 character limit

        result = await listing_agent._validate_listing(sample_listing_data)
        assert result is False

    @pytest.mark.asyncio
    async def test_validate_listing_no_images(self, listing_agent, sample_listing_data):
        """Test listing validation with no images."""
        sample_listing_data["images"] = []

        result = await listing_agent._validate_listing(sample_listing_data)
        assert result is False

    @pytest.mark.asyncio
    async def test_execute_with_retry_success(self, listing_agent):
        """Test retry mechanism with successful operation."""
        operation = MagicMock(return_value="success")

        result = await listing_agent._execute_with_retry(operation)

        assert result == "success"
        assert operation.call_count == 1

    @pytest.mark.asyncio
    async def test_execute_with_retry_eventual_success(self, listing_agent):
        """Test retry mechanism with eventual success."""
        operation = MagicMock(
            side_effect=[Exception("fail"), Exception("fail"), "success"]
        )

        with patch("asyncio.sleep"):  # Mock sleep to speed up test
            result = await listing_agent._execute_with_retry(operation)

        assert result == "success"
        assert operation.call_count == 3

    @pytest.mark.asyncio
    async def test_execute_with_retry_max_retries(self, listing_agent):
        """Test retry mechanism reaching max retries."""
        operation = MagicMock(side_effect=Exception("persistent failure"))

        with patch("asyncio.sleep"):  # Mock sleep to speed up test
            with pytest.raises(Exception, match="persistent failure"):
                await listing_agent._execute_with_retry(operation)

        assert operation.call_count == 3  # max_retries

    @pytest.mark.asyncio
    async def test_prepare_listing_payload(self, listing_agent, sample_listing_data):
        """Test eBay API payload preparation."""
        payload = listing_agent._prepare_listing_payload(sample_listing_data)

        assert "Item" in payload
        item = payload["Item"]
        assert item["Title"] == sample_listing_data["title"]
        assert item["StartPrice"] == str(sample_listing_data["price"])
        assert (
            item["PrimaryCategory"]["CategoryID"] == sample_listing_data["category_id"]
        )
        assert item["ListingType"] == "FixedPriceItem"

    @pytest.mark.asyncio
    async def test_validate_image_valid_url(self, listing_agent):
        """Test image validation with valid URL."""
        result = await listing_agent._validate_image("https://example.com/image.jpg")
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_image_invalid_url(self, listing_agent):
        """Test image validation with invalid URL."""
        result = await listing_agent._validate_image("not_a_url")
        assert result is False

        result = await listing_agent._validate_image("")
        assert result is False

    @pytest.mark.asyncio
    async def test_mock_methods(
        self, listing_agent, sample_product_data, sample_market_data
    ):
        """Test mock implementation methods."""
        # Test title optimization
        title = await listing_agent._optimize_title(
            sample_product_data, sample_market_data
        )
        assert "Optimized" in title

        # Test description generation
        description = await listing_agent._generate_description(
            sample_product_data, sample_market_data
        )
        assert "Optimized description" in description

        # Test item specifics generation
        specifics = await listing_agent._generate_item_specifics(
            sample_product_data, sample_market_data
        )
        assert isinstance(specifics, dict)
        assert "Brand" in specifics

        # Test category ID determination
        category_id = await listing_agent._get_category_id(sample_product_data)
        assert category_id == "12345"

        # Test pricing optimization
        pricing = await listing_agent._optimize_pricing(
            sample_product_data, sample_market_data
        )
        assert "recommended_price" in pricing
        assert pricing["recommended_price"] > sample_product_data["price"]

    @pytest.mark.asyncio
    async def test_get_shipping_details(self, listing_agent):
        """Test shipping details configuration."""
        shipping_details = listing_agent._get_shipping_details()

        assert shipping_details["ShippingType"] == "Flat"
        assert "ShippingServiceOptions" in shipping_details
        assert (
            shipping_details["ShippingServiceOptions"]["ShippingService"] == "USPSMedia"
        )
