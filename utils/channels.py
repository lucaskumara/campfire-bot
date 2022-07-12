import hikari


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
