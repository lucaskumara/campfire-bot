import hikari
import pytest

from lib import tags
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch


class AsyncIterator:
    """A wrapper class to convert a synchronous iterable to an asynchronous one."""

    def __init__(self, iterable):
        self.iterable = iter(iterable)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self.iterable)
        except StopIteration:
            raise StopAsyncIteration


@pytest.fixture
def mock_tag_name() -> str:
    return "Sample Tag"


@pytest.fixture
def mock_tag_content() -> str:
    return "Sample Content"


@pytest.fixture
def mock_id() -> hikari.Snowflake:
    return hikari.Snowflake(123)


@pytest.fixture
def mock_date() -> datetime:
    return datetime(2023, 1, 1)


@pytest.fixture
def mock_document(
    mock_tag_name: str,
    mock_tag_content: str,
    mock_id: hikari.Snowflake,
    mock_date: datetime,
) -> dict:
    return {
        "name": mock_tag_name,
        "content": mock_tag_content,
        "guild_id": mock_id,
        "author_id": mock_id,
        "created_at": mock_date,
        "modified_at": mock_date,
        "uses": 0,
    }


def test_tag(
    mock_tag_name: str,
    mock_tag_content: str,
    mock_id: hikari.Snowflake,
    mock_date: datetime,
    mock_document: dict,
):
    result = tags.Tag(mock_document)

    assert result.name == mock_tag_name
    assert result.content == mock_tag_content
    assert result.guild_id == mock_id
    assert result.author_id == mock_id
    assert result.created_date == mock_date
    assert result.modified_date == mock_date
    assert result.uses == 0


@pytest.mark.asyncio
async def test_get_tag_with_valid_tag(
    mock_tag_name: str,
    mock_tag_content: str,
    mock_id: hikari.Snowflake,
    mock_date: datetime,
    mock_document: dict,
) -> None:
    mock_collection = MagicMock()
    mock_collection.find_one = AsyncMock()
    mock_collection.find_one.return_value = mock_document

    result = await tags.get_tag(mock_collection, mock_tag_name, mock_id)

    assert isinstance(result, tags.Tag)
    assert result.name == mock_tag_name
    assert result.content == mock_tag_content
    assert result.guild_id == mock_id
    assert result.author_id == mock_id
    assert result.created_date == mock_date
    assert result.modified_date == mock_date
    assert result.uses == 0


@pytest.mark.asyncio
async def test_get_tag_with_invalid_tag(
    mock_tag_name: str,
    mock_id: hikari.Snowflake,
) -> None:
    mock_collection = MagicMock()
    mock_collection.find_one = AsyncMock()
    mock_collection.find_one.return_value = None

    result = await tags.get_tag(mock_collection, mock_tag_name, mock_id)

    assert result is None


@pytest.mark.asyncio
async def test_get_tags_with_some_tags(
    mock_tag_name: str,
    mock_tag_content: str,
    mock_id: hikari.Snowflake,
    mock_date: datetime,
    mock_document: dict,
) -> None:
    mock_collection = MagicMock()
    mock_collection.find = MagicMock()
    mock_collection.find.return_value = AsyncIterator([mock_document, mock_document])

    result = await tags.get_tags(mock_collection, mock_id)

    assert result != []

    for tag in result:
        assert isinstance(tag, tags.Tag)
        assert tag.name == mock_tag_name
        assert tag.content == mock_tag_content
        assert tag.guild_id == mock_id
        assert tag.author_id == mock_id
        assert tag.created_date == mock_date
        assert tag.modified_date == mock_date
        assert tag.uses == 0


@pytest.mark.asyncio
async def test_get_tags_with_no_tags(mock_id: hikari.Snowflake) -> None:
    mock_collection = MagicMock()
    mock_collection.find = MagicMock()
    mock_collection.find.return_value = AsyncIterator([])

    result = await tags.get_tags(mock_collection, mock_id)

    assert result == []


