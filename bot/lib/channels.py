from __future__ import annotations

import hikari

import motor.motor_asyncio as motor


class TemplateChannel:
    def __init__(self, channel: hikari.GuildVoiceChannel) -> None:
        self.channel = channel

    @staticmethod
    async def create(
        collection: motor.AsyncIOMotorCollection, guild: hikari.Guild
    ) -> TemplateChannel:
        # Create the channel
        channel = guild.create_voice_channel("Name")

        # Store the channel in the db
        await insert_template_channel(collection, guild.id, channel.id)

        # Return the channel
        return TemplateChannel(channel)

    @staticmethod
    async def get(
        collection: motor.AsyncIOMotorCollection,
        guild: hikari.Guild,
        channel_id: hikari.Snowflake,
    ) -> TemplateChannel | None:
        # Check if the channel is in the db, return None if not
        if not await has_channel(collection, channel_id):
            return None

        # Get the channel guild.get_channel()
        channel = guild.get_channel(channel_id)

        # Return the channel
        return TemplateChannel(channel)

    @staticmethod
    async def delete(
        collection: motor.AsyncIOMotorChangeStream, channel_id: hikari.Snowflake
    ) -> None:
        # Delete the channel from the db
        await delete_channel(collection, channel_id)

    async def spawn_lobby(self, member: hikari.Member) -> None:
        await LobbyChannel.create(self.channel, member)


class LobbyChannel:
    def __init__(self, channel: hikari.GuildVoiceChannel, owner: hikari.Member) -> None:
        self.channel = channel
        self.owner = owner

    @staticmethod
    async def create(
        collection: motor.AsyncIOMotorCollection,
        template_channel: hikari.GuildVoiceChannel,
        owner: hikari.Member,
    ) -> LobbyChannel:
        # Clone the template channel
        channel = template_channel.get_guild().create_voice_channel(
            "Lobby",
            position=template_channel.position,
            user_limit=template_channel.user_limit,
            bitrate=template_channel.bitrate,
            video_quality_mode=template_channel.video_quality_mode,
            permission_overwrites=template_channel.permission_overwrites,
            region=template_channel.region,
            category=template_channel.parent_id,
        )

        # Store the channel in the db
        await insert_lobby_channel(
            collection,
            template_channel.guild_id,
            template_channel.id,
            channel.id,
            owner.id,
        )

        # Return the channel
        return LobbyChannel(channel)

    @staticmethod
    async def get(
        collection: motor.AsyncIOMotorCollection,
        guild: hikari.Guild,
        channel_id: hikari.Snowflake,
    ) -> LobbyChannel | None:
        # Check if the channel is in the db, return None if not
        if not await has_channel(collection, channel_id):
            return None

        # Get the channel guild.get_channel()
        channel = guild.get_channel(channel)

        # Return the channel
        return LobbyChannel(channel)

    @staticmethod
    async def delete(
        collection: motor.AsyncIOMotorCollection, channel_id: hikari.Snowflake
    ) -> None:
        # Delete the channel from the db
        await delete_channel(collection, channel_id)

    async def rename(self, new_name: str) -> None:
        self.channel.edit(name=new_name)

    async def kick(self, member: hikari.Member) -> None:
        await member.edit(voice_channel=None)

    async def set_owner(
        self, collection: motor.AsyncIOMotorCollection, new_owner: hikari.Member
    ) -> None:
        # Set the channel owner to the member
        await collection.update_one(
            {"channel_id": str(self.channel.id)},
            {"$set": {"owner_id": str(new_owner.id)}},
        )


async def insert_template_channel(
    collection: motor.AsyncIOMotorCollection,
    guild_id: hikari.Snowflake,
    channel_id: hikari.Snowflake,
) -> None:
    await collection.insert_one(
        {"guild_id": str(guild_id), "channel_id": str(channel_id)}
    )


async def insert_lobby_channel(
    collection: motor.AsyncIOMotorCollection,
    guild_id: hikari.Snowflake,
    template_channel_id: hikari.Snowflake,
    channel_id: hikari.Snowflake,
    owner_id: hikari.Snowflake,
) -> None:
    await collection.insert_one(
        {
            "guild_id": str(guild_id),
            "template_id": str(template_channel_id),
            "channel_id": str(channel_id),
            "owner_id": str(owner_id),
        }
    )


async def has_channel(
    collection: motor.AsyncIOMotorCollection, channel_id: hikari.Snowflake
) -> bool:
    return await collection.find_one({"channel_id": str(channel_id)}) is not None


async def delete_channel(
    collection: motor.AsyncIOMotorCollection, channel_id: hikari.Snowflake
) -> None:
    await collection.delete_one({"channel_id": str(channel_id)})
