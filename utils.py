import hikari
from datetime import datetime, timezone

INFO_EMBED_COLOUR = hikari.Colour(0xE67E22)
ERROR_EMBED_COLOUR = None  # hikari.Colour(0xE74C3C)
DELETE_ERROR_DELAY = 10


def create_info_embed(
    title: str,
    description: str,
    icon: str,
    timestamp: bool = False
) -> hikari.Embed:
    '''Creates and returns an embed to display information to users.

    Creates an instance of an embed and fills it with the data provided by the 
    function arguments.

    Arguments:
        title: The title of the embed.
        description: The description of the embed.
        icon: The URL of the embed icon.
        timestamp: Whether or not to include a timestamp in the embed.

    Returns:
        The created embed.
    '''
    embed = hikari.Embed(
        title=title,
        description=description,
        colour=INFO_EMBED_COLOUR,
        timestamp=datetime.now(timezone.utc) if timestamp else None
    )
    embed.set_author(name='Campfire', icon=icon)
    return embed


def create_error_embed(
    description: str,
    icon: str,
    timestamp: bool = False
) -> hikari.Embed:
    '''Creates and returns an embed to display errors to users.

    Creates an instance of an embed and fills it with the data provided by the 
    function arguments.

    Arguments:
        description: The description of the embed.
        icon: The URL of the embed icon.
        timestamp: Whether or not to include a timestamp in the embed.

    Returns:
        The created embed.
    '''
    embed = hikari.Embed(
        description=description,
        colour=ERROR_EMBED_COLOUR,
        timestamp=datetime.now(timezone.utc) if timestamp else None
    )
    embed.set_author(name='Campfire', icon=icon)
    return embed


async def clone_channel(
    channel: hikari.GuildVoiceChannel,
    **kwargs
) -> hikari.GuildVoiceChannel:
    '''Clones a voice channel in a guild.

    Creates a new voice channel in a specified guild and copies all values from
    an existing voice channel unless otherwise specified.

    Arguments:
        channel: The voice channel to clone.
        **kwargs: The channel kwargs to set instead of clone from channel.

    Returns:
        The clone voice channel.
    '''
    clone_channel = await channel.get_guild().create_voice_channel(
        kwargs.get('name', channel.name),
        position=kwargs.get('position', channel.position),
        user_limit=kwargs.get('user_limit', channel.user_limit),
        bitrate=kwargs.get('bitrate', channel.bitrate),
        video_quality_mode=kwargs.get(
            'video_quality_mode', channel.video_quality_mode),
        permission_overwrites=kwargs.get(
            'permission_overwrites',
            list(channel.permission_overwrites.values())
        ),
        region=kwargs.get('region', channel.region),
        category=kwargs.get('category', channel.parent_id)
    )
    return clone_channel
