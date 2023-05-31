from __future__ import annotations

import hikari

import hikari.impl.cache as cache
import motor.motor_asyncio as motor


class TemplateChannel:
    """A class to represent a template channel.

    Arguments:
        collection: The mongo collection to store channel data in.
        channel: The voice channel to be represented as a template channel.

    Attributes:
        _collection: The mongo collection to store channel data in.
        _channel: The voice channel to be represented as a template channel.
    """

    def __init__(
        self,
        collection: motor.AsyncIOMotorCollection,
        channel: hikari.GuildVoiceChannel,
    ) -> None:
        self._collection = collection
        self._channel = channel

    def get_channel(self) -> hikari.GuildVoiceChannel:
        """Gets the voice channel object."""
        return self._channel

    async def spawn_clone(self, owner: hikari.Member, name: str) -> CloneChannel:
        """Creates a clone channel associated with the template channel.

        Arguments:
            owner: The lobby owner.
            name: The lobby name.

        Returns:
            The created clone channel.
        """
        return await create_clone(self._collection, self._channel, owner, name)


class CloneChannel:
    """A class to represent a clone channel.

    Arguments:
        collection: The mongo collection to store channel data in.
        channel: The voice channel to be represented as a template channel.

    Attributes:
        _collection: The mongo collection to store channel data in.
        _channel: The voice channel to be represented as a template channel.
    """

    def __init__(
        self,
        collection: motor.AsyncIOMotorCollection,
        channel: hikari.GuildVoiceChannel,
    ) -> None:
        self._collection = collection
        self._channel = channel

    def is_empty(self, cache: cache.CacheImpl) -> bool:
        """Returns if the channel is empty or not."""
        voice_states = cache.get_voice_states_view_for_channel(
            self._channel.get_guild(), self._channel.id
        )

        return list(voice_states) == []

    def get_channel(self) -> hikari.GuildVoiceChannel:
        """Gets the voice channel object."""
        return self._channel

    async def get_owner(self) -> hikari.Member:
        """Gets the member object of the lobby owner."""
        document = await self._collection.find_one(
            {"channel_id": str(self._channel.id), "type": "clone"}
        )

        return self._channel.get_guild().get_member(document["owner_id"])

    async def set_owner(self, new_owner: hikari.Member) -> None:
        """Sets the lobby owner to the specified member."""
        await self._collection.update_one(
            {"channel_id": str(self._channel.id)},
            {"$set": {"owner_id": str(new_owner.id)}},
        )

    async def rename(self, new_name: str) -> None:
        """Renames the voice channel."""
        await self._channel.edit(name=new_name)

    async def kick(self, member: hikari.Member) -> None:
        """Kicks the specified member from the voice channel."""
        await member.edit(voice_channel=None)


async def create_template(
    collection: motor.AsyncIOMotorCollection, guild: hikari.Guild, name: str
) -> TemplateChannel:
    """Creates a voice channel and registers it as a template channel.

    Arguments:
        collection: The mongo collection.
        guild: The guild to create the voice channel in.
        name: The name of the new voice channel.

    Returns:
        The created template channel.
    """
    template = await guild.create_voice_channel(name)

    await register_template(collection, guild.id, template.id)

    return TemplateChannel(collection, template)


async def create_clone(
    collection: motor.AsyncIOMotorCollection,
    template: hikari.GuildVoiceChannel,
    owner: hikari.Member,
    name: str,
) -> CloneChannel:
    """Creates a voice channel and registers it as a clone channel.

    Arguments:
        collection: The mongo collection.
        template: The voice channel to clone.
        owner: The owner of the new clone channel.
        name: The name of the new voice channel.

    Returns:
        The created clone channel.
    """
    clone = await template.get_guild().create_voice_channel(
        name,
        position=template.position,
        user_limit=template.user_limit,
        bitrate=template.bitrate,
        video_quality_mode=template.video_quality_mode,
        permission_overwrites=template.permission_overwrites,
        region=template.region,
        category=template.parent_id,
    )

    await register_clone(
        collection, template.get_guild().id, template.id, clone.id, owner.id
    )

    return CloneChannel(collection, clone)


async def get_template(
    collection: motor.AsyncIOMotorCollection, channel: hikari.GuildVoiceChannel
) -> TemplateChannel | None:
    """Checks if the channel is registered as a template channel.

    Arguments:
        collection: The mongo collection.
        channel: The voice channel to check.

    Returns:
        The template channel if it exists otherwise None.
    """
    if not await template_exists(collection, channel.id):
        return None

    return TemplateChannel(collection, channel)


async def get_clone(
    collection: motor.AsyncIOMotorCollection, channel: hikari.GuildVoiceChannel
) -> CloneChannel | None:
    """Checks if the channel is registered as a clone channel.

    Arguments:
        collection: The mongo collection.
        channel: The voice channel to check.

    Returns:
        The clone channel if it exists otherwise None.
    """
    if not await clone_exists(collection, channel.id):
        return None

    return CloneChannel(collection, channel)


