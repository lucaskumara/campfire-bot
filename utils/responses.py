import hikari
import lightbulb

from datetime import datetime, timezone


INFO_EMBED_COLOUR = hikari.Colour(0xE67E22)
ERROR_EMBED_COLOUR = None  # hikari.Colour(0xE74C3C)
ERROR_DELETE_DELAY = 10


def create_info_embed(title: str, description: str, icon: hikari.URL) -> hikari.Embed:
    """Creates and returns an embed to display information to users.

    Creates an instance of an embed and fills it with the data provided by the
    function arguments.

    Arguments:
        title: The title of the embed.
        description: The description of the embed.
        icon: The URL of the embed icon.

    Returns:
        The created embed.
    """
    embed = hikari.Embed(
        title=title,
        description=description,
        colour=INFO_EMBED_COLOUR,
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_author(name="Campfire", icon=icon)
    return embed


async def info_response(
    context: lightbulb.Context, title: str, description: str
) -> None:
    """Creates an info response and sends it via the passed in context.

    Arguments:
        context: The context of the command.
        title: The title of the response embed.
        description: The description of the response embed.

    Returns:
        None.
    """
    bot_avatar_url = context.app.get_me().avatar_url
    info_embed = create_info_embed(title, description, bot_avatar_url)

    await context.respond(embed=info_embed)


def create_error_embed(description: str, icon: str) -> hikari.Embed:
    """Creates and returns an embed to display errors to users.

    Creates an instance of an embed and fills it with the data provided by the
    function arguments.

    Arguments:
        description: The description of the embed.
        icon: The URL of the embed icon.

    Returns:
        The created embed.
    """
    embed = hikari.Embed(
        description=description,
        colour=ERROR_EMBED_COLOUR,
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_author(name="Campfire", icon=icon)
    return embed


async def error_response(context: lightbulb.Context, description: str) -> None:
    """Creates an error response and sends it via the passed in context.

    Arguments:
        context: The context of the command.
        description: The description of the response embed.

    Returns:
        None.
    """
    bot_avatar_url = context.app.get_me().avatar_url
    error_embed = create_error_embed(description, bot_avatar_url)

    await context.respond(embed=error_embed, delete_after=ERROR_DELETE_DELAY)
