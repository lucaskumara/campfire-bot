import hikari
import lightbulb
import typing

from utils.responses import create_info_embed


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


def get_reputation_string(upvotes: int, downvotes: int) -> str:
    """Takes upvotes and downvotes to return reputation as a formatted string.

    Arguments:
        upvotes: The number of upvotes.
        downvotes: The number of downvotes.

    Returns:
        The formatted string.
    """
    reputation = upvotes - downvotes

    if reputation > 0:
        reputation = "+" + str(reputation)
    elif reputation < 0:
        reputation = str(reputation)
    else:
        reputation = "-"

    return reputation


async def extract_member_details(member: hikari.Member) -> dict:
    """Pull all data about a member from the database.

    Arguments:
        member: The member to get the information of.

    Returns:
        A dictionary of the members information.
    """
    upvotes, downvotes = await get_reputation(member.id)
    data = {
        "name": f"{member.username}#{member.discriminator}",
        "joined": member.joined_at.strftime("%b %d, %Y"),
        "created": member.created_at.strftime("%b %d, %Y"),
        "upvotes": upvotes,
        "downvotes": downvotes,
    }

    return data


@plugin.command
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.option(
    "member",
    "The member to see the profile of",
    type=hikari.Member,
    required=False,
)
@lightbulb.command("profile", "Displays information about the member")
@lightbulb.implements(lightbulb.SlashCommand, lightbulb.PrefixCommand)
async def profile(
    context: typing.Union[lightbulb.SlashContext, lightbulb.PrefixContext]
) -> None:
    """Displays a members profile in the guild.

    Arguments:
        context: The context for the command.

    Returns:
        None.
    """
    target = context.options.member or context.member
    target_data = await extract_member_details(target)
    target_reputation = get_reputation_string(
        target_data["upvotes"], target_data["downvotes"]
    )

    profile_embed = create_info_embed(
        f"{target_data['name']}'s Profile",
        f"Here are some details about `{target_data['name']}`",
        context.app.get_me().avatar_url,
    )

    profile_embed.set_thumbnail(target.avatar_url or target.default_avatar_url)
    profile_embed.add_field("User ID", target.id, inline=True)
    profile_embed.add_field("Joined at", target_data["joined"], inline=True)
    profile_embed.add_field("Created at", target_data["created"], inline=True)
    profile_embed.add_field("Global Reputation", target_reputation, inline=True)
    profile_embed.add_field("Total Upvotes", target_data["upvotes"], inline=True)
    profile_embed.add_field("Total Downvotes", target_data["downvotes"], inline=True)

    await context.respond(embed=profile_embed)


def load(bot: lightbulb.BotApp) -> None:
    """Loads the 'Profile' plugin. Called when extension is loaded.

    Arguments:
        bot: The bot application to add the plugin to.

    Returns:
        None.
    """
    bot.add_plugin(plugin)
