from __future__ import annotations

import hikari

import hikari.impl.cache as cache
import motor.motor_asyncio as motor


class TemplateChannel:
    def __init__(
        self,
        collection: motor.AsyncIOMotorCollection,
        channel: hikari.GuildVoiceChannel,
    ) -> None:
        self.collection = collection
        self.channel = channel

    @staticmethod
    async def create(
        collection: motor.AsyncIOMotorCollection, guild: hikari.Guild, name: str
    ) -> TemplateChannel:
        template = await guild.create_voice_channel(name)

        await add_template(collection, guild.id, template.id)

        return TemplateChannel(collection, template)

    @staticmethod
    async def get(
        collection: motor.AsyncIOMotorCollection, channel: hikari.GuildVoiceChannel
    ) -> TemplateChannel | None:
        if not await template_exists(collection, channel.id):
            return None

        return TemplateChannel(collection, channel)

    @staticmethod
    async def delete(
        collection: motor.AsyncIOMotorCollection, channel: hikari.GuildVoiceChannel
    ) -> None:
        await channel.delete()
        await delete_template(collection, channel.id)

    async def spawn_clone(self, owner: hikari.Member, name: str) -> CloneChannel:
        return await CloneChannel.create(self.collection, self.channel, owner, name)


class CloneChannel:
    def __init__(
        self,
        collection: motor.AsyncIOMotorCollection,
        channel: hikari.GuildVoiceChannel,
    ) -> None:
        self.collection = collection
        self.channel = channel

    @staticmethod
    async def create(
        collection: motor.AsyncIOMotorCollection,
        template: hikari.GuildVoiceChannel,
        owner: hikari.Member,
        name: str,
    ) -> CloneChannel:
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

        await add_clone(
            collection, template.get_guild().id, template.id, clone.id, owner.id
        )

        return CloneChannel(collection, clone)

    @staticmethod
    async def get(
        collection: motor.AsyncIOMotorCollection, channel: hikari.GuildVoiceChannel
    ) -> CloneChannel | None:
        if not await clone_exists(collection, channel.id):
            return None

        return CloneChannel(collection, channel)

    @staticmethod
    async def delete(
        collection: motor.AsyncIOMotorCollection, channel: hikari.GuildVoiceChannel
    ) -> None:
        await channel.delete()
        await delete_clone(collection, channel.id)

    def is_empty(self, cache: cache.CacheImpl) -> bool:
        voice_states = cache.get_voice_states_view_for_channel(
            self.channel.get_guild(), self.channel.id
        )

        return list(voice_states) == []

    async def get_owner(self) -> hikari.Member:
        document = await self.collection.find_one(
            {"channel_id": str(self.channel.id), "type": "lobby"}
        )

        return self.channel.get_guild().get_member(document["owner_id"])

    async def set_owner(self, new_owner: hikari.Member) -> None:
        await self.collection.update_one(
            {"channel_id": str(self.channel.id)},
            {"$set": {"owner_id": str(new_owner.id)}},
        )

    async def rename(self, new_name: str) -> None:
        await self.channel.edit(name=new_name)

    async def kick(self, member: hikari.Member) -> None:
        await member.edit(voice_channel=None)


def joined_a_channel(new_state: hikari.VoiceState) -> bool:
    return new_state.channel_id is not None


def left_a_channel(old_state: hikari.VoiceState) -> bool:
    return old_state is not None and old_state.channel_id is not None


async def add_template(collection, guild_id, channel_id):
    await collection.insert_one(
        {
            "guild_id": str(guild_id),
            "channel_id": str(channel_id),
            "type": "template",
        }
    )


async def add_clone(collection, guild_id, template_id, clone_id, owner_id):
    await collection.insert_one(
        {
            "guild_id": str(guild_id),
            "template_id": str(template_id),
            "channel_id": str(clone_id),
            "owner_id": str(owner_id),
            "type": "clone",
        }
    )


async def delete_template(collection, channel_id):
    await collection.delete_one({"channel_id": str(channel_id), "type": "template"})


async def delete_clone(collection, channel_id):
    await collection.delete_one({"channel_id": str(channel_id), "type": "clone"})


async def delete_guild_data(collection, guild_id):
    await collection.delete_many({"guild_id": str(guild_id)})


async def template_exists(collection, channel_id):
    document = await collection.find_one(
        {"channel_id": str(channel_id), "type": "template"}
    )

    return document is not None


async def clone_exists(collection, channel_id):
    document = await collection.find_one(
        {"channel_id": str(channel_id), "type": "clone"}
    )

    return document is not None


async def get_all_documents(collection):
    cursor = collection.find()

    return await cursor.to_list(None)
