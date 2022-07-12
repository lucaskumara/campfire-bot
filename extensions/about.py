import lightbulb
import typing

from utils.responses import info_response

plugin = lightbulb.Plugin("About")


@plugin.command
@lightbulb.command("about", "Displays info about the bot")
@lightbulb.implements(lightbulb.SlashCommand, lightbulb.PrefixCommand)
async def about(
    context: typing.Union[lightbulb.SlashContext, lightbulb.PrefixContext]
) -> None:
    """Sends a message containing bot information to the server.

    Arguments:
        ctx: The context for the command.

    Returns:
        None.
    """
    message = (
        "Campfire is a utility discord bot that began development in November 2021. "
        "The goal of the project was to provide users with an expanded set of features "
        "available to them when using a discord server.\n"
        "\n"
        "**Donate**: https://ko-fi.com/campfire\n"
        "**Support server**: COMING SOON"
    )

    await info_response(context, "About Campfire", message)


def load(bot: lightbulb.BotApp) -> None:
    """Loads the 'Info' plugin. Called when extension is loaded.

    Arguments:
        bot: The bot application to add the plugin to.

    Returns:
        None.
    """
    bot.add_plugin(plugin)
