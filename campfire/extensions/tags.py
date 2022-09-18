import hikari
import lightbulb
import typing

from utils.responses import create_info_embed, info_response, error_response
from datetime import datetime, timezone
from hikari.messages import ButtonStyle
from lightbulb.utils.permissions import permissions_for
from lightbulb.utils.pag import EmbedPaginator
from lightbulb.utils.nav import (
    ComponentButton as Button,
    ButtonNavigator,
    prev_page,
    next_page,
)


plugin = lightbulb.Plugin("Tags")


async def guild_has_tags(
    tag_author: typing.Optional[hikari.User],
    tag_guild: hikari.GatewayGuild,
) -> bool:
    """Checks if the guild has any tags in it.

    Query the database for any tags in the guild. If the tag author is not None, query
    the database for any tags in the guild made by the author. If the query gets at
    least one tag, the guild has tags.

    Arguments:
        tag_author: The author of the tags to search. Checks all tags if None.
        tag_guild: The guild of the tags to search.

    Returns:
        True if the query retrieved at least one document, false if otherwise.
    """
    if tag_author is None:
        cursor = plugin.bot.d.db_conn.tags.aggregate(
            [
                {"$match": {"guild_id": tag_guild.id}},
                {"$unwind": "$tags"},
                {"$limit": 1},
            ]
        )
    else:
        cursor = plugin.bot.d.db_conn.tags.aggregate(
            [
                {"$match": {"guild_id": tag_guild.id}},
                {"$unwind": "$tags"},
                {"$match": {"tags.author_id": tag_author.id}},
                {"$limit": 1},
            ]
        )

    documents = await cursor.to_list(length=1)

    return documents != []


async def paginate_all_tags(
    tag_author: typing.Optional[hikari.User], tag_guild: hikari.GatewayGuild
) -> EmbedPaginator:
    """Adds guild tags to the paginator.

    Creates an EmbedPaginator and adds formatted lines containing a list of tags in a
    guild to it. The queried tags depend on whether the author is None or not. If the
    author is none, query all tags for the guild, otherwise, query all tags for the
    guild that were written by the author.

    Arguments:
        tag_author: The author of all the tags to list. Lists all if None.
        tag_guild: The guild of all the tags to list.

    Returns:
        The constructed embed paginator.
    """
    paginator = EmbedPaginator(prefix="```", suffix="```", max_lines=10)

    @paginator.embed_factory()
    def build_embed(index, content):
        """Specify how embed paginator builds the embed"""
        embed = create_info_embed(
            "Tag list",
            f"Here is a list of tags. Use `/tag show [tag]` to view its contents. {content}",
            plugin.app.get_me().avatar_url,
        )
        embed.set_footer(f"Page {index}")

        return embed

    if tag_author is None:
        pipeline = [
            {"$match": {"guild_id": tag_guild.id}},
            {"$unwind": "$tags"},
        ]
    else:
        pipeline = [
            {"$match": {"guild_id": tag_guild.id}},
            {"$unwind": "$tags"},
            {"$match": {"tags.author_id": tag_author.id}},
        ]

    async for document in plugin.bot.d.db_conn.tags.aggregate(pipeline):
        tag_name = document["tags"]["name"]
        paginator.add_line(f"• {tag_name}")

    return paginator


async def get_tag(tag_name: str, tag_guild: hikari.GatewayGuild) -> dict:
    """Returns the retrived document of the tag in the guild.

    Query the database for a tag in the specified guild with the specified tag name. If
    a document is found, return the document itself from the list of queried documents.

    Arguments:
        tag_name: The name of the tag to find.
        tag_guild: The guild of the tag to find.

    Returns:
        The document of the tag if it exists, otherwise None.
    """
    cursor = plugin.bot.d.db_conn.tags.aggregate(
        [
            {"$match": {"guild_id": tag_guild.id}},
            {"$unwind": "$tags"},
            {"$match": {"tags.name": tag_name}},
            {"$limit": 1},
        ]
    )
    documents = await cursor.to_list(length=1)

    if documents != []:
        return documents[0]

    return None


