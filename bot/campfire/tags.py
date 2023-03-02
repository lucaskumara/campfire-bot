import hikari

import campfire.responses as responses

from datetime import datetime, timezone


class Tag:
    """A class to represent a guild tag.

    Arguments:
        document: The queried document to represent as a tag.
        rest_client: The REST client associated with the bot.

    Attributes:
        _name: The name of the tag.
        _content: The content of the tag.
        _guild_id: The guild ID of the tag.
        _author_id: The author ID of the tag.
        _created_date: The date the tag was created.
        _modified_date: The date the tag was last modified.
        _uses: The number of times the tag was used.
    """

    def __init__(self, document: dict, rest_client: hikari.api.RESTClient) -> None:
        self._name = document["name"]
        self._content = document["content"]
        self._guild_id = int(document["guild_id"])
        self._author_id = int(document["author_id"])
        self._created_date = document["created_at"]
        self._modified_date = document["modified_at"]
        self._uses = document["uses"]

        self._rest_client = rest_client

    def get_name(self) -> str:
        """Retrieves the tag name."""
        return self._name

    def get_content(self) -> str:
        """Retrieves the tag content."""
        return self._content

    async def get_guild(self) -> hikari.Guild:
        """Retrieves the tag guild using the guild ID."""
        return await self._rest_client.fetch_guild(self._guild_id)

    async def get_author(self) -> hikari.User:
        """Retrieves the tag author using the author ID."""
        return await self._rest_client.fetch_user(self._author_id)

    def get_created_date(self) -> datetime:
        """Retrieves the date the tag was created."""
        return self._created_date

    def get_modified_date(self) -> datetime:
        """Retrieves the date the tag was last modified."""
        return self._modified_date

    def get_uses(self) -> int:
        """Retrieves the number of times the tag was used."""
        return self._uses

    async def info_embed(
        self, embed_title: str, embed_description: str, embed_icon_url: hikari.URL
    ) -> hikari.Embed:
        """Returns an embed containing tag information."""
        tag_author = await self.get_author()

        return responses.build_embed(
            embed_title,
            embed_description,
            embed_icon_url,
            responses.INFO_MESSAGE_COLOUR,
            [
                responses.Field("Name", self._name, True),
                responses.Field("Author", tag_author.mention, True),
                responses.Field("Uses", self._uses, True),
                responses.Field("Created at", self._created_date, True),
                responses.Field("Modified at", self._modified_date, True),
            ],
        )


async def get_tag(
    bot: hikari.GatewayBot,
    tag_name: str,
    tag_guild: hikari.Guild,
) -> Tag | None:
    """Gets a tag.

    Arguments:
        bot: The bot instance.
        tag_name: The name of the tag.
        tag_guild: The guild of the tag.

    Returns:
        The Tag object otherwise None.
    """
    collection = bot.d.mongo_database.tags
    document = await collection.find_one(
        {"name": tag_name, "guild_id": str(tag_guild.id)}
    )

    return Tag(document, bot.rest) if document is not None else None


async def get_tags(bot: hikari.GatewayBot, tag_guild: hikari.Guild) -> list[Tag]:
    """Gets multiple tags.

    Arguments:
        bot: The bot instance.
        tag_guild: The guild of the tags.

    Returns:
        A list of Tag objects.
    """
    collection = bot.d.mongo_database.tags
    cursor = collection.find({"guild_id": str(tag_guild.id)})

    return [Tag(document, bot.rest) async for document in cursor]


async def get_tags_by_author(
    bot: hikari.GatewayBot, tag_guild: hikari.Guild, tag_author: hikari.User
) -> None:
    """Gets multiple tags authored by a specific user.

    Arguments:
        bot: The bot instance.
        tag_guild: The guild of the tags.
        tag_author: The author of the tags.

    Returns:
        A list of Tag objects.
    """
    collection = bot.d.mongo_database.tags
    cursor = collection.find(
        {"guild_id": str(tag_guild.id), "author_id": str(tag_author.id)}
    )

    return [Tag(document, bot.rest) async for document in cursor]


