import hikari
import lightbulb

from bot import config
from motor.motor_asyncio import AsyncIOMotorClient

plugin = lightbulb.Plugin("Admin")


@plugin.listener(hikari.StartingEvent)
async def open_database_connection(event: hikari.StartingEvent) -> None:
    """Create a database connection when the bot is starting.

    Arguments:
        event: The event that was fired. (StartingEvent)

    Returns:
        None.
    """
    plugin.bot.database_client = AsyncIOMotorClient(
        config.get("DEVELOPMENT", "DATABASE_URI")
    )
    plugin.bot.database = plugin.bot.database_client["campfire"]


@plugin.listener(hikari.StoppingEvent)
async def close_database_connection(event: hikari.StoppingEvent) -> None:
    """Close the database connection when the bot stops.

    Arguments:
        event: The event that was fired. (StoppingEvent)

    Returns:
        None.
    """
    plugin.bot.database_client.close()


def load(bot: lightbulb.BotApp) -> None:
    """Loads the 'Admin' plugin. Called when extension is loaded.

    Arguments:
        bot: The bot application to add the plugin to.

    Returns:
        None.
    """
    bot.add_plugin(plugin)