async def create_tag(
    tag_name: str,
    tag_content: str,
    tag_author: hikari.User,
    tag_guild: hikari.GatewayGuild,
) -> None:
    """Creates a new tag in the guild.

    Pushes a new document with the specified tag name and content into the guild
    document tags list if it exists. Otherwise, create a guild document with the tags
    list containing the tag document.

    Arguments:
        tag_name: The name of the tag.
        tag_content: The content of the tag.
        tag_author: The author of the tag.
        tag_guild: The guild of the tag.

    Returns:
        None.
    """
    creation_time = datetime.now(timezone.utc).isoformat()

    await plugin.bot.d.db_conn.tags.update_one(
        {"guild_id": tag_guild.id},
        {
            "$push": {
                "tags": {
                    "name": tag_name,
                    "content": tag_content,
                    "author_id": tag_author.id,
                    "created_at": creation_time,
                    "modified_at": creation_time,
                    "uses": 0,
                }
            }
        },
        upsert=True,
    )


async def delete_tag(tag_name: str, tag_guild: hikari.GatewayGuild) -> None:
    """Deletes a tag in the guild.

    Pulls a document with the specified tag name from the guild document tags list.

    Arguments:
        tag_name: The name of the tag.
        tag_guild: The guild of the tag.

    Returns:
        None.
    """
    await plugin.bot.d.db_conn.tags.update_one(
        {"guild_id": tag_guild.id}, {"$pull": {"tags": {"name": tag_name}}}
    )


async def edit_tag(
    tag_name: str, tag_content: str, tag_guild: hikari.GatewayGuild
) -> None:
    """Edits a tag in the guild.

    Updates a document with the specified tag name from the guild document tags list to
    have the new specified tag content. Also updates the time the tag was last
    modified.

    Arguments:
        tag_name: The name of the tag to update.
        tag_content: The new contents of the tag.
        tag_guild: The guild of the tag to update.

    Returns:
        None.
    """
    edit_time = datetime.now(timezone.utc).isoformat()

    await plugin.bot.d.db_conn.tags.update_one(
        {"guild_id": tag_guild.id, "tags.name": tag_name},
        {"$set": {"tags.$.content": tag_content, "tags.$.modified_at": edit_time}},
    )


async def increment_tag(tag_name: str, tag_guild: hikari.GatewayGuild) -> None:
    """Increments the number of uses of a tag in a guild by one.

    Updates a document with the specified tag name from the guild document tags list by
    incrementing the uses of the tag has been used by 1.

    Arguments:
        tag_name: The name of the tag to increment.
        tag_guild: The guild of the tag to increment.

    Returns:
        None.
    """
    await plugin.bot.d.db_conn.tags.update_one(
        {"guild_id": tag_guild.id, "tags.name": tag_name}, {"$inc": {"tags.$.uses": 1}}
    )


async def extract_tag_details(tag_document: dict) -> dict:
    """Pull all data about a tag from a document.

    Arguments:
        tag_document: The tag to extract the information from.

    Returns:
        A dictionary of the tags information.
    """
    author_id = tag_document["tags"]["author_id"]

    created_at_iso = tag_document["tags"]["created_at"]
    created_at_str = datetime.fromisoformat(created_at_iso)
    created_at_formatted = created_at_str.strftime("%b %d, %Y")

    modified_at_iso = tag_document["tags"]["modified_at"]
    modified_at_str = datetime.fromisoformat(modified_at_iso)
    modified_at_formatted = modified_at_str.strftime("%b %d, %Y")

    data = {
        "author": await plugin.bot.rest.fetch_user(author_id),
        "uses": tag_document["tags"]["uses"],
        "created_at": created_at_formatted,
        "modified_at": modified_at_formatted,
    }

    return data


