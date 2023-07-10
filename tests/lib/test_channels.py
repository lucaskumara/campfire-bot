import hikari
import pytest

from lib import channels
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_id() -> hikari.Snowflake:
    return hikari.Snowflake(123)


def test_template_channel() -> None:
    mock_collection = MagicMock()
    mock_channel = MagicMock()

    result = channels.TemplateChannel(mock_collection, mock_channel)

    assert result.collection == mock_collection
    assert result.channel == mock_channel


@patch("lib.channels.create_clone", return_value=channels.CloneChannel(None, None))
@pytest.mark.asyncio
async def test_template_channel_spawn_clone(mock_create_clone: AsyncMock) -> None:
    mock_collection = MagicMock()
    mock_channel = MagicMock()
    mock_owner = MagicMock()
    mock_channel_name = MagicMock()

    template_channel = channels.TemplateChannel(mock_collection, mock_channel)

    result = await template_channel.spawn_clone(mock_owner, mock_channel_name)

    assert isinstance(result, channels.CloneChannel)

    mock_create_clone.assert_awaited_once_with(
        mock_collection, mock_channel, mock_owner, mock_channel_name
    )


def test_clone_channel() -> None:
    mock_collection = MagicMock()
    mock_channel = MagicMock()

    result = channels.CloneChannel(mock_collection, mock_channel)

    assert result.collection == mock_collection
    assert result.channel == mock_channel


@patch("lib.channels.cache", return_value=MagicMock())
def test_clone_channel_is_empty_with_empty_result(mock_cache: MagicMock) -> None:
    mock_cache.get_voice_states_view_for_channel = MagicMock()
    mock_cache.get_voice_states_view_for_channel.return_value = []

    clone_channel = channels.CloneChannel(MagicMock(), MagicMock())

    result = clone_channel.is_empty(mock_cache)

    assert result


@patch("lib.channels.cache", return_value=MagicMock())
def test_clone_channel_is_empty_with_non_empty_result(mock_cache: MagicMock) -> None:
    mock_cache.get_voice_states_view_for_channel = MagicMock()
    mock_cache.get_voice_states_view_for_channel.return_value = [MagicMock()]

    clone_channel = channels.CloneChannel(MagicMock(), MagicMock())

    result = clone_channel.is_empty(mock_cache)

    assert not result


@pytest.mark.asyncio
async def test_clone_channel_get_owner(mock_id: hikari.Snowflake) -> None:
    mock_collection = MagicMock()
    mock_collection.find_one = AsyncMock()
    mock_collection.find_one.return_value = {"owner_id": mock_id}

    mock_channel = MagicMock()
    mock_channel.get_guild = MagicMock()
    mock_channel.get_guild.return_value = MagicMock()
    mock_channel.get_guild.return_value.get_member = MagicMock()

    clone_channel = channels.CloneChannel(mock_collection, mock_channel)

    await clone_channel.get_owner()

    mock_channel.get_guild.return_value.get_member.assert_called_once_with(mock_id)


@pytest.mark.asyncio
async def test_clone_channel_set_owner(mock_id: hikari.Snowflake) -> None:
    mock_collection = MagicMock()
    mock_collection.update_one = AsyncMock()

    mock_channel = MagicMock()
    mock_channel.id = mock_id

    mock_member = MagicMock()
    mock_member.id = mock_id

    clone_channel = channels.CloneChannel(mock_collection, mock_channel)

    await clone_channel.set_owner(mock_member)

    mock_collection.update_one.assert_awaited_once_with(
        {"channel_id": str(mock_id)}, {"$set": {"owner_id": str(mock_id)}}
    )


@pytest.mark.asyncio
async def test_clone_channel_rename() -> None:
    mock_channel = MagicMock()
    mock_channel.edit = AsyncMock()

    new_channel_name = "Sample Name"

    clone_channel = channels.CloneChannel(MagicMock(), mock_channel)

    await clone_channel.rename(new_channel_name)

    mock_channel.edit.assert_awaited_once_with(name=new_channel_name)


