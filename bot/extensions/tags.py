import hikari
import lightbulb

import lib.tags as tags
import lib.responses as responses

from lightbulb.utils.permissions import permissions_for

plugin = lightbulb.Plugin("Tags")


async def purge_old_guilds() -> None:
    """Delete all tags from guilds that the bot is no longer in.

    Returns:
        None.
    """
    collection = plugin.bot.d.mongo_database.tags
    cursor = await collection.distinct("guild_id")

    for guild_id in cursor:
        try:
            await plugin.bot.rest.fetch_guild(int(guild_id))
        except:
            await tags.delete_all_tags(plugin.bot, guild_id)


async def purge_guild(tag_guild: hikari.Guild) -> None:
    """Delete all tags from a guild.

    Arguments:
        tag_guild: The guild of the tag.

    Returns:
        None.
    """
    await tags.delete_all_tags({"guild_id": str(tag_guild.id)})


async def show_tag(
    context: lightbulb.SlashContext | lightbulb.PrefixContext,
    tag_name: str,
    tag_guild: hikari.Guild,
) -> None:
    """Display tag content.

    Arguments:
        context: The command context.
        tag_name: The name of the tag.
        tag_guild: The guild of the tag.

    Returns:
        None.
    """
    tag = await tags.get_tag(plugin.bot, tag_name, tag_guild)

    if tag is None:
        await responses.error(context, "That tag does not exist.")
        return

    await tags.increment_tag(plugin.bot, tag_name, tag_guild)
    await context.respond(tag.get_content())


async def create_tag(
    context: lightbulb.SlashContext | lightbulb.PrefixContext,
    tag_name: str,
    tag_content: str,
    tag_guild: hikari.Guild,
    tag_author: hikari.User,
) -> None:
    """Creates a new tag.

    Arguments:
        context: The command context.
        tag_name: The name of the tag.
        tag_content: The content of the tag.
        tag_guild: The guild of the tag.
        tag_author: The author of the tag.

    Returns:
        None.
    """
    tag = await tags.get_tag(plugin.bot, tag_name, tag_guild)

    if tag is not None:
        await responses.error(context, "That tag already exists.")
        return

    if len(tag_name) > 54:
        await responses.error(
            context, "The tag name must be less than 54 characters long."
        )
        return

    if len(tag_content) > 2000:
        await responses.error(
            context, "The tag content must be less than 2000 characters long."
        )
        return

    await tags.create_tag(plugin.bot, tag_name, tag_content, tag_guild, tag_author)
    await responses.info(
        context,
        "Tag created",
        f"Your tag has been successfully created. \nUse `/tag show {tag_name}` to view it.",
    )


async def edit_tag(
    context: lightbulb.SlashContext | lightbulb.PrefixContext,
    tag_name: str,
    tag_content: str,
    tag_guild: hikari.Guild,
    tag_editor: hikari.User,
) -> None:
    """Edits a tag.

    Arguments:
        context: The command context.
        tag_name: The name of the tag.
        tag_content: The content of the tag.
        tag_guild: The guild of the tag.
        tag_editor: The user making the edit.

    Returns:
        None.
    """
    tag = await tags.get_tag(plugin.bot, tag_name, tag_guild)

    if tag is None:
        await responses.error(context, "That tag does not exist.")
        return

    if tag_editor != await tag.get_author():
        await responses.error(context, "You don't have permission to edit that tag.")
        return

    await tags.edit_tag(plugin.bot, tag_name, tag_content, tag_guild)
    await responses.info(
        context, "Tag edited", f"The tag `{tag_name}` has been successfully updated."
    )


async def delete_tag(
    context: lightbulb.SlashContext | lightbulb.PrefixContext,
    tag_name: str,
    tag_guild: hikari.Guild,
    tag_deleter: hikari.User,
) -> None:
    """Deletes a tag.

    Arguments:
        context: The command context.
        tag_name: The name of the tag.
        tag_guild: The guild of the tag.
        tag_deleted: The user deleting the tag.

    Returns:
        None.
    """
    tag = await tags.get_tag(plugin.bot, tag_name, tag_guild)

    if tag is None:
        await responses.error(context, "That tag does not exist.")
        return

    if (
        tag_deleter != await tag.get_author()
        or not permissions_for(tag_deleter) & hikari.Permissions.MANAGE_MESSAGES
    ):
        await responses.error(context, "You don't have permission to delete that tag.")
        return

    await tags.delete_tag(plugin.bot, tag_name, tag_guild)
    await responses.info(
        context, "Tag deleted", f"The tag `{tag_name}` has been successfully deleted."
    )


