import hikari
import lightbulb
import utils

plugin = lightbulb.Plugin('Profile')


async def get_reputation(
    member_id: hikari.Snowflake,
    guild_id: hikari.Snowflake
) -> int:
    '''Gets a members reputation from the database.

    Tries to pull the members reputation document from the database. If there 
    is a document, return the members reputation. Otherwise, return 0

    Arguments:
        member_id: The ID of the member to get the reputation
        guild_id: The ID of the guild for the member to get the reputation in

    Returns:
        The members reputation.
    '''
    document = await plugin.bot.database.reputations.find_one(
        {
            'member_id': member_id,
            'guild_id': guild_id
        }
    )

    if document is None:
        return 0
    else:
        return document['reputation']


@plugin.command
@lightbulb.option(
    'member',
    'The member to see the profile of',
    type=hikari.Member,
    required=False
)
@lightbulb.command('profile', 'Displays information about the member')
@lightbulb.implements(lightbulb.SlashCommand)
async def profile(ctx: lightbulb.SlashContext) -> None:
    '''Displays a members profile in the guild.

    Called when a member uses /profile [member].

    Arguments:
        ctx: The context for the command.

    Returns:
        None.
    '''
    member = ctx.options.member or ctx.member
    member_full_name = f'{member.username}#{member.discriminator}'
    member_joined = member.joined_at.strftime('%b %d, %Y')
    member_created = member.created_at.strftime('%b %d, %Y')
    member_reputation = await get_reputation(member.id, ctx.guild_id)
    bot_avatar_url = plugin.bot.get_me().avatar_url

    embed = utils.create_info_embed(
        f'{member_full_name}\'s Profile',
        f'Here are some details about `{member_full_name}`',
        bot_avatar_url,
        timestamp=True
    )

    embed.set_thumbnail(member.avatar_url or member.default_avatar_url)
    embed.add_field('User ID', member.id, inline=True)
    embed.add_field('Joined at', member_joined, inline=True)
    embed.add_field('Created at', member_created, inline=True)
    embed.add_field('Reputation', f'{member_reputation} points', inline=True)

    await ctx.respond(embed=embed)


def load(bot: lightbulb.BotApp) -> None:
    '''Loads the 'Profile' plugin. Called when extension is loaded.

    Arguments:
        bot: The bot application to add the plugin to.

    Returns:
        None.
    '''
    bot.add_plugin(plugin)
