import hikari


async def is_filter_enabled(bot: hikari.GatewayBot, guild_id: hikari.Snowflake) -> None:
    """Checks if the profanity filter is enabled for the specific guild.

    Arguments:
        bot: The bot instance.
        guild_id: The ID of the guild to check.

    Returns:
        True if it is enabled, otherwise False.
    """
    collection = bot.d.mongo_database.settings

    document = await collection.find_one({"guild_id": str(guild_id)})

    return document.get("profanity_filter", False) if document is not None else False


async def enable_filter(bot: hikari.GatewayBot, guild_id: hikari.Snowflake) -> None:
    """Enables the profanity filter for the specified guild.

    Arguments:
        bot: The bot instance.
        guild_id: The ID of the guild to enable the filter for.

    Returns:
        None.
    """
    collection = bot.d.mongo_database.settings

    await collection.update_one(
        {"guild_id": str(guild_id)}, {"$set": {"profanity_filter": True}}, upsert=True
    )


async def disable_filter(bot: hikari.GatewayBot, guild_id: hikari.Snowflake) -> None:
    """Disables the profanity filter for the specified guild.

    Arguments:
        bot: The bot instance.
        guild_id: The ID of the guild to disable the filter for.

    Returns:
        None.
    """
    collection = bot.d.mongo_database.settings

    await collection.update_one(
        {"guild_id": str(guild_id)}, {"$set": {"profanity_filter": False}}, upsert=True
    )