@pytest.mark.asyncio
async def test_clone_channel_kick() -> None:
    mock_member = MagicMock()
    mock_member.edit = AsyncMock()

    clone_channel = channels.CloneChannel(MagicMock(), MagicMock())

    await clone_channel.kick(mock_member)

    mock_member.edit.assert_awaited_once_with(voice_channel=None)


@patch("lib.channels.register_template", return_value=AsyncMock())
@pytest.mark.asyncio
async def test_create_template(
    mock_register_template: AsyncMock, mock_id: hikari.Snowflake
) -> None:
    mock_collection = MagicMock()

    mock_guild = MagicMock()
    mock_guild.id = mock_id
    mock_guild.create_voice_channel = AsyncMock()
    mock_guild.create_voice_channel.return_value = MagicMock()
    mock_guild.create_voice_channel.return_value.id = mock_id

    result = await channels.create_template(mock_collection, mock_guild, "Sample Name")

    assert isinstance(result, channels.TemplateChannel)
    assert result.channel.id == mock_id

    mock_register_template.assert_awaited_once_with(
        mock_collection, mock_guild.id, mock_id
    )


@patch("lib.channels.register_clone", return_value=AsyncMock())
@pytest.mark.asyncio
async def test_create_clone(
    mock_register_clone: AsyncMock, mock_id: hikari.Snowflake
) -> None:
    mock_collection = MagicMock()

    mock_template_channel = MagicMock()
    mock_template_channel.id = mock_id
    mock_template_channel.get_guild = MagicMock()
    mock_template_channel.get_guild.return_value = MagicMock()
    mock_template_channel.get_guild.return_value.id = mock_id
    mock_template_channel.get_guild.return_value.create_voice_channel = AsyncMock()
    mock_template_channel.get_guild.return_value.create_voice_channel.return_value = (
        MagicMock()
    )
    mock_template_channel.get_guild.return_value.create_voice_channel.return_value.id = (
        mock_id
    )

    mock_owner = MagicMock()
    mock_owner.id = mock_id

    result = await channels.create_clone(
        mock_collection, mock_template_channel, mock_owner, "Sample Name"
    )

    assert isinstance(result, channels.CloneChannel)
    assert result.channel.id == mock_id

    mock_register_clone.assert_awaited_once_with(
        mock_collection, mock_id, mock_id, mock_id, mock_id
    )


@patch("lib.channels.template_exists", return_value=True)
@pytest.mark.asyncio
async def test_get_template_with_existing_template(
    mock_template_exists: MagicMock, mock_id: hikari.Snowflake
) -> None:
    mock_collection = MagicMock()

    mock_channel = MagicMock()
    mock_channel.id = mock_id

    result = await channels.get_template(mock_collection, mock_channel)

    assert isinstance(result, channels.TemplateChannel)
    assert result.channel.id == mock_id


@patch("lib.channels.template_exists", return_value=False)
@pytest.mark.asyncio
async def test_get_template_with_non_existing_template(
    mock_template_exists: MagicMock,
) -> None:
    mock_collection = MagicMock()
    mock_channel = MagicMock()

    result = await channels.get_template(mock_collection, mock_channel)

    assert result is None


@patch("lib.channels.clone_exists", return_value=True)
@pytest.mark.asyncio
async def test_get_clone_with_existing_template(
    mock_clone_exists: MagicMock, mock_id: hikari.Snowflake
) -> None:
    mock_collection = MagicMock()

    mock_channel = MagicMock()
    mock_channel.id = mock_id

    result = await channels.get_clone(mock_collection, mock_channel)

    assert isinstance(result, channels.CloneChannel)
    assert result.channel.id == mock_id


@patch("lib.channels.clone_exists", return_value=False)
@pytest.mark.asyncio
async def test_get_clone_with_non_existing_template(
    mock_clone_exists: MagicMock,
) -> None:
    mock_collection = MagicMock()
    mock_channel = MagicMock()

    result = await channels.get_clone(mock_collection, mock_channel)

    assert result is None


