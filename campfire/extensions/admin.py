import hikari
import lightbulb
import typing
import os

from utils.exceptions import evaluate_exception
from utils.responses import error_response
from motor.motor_asyncio import AsyncIOMotorClient


plugin = lightbulb.Plugin("Admin")


@plugin.listener(hikari.StartingEvent)
async def open_database_connection(event: hikari.StartingEvent) -> None:
    """Create a database connection when the bot is starting.

    Arguments:
        event: The event that was fired.

    Returns:
        None.
    """
    plugin.bot.d.db_client = AsyncIOMotorClient(os.getenv("DATABASE_URI"))
    plugin.bot.d.db_conn = plugin.bot.d.db_client["campfire"]


@plugin.listener(hikari.StoppingEvent)
async def close_database_connection(event: hikari.StoppingEvent) -> None:
    """Close the database connection when the bot stops.

    Arguments:
        event: The event that was fired.

    Returns:
        None.
    """
    plugin.bot.d.db_client.close()


@plugin.listener(lightbulb.CommandErrorEvent)
async def on_command_error(event: lightbulb.CommandErrorEvent) -> typing.Optional[bool]:
    """Handles bot command errors if they aren't handled by plugin/command handlers.

    Arguments:
        event: The event that was fired.

    Returns:
        True if the exception can be handled, false if not.
    """
    exception = event.exception

    if evaluate_exception(exception, lightbulb.CommandNotFound):
        return True

    elif evaluate_exception(exception, lightbulb.OnlyInGuild):
        await error_response(event.context, "You cannot use this command in DMs.")
        return True

    raise exception


def load(bot: lightbulb.BotApp) -> None:
    """Loads the 'Admin' plugin. Called when extension is loaded.

    Arguments:
        bot: The bot application to add the plugin to.

    Returns:
        None.
    """
    bot.add_plugin(plugin)
