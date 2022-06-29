import hikari
import lightbulb
import utils

plugin = lightbulb.Plugin("Reputation")


async def get_upvotes(target_id: hikari.Snowflake) -> list:
    """Gets a list of IDs for users who have upvoted the target."""
    document = await plugin.bot.d.db_conn.reputations.find_one({"member_id": target_id})
    return document.get("upvotes", []) if document is not None else []


async def get_downvotes(target_id: hikari.Snowflake) -> list:
    """Gets a list of IDs for users who have downvoted the target."""
    document = await plugin.bot.d.db_conn.reputations.find_one({"member_id": target_id})
    return document.get("downvotes", []) if document is not None else []


async def upvote_member(
    voter_id: hikari.Snowflake, target_id: hikari.Snowflake
) -> None:
    """Updates the database to show that the voter has upvoted the target.

    Pulls the voter ID from the array of IDs for users who have downvoted the target and
    pushes it to the array of users who have upvoted.

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


@lightbulb.Check
def check_target_is_not_author(ctx: lightbulb.SlashContext) -> bool:
    """A check to ensure that the target member is not the command author.

    Arguments:
        ctx: The context for the command.

    Returns:
        True if check passes, false if not.
    """
    return ctx.member.id != ctx.options.member.id


@plugin.command
@lightbulb.add_checks(check_target_is_not_author, lightbulb.guild_only)
@lightbulb.option("member", "The member to upvote", type=hikari.OptionType.USER)
@lightbulb.command("upvote", "Upvotes a member")
@lightbulb.implements(lightbulb.SlashCommand)
async def upvote(ctx: lightbulb.SlashContext) -> None:
    """Upvotes a member.

    Called when a member uses /upvote [member].

    Arguments:
        ctx: The context for the command.

    Returns:
        None.
    """
    bot_avatar_url = plugin.bot.get_me().avatar_url
    voter_member = ctx.member
    target_member = ctx.options.member
    target_member_upvotes = await get_upvotes(target_member.id)

    # Check if target has already been upvoted by the author
    if voter_member.id in target_member_upvotes:
        error_embed = utils.create_error_embed(
            "You have already upvoted that member", bot_avatar_url
        )
        await ctx.respond(embed=error_embed, delete_after=utils.DELETE_ERROR_DELAY)
        return

    upvote_embed = utils.create_info_embed(
        "Member upvoted", f"You have upvoted {target_member.mention}", bot_avatar_url
    )

    await upvote_member(voter_member.id, target_member.id)
    await ctx.respond(embed=upvote_embed)


@plugin.command
@lightbulb.add_checks(check_target_is_not_author, lightbulb.guild_only)
@lightbulb.option("member", "The member to downvote", type=hikari.OptionType.USER)
@lightbulb.command("downvote", "Downvotes a member")
@lightbulb.implements(lightbulb.SlashCommand)
async def downvote(ctx: lightbulb.SlashContext) -> None:
    """Downvotes a member.

    Called when a member uses /downvote [member].

    Arguments:
        ctx: The context for the command.

    Returns:
        None.
    """
    bot_avatar_url = plugin.bot.get_me().avatar_url
    voter_member = ctx.member
    target_member = ctx.options.member
    target_member_downvotes = await get_downvotes(target_member.id)

    # Check if target has already been downvoted by the author
    if voter_member.id in target_member_downvotes:
        error_embed = utils.create_error_embed(
            "You have already downvoted that member", bot_avatar_url
        )
        await ctx.respond(embed=error_embed, delete_after=utils.DELETE_ERROR_DELAY)
        return

    downvote_embed = utils.create_info_embed(
        "Member downvoted",
        f"You have downvoted {target_member.mention}",
        bot_avatar_url,
    )

    await downvote_member(voter_member.id, target_member.id)
    await ctx.respond(embed=downvote_embed)


@upvote.set_error_handler()
@downvote.set_error_handler()
async def voting_errors(event: lightbulb.CommandErrorEvent) -> bool:
    """Handles errors for the upvote and downvote commands.

    Arguments:
        event: The event that was fired.

    Returns:
        True if the exception can be handled, false if not.
    """
    bot_avatar_url = plugin.bot.get_me().avatar_url
    exception = event.exception

    if utils.evaluate_exception(exception, lightbulb.OnlyInGuild):
        return False

    elif utils.evaluate_exception(exception, lightbulb.CheckFailure):
        error_embed = utils.create_error_embed(
            "You cannot vote for yourself.", bot_avatar_url
        )
        await event.context.respond(
            embed=error_embed,
            delete_after=utils.DELETE_ERROR_DELAY,
        )
        return True

    return False


def load(bot: lightbulb.BotApp) -> None:
    """Loads the 'Reputation' plugin. Called when extension is loaded.

    Arguments:
        bot: The bot application to add the plugin to.

    Returns:
        None.
    """
    bot.add_plugin(plugin)
