import hikari
import lightbulb
import utils

from hikari.messages import ButtonStyle
from lightbulb.utils.permissions import permissions_for
from lightbulb.utils.pag import EmbedPaginator
from lightbulb.utils.nav import ComponentButton as Button, ButtonNavigator, \
    prev_page, next_page
from datetime import datetime, timezone

plugin = lightbulb.Plugin('Tags')


async def guild_has_tags(
    guild_id: hikari.Snowflake,
    author: hikari.Member
) -> bool:
    '''Checks if the guild has any tags in it.

    Arguments:
        guild_id: The ID of the guild to check.
        author: The author of the tags to search. Checks all tags if None.

    Returns:
        True if there is at least one tag in the guild, false if not.
    '''
    if author is None:
        document = await plugin.bot.database.tags.find_one(
            {'guild_id': guild_id}
        )
    else:
        document = await plugin.bot.database.tags.find_one(
            {'guild_id': guild_id, 'author_id': author.id}
        )
    return document is not None


async def paginate_all_tags(
    guild_id: hikari.Snowflake,
    author: hikari.Member
) -> EmbedPaginator:
    '''Adds all tags in the server to the paginator.

    Creates an EmbedPaginator and adds formatted lines containing a list of 
    all tags in a guild.

    Arguments:
        guild_id: The ID of the guild to list tags for.
        author: The author of all the tags to list. Lists all tags if None

    Returns:
        The constructed embed paginator.
    '''
    paginator = EmbedPaginator(prefix='```', suffix='```', max_lines=10)

    @paginator.embed_factory()
    def build_embed(index, content):
        '''Specify how embed paginator builds the embed'''
        embed = utils.create_info_embed(
            title='Tag list',
            description=f'Here is a list of tags. Use `/tag show [tag]` to view its contents. {content}',
            icon=plugin.bot.get_me().avatar_url,
            timestamp=True
        )
        embed.set_footer(f'Page {index}')
        return embed

    if author is None:
        async for document in plugin.bot.database.tags.find(
            {'guild_id': guild_id}
        ):
            paginator.add_line(f'• {document["name"]}')
    else:
        async for document in plugin.bot.database.tags.find(
            {'guild_id': guild_id, 'author_id': author.id}
        ):
            paginator.add_line(f'• {document["name"]}')

    return paginator


async def get_tag(tag_name: str, guild_id: hikari.Snowflake) -> dict:
    '''Returns the retrived document of the tag in the server.

    Arguments:
        tag_name: The name of the tag to find.
        guild_id: The guild of the tag to find.

    Returns:
        The document of the tag.
    '''
    document = await plugin.bot.database.tags.find_one(
        {'name': tag_name, 'guild_id': guild_id}
    )
    return document


async def create_tag(
    tag_name: str,
    tag_content: str,
    author_id: hikari.Snowflake,
    guild_id: hikari.Snowflake
) -> None:
    '''Creates a new tag in the server.

    Arguments:
        tag_name: The name of the tag.
        tag_content: The content of the tag.
        author_id: The ID of the tag author.
        guild_id: The ID of the tags guild.

    Returns:
        None.
    '''
    creation_time = datetime.now(timezone.utc).isoformat()

    await plugin.bot.database.tags.insert_one(
        {
            'name': tag_name,
            'content': tag_content,
            'created': creation_time,
            'modified': creation_time,
            'guild_id': guild_id,
            'author_id': author_id
        }
    )


async def delete_tag(tag_name: str, guild_id: hikari.Snowflake) -> None:
    '''Deletes a tag in the server.

    Arguments:
        tag_name: The name of the tag.
        guild_id: The ID of the tags guild.

    Returns:
        None.
    '''
    await plugin.bot.database.tags.delete_one(
        {'name': tag_name, 'guild_id': guild_id}
    )


async def edit_tag(
    tag_name: str,
    tag_content: str,
    guild_id: hikari.Snowflake
) -> None:
    '''Edits a tag in the server.

    Arguments:
        tag_name: The name of the tag.
        tag_content: The new content of the tag.
        guild_id: The ID of the tags guild.

    Returns:
        None.
    '''
    edit_time = datetime.now(timezone.utc).isoformat()

    await plugin.bot.database.tags.update_one(
        {'name': tag_name, 'guild_id': guild_id},
        {'$set': {'content': tag_content, 'modified': edit_time}}
    )


