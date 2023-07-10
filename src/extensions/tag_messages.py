import hikari
import lightbulb

from lib import responses, tags
from lightbulb.utils import permissions


plugin = lightbulb.Plugin("Tags")


@plugin.listener(hikari.StartedEvent)
async def remove_old_tag_data(event: hikari.StartedEvent) -> None:
    """Removes all tag data from guilds that the bot is no longer in when the bot starts.

    Arguments:
        event: The event object.

    Returns:
        None.
    """
    collection = plugin.bot.d.mongo_database.tags
    cursor = await collection.distinct("guild_id")

    for guild_id in cursor:
        try:
            await plugin.bot.rest.fetch_guild(int(guild_id))
        except:
            await tags.delete_all_tags(collection, guild_id)


@plugin.listener(hikari.GuildLeaveEvent)
async def remove_all_guild_tag_data(event: hikari.GuildLeaveEvent) -> None:
    """Delete all tag data from a guild when the bot leaves it.

    Arguments:
        tag_guild: The guild of the tag.

    Returns:
        None.
    """
    collection = plugin.bot.d.mongo_database.tags

    await tags.delete_all_tags(collection, event.get_guild().id)


@plugin.command
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command("tag", "Base of tag command group")
@lightbulb.implements(lightbulb.SlashCommandGroup, lightbulb.PrefixCommandGroup)
async def tag(context: lightbulb.SlashContext | lightbulb.PrefixContext) -> None:
    """The tag base command.

    Arguments:
        context: The command context.

    Returns:
        None.
    """
    pass


@tag.child
@lightbulb.option("name", "The name of the tag")
@lightbulb.command("show", "Shows the content of a tag", inherit_checks=True)
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def show(context: lightbulb.SlashContext | lightbulb.PrefixContext) -> None:
    """The tag show subcommand.

    Arguments:
        context: The command context.

    Returns:
        None.
    """
    collection = plugin.bot.d.mongo_database.tags
    tag_name = context.options.name
    tag_guild = context.get_guild()

    tag = await tags.get_tag(collection, tag_name, tag_guild.id)

    if tag is None:
        await responses.error(context, "That tag does not exist.")
        return

    await tags.increment_tag(collection, tag_name, tag_guild.id)
    await context.respond(tag.content)


@tag.child
@lightbulb.option("content", "The content of the tag")
@lightbulb.option("name", "The name of the tag")
@lightbulb.command("create", "Creates a new tag", inherit_checks=True)
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def create(context: lightbulb.SlashContext | lightbulb.PrefixContext) -> None:
    """The tag create subcommand.

    Arguments:
        context: The command context.

    Returns:
        None.
    """
    collection = plugin.bot.d.mongo_database.tags
    tag_name = context.options.name
    tag_content = context.options.content
    tag_guild = context.get_guild()
    tag_author = context.author

    tag = await tags.get_tag(collection, tag_name, tag_guild.id)

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

    await tags.create_tag(
        collection, tag_name, tag_content, tag_guild.id, tag_author.id
    )
    await responses.info(
        context,
        "Tag created",
        f"Your tag has been successfully created. \nUse `/tag show {tag_name}` to view it.",
    )


@tag.child
@lightbulb.option("content", "The content of the tag")
@lightbulb.option("name", "The name of the tag")
@lightbulb.command("edit", "Edits an existing tag", inherit_checks=True)
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def edit(context: lightbulb.SlashContext | lightbulb.PrefixContext) -> None:
    """The tag edit subcommand.

    Arguments:
        context: The command context.

    Returns:
        None.
    """
    collection = plugin.bot.d.mongo_database.tags
    tag_name = context.options.name
    tag_content = context.options.content
    tag_guild = context.get_guild()
    tag_editor = context.author

    tag = await tags.get_tag(collection, tag_name, tag_guild.id)

    if tag is None:
        await responses.error(context, "That tag does not exist.")
        return

    if tag_editor.id != tag.author_id:
        await responses.error(context, "You don't have permission to edit that tag.")
        return

    await tags.edit_tag(collection, tag_name, tag_content, tag_guild.id)
    await responses.info(
        context,
        "Tag edited",
        f"The tag `{tag_name}` has been successfully updated.",
    )


