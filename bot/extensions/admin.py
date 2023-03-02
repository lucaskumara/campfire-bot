import hikari
import lightbulb
import os

from utils.exceptions import evaluate_exception
from utils.responses import error_response
from motor.motor_asyncio import AsyncIOMotorClient

plugin = lightbulb.Plugin("Admin")


def connect_database(bot: hikari.GatewayBot) -> None:
    """Open and store a new database connection.

    Arguments:
        bot: The bot instance to associate the connection with.

    Returns:
        None.
    """
    bot.d.mongo_client = AsyncIOMotorClient(os.getenv("DATABASE_URI"))
    bot.d.mongo_database = bot.d.mongo_client["campfire"]


def disconnect_database(bot: hikari.GatewayBot) -> None:
    """Close the existing database connection.

    Arguments:
        bot: The bot instance with the connection to close.

    Returns:
        None.
    """
    bot.d.mongo_client.close()


async def handle_error(
    error: lightbulb.CommandErrorEvent, context: lightbulb.Context
) -> bool | None:
    """Handles command errors thrown by the bot.

    Arguments:
        error: The error to handle.

    Returns:
        True if the exception can be handled, false if not.
    """
    if evaluate_exception(error, lightbulb.CommandNotFound):
        return True

    elif evaluate_exception(error, lightbulb.OnlyInGuild):
        await error_response(context, "You cannot use this command in DMs.")
        return True

    raise error


@plugin.listener(hikari.StartingEvent)
async def open_database_connection(event: hikari.StartingEvent) -> None:
    """Connect to MongoDB when the bot starts up."""
    connect_database(plugin.bot)


@plugin.listener(hikari.StoppingEvent)
async def close_database_connection(event: hikari.StoppingEvent) -> None:
    """Disconnect from MongoDB when the bot stops."""
    disconnect_database(plugin.bot)


@plugin.listener(lightbulb.CommandErrorEvent)
async def on_command_error(event: lightbulb.CommandErrorEvent) -> bool | None:
    """Handle errors when a command fails."""
    return await handle_error(event.exception, event.context)


def load(bot: lightbulb.BotApp) -> None:
    """Loads the admin plugin."""
    bot.add_plugin(plugin)
