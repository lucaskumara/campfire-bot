import lightbulb
import utils

plugin = lightbulb.Plugin('Info')


@plugin.command
@lightbulb.command('info', 'Displays information about the bot')
@lightbulb.implements(lightbulb.SlashCommand)
async def info(ctx: lightbulb.SlashContext) -> None:
    '''Sends a message containing bot information to the server.

    Called when a user uses /info

    Arguments:
        ctx: The context for the command.

    Returns:
        None. 
    '''
    pass


def load(bot: lightbulb.BotApp) -> None:
    '''Loads the 'Info' plugin. Called when extension is loaded.

    Arguments:
        bot: The bot application to add the plugin to.

    Returns:
        None.
    '''
    bot.add_plugin(plugin)
