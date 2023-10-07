import hikari
import lightbulb
import os

from lib import exceptions, responses
from motor.motor_asyncio import AsyncIOMotorClient


plugin = lightbulb.Plugin("Setup")


@plugin.listener(hikari.StartingEvent)
async def open_database_connection(event: hikari.StartingEvent) -> None:
    """Connect to MongoDB when the bot starts."""

    """Open and store a new database connection.
    
    Arguments:
        event: The event object.

    Returns:
        None.
    """
    plugin.bot.d.mongo_client = AsyncIOMotorClient(os.getenv("DATABASE_URI"))
    plugin.bot.d.mongo_database = plugin.bot.d.mongo_client["campfire"]


@plugin.listener(hikari.StoppingEvent)
async def close_database_connection(event: hikari.StoppingEvent) -> None:
    """Close the mongo connection when the bot stops.

    Arguments:
        event: The event object.

    Returns:
        None.
    """
    plugin.bot.d.mongo_client.close()


@plugin.listener(lightbulb.CommandErrorEvent)
async def on_command_error(event: lightbulb.CommandErrorEvent) -> bool | None:
    """Handles command errors thrown by the bot.

    Arguments:
        event: The event object.

    Returns:
        True if the exception can be handled, false if not.
    """
    if exceptions.evaluate_exception(event.exception, lightbulb.CommandNotFound):
        return True
    elif exceptions.evaluate_exception(event.exception, lightbulb.OnlyInGuild):
        await responses.error(event.context, "You cannot use this command in DMs.")
        return True

    raise event.exception


def load(bot: lightbulb.BotApp) -> None:
    """Loads the setup plugin."""
    bot.add_plugin(plugin)