async def info_tag(
    context: lightbulb.SlashContext | lightbulb.PrefixContext,
    tag_name: str,
    tag_guild: hikari.Guild,
) -> None:
    """Retrieves tag information.

    Arguments:
        context: The command context.
        tag_name: The name of the tag.
        tag_guild: The guild of the tag.

    Returns:
        None.
    """
    tag = await tags.get_tag(plugin.bot, tag_name, tag_guild)

    if tag is None:
        await responses.error(context, "That tag does not exist.")
        return

    embed = await tag.info_embed(
        "Tag info",
        f"Use `/tag show {tag_name}` to view its contents.",
        plugin.bot.get_me().avatar_url,
    )

    await context.respond(embed=embed)


async def list_tags(
    context: lightbulb.SlashContext | lightbulb.PrefixContext,
    tag_guild: hikari.Guild,
    tag_author: hikari.User | None,
) -> None:
    """Lists all guild tags. If a user is specified, filters for tags authored by them.

    Arguments:
        context: The command context.
        tag_guild: The guild of the tags.
        tag_author: The author of the tags.

    Returns:
        None.
    """
    if tag_author is not None:
        tag_count = await tags.guild_tag_count_by_author(
            plugin.bot, tag_guild, tag_author
        )
    else:
        tag_count = await tags.guild_tag_count(plugin.bot, tag_guild)

    if tag_count == 0:
        await responses.error(context, "There are no tags to show.")
        return

    tag_list = await tags.get_tags(plugin.bot, tag_guild)
    tag_list_formatted = [f"• {tag.get_name()}" for tag in tag_list]

    await responses.paginated_info(
        context,
        "Tag list",
        f"There are {len(tag_list)} tags. Use `/tag show [tag]` to view its contents.",
        tag_list_formatted,
    )


@plugin.listener(hikari.StartedEvent)
async def purge_old_guilds_on_start(event: hikari.StartedEvent) -> None:
    """Remove unneeded data when the bot starts up."""
    await purge_old_guilds()


@plugin.listener(hikari.GuildLeaveEvent)
async def purge_guild_on_leave(event: hikari.GuildLeaveEvent) -> None:
    """Remove unneeded data when the bot leaves a guild."""
    await purge_guild(event.get_guild())


@plugin.command
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command("tag", "Base of tag command group")
@lightbulb.implements(lightbulb.SlashCommandGroup, lightbulb.PrefixCommandGroup)
async def tag(context: lightbulb.SlashContext | lightbulb.PrefixContext) -> None:
    """The tag base command."""
    pass


@tag.child
@lightbulb.option("name", "The name of the tag")
@lightbulb.command("show", "Shows the content of a tag", inherit_checks=True)
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def show(context: lightbulb.SlashContext | lightbulb.PrefixContext) -> None:
    """The tag show subcommand."""
    await show_tag(context, context.options.name, context.get_guild())


@tag.child
@lightbulb.option("content", "The content of the tag")
@lightbulb.option("name", "The name of the tag")
@lightbulb.command("create", "Creates a new tag", inherit_checks=True)
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def create(context: lightbulb.SlashContext | lightbulb.PrefixContext) -> None:
    """The tag create subcommand."""
    await create_tag(
        context,
        context.options.name,
        context.options.content,
        context.get_guild(),
        context.author,
    )


@tag.child
@lightbulb.option("content", "The content of the tag")
@lightbulb.option("name", "The name of the tag")
@lightbulb.command("edit", "Edits an existing tag", inherit_checks=True)
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def edit(context: lightbulb.SlashContext | lightbulb.PrefixContext) -> None:
    """The tag edit subcommand."""
    await edit_tag(
        context,
        context.options.name,
        context.options.content,
        context.get_guild(),
        context.author,
    )


@tag.child
@lightbulb.option("name", "The name of the tag")
@lightbulb.command("delete", "Deletes an existing tag", inherit_checks=True)
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def delete(context: lightbulb.SlashContext | lightbulb.PrefixContext) -> None:
    """The tag delete subcommand."""
    await delete_tag(context, context.options.name, context.get_guild(), context.author)


@tag.child
@lightbulb.option("name", "The name of the tag")
@lightbulb.command("info", "Shows info about an existing tag", inherit_checks=True)
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def info(context: lightbulb.SlashContext | lightbulb.PrefixContext) -> None:
    """The tag info subcommand."""
    await info_tag(context, context.options.name, context.get_guild())


@tag.child
@lightbulb.option(
    "member", "The owner of the tags to view", type=hikari.Member, required=False
)
@lightbulb.command("list", "Lists all server tags", inherit_checks=True)
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def list(context: lightbulb.SlashContext | lightbulb.PrefixContext) -> None:
    """The tag list subcommand."""
    await list_tags(context, context.get_guild(), context.options.member)


def load(bot: lightbulb.BotApp) -> None:
    """Loads the tags plugin."""
    bot.add_plugin(plugin)
