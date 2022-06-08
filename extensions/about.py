import lightbulb
import utils

plugin = lightbulb.Plugin("About")


@plugin.command
@lightbulb.command("about", "Displays info about the bot")
@lightbulb.implements(lightbulb.SlashCommand)
async def about(ctx: lightbulb.SlashContext) -> None:
    """Sends a message containing bot information to the server.

    Called when a user uses /about

    Arguments:
        ctx: The context for the command.

    Returns:
        None.
    """
    message = (
        "Campfire is a utility discord bot that began development in "
        "November 2021. The goal of the project was to provide users "
        "with an expanded set of features available to them when using "
        "a discord server.\n\n"
    )
    links = "**Donate**: https://ko-fi.com/campfire\n" "**Support server**: COMING SOON"
    bot_avatar_url = plugin.bot.get_me().avatar_url
    about_embed = utils.create_info_embed(
        "About Campfire", message + links, bot_avatar_url
    )

    await ctx.respond(embed=about_embed)


def load(bot: lightbulb.BotApp) -> None:
    """Loads the 'Info' plugin. Called when extension is loaded.

    Arguments:
        bot: The bot application to add the plugin to.

    Returns:
        None.
    """
    bot.add_plugin(plugin)
