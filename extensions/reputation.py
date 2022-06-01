import hikari
import lightbulb

from lightbulb.buckets import GuildBucket

plugin = lightbulb.Plugin('Reputation')


async def give_reputation(
    member_id: hikari.Snowflake,
    guild_id: hikari.Snowflake
) -> None:
    '''Gives 1 reputation point to a member in a guild.

    Checks the database for existing reputation and increments it if possible.
    Otherwise, create a new document for the member in the guild with 1 
    reputation.

    Arguments:
        member_id: The ID of the member to get the reputation
        guild_id: The ID of the guild for the member to get the reputation in

    Returns:
        None.
    '''
    document = await plugin.bot.database.reputations.find_one(
        {
            'member_id': member_id,
            'guild_id': guild_id
        }
    )

    if document is None:
        await plugin.bot.database.reputations.insert_one(
            {
                'member_id': member_id,
                'guild_id': guild_id,
                'reputation': 1
            }
        )
    else:
        await plugin.bot.database.reputations.update_one(
            {
                'member_id': member_id,
                'guild_id': guild_id
            },
            {
                '$inc': {
                    'reputation': 1
                }
            }
        )


@plugin.command
@lightbulb.add_cooldown(600, 1, GuildBucket)
@lightbulb.option(
    'member',
    'The member to give reputation to',
    type=hikari.Member
)
@lightbulb.command('reputation', 'Grants a member a point of reputation')
@lightbulb.implements(lightbulb.SlashCommand)
async def reputation(ctx: lightbulb.SlashContext) -> None:
    '''Grants a member a point of reputation.

    Called when a member uses /reputation <member>.

    Arguments:
        ctx: The context for the command.

    Returns:
        None.
    '''
    author_member = ctx.member
    target_member = ctx.options.member

    if author_member.id == target_member.id:
        await ctx.respond('You cannot give yourself reputation.')
        return

    await give_reputation(target_member.id, ctx.guild_id)
    await ctx.respond(f'You have given a point of reputation to {int(target_member.username)}')


@reputation.set_error_handler()
async def reputation_errors(event: lightbulb.CommandErrorEvent) -> bool:
    '''Handles errors for the reputation command.

    Arguments:
        event: The event that was fired. (CommandErrorEvent)

    Returns:
        True if the exception can be handled, false if not.
    '''
    exception = event.exception

    if isinstance(exception, lightbulb.CommandIsOnCooldown):
        await event.context.respond(f'Try again in {exception.retry_after} seconds')
        return True

    return False


def load(bot: lightbulb.BotApp) -> None:
    '''Loads the 'Reputation' plugin. Called when extension is loaded.

    Arguments:
        bot: The bot application to add the plugin to.

    Returns:
        None.
    '''
    bot.add_plugin(plugin)
