import hikari
import lightbulb
import typing

from utils.responses import info_response, error_response


plugin = lightbulb.Plugin("Reputation")


async def get_upvotes(target_id: hikari.Snowflake) -> list:
    """Gets a list of IDs for users who have upvoted the target.

    Arguments:
        target_id: The ID of the user to get the upvotes of.

    Returns:
        The list of member IDs that upvoted the target.
    """
    document = await plugin.bot.d.db_conn.reputations.find_one({"member_id": target_id})

    return document.get("upvotes", []) if document is not None else []


async def get_downvotes(target_id: hikari.Snowflake) -> list:
    """Gets a list of IDs for users who have downvoted the target.

    Arguments:
        target_id: The ID of the user to get the downvotes of.

    Returns:
        The list of member IDs that downvoted the target.
    """
    document = await plugin.bot.d.db_conn.reputations.find_one({"member_id": target_id})

    return document.get("downvotes", []) if document is not None else []


async def upvote_member(
    voter_id: hikari.Snowflake, target_id: hikari.Snowflake
) -> None:
    """Updates the database to show that the voter has upvoted the target.

    Pulls the voter ID from the array of IDs for users who have downvoted the target
    and pushes it to the array of users who have upvoted.

    Arguments:
        voter_id: The ID of the voting users.
        target_id: The ID of the user getting upvoted.

    Returns:
        None.
    """
    plugin.bot.d.db_conn.reputations.update_one(
        {"member_id": target_id},
        {"$pull": {"downvotes": voter_id}},
    )

    plugin.bot.d.db_conn.reputations.update_one(
        {"member_id": target_id},
        {"$push": {"upvotes": voter_id}},
        upsert=True,
    )


async def downvote_member(
    voter_id: hikari.Snowflake, target_id: hikari.Snowflake
) -> None:
    """Updates the database to show that the voter has downvoted the target.

    Pulls the voter ID from the array of IDs for users who have upvoted the target and
    pushes it to the array of users who have downvoted.

    Arguments:
        voter_id: The ID of the voting user.
        target_id: The ID of the user getting downvoted.

    Returns:
        None.
    """
    plugin.bot.d.db_conn.reputations.update_one(
        {"member_id": target_id},
        {"$pull": {"upvotes": voter_id}},
    )

    plugin.bot.d.db_conn.reputations.update_one(
        {"member_id": target_id},
        {"$push": {"downvotes": voter_id}},
        upsert=True,
    )


@plugin.command
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.option("member", "The member to upvote", type=hikari.Member)
@lightbulb.command("upvote", "Upvotes a member")
@lightbulb.implements(lightbulb.SlashCommand, lightbulb.PrefixCommand)
async def upvote(
    context: typing.Union[lightbulb.SlashContext, lightbulb.PrefixContext]
) -> None:
    """Upvotes a member.

    Arguments:
        context: The context for the command.

    Returns:
        None.
    """
    voter_member = context.member
    target_member = context.options.member

    # Check if the target is the author
    if voter_member.id == target_member.id:
        await error_response(context, "You cannot vote for yourself.")
        return

    # Check if the target has already been upvoted by the author
    if voter_member.id in await get_upvotes(target_member.id):
        await error_response(context, "You have already upvoted that member.")
        return

    await upvote_member(voter_member.id, target_member.id)
    await info_response(
        context, "Member upvoted", f"You have upvoted {target_member.mention}"
    )


@plugin.command
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.option("member", "The member to downvote", type=hikari.Member)
@lightbulb.command("downvote", "Downvotes a member")
@lightbulb.implements(lightbulb.SlashCommand, lightbulb.PrefixCommand)
async def downvote(
    context: typing.Union[lightbulb.SlashContext, lightbulb.PrefixContext]
) -> None:
    """Downvotes a member.

    Arguments:
        context: The context for the command.

    Returns:
        None.
    """
    voter_member = context.member
    target_member = context.options.member

    # Check if the target is the author
    if voter_member.id == target_member.id:
        await error_response(context, "You cannot vote for yourself.")
        return

    # Check if the target has already been downvoted by the author
    if voter_member.id in await get_downvotes(target_member.id):
        await error_response(context, "You have already downvoted that member.")
        return

    await downvote_member(voter_member.id, target_member.id)
    await info_response(
        context, "Member downvoted", f"You have downvoted {target_member.mention}"
    )


def load(bot: lightbulb.BotApp) -> None:
    """Loads the 'Reputation' plugin. Called when extension is loaded.

    Arguments:
        bot: The bot application to add the plugin to.

    Returns:
        None.
    """
    bot.add_plugin(plugin)