@pytest.mark.asyncio
async def test_get_tags_by_author_with_some_tags(
    mock_tag_name: str,
    mock_tag_content: str,
    mock_id: hikari.Snowflake,
    mock_date: datetime,
    mock_document: dict,
) -> None:
    mock_collection = MagicMock()
    mock_collection.find = MagicMock()
    mock_collection.find.return_value = AsyncIterator([mock_document, mock_document])

    result = await tags.get_tags_by_author(mock_collection, mock_id, mock_id)

    assert result != []

    for tag in result:
        assert isinstance(tag, tags.Tag)
        assert tag.name == mock_tag_name
        assert tag.content == mock_tag_content
        assert tag.guild_id == mock_id
        assert tag.author_id == mock_id
        assert tag.created_date == mock_date
        assert tag.modified_date == mock_date
        assert tag.uses == 0


@pytest.mark.asyncio
async def test_get_tags_by_author_with_no_tags(mock_id: hikari.Snowflake) -> None:
    mock_collection = MagicMock()
    mock_collection.find = MagicMock()
    mock_collection.find.return_value = AsyncIterator([])

    result = await tags.get_tags_by_author(mock_collection, mock_id, mock_id)

    assert result == []


@patch("lib.tags.datetime", return_value=MagicMock())
@pytest.mark.asyncio
async def test_create_tag(
    mock_datetime: MagicMock,
    mock_tag_name: str,
    mock_tag_content: str,
    mock_id: hikari.Snowflake,
) -> None:
    mock_collection = MagicMock()
    mock_collection.insert_one = AsyncMock()

    await tags.create_tag(
        mock_collection, mock_tag_name, mock_tag_content, mock_id, mock_id
    )

    mock_collection.insert_one.assert_awaited_once_with(
        {
            "name": mock_tag_name,
            "content": mock_tag_content,
            "guild_id": str(mock_id),
            "author_id": str(mock_id),
            "created_at": mock_datetime.now.return_value,
            "modified_at": mock_datetime.now.return_value,
            "uses": 0,
        }
    )


@patch("lib.tags.datetime", return_value=MagicMock())
@pytest.mark.asyncio
async def test_edit_tag(
    mock_datetime: MagicMock,
    mock_tag_name: str,
    mock_tag_content: str,
    mock_id: hikari.Snowflake,
) -> None:
    mock_collection = MagicMock()
    mock_collection.update_one = AsyncMock()

    await tags.edit_tag(mock_collection, mock_tag_name, mock_tag_content, mock_id)

    mock_collection.update_one.assert_awaited_once_with(
        {"name": mock_tag_name, "guild_id": str(mock_id)},
        {
            "$set": {
                "content": mock_tag_content,
                "modified_at": mock_datetime.now.return_value,
            }
        },
    )


@pytest.mark.asyncio
async def test_delete_tag(mock_tag_name: str, mock_id: hikari.Snowflake) -> None:
    mock_collection = MagicMock()
    mock_collection.delete_one = AsyncMock()

    await tags.delete_tag(mock_collection, mock_tag_name, mock_id)

    mock_collection.delete_one.assert_awaited_once_with(
        {"name": mock_tag_name, "guild_id": str(mock_id)}
    )


@pytest.mark.asyncio
async def test_delete_all_tags(mock_id: hikari.Snowflake) -> None:
    mock_collection = MagicMock()
    mock_collection.delete_many = AsyncMock()

    await tags.delete_all_tags(mock_collection, mock_id)

    mock_collection.delete_many.assert_awaited_once_with({"guild_id": str(mock_id)})


@pytest.mark.asyncio
async def test_increment_tag(mock_tag_name: str, mock_id: hikari.Snowflake) -> None:
    mock_collection = MagicMock()
    mock_collection.update_one = AsyncMock()

    await tags.increment_tag(mock_collection, mock_tag_name, mock_id)

    mock_collection.update_one.assert_awaited_once_with(
        {"name": mock_tag_name, "guild_id": str(mock_id)}, {"$inc": {"uses": 1}}
    )