@patch("lib.channels.deregister_template", return_value=MagicMock())
@pytest.mark.asyncio
async def test_delete_template(
    mock_deregister_template: MagicMock, mock_id: hikari.Snowflake
) -> None:
    mock_collection = MagicMock()

    mock_channel = MagicMock()
    mock_channel.id = mock_id
    mock_channel.delete = AsyncMock()

    await channels.delete_template(mock_collection, mock_channel)

    mock_channel.delete.assert_awaited_once_with()
    mock_deregister_template.assert_called_once_with(mock_collection, mock_id)


@patch("lib.channels.deregister_clone", return_value=MagicMock())
@pytest.mark.asyncio
async def test_delete_clone(
    mock_deregister_clone: MagicMock, mock_id: hikari.Snowflake
) -> None:
    mock_collection = MagicMock()

    mock_channel = MagicMock()
    mock_channel.id = mock_id
    mock_channel.delete = AsyncMock()

    await channels.delete_clone(mock_collection, mock_channel)

    mock_channel.delete.assert_awaited_once_with()
    mock_deregister_clone.assert_called_once_with(mock_collection, mock_id)


def test_joined_a_channel_with_channel_id(mock_id: hikari.Snowflake) -> None:
    mock_state = MagicMock()
    mock_state.channel_id = mock_id

    result = channels.joined_a_channel(mock_state)

    assert result


def test_joined_a_channel_with_no_channel_id() -> None:
    mock_state = MagicMock()
    mock_state.channel_id = None

    result = channels.joined_a_channel(mock_state)

    assert not result


def test_left_a_channel_with_no_state() -> None:
    result = channels.left_a_channel(None)

    assert not result


def test_left_a_channel_with_channel_id(mock_id: hikari.Snowflake) -> None:
    mock_state = MagicMock()
    mock_state.channel_id = mock_id

    result = channels.left_a_channel(mock_state)

    assert result


def test_left_a_channel_with_no_channel_id() -> None:
    mock_state = MagicMock()
    mock_state.channel_id = None

    result = channels.left_a_channel(mock_state)

    assert not result


@pytest.mark.asyncio
async def test_register_template(mock_id: hikari.Snowflake) -> None:
    mock_collection = MagicMock()
    mock_collection.insert_one = AsyncMock()

    await channels.register_template(mock_collection, mock_id, mock_id)

    mock_collection.insert_one.assert_awaited_once_with(
        {
            "guild_id": str(mock_id),
            "channel_id": str(mock_id),
            "type": "template",
        }
    )


@pytest.mark.asyncio
async def test_register_clone(mock_id: hikari.Snowflake) -> None:
    mock_collection = MagicMock()
    mock_collection.insert_one = AsyncMock()

    await channels.register_clone(mock_collection, mock_id, mock_id, mock_id, mock_id)

    mock_collection.insert_one.assert_awaited_once_with(
        {
            "guild_id": str(mock_id),
            "template_id": str(mock_id),
            "channel_id": str(mock_id),
            "owner_id": str(mock_id),
            "type": "clone",
        }
    )


@pytest.mark.asyncio
async def test_deregister_template(mock_id: hikari.Snowflake) -> None:
    mock_collection = MagicMock()
    mock_collection.delete_one = AsyncMock()

    await channels.deregister_template(mock_collection, mock_id)

    mock_collection.delete_one.assert_awaited_once_with(
        {"channel_id": str(mock_id), "type": "template"}
    )


@pytest.mark.asyncio
async def test_deregister_clone(mock_id: hikari.Snowflake) -> None:
    mock_collection = MagicMock()
    mock_collection.delete_one = AsyncMock()

    await channels.deregister_clone(mock_collection, mock_id)

    mock_collection.delete_one.assert_awaited_once_with(
        {"channel_id": str(mock_id), "type": "clone"}
    )