async def delete_template(
    collection: motor.AsyncIOMotorCollection, channel: hikari.GuildVoiceChannel
) -> None:
    """Deletes the channel and deregisters it as a template.

    Arguments:
        collection: The mongo collection.
        channel: The voice channel to delete.

    Returns:
        None.
    """
    await channel.delete()
    await deregister_template(collection, channel.id)


async def delete_clone(
    collection: motor.AsyncIOMotorCollection, channel: hikari.GuildVoiceChannel
) -> None:
    """Deletes the channel and deregisters it as a clone.

    Arguments:
        collection: The mongo collection.
        channel: The voice channel to delete.

    Returns:
        None.
    """
    await channel.delete()
    await deregister_clone(collection, channel.id)


def joined_a_channel(new_state: hikari.VoiceState) -> bool:
    """Returns if the new voice state implies a channel has been joined.

    Arguments:
        new_state: The voice state to check.

    Returns:
        True if a channel has been joined otherwise False.
    """
    return new_state.channel_id is not None


def left_a_channel(old_state: hikari.VoiceState) -> bool:
    """Returns if the old voice state implies a channel has been left.

    Arguments:
        old_state: The voice state to check.

    Returns:
        True if a channel has been left otherwise False.
    """
    return old_state is not None and old_state.channel_id is not None


async def register_template(
    collection: motor.AsyncIOMotorCollection,
    guild_id: hikari.Snowflake,
    channel_id: hikari.Snowflake,
) -> None:
    """Registers a channel as a template channel.

    Arguments:
        collection: The mongo collection.
        guild_id: The ID of the guild the voice channel is in.
        channel_id: The ID of the voice channel.

    Returns:
        None.
    """
    await collection.insert_one(
        {
            "guild_id": str(guild_id),
            "channel_id": str(channel_id),
            "type": "template",
        }
    )


async def register_clone(
    collection: motor.AsyncIOMotorCollection,
    guild_id: hikari.Snowflake,
    template_id: hikari.Snowflake,
    clone_id: hikari.Snowflake,
    owner_id: hikari.Snowflake,
) -> None:
    """Registers a channel as a clone channel.

    Arguments:
        collection: The mongo collection.
        guild_id: The ID of the guild the voice channel is in.
        template_id: The ID of the voice channel that was cloned.
        clone_id: The ID of the clone voice channel.
        owner_id: The ID of the lobby owner.

    Returns:
        None.
    """
    await collection.insert_one(
        {
            "guild_id": str(guild_id),
            "template_id": str(template_id),
            "channel_id": str(clone_id),
            "owner_id": str(owner_id),
            "type": "clone",
        }
    )


async def deregister_template(
    collection: motor.AsyncIOMotorCollection, channel_id: hikari.Snowflake
) -> None:
    """Deregisters a channel as a template channel.

    Arguments:
        collection: The mongo collection.
        channel_id: The ID of the template voice channel.

    Returns:
        None.
    """
    await collection.delete_one({"channel_id": str(channel_id), "type": "template"})


async def deregister_clone(
    collection: motor.AsyncIOMotorCollection, channel_id: hikari.Snowflake
) -> None:
    """Deregisters a channel as a clone channel.

    Arguments:
        collection: The mongo collection.
        channel_id: The ID of the clone voice channel.

    Returns:
        None.
    """
    await collection.delete_one({"channel_id": str(channel_id), "type": "clone"})


async def delete_guild_data(
    collection: motor.AsyncIOMotorCollection, guild_id: hikari.Snowflake
) -> None:
    """Deregisters all channels in a guild.

    Arguments:
        collection: The mongo collection.
        guild_id: The ID of the guild data to delete.

    Returns:
        None.
    """
    await collection.delete_many({"guild_id": str(guild_id)})


async def template_exists(
    collection: motor.AsyncIOMotorCollection, channel_id: hikari.Snowflake
) -> bool:
    """Returns whether the channel ID is associated with a registered template channel.

    Arguments:
        collection: The mongo collection.
        channel_id: The ID of the channel to check.

    Returns:
        True if the channel_id is registered as a template otherwise False.
    """
    document = await collection.find_one(
        {"channel_id": str(channel_id), "type": "template"}
    )

    return document is not None


async def clone_exists(
    collection: motor.AsyncIOMotorCollection, channel_id: hikari.Snowflake
) -> bool:
    """Returns whether the channel ID is associated with a registered clone channel.

    Arguments:
        collection: The mongo collection.
        channel_id: The ID of the channel to check.

    Returns:
        True if the channel_id is registered as a clone otherwise False.
    """
    document = await collection.find_one(
        {"channel_id": str(channel_id), "type": "clone"}
    )

    return document is not None


async def is_in_lobby(
    collection: motor.AsyncIOMotorCollection, guild: hikari.Guild, member: hikari.Member
) -> bool:
    """Returns whether or not the member is in a valid lobby channel.

    Arguments:
        collection: The collection to check for the channel in.
        guild: The guild associated with the member.
        member: The member to check.

    Returns:
        True if the member is in a valid lobby channel else False.
    """
    member_voice_state = guild.get_voice_state(member)

    if member_voice_state is None or member_voice_state.channel_id is None:
        return False

    channel = guild.get_channel(member_voice_state.channel_id)
    clone = await get_clone(collection, channel)

    return clone is not None