@plugin.command
@lightbulb.command('tag', 'Base of tag command group')
@lightbulb.implements(lightbulb.SlashCommandGroup)
async def tag(ctx: lightbulb.SlashContext) -> None:
    '''Base of the tag command group.

    Arguments:
        ctx: The context for the command.

    Returns:
        None.
    '''
    pass


@tag.child
@lightbulb.option('name', 'The name of the tag')
@lightbulb.command('show', 'Shows the content of a tag')
@lightbulb.implements(lightbulb.SlashSubCommand)
async def show(ctx: lightbulb.SlashCommand) -> None:
    '''Displays a tag in the server.

    Called when a user uses /tag show <tag name>

    Arguments:
        ctx: The context for the command.

    Returns:
        None. 
    '''
    document = await get_tag(ctx.options.name.lower(), ctx.guild_id)

    if document is None:
        await ctx.respond(
            embed=utils.create_error_embed(
                'That tag does not exist.',
                plugin.bot.get_me().avatar_url,
                timestamp=True
            ),
            delete_after=utils.DELETE_ERROR_DELAY
        )
        return

    await ctx.respond(document['content'])


@tag.child
@lightbulb.option('content', 'The content of the tag')
@lightbulb.option('name', 'The name of the tag')
@lightbulb.command('create', 'Creates a new tag')
@lightbulb.implements(lightbulb.SlashSubCommand)
async def create(ctx: lightbulb.SlashContext) -> None:
    '''Creates a new tag in the server.

    Called when a user uses /tag create <tag name> <tag content>

    Arguments:
        ctx: The context for the command.

    Returns:
        None. 
    '''
    tag_name = ctx.options.name.lower()
    document = await get_tag(tag_name, ctx.guild_id)

    if document is not None:
        await ctx.respond(
            embed=utils.create_error_embed(
                'That tag already exists.',
                plugin.bot.get_me().avatar_url,
                timestamp=True
            ),
            delete_after=utils.DELETE_ERROR_DELAY
        )
        return

    if len(ctx.options.name) > 54:
        await ctx.respond(
            embed=utils.create_error_embed(
                'The tag name must be less than 54 characters long.',
                plugin.bot.get_me().avatar_url,
                timestamp=True
            ),
            delete_after=utils.DELETE_ERROR_DELAY
        )
        return

    if len(ctx.options.content) > 2000:
        await ctx.respond(
            embed=utils.create_error_embed(
                'The tag content must be less than 2000 characters long.',
                plugin.bot.get_me().avatar_url,
                timestamp=True
            )
        )
        return

    await create_tag(
        tag_name,
        ctx.options.content,
        ctx.author.id,
        ctx.guild_id
    )
    await ctx.respond(
        embed=utils.create_info_embed(
            'Tag created',
            'Your tag has been successfully created. \n'
            f'Use `/tag show {tag_name}` to view it.',
            plugin.bot.get_me().avatar_url,
            timestamp=True
        )
    )


@tag.child
@lightbulb.option('name', 'The name of tag')
@lightbulb.command('delete', 'Deletes an existing tag')
@lightbulb.implements(lightbulb.SlashSubCommand)
async def delete(ctx: lightbulb.SlashContext) -> None:
    '''Deletes an existing tag from the server.

    Called when a user uses /tag delete <tag name>

    Arguments:
        ctx: The context for the command.

    Returns:
        None. 
    '''
    tag_name = ctx.options.name.lower()
    document = await get_tag(tag_name, ctx.guild_id)

    if document is None:
        await ctx.respond(
            embed=utils.create_error_embed(
                'That tag does not exist.',
                plugin.bot.get_me().avatar_url,
                timestamp=True
            ),
            delete_after=utils.DELETE_ERROR_DELAY
        )
        return

    if (ctx.member.id != document['author_id'] and
            not permissions_for(ctx.member) &
            hikari.Permissions.MANAGE_MESSAGES):
        await ctx.respond(
            embed=utils.create_error_embed(
                'You don\'t have permission to delete that tag.',
                plugin.bot.get_me().avatar_url,
                timestamp=True
            ),
            delete_after=utils.DELETE_ERROR_DELAY
        )
        return

    await delete_tag(tag_name, ctx.guild_id)
    await ctx.respond(
        embed=utils.create_info_embed(
            'Tag deleted',
            f'The tag `{tag_name}` has been successfully deleted.',
            plugin.bot.get_me().avatar_url,
            timestamp=True
        )
    )