@pytest.mark.asyncio
async def test_delete_guild_data(mock_id: hikari.Snowflake) -> None:
    mock_collection = MagicMock()
    mock_collection.delete_many = AsyncMock()

    await channels.delete_guild_data(mock_collection, mock_id)

    mock_collection.delete_many.assert_awaited_once_with({"guild_id": str(mock_id)})


@pytest.mark.asyncio
async def test_template_exists_with_existing_template(
    mock_id: hikari.Snowflake,
) -> None:
    mock_collection = MagicMock()
    mock_collection.find_one = AsyncMock()
    mock_collection.find_one.return_value = {}

    result = await channels.template_exists(mock_collection, mock_id)

    assert result


@pytest.mark.asyncio
async def test_template_exists_with_existing_template(
    mock_id: hikari.Snowflake,
) -> None:
    mock_collection = MagicMock()
    mock_collection.find_one = AsyncMock()
    mock_collection.find_one.return_value = None

    result = await channels.template_exists(mock_collection, mock_id)

    assert not result


@pytest.mark.asyncio
async def test_clone_exists_with_existing_template(
    mock_id: hikari.Snowflake,
) -> None:
    mock_collection = MagicMock()
    mock_collection.find_one = AsyncMock()
    mock_collection.find_one.return_value = {}

    result = await channels.clone_exists(mock_collection, mock_id)

    assert result


@pytest.mark.asyncio
async def test_clone_exists_with_existing_template(
    mock_id: hikari.Snowflake,
) -> None:
    mock_collection = MagicMock()
    mock_collection.find_one = AsyncMock()
    mock_collection.find_one.return_value = None

    result = await channels.clone_exists(mock_collection, mock_id)

    assert not result


@pytest.mark.asyncio
async def test_is_in_lobby_with_no_guild_voice_state() -> None:
    mock_collection = MagicMock()

    mock_guild = MagicMock()
    mock_guild.get_voice_state = MagicMock()
    mock_guild.get_voice_state.return_value = None

    mock_member = MagicMock()

    result = await channels.is_in_lobby(mock_collection, mock_guild, mock_member)

    assert not result


@pytest.mark.asyncio
async def test_is_in_lobby_with_no_channel_id() -> None:
    mock_collection = MagicMock()

    mock_guild = MagicMock()
    mock_guild.get_voice_state = MagicMock()
    mock_guild.get_voice_state.return_value = MagicMock()
    mock_guild.get_voice_state.return_value.channel_id = None

    mock_member = MagicMock()

    result = await channels.is_in_lobby(mock_collection, mock_guild, mock_member)

    assert not result


@patch("lib.channels.get_clone", return_value=None)
@pytest.mark.asyncio
async def test_is_in_lobby_with_non_clone_channel(
    mock_get_clone: MagicMock, mock_id: hikari.Snowflake
) -> None:
    mock_collection = MagicMock()

    mock_guild = MagicMock()
    mock_guild.get_voice_state = MagicMock()
    mock_guild.get_voice_state.return_value = MagicMock()
    mock_guild.get_voice_state.return_value.channel_id = mock_id
    mock_guild.get_channel = MagicMock()
    mock_guild.get_channel.return_value = MagicMock()

    mock_member = MagicMock()

    result = await channels.is_in_lobby(mock_collection, mock_guild, mock_member)

    assert not result


@patch("lib.channels.get_clone", return_value=MagicMock())
@pytest.mark.asyncio
async def test_is_in_lobby_with_clone_channel(
    mock_get_clone: MagicMock, mock_id: hikari.Snowflake
) -> None:
    mock_collection = MagicMock()

    mock_guild = MagicMock()
    mock_guild.get_voice_state = MagicMock()
    mock_guild.get_voice_state.return_value = MagicMock()
    mock_guild.get_voice_state.return_value.channel_id = mock_id
    mock_guild.get_channel = MagicMock()
    mock_guild.get_channel.return_value = MagicMock()

    mock_member = MagicMock()

    result = await channels.is_in_lobby(mock_collection, mock_guild, mock_member)

    assert result