@plugin.listener(hikari.StartedEvent)
async def purge_guild_documents(event: hikari.StartedEvent) -> None:
    """Removes data of any guild the bot is no longer a part of.

    Arguments:
        event: The event that was fired.

    Returns:
        None.
    """
    tags_cursor = plugin.bot.d.db_conn.tags

    async for document in tags_cursor.find({}):
        guild_id = document["guild_id"]

        try:
            await plugin.bot.rest.fetch_guild(guild_id)
        except:
            await tags_cursor.delete_one({"guild_id": guild_id})


@plugin.listener(hikari.GuildLeaveEvent)
async def delete_guild_document(event: hikari.GuildLeaveEvent) -> None:
    """Deletes guild document from the database when the bot leaves a guild.

    Arguments:
        event: The event that was fired.

    Returns:
        None.
    """
    await plugin.bot.d.db_conn.tags.delete_one({"guild_id": event.guild_id})


@plugin.command
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command("tag", "Base of tag command group")
@lightbulb.implements(lightbulb.SlashCommandGroup, lightbulb.PrefixCommandGroup)
async def tag(
    context: typing.Union[lightbulb.SlashContext, lightbulb.PrefixContext]
) -> None:
    """Base of the tag command group.

    Arguments:
        context: The context for the command.

    Returns:
        None.
    """
    pass


@tag.child
@lightbulb.option("name", "The name of the tag")
@lightbulb.command("show", "Shows the content of a tag", inherit_checks=True)
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def show(
    context: typing.Union[lightbulb.SlashContext, lightbulb.PrefixContext]
) -> None:
    """Displays a tag in the guild.

    Called when a user uses /tag show <tag name>

    Arguments:
        context: The context for the command.

    Returns:
        None.
    """
    tag_name = context.options.name.lower()
    tag_guild = context.get_guild()
    document = await get_tag(tag_name, tag_guild)

    # Check if there is no existing tag
    if document is None:
        await error_response(context, "That tag does not exist.")
        return

    await increment_tag(tag_name, tag_guild)
    await context.respond(document["tags"]["content"])


@tag.child
@lightbulb.option("content", "The content of the tag")
@lightbulb.option("name", "The name of the tag")
@lightbulb.command("create", "Creates a new tag", inherit_checks=True)
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def create(
    context: typing.Union[lightbulb.SlashContext, lightbulb.PrefixContext]
) -> None:
    """Creates a new tag in the guild.

    Called when a user uses /tag create <tag name> <tag content>

    Arguments:
        context: The context for the command.

    Returns:
        None.
    """
    tag_name = context.options.name.lower()
    tag_content = context.options.content
    tag_guild = context.get_guild()

    # Check if there is already an existing tag
    if await get_tag(tag_name, tag_guild) is not None:
        await error_response(context, "That tag already exists.")
        return

    # Check if the desired tag name is greater than 54 characters long
    if len(tag_name) > 54:
        await error_response(
            context, "The tag name must be less than 54 characters long."
        )
        return

    # Check if the desired tag content is greater than 2000 characters long
    if len(tag_content) > 2000:
        await error_response(
            context, "The tag content must be less than 2000 characters long."
        )
        return

    await create_tag(tag_name, tag_content, context.author, tag_guild)
    await info_response(
        context,
        "Tag created",
        f"Your tag has been successfully created. \nUse `/tag show {tag_name}` to view it.",
    )


@tag.child
@lightbulb.option("name", "The name of tag")
@lightbulb.command("delete", "Deletes an existing tag", inherit_checks=True)
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def delete(
    context: typing.Union[lightbulb.SlashContext, lightbulb.PrefixContext]
) -> None:
    """Deletes an existing tag from the guild.

    Called when a user uses /tag delete <tag name>

    Arguments:
        context: The context for the command.

    Returns:
        None.
    """
    tag_name = context.options.name.lower()
    tag_author = context.author
    tag_guild = context.get_guild()
    document = await get_tag(tag_name, tag_guild)

    # Check if there is no existing tag
    if document is None:
        await error_response(context, "That tag does not exist.")
        return

    # Check if the author does not own or have the permissions to delete the tag
    if (
        tag_author.id != document["tags"]["author_id"]
        and not permissions_for(tag_author) & hikari.Permissions.MANAGE_MESSAGES
    ):
        await error_response(context, "You don't have permission to delete that tag.")
        return

    await delete_tag(tag_name, tag_guild)
    await info_response(
        context, "Tag deleted", f"The tag `{tag_name}` has been successfully deleted."
    )


