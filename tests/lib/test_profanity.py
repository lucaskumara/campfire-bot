import hikari
import pytest

from lib import profanity
from unittest.mock import MagicMock, AsyncMock


@pytest.fixture
def mock_id() -> hikari.Snowflake:
    return hikari.Snowflake(123)


@pytest.mark.asyncio
async def test_is_filter_enabled_with_filter_explicitly_enabled(
    mock_id: hikari.Snowflake,
) -> None:
    mock_collection = MagicMock()
    mock_collection.find_one = AsyncMock()
    mock_collection.find_one.return_value = {
        "guild_id": mock_id,
        "profanity_filter": True,
    }

    result = await profanity.is_filter_enabled(mock_collection, mock_id)

    assert result


@pytest.mark.asyncio
async def test_is_filter_enabled_with_filter_explicitly_disabled(
    mock_id: hikari.Snowflake,
) -> None:
    mock_collection = MagicMock()
    mock_collection.find_one = AsyncMock()
    mock_collection.find_one.return_value = {
        "guild_id": mock_id,
        "profanity_filter": False,
    }

    result = await profanity.is_filter_enabled(mock_collection, mock_id)

    assert not result


@pytest.mark.asyncio
async def test_is_filter_enabled_with_filter_implicitly_disabled_with_document(
    mock_id: hikari.Snowflake,
) -> None:
    mock_collection = MagicMock()
    mock_collection.find_one = AsyncMock()
    mock_collection.find_one.return_value = {"guild_id": mock_id}

    result = await profanity.is_filter_enabled(mock_collection, mock_id)

    assert not result


@pytest.mark.asyncio
async def test_is_filter_enabled_with_filter_implicitly_disabled_without_document() -> None:
    mock_collection = MagicMock()
    mock_collection.find_one = AsyncMock()
    mock_collection.find_one.return_value = None

    result = await profanity.is_filter_enabled(mock_collection, mock_id)

    assert not result


@pytest.mark.asyncio
async def test_enable_filter(mock_id: hikari.Snowflake) -> None:
    mock_collection = MagicMock()
    mock_collection.update_one = AsyncMock()

    await profanity.enable_filter(mock_collection, mock_id)

    mock_collection.update_one.assert_awaited_once_with(
        {"guild_id": str(mock_id)}, {"$set": {"profanity_filter": True}}, upsert=True
    )


@pytest.mark.asyncio
async def test_disable_filter(mock_id: hikari.Snowflake) -> None:
    mock_collection = MagicMock()
    mock_collection.update_one = AsyncMock()

    await profanity.disable_filter(mock_collection, mock_id)

    mock_collection.update_one.assert_awaited_once_with(
        {"guild_id": str(mock_id)}, {"$set": {"profanity_filter": False}}, upsert=True
    )
