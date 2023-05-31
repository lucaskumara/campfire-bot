import hikari
import os
import pytest

import motor.motor_asyncio as motor

from lib import channels
from unittest.mock import AsyncMock, MagicMock, patch


MONGO_TEST_CLIENT = motor.AsyncIOMotorClient(os.getenv("DATABASE_URI"))
MONGO_TEST_DATABASE = MONGO_TEST_CLIENT["campfire-test"]


@pytest.fixture
def mongo_client():
    """The mongo client."""
    return motor.AsyncIOMotorClient(os.getenv("DATABASE_URI"))


@pytest.fixture
def mongo_database(mongo_client):
    """The mongo database."""
    return mongo_client["campfire-test"]


@pytest.fixture
def mongo_collection(mongo_database):
    """The mongo collection."""
    return mongo_database["channels"]


@pytest.fixture
def test_id():
    """A sample ID to reuse."""
    return hikari.Snowflake(123)


@patch("lib.channels.register_template", return_value=None)
@pytest.mark.asyncio
async def test_create_template(
    mock_register_template: AsyncMock, test_id: hikari.Snowflake
) -> None:
    """Test the create_template function.

    Arguments:
        mock_register_template: The mocked register_template function.
        test_id: The test_id fixture.

    Returns:
        None.
    """
    mock_channel = MagicMock()
    mock_channel.id = test_id

    mock_guild = AsyncMock()
    mock_guild.create_voice_channel.return_value = mock_channel

    result = await channels.create_template(mongo_collection, mock_guild, "Name")

    assert type(result) == channels.TemplateChannel
    assert result.get_channel().id == test_id


@patch("lib.channels.register_clone", return_value=None)
@pytest.mark.asyncio
async def test_create_clone(
    mock_register_clone: AsyncMock, test_id: hikari.Snowflake
) -> None:
    """Test the create_clone function.

    Arguments:
        mock_register_clone: The mocked register_clone function.
        test_id: The test_id fixture.

    Returns:
        None.
    """
    mock_clone = MagicMock()
    mock_clone.id = test_id

    mock_guild = AsyncMock()
    mock_guild.create_voice_channel.return_value = mock_clone

    mock_template = MagicMock()
    mock_template.get_guild.return_value = mock_guild

    result = await channels.create_clone(
        MagicMock(), mock_template, MagicMock(), "Name"
    )

    assert type(result) == channels.CloneChannel
    assert result.get_channel().id == test_id


@patch("lib.channels.template_exists", return_value=True)
@pytest.mark.asyncio
async def test_get_template_template_exists(
    mock_template_exists: AsyncMock, test_id: hikari.Snowflake
) -> None:
    """Test the template_exists function.

    template_exists function is patched to return True.

    Arguments:
        mock_template_exists: The mocked template_exists function.
        test_id: The test_id fixture.

    Returns:
        None.
    """
    mock_channel = MagicMock()
    mock_channel.id = test_id

    result = await channels.get_template(MagicMock(), mock_channel)

    assert type(result) == channels.TemplateChannel
    assert result.get_channel().id == test_id


@patch("lib.channels.template_exists", return_value=False)
@pytest.mark.asyncio
async def test_get_template_template_doesnt_exist(
    mock_template_exists: AsyncMock,
) -> None:
    """Test the template_exists function.

    template_exists function is patched to return False.

    Arguments:
        mock_template_exists: The mocked template_exists function.

    Returns:
        None.
    """
    result = await channels.get_template(MagicMock(), MagicMock())

    assert result is None


@patch("lib.channels.clone_exists", return_value=True)
@pytest.mark.asyncio
async def test_get_clone_clone_exists(
    mock_clone_exists: AsyncMock, test_id: hikari.Snowflake
) -> None:
    """Test the clone_exists function.

    clone_exists function is patched to return True.

    Arguments:
        mock_clone_exists: The mocked clone_exists function.
        test_id: The test_id fixture.

    Returns:
        None.
    """
    mock_channel = MagicMock()
    mock_channel.id = test_id

    result = await channels.get_clone(MagicMock(), mock_channel)

    assert type(result) == channels.CloneChannel
    assert result.get_channel().id == test_id