@tag.child
@lightbulb.option('content', 'The content of the tag')
@lightbulb.option('name', 'The name of the tag')
@lightbulb.command('edit', 'Edits an existing tag')
@lightbulb.implements(lightbulb.SlashSubCommand)
async def edit(ctx: lightbulb.SlashCommand) -> None:
    '''Edits the content of a tag in the server.

    Called when a user uses /tag edit <tag name> <tag content>

    Arguments:
        ctx: The context for the command.

    Returns:
        None. 
    '''
    tag_name = ctx.options.name.lower()
    document = await get_tag(tag_name, ctx.guild_id)

    if document is None:
        await ctx.respond(
            embed=utils.create_error_embed(
                'That tag does not exist.',
                plugin.bot.get_me().avatar_url,
                timestamp=True
            ),
            delete_after=utils.DELETE_ERROR_DELAY
        )
        return

    if ctx.member.id != document['author_id']:
        await ctx.respond(
            embed=utils.create_error_embed(
                'You don\'t have permission to edit that tag.',
                plugin.bot.get_me().avatar_url,
                timestamp=True
            ),
            delete_after=utils.DELETE_ERROR_DELAY
        )
        return

    await edit_tag(tag_name, ctx.options.content, ctx.guild_id)
    await ctx.respond(
        embed=utils.create_info_embed(
            'Tag updated',
            f'The tag `{tag_name}` has been successfully updated.',
            plugin.bot.get_me().avatar_url,
            timestamp=True
        )
    )


@tag.child
@lightbulb.option('name', 'The name of the tag')
@lightbulb.command('info', 'Shows info about an existing tag')
@lightbulb.implements(lightbulb.SlashSubCommand)
async def info(ctx: lightbulb.SlashCommand) -> None:
    '''Shows information about a tag in the server.

    Called when a user uses /tag info <tag name>

    Arguments:
        ctx: The context for the command.

    Returns:
        None. 
    '''
    tag_name = ctx.options.name.lower()
    document = await get_tag(tag_name, ctx.guild_id)

    if document is None:
        await ctx.respond(
            embed=utils.create_error_embed(
                'That tag does not exist.',
                plugin.bot.get_me().avatar_url,
                timestamp=True
            ),
            delete_after=utils.DELETE_ERROR_DELAY
        )
        return

    # Convert database information into usable data
    author = await plugin.bot.rest.fetch_user(document['author_id'])
    created = datetime.fromisoformat(document['created'])
    modified = datetime.fromisoformat(document['modified'])

    data = {
        'Tag name': tag_name,
        'Tag author': f'{author.username}#{author.discriminator}',
        'Guild ID': ctx.guild_id,
        'Created at': created.strftime("%b %d, %Y @%I:%M %p UTC"),
        'Last modified': modified.strftime("%b %d, %Y @%I:%M %p UTC")
    }

    # Format data into a string
    formatted = '\n'.join([f'{key}: {value}' for key, value in data.items()])
    formatted = '```' + formatted + '```'

    await ctx.respond(
        embed=utils.create_info_embed(
            'Tag info',
            f'Use `/tag show {tag_name}` to view its contents. {formatted}',
            plugin.bot.get_me().avatar_url,
            timestamp=True
        )
    )


@tag.child
@lightbulb.option(
    'member',
    'The owner of the tags to view',
    type=hikari.Member,
    required=False
)
@lightbulb.command('list', 'Lists all server tags')
@lightbulb.implements(lightbulb.SlashSubCommand)
async def list(ctx: lightbulb.SlashCommand) -> None:
    '''Lists all tags in the server.

    Called when a user uses /tag list [member]

    Arguments:
        ctx: The context for the command.

    Returns:
        None. 
    '''
    if not await guild_has_tags(ctx.guild_id, ctx.options.member):
        await ctx.respond(
            embed=utils.create_error_embed(
                'There are no tags to display.',
                plugin.bot.get_me().avatar_url,
                timestamp=True
            ),
            delete_after=utils.DELETE_ERROR_DELAY
        )
        return

    paginator = await paginate_all_tags(ctx.guild_id, ctx.options.member)
    buttons = [
        Button('Previous', False, ButtonStyle.PRIMARY, 'previous', prev_page),
        Button('Next', False, ButtonStyle.PRIMARY, 'next', next_page)
    ]

    await ButtonNavigator(paginator.build_pages(), buttons=buttons).run(ctx)


def load(bot: lightbulb.BotApp) -> None:
    '''Loads the 'Tags' plugin. Called when extension is loaded.

    Arguments:
        bot: The bot application to add the plugin to.

    Returns:
        None.
    '''
    bot.add_plugin(plugin)