@tag.child
@lightbulb.option("name", "The name of the tag")
@lightbulb.command("delete", "Deletes an existing tag", inherit_checks=True)
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def delete(context: lightbulb.SlashContext | lightbulb.PrefixContext) -> None:
    """The tag delete subcommand.

    Arguments:
        context: The command context.

    Returns:
        None.
    """
    collection = plugin.bot.d.mongo_database.tags
    tag_name = context.options.name
    tag_guild = context.get_guild()
    tag_deleter = tag_guild.get_member(context.author.id)

    tag = await tags.get_tag(collection, tag_name, tag_guild.id)

    if tag is None:
        await responses.error(context, "That tag does not exist.")
        return

    if (
        tag_deleter.id != tag.author_id
        and not permissions.permissions_for(tag_deleter)
        & hikari.Permissions.MANAGE_MESSAGES
    ):
        await responses.error(context, "You don't have permission to delete that tag.")
        return

    await tags.delete_tag(collection, tag_name, tag_guild.id)
    await responses.info(
        context,
        "Tag deleted",
        f"The tag `{tag_name}` has been successfully deleted.",
    )


@tag.child
@lightbulb.option("name", "The name of the tag")
@lightbulb.command("info", "Shows info about an existing tag", inherit_checks=True)
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def info(context: lightbulb.SlashContext | lightbulb.PrefixContext) -> None:
    """The tag info subcommand.

    Arguments:
        context: The command context.

    Returns:
        None.
    """
    collection = plugin.bot.d.mongo_database.tags
    tag_name = context.options.name
    tag_guild = context.get_guild()

    tag = await tags.get_tag(collection, tag_name, tag_guild.id)

    if tag is None:
        await responses.error(context, "That tag does not exist.")
        return

    embed = responses.build_embed(
        "Tag info",
        f"Use `/tag show {tag_name}` to view its contents.",
        plugin.bot.get_me().avatar_url,
        responses.INFO_MESSAGE_COLOUR,
        [
            responses.Field("Name", tag.name, True),
            responses.Field("Author", f"<@{tag.author_id}>", True),
            responses.Field("Uses", tag.uses, True),
            responses.Field("Created at", tag.created_date, True),
            responses.Field("Modified at", tag.modified_date, True),
        ],
    )

    await context.respond(embed=embed)


@tag.child
@lightbulb.option(
    "member", "The owner of the tags to view", type=hikari.Member, required=False
)
@lightbulb.command("list", "Lists all server tags", inherit_checks=True)
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def list(context: lightbulb.SlashContext | lightbulb.PrefixContext) -> None:
    """The tag list subcommand.

    Arguments:
        context: The command context.

    Returns:
        None.
    """
    collection = plugin.bot.d.mongo_database.tags
    tag_guild = context.get_guild()
    tag_author = context.options.member

    if tag_author is not None:
        tag_list = await tags.get_tags_by_author(
            collection, tag_guild.id, tag_author.id
        )
    else:
        tag_list = await tags.get_tags(collection, tag_guild.id)

    tag_list_size = len(tag_list)

    if tag_list_size == 0:
        await responses.error(context, "There are no tags to show.")
        return

    await responses.paginated_info(
        context,
        "Tag list",
        f"There are {tag_list_size} tags. Use `/tag show [tag]` to view its contents.",
        [f"• {tag.name}" for tag in tag_list],
    )


def load(bot: lightbulb.BotApp) -> None:
    """Loads the tags plugin.

    Arguments:
        bot: The bot instance.

    Returns:
        None.
    """
    bot.add_plugin(plugin)