@patch("lib.channels.clone_exists", return_value=False)
@pytest.mark.asyncio
async def test_get_clone_clone_doesnt_exist(mock_clone_exists: AsyncMock) -> None:
    """Test the clone_exists function.

    clone_exists function is patched to return False.

    Arguments:
        mock_clone_exists: The mocked clone_exists function.

    Returns:
        None.
    """
    result = await channels.get_clone(MagicMock(), MagicMock())

    assert result is None


@patch("lib.channels.deregister_template", return_value=None)
@pytest.mark.asyncio
async def test_delete_template(mock_deregister_template: AsyncMock) -> None:
    """Test the delete_template function.

    Arguments:
        mock_deregister_template: The mocked deregister_template function.

    Returns:
        None.
    """
    mock_channel = MagicMock()
    mock_channel.delete = AsyncMock()

    await channels.delete_template(MagicMock(), mock_channel)

    mock_channel.delete.assert_called_once()
    mock_deregister_template.assert_called_once()


@patch("lib.channels.deregister_clone", return_value=None)
@pytest.mark.asyncio
async def test_delete_clone(mock_deregister_clone: AsyncMock) -> None:
    """Test the delete_clone function.

    Arguments:
        mock_deregister_clone: The mocked deregister_clone function.

    Returns:
        None.
    """
    mock_channel = MagicMock()
    mock_channel.delete = AsyncMock()

    await channels.delete_clone(MagicMock(), mock_channel)

    mock_channel.delete.assert_called_once()
    mock_deregister_clone.assert_called_once()


def test_joined_a_channel(test_id: hikari.Snowflake) -> None:
    """Test the joined_a_channel function.

    Arguments:
        test_id: The test_id fixture.

    Returns:
        None.
    """
    voice_state1 = MagicMock()
    voice_state1.channel_id = test_id

    voice_state2 = MagicMock()
    voice_state2.channel_id = None

    assert channels.joined_a_channel(voice_state1) == True
    assert channels.joined_a_channel(voice_state2) == False


def test_left_a_channel(test_id: hikari.Snowflake) -> None:
    """Test the left_a_channel function.

    Arguments:
        test_id: The test_id fixture.

    Returns:
        None.
    """
    voice_state1 = MagicMock()
    voice_state1.channel_id = test_id

    voice_state2 = MagicMock()
    voice_state2.channel_id = None

    voice_state3 = None

    assert channels.left_a_channel(voice_state1) == True
    assert channels.left_a_channel(voice_state2) == False
    assert channels.left_a_channel(voice_state3) == False


@pytest.mark.asyncio
async def test_register_template(
    mongo_collection: motor.AsyncIOMotorCollection, test_id: hikari.Snowflake
) -> None:
    """Test the register_template function.

    Arguments:
        mongo_collection: The mongo_collection fixture.
        test_id: The test_id fixture.

    Returns:
        None.
    """
    await channels.register_template(mongo_collection, test_id, test_id)

    document = await mongo_collection.find_one(
        {"guild_id": str(test_id), "channel_id": str(test_id), "type": "template"}
    )

    assert document is not None

    await mongo_collection.delete_many({})


@pytest.mark.asyncio
async def test_register_clone(
    mongo_collection: motor.AsyncIOMotorCollection, test_id: hikari.Snowflake
) -> None:
    """Test the register_clone function.

    Arguments:
        mongo_collection: The mongo_collection fixture.
        test_id: The test_id fixture.

    Returns:
        None.
    """
    await channels.register_clone(mongo_collection, test_id, test_id, test_id, test_id)

    document = await mongo_collection.find_one(
        {
            "guild_id": str(test_id),
            "template_id": str(test_id),
            "channel_id": str(test_id),
            "owner_id": str(test_id),
            "type": "clone",
        }
    )

    assert document is not None

    await mongo_collection.delete_many({})


@pytest.mark.asyncio
async def test_deregister_template(
    mongo_collection: motor.AsyncIOMotorCollection, test_id: hikari.Snowflake
) -> None:
    """Test the deregister_template function.

    Arguments:
        mongo_collection: The mongo_collection fixture.
        test_id: The test_id fixture.

    Returns:
        None.
    """
    await mongo_collection.insert_one(
        {"guild_id": str(test_id), "channel_id": str(test_id), "type": "template"}
    )

    await channels.deregister_template(mongo_collection, test_id)

    document = await mongo_collection.find_one(
        {"channel_id": str(test_id), "type": "template"}
    )

    assert document is None

    await mongo_collection.delete_many({})


