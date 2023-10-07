import hikari

import motor.motor_asyncio as motor


async def is_filter_enabled(
    collection: motor.AsyncIOMotorCollection, guild_id: hikari.Snowflake
) -> bool:
    """Checks if the profanity filter is enabled for the specific guild.

    Arguments:
        collection: The mongo collection.
        guild_id: The ID of the guild to check.

    Returns:
        True if it is enabled, otherwise False.
    """
    document = await collection.find_one({"guild_id": str(guild_id)})

    return document.get("filter_profanity", False) if document is not None else False


async def enable_filter(
    collection: motor.AsyncIOMotorCollection, guild_id: hikari.Snowflake
) -> None:
    """Enables the profanity filter for the specified guild.

    Arguments:
        collection: The mongo collection.
        guild_id: The ID of the guild to enable the filter for.

    Returns:
        None.
    """
    await collection.update_one(
        {"guild_id": str(guild_id)}, {"$set": {"filter_profanity": True}}, upsert=True
    )


async def disable_filter(
    collection: motor.AsyncIOMotorCollection, guild_id: hikari.Snowflake
) -> None:
    """Disables the profanity filter for the specified guild.

    Arguments:
        collection: The mongo collection.
        guild_id: The ID of the guild to disable the filter for.

    Returns:
        None.
    """
    await collection.update_one(
        {"guild_id": str(guild_id)}, {"$set": {"filter_profanity": False}}, upsert=True
    )