@tag.child
@lightbulb.option("content", "The content of the tag")
@lightbulb.option("name", "The name of the tag")
@lightbulb.command("edit", "Edits an existing tag", inherit_checks=True)
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def edit(
    context: typing.Union[lightbulb.SlashContext, lightbulb.PrefixContext]
) -> None:
    """Edits the content of a tag in the guild.

    Called when a user uses /tag edit <tag name> <tag content>

    Arguments:
        context: The context for the command.

    Returns:
        None.
    """
    tag_name = context.options.name.lower()
    tag_guild = context.get_guild()
    document = await get_tag(tag_name, tag_guild)

    # Check if there is no existing tag
    if document is None:
        await error_response(context, "That tag does not exist.")
        return

    # Check if the author does not own the tag
    if context.author.id != document["tags"]["author_id"]:
        await error_response(context, "You don't have permission to edit that tag.")
        return

    await edit_tag(tag_name, context.options.content, tag_guild)
    await info_response(
        context, "Tag updated", f"The tag `{tag_name}` has been successfully updated."
    )


@tag.child
@lightbulb.option("name", "The name of the tag")
@lightbulb.command("info", "Shows info about an existing tag", inherit_checks=True)
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def info(
    context: typing.Union[lightbulb.SlashContext, lightbulb.PrefixContext]
) -> None:
    """Shows information about a tag in the guild.

    Called when a user uses /tag info <tag name>

    Arguments:
        context: The context for the command.

    Returns:
        None.
    """
    tag_name = context.options.name.lower()
    document = await get_tag(tag_name, context.get_guild())

    # Check if there is no existing tag
    if document is None:
        await error_response(context, "That tag does not exist.")
        return

    tag_data = extract_tag_details(document)
    info_embed = create_info_embed(
        "Tag info",
        f"Use `/tag show {tag_name}` to view its contents.",
        context.app.get_me().avatar_url,
    )

    info_embed.add_field("Name", tag_name, inline=True)
    info_embed.add_field("Author", tag_data["author"].mention, inline=True)
    info_embed.add_field("Author ID", tag_data["author"].id, inline=True)
    info_embed.add_field("Uses", tag_data["uses"], inline=True)
    info_embed.add_field("Created at", tag_data["created_at"], inline=True)
    info_embed.add_field("Modified at", tag_data["modified_at"], inline=True)

    await context.respond(embed=info_embed)


@tag.child
@lightbulb.option(
    "member", "The owner of the tags to view", type=hikari.Member, required=False
)
@lightbulb.command("list", "Lists all server tags", inherit_checks=True)
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def list(
    context: typing.Union[lightbulb.SlashContext, lightbulb.PrefixContext]
) -> None:
    """Lists all tags in the guild.

    Called when a user uses /tag list [member]

    Arguments:
        context: The context for the command.

    Returns:
        None.
    """
    tag_author = context.options.member
    tag_guild = context.get_guild()

    # Check if there are no tags to display
    if not await guild_has_tags(tag_author, tag_guild):
        await error_response(context, "There are no tags to display.")
        return

    paginator = await paginate_all_tags(tag_author, tag_guild)
    buttons = [
        Button("Previous", False, ButtonStyle.PRIMARY, "previous", prev_page),
        Button("Next", False, ButtonStyle.PRIMARY, "next", next_page),
    ]

    await ButtonNavigator(paginator.build_pages(), buttons=buttons).run(context)


def load(bot: lightbulb.BotApp) -> None:
    """Loads the 'Tags' plugin. Called when extension is loaded.

    Arguments:
        bot: The bot application to add the plugin to.

    Returns:
        None.
    """
    bot.add_plugin(plugin)
