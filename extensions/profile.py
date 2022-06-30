import hikari
import lightbulb
import utils

plugin = lightbulb.Plugin("Profile")


async def get_reputation(member_id: hikari.Snowflake) -> tuple:
    """Gets a members reputation from the database.

    Tries to pull the members reputation document from the database. If there is a
    document, return the members reputation. Otherwise, return 0.

    Arguments:
        member_id: The ID of the member whos member to get.

    Returns:
        The members reputation.
    """
    document = await plugin.bot.d.db_conn.reputations.find_one({"member_id": member_id})

    if document is None:
        return (0, 0)
    else:
        upvotes = len(document.get("upvotes", []))
        downvotes = len(document.get("downvotes", []))
        return (upvotes, downvotes)


@plugin.command
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.option(
    "member",
    "The member to see the profile of",
    type=hikari.OptionType.USER,
    required=False,
)
@lightbulb.command("profile", "Displays information about the member")
@lightbulb.implements(lightbulb.SlashCommand)
async def profile(ctx: lightbulb.SlashContext) -> None:
    """Displays a members profile in the guild.

    Called when a member uses /profile [member].

    Arguments:
        ctx: The context for the command.

    Returns:
        None.
    """
    bot_avatar_url = plugin.bot.get_me().avatar_url
    member = ctx.options.member or ctx.member
    member_full_name = f"{member.username}#{member.discriminator}"
    member_joined = member.joined_at.strftime("%b %d, %Y")
    member_created = member.created_at.strftime("%b %d, %Y")
    member_upvotes, member_downvotes = await get_reputation(member.id)
    member_reputation = member_upvotes - member_downvotes

    if member_reputation > 0:
        member_reputation = f"+{member_reputation}"
    elif member_reputation == 0:
        member_reputation = "-"

    profile_embed = utils.create_info_embed(
        f"{member_full_name}'s Profile",
        f"Here are some details about `{member_full_name}`",
        bot_avatar_url,
    )

    profile_embed.set_thumbnail(member.avatar_url or member.default_avatar_url)
    profile_embed.add_field("User ID", member.id, inline=True)
    profile_embed.add_field("Joined at", member_joined, inline=True)
    profile_embed.add_field("Created at", member_created, inline=True)
    profile_embed.add_field("Global Reputation", f"{member_reputation}", inline=True)
    profile_embed.add_field("Total Upvotes", f"{member_upvotes}", inline=True)
    profile_embed.add_field("Total Downvotes", f"{member_downvotes}", inline=True)

    await ctx.respond(embed=profile_embed)


def load(bot: lightbulb.BotApp) -> None:
    """Loads the 'Profile' plugin. Called when extension is loaded.

    Arguments:
        bot: The bot application to add the plugin to.

    Returns:
        None.
    """
    bot.add_plugin(plugin)
