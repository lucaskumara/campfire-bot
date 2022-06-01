import hikari
import lightbulb
import utils

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


@lightbulb.Check
def check_target_is_not_author(ctx: lightbulb.SlashContext) -> bool:
    '''A simple check to ensure that specified member is not the author.

    Arguments:
        ctx: The context for the command.

    Returns:
        True if check passes, false if not.
    '''
    return ctx.member.id != ctx.options.member.id


@plugin.command
@lightbulb.add_checks(check_target_is_not_author)
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
    target_member = ctx.options.member
    bot_avatar_url = plugin.bot.get_me().avatar_url

    await give_reputation(target_member.id, ctx.guild_id)
    await ctx.respond(
        embed=utils.create_info_embed(
            'Reputation given',
            ('You have given a point of reputation to '
             f'`{target_member.username}`'),
            bot_avatar_url,
            timestamp=True
        )
    )


@reputation.set_error_handler()
async def reputation_errors(event: lightbulb.CommandErrorEvent) -> bool:
    '''Handles errors for the reputation command.

    Arguments:
        event: The event that was fired. (CommandErrorEvent)

    Returns:
        True if the exception can be handled, false if not.
    '''
    exception = event.exception
    bot_avatar_url = plugin.bot.get_me().avatar_url

    if isinstance(exception, lightbulb.CommandIsOnCooldown):
        await event.context.respond(
            embed=utils.create_error_embed(
                f'Try again in `{int(exception.retry_after)}` seconds.',
                bot_avatar_url,
                timestamp=True
            ),
            delete_after=utils.DELETE_ERROR_DELAY
        )
        return True

    elif isinstance(exception, lightbulb.CheckFailure):
        await event.context.respond(
            embed=utils.create_error_embed(
                'You can not give yourself reputation.',
                bot_avatar_url,
                timestamp=True
            ),
            delete_after=utils.DELETE_ERROR_DELAY
        )
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