@pytest.mark.asyncio
async def test_deregister_clone(
    mongo_collection: motor.AsyncIOMotorCollection, test_id: hikari.Snowflake
) -> None:
    """Test the deregister_clone function.

    Arguments:
        mongo_collection: The mongo_collection fixture.
        test_id: The test_id fixture.

    Returns:
        None.
    """
    await mongo_collection.insert_one(
        {
            "guild_id": str(test_id),
            "template_id": str(test_id),
            "channel_id": str(test_id),
            "owner_id": str(test_id),
            "type": "clone",
        }
    )

    await channels.deregister_clone(mongo_collection, test_id)

    document = await mongo_collection.find_one(
        {"channel_id": str(test_id), "type": "clone"}
    )

    assert document is None

    await mongo_collection.delete_many({})


@pytest.mark.asyncio
async def test_delete_guild_data(
    mongo_collection: motor.AsyncIOMotorCollection, test_id: hikari.Snowflake
) -> None:
    """Test the delete_guild_data function.

    Arguments:
        mongo_collection: The mongo_collection fixture.
        test_id: The test_id fixture.

    Returns:
        None.
    """
    await mongo_collection.insert_many(
        [
            {"guild_id": str(test_id), "channel_id": str(test_id), "type": "template"},
            {
                "guild_id": str(test_id),
                "template_id": str(test_id),
                "channel_id": str(test_id),
                "owner_id": str(test_id),
                "type": "clone",
            },
        ]
    )

    await channels.delete_guild_data(mongo_collection, test_id)

    cursor = mongo_collection.find({"guild_id": str(test_id)})

    document_list = await cursor.to_list(None)

    assert document_list == []

    await mongo_collection.delete_many({})


@pytest.mark.asyncio
async def test_template_exists(
    mongo_collection: motor.AsyncIOMotorCollection, test_id: hikari.Snowflake
) -> None:
    """Test the template_exists function.

    Arguments:
        mongo_collection: The mongo_collection fixture.
        test_id: The test_id fixture.

    Returns:
        None.
    """
    await mongo_collection.insert_one(
        {"guild_id": str(test_id), "channel_id": str(test_id), "type": "template"}
    )

    result = await channels.template_exists(mongo_collection, test_id)

    assert result == True

    await mongo_collection.delete_many({})

    result = await channels.template_exists(mongo_collection, test_id)

    assert result == False


@pytest.mark.asyncio
async def test_clone_exists(
    mongo_collection: motor.AsyncIOMotorCollection, test_id: hikari.Snowflake
) -> None:
    """Test the clone_exists function.

    Arguments:
        mongo_collection: The mongo_collection fixture.
        test_id: The test_id fixture.

    Returns:
        None.
    """
    await mongo_collection.insert_one(
        {
            "guild_id": str(test_id),
            "template_id": str(test_id),
            "channel_id": str(test_id),
            "owner_id": str(test_id),
            "type": "clone",
        },
    )

    result = await channels.clone_exists(mongo_collection, test_id)

    assert result == True

    await mongo_collection.delete_many({})

    result = await channels.clone_exists(mongo_collection, test_id)

    assert result == False


@patch("lib.channels.get_clone", return_value=MagicMock())
@pytest.mark.asyncio
async def test_is_in_lobby(
    mongo_collection: motor.AsyncIOMotorCollection, test_id: hikari.Snowflake
) -> None:
    """Test the is_in_lobby function.

    Arguments:
        mongo_collection: The mongo_collection fixture.
        test_id: The test_id fixture.

    Returns:
        None.
    """
    mock_voice_state = MagicMock()
    mock_voice_state.channel_id = test_id

    mock_guild = MagicMock()
    mock_guild.get_voice_state.return_value = mock_voice_state
    mock_guild.get_channel.return_value = MagicMock()

    assert await channels.is_in_lobby(mongo_collection, mock_guild, MagicMock()) == True

    mock_voice_state.channel_id = None
    mock_guild.get_voice_state.return_value = mock_voice_state

    assert (
        await channels.is_in_lobby(mongo_collection, mock_guild, MagicMock()) == False
    )

    mock_voice_state = None
    mock_guild.get_voice_state.return_value = mock_voice_state

    assert (
        await channels.is_in_lobby(mongo_collection, mock_guild, MagicMock()) == False
    )