async def create_tag(
    bot: hikari.GatewayBot,
    tag_name: str,
    tag_content: str,
    tag_guild: hikari.Guild,
    tag_author: hikari.User,
) -> None:
    """Creates a new tag.

    Arguments:
        bot: The bot instance.
        tag_name: The name of the tag.
        tag_content: The content of the tag.
        tag_guild: The guild of the tag.
        tag_author: The author of the tag.

    Returns:
        None.
    """
    collection = bot.d.mongo_database.tags
    creation_time = datetime.now(timezone.utc)

    await collection.insert_one(
        {
            "name": tag_name,
            "content": tag_content,
            "guild_id": str(tag_guild.id),
            "author_id": str(tag_author.id),
            "created_at": creation_time,
            "modified_at": creation_time,
            "uses": 0,
        }
    )


async def edit_tag(
    bot: hikari.GatewayBot,
    tag_name: str,
    tag_content: str,
    tag_guild: hikari.Guild,
) -> None:
    """Edits an existing tag.

    Arguments:
        bot: The bot instance.
        tag_name: The name of the tag.
        tag_content: The new content of the tag.
        tag_guild: The guild of the tag.

    Returns:
        None.
    """
    collection = bot.d.mongo_database.tags
    modification_time = datetime.now(timezone.utc)

    await collection.update_one(
        {"name": tag_name, "guild_id": str(tag_guild.id)},
        {"$set": {"content": tag_content, "modified_at": modification_time}},
    )


async def delete_tag(
    bot: hikari.GatewayBot,
    tag_name: str,
    tag_guild: hikari.Guild,
) -> None:
    """Deletes an existing tag.

    Arguments:
        bot: The bot instance.
        tag_name: The name of the tag.
        tag_guild: The guild of the tag.

    Returns:
        None.
    """
    collection = bot.d.mongo_database.tags

    await collection.delete_one({"name": tag_name, "guild_id": str(tag_guild.id)})


async def delete_all_tags(bot: hikari.GatewayBot, tag_guild: hikari.Guild) -> None:
    """Deletes all guild tags.

    Arguments:
        bot: The bot instance.
        tag_guild: The guild of the tag.

    Returns:
        None.
    """
    collection = bot.d.mongo_database.tags

    await collection.delete_many({"guild_id": str(tag_guild.id)})


async def increment_tag(
    bot: hikari.GatewayBot,
    tag_name: str,
    tag_guild: hikari.Guild,
) -> None:
    """Increments a tags uses by 1.

    Arguments:
        bot: The bot instance.
        tag_name: The name of the tag.
        tag_guild: The guild of the tag.

    Returns:
        None.
    """
    collection = bot.d.mongo_database.tags

    await collection.update_one(
        {"name": tag_name, "guild_id": str(tag_guild.id)},
        {"$inc": {"uses": 1}},
    )


async def guild_tag_count(bot: hikari.GatewayBot, tag_guild: hikari.Guild) -> int:
    """Counts the number of tags in a guild.

    Arguments:
        bot: The bot instance.
        tag_guild: The guild to count the tags of.

    Returns:
        The number of tags.
    """
    collection = bot.d.mongo_database.tags

    return await collection.count_documents({"guild_id": str(tag_guild.id)})


async def guild_tag_count_by_author(
    bot: hikari.GatewayBot,
    tag_guild: hikari.Guild,
    tag_author: hikari.User,
) -> int:
    """Counts the number of tags in a guild authored by a specific user.

    Arguments:
        bot: The bot instance.
        tag_guild: The guild to count the tags of.
        tag_author: The author of the tags.

    Returns:
        The number of tags.
    """
    collection = bot.d.mongo_database.tags

    return await collection.count_documents(
        {"guild_id": str(tag_guild.id), "author_id": str(tag_author.id)}
    )
