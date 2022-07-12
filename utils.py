import hikari
import lightbulb
import typing

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


async def clone_channel(
    channel: hikari.GuildVoiceChannel, **kwargs
) -> hikari.GuildVoiceChannel:
    """Clones a voice channel in a guild.

    Creates a new voice channel in a specified guild and copies all values from
    an existing voice channel unless otherwise specified.

    Arguments:
        channel: The voice channel to clone.
        **kwargs: The channel kwargs to set instead of clone from channel.

    Returns:
        The clone voice channel.
    """
    clone_channel = await channel.get_guild().create_voice_channel(
        kwargs.get("name", channel.name),
        position=kwargs.get("position", channel.position),
        user_limit=kwargs.get("user_limit", channel.user_limit),
        bitrate=kwargs.get("bitrate", channel.bitrate),
        video_quality_mode=kwargs.get("video_quality_mode", channel.video_quality_mode),
        permission_overwrites=kwargs.get(
            "permission_overwrites", list(channel.permission_overwrites.values())
        ),
        region=kwargs.get("region", channel.region),
        category=kwargs.get("category", channel.parent_id),
    )
    return clone_channel


def evaluate_exception(
    exception: lightbulb.LightbulbError,
    exception_type: typing.Type[lightbulb.LightbulbError],
):
    """Evaluates whether an exception is of or contains a specified type.

    Check if the exception type is the specified type. If it isn't, check its causes to
    see if it contains the exception type.

    Arguments:
        exception: The exception to check.
        exception_type: The type to check for.

    Returns:
        True if the except is or contains the type, false if not.
    """
    if type(exception) is exception_type:
        return True

    if hasattr(exception, "causes"):
        for cause in exception.causes:
            if type(cause) is exception_type:
                return True

    return False
