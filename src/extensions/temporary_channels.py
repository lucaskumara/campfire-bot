import hikari
import lightbulb

from lib import channels, responses


plugin = lightbulb.Plugin("Temporary Channels")


@plugin.listener(hikari.StartedEvent)
async def remove_old_channel_data(event: hikari.StartedEvent) -> None:
    """Removes all channel data from guilds that the bot is no longer in when the bot starts.

    Arguments:
        event: The event object.

    Returns:
        None.
    """
    collection = plugin.bot.d.mongo_database.channels
    cursor = await collection.distinct("channel_id")

    for channel_id in cursor:
        try:
            await plugin.bot.rest.fetch_channel(int(channel_id))
        except:
            await channels.delete_template(collection, int(channel_id))
            await channels.delete_clone(collection, int(channel_id))


@plugin.listener(hikari.GuildLeaveEvent)
async def remove_all_guild_channel_data(event: hikari.GuildLeaveEvent) -> None:
    """Removes all channel data from a guild when the bot leaves it.

    Arguments:
        event: The event object.

    Returns:
        None.
    """
    collection = plugin.bot.d.mongo_database.channels

    await channels.delete_guild_data(collection, event.guild_id)


@plugin.listener(hikari.GuildChannelDeleteEvent)
async def remove_channel_data(event: hikari.GuildChannelDeleteEvent) -> None:
    """Removes a channels data when the channel is deleted.

    Arguments:
        event: The event object.

    Returns:
        None.
    """
    collection = plugin.bot.d.mongo_database.channels

    await channels.delete_template(collection, event.channel_id)
    await channels.delete_clone(collection, event.channel_id)


@plugin.listener(hikari.VoiceStateUpdateEvent)
async def create_template_channel(event: hikari.VoiceStateUpdateEvent) -> None:
    """Creates a clone channel when a member joins a template channel.

    Arguments:
        event: The event object.

    Returns:
        None.
    """
    if not channels.joined_a_channel(event.state):
        return

    collection = plugin.bot.d.mongo_database.channels
    channel = await plugin.bot.rest.fetch_channel(event.state.channel_id)
    template = await channels.TemplateChannel.get(collection, channel)

    if template is None:
        return

    clone = await template.spawn_clone(event.state.member, "Lobby")

    await event.state.member.edit(voice_channel=clone.get_channel())


@plugin.listener(hikari.VoiceStateUpdateEvent)
async def delete_clone_channel(event: hikari.VoiceStateUpdateEvent) -> None:
    """Deletes a clone channel when the last member leaves it.

    Arguments:
        event: The event object.

    Returns:
        None.
    """
    if not channels.left_a_channel(event.old_state):
        return

    collection = plugin.bot.d.mongo_database.channels
    channel = await plugin.bot.rest.fetch_channel(event.old_state.channel_id)
    lobby = await channels.CloneChannel.get(collection, channel)

    if lobby is None:
        return

    if lobby.is_empty(plugin.bot.cache):
        await channels.CloneChannel.delete(collection, channel)


@plugin.command
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command("lobby", "Base of the lobby command group")
@lightbulb.implements(lightbulb.SlashCommandGroup, lightbulb.PrefixCommandGroup)
async def lobby(context: lightbulb.SlashContext | lightbulb.PrefixContext) -> None:
    """The lobby base command.

    Arguments:
        context: The command context.

    Returns:
        None.
    """
    pass


@lobby.child
@lightbulb.command("create", "Creates a template channel to spawn lobbies")
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def create(context: lightbulb.SlashContext | lightbulb.PrefixContext) -> None:
    """The lobby create subcomand. Creates a template channel in the guild.

    Arguments:
        context: The command context.

    Returns:
        None.
    """
    collection = plugin.bot.d.mongo_database.channels

    await channels.TemplateChannel.create(
        collection,
        context.get_guild(),
        "New Lobby - Edit Me!",
    )
    await responses.info(
        context, "Channel Created", "You lobby has been created. Feel free to edit it!"
    )


@lobby.child
@lightbulb.option("name", "The new channel name")
@lightbulb.command("rename", "Renames the lobby channel")
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def rename(context: lightbulb.SlashContext | lightbulb.PrefixContext) -> None:
    """The lobby rename subcommand. Renames a clone channel to a new specified name.

    Arguments:
        context: The command context.

    Returns:
        None.
    """
    collection = plugin.bot.d.mongo_database.channels
    guild = context.get_guild()

    if not await channels.is_in_lobby(collection, guild, context.author):
        await responses.error(context, "You are not in a lobby.")
        return

    author_voice_state = guild.get_voice_state(context.author)
    author_channel = guild.get_channel(author_voice_state.channel_id)

    clone = await channels.CloneChannel.get(collection, author_channel)

    if context.author != await clone.get_owner():
        await responses.error(context, "You are not the owner of this lobby.")
        return

    channel_name = context.options.name.strip()
    channel_name_length = len(channel_name)

    if channel_name_length == 0 or channel_name_length > 100:
        await responses.error(context, "The new name must be 1-100 characters long.")
        return

    try:
        await clone.rename(channel_name)
        await responses.info(
            context,
            "Channel renamed",
            f"The lobby has been renamed to `{channel_name}`.",
        )
    except hikari.errors.RateLimitTooLongError as error:
        await responses.error(
            context,
            f"You are being rate limited. Try again in `{int(error.retry_after)}` seconds.",
        )


@lobby.child
@lightbulb.option("member", "The member to kick", type=hikari.Member)
@lightbulb.command("kick", "Kicks a member from the lobby channel")
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def kick(context: lightbulb.SlashContext | lightbulb.PrefixContext) -> None:
    """The lobby kick subcommand. Kicks a member from a clone channel.

    Arguments:
        context: The command context.

    Returns:
        None.
    """
    collection = plugin.bot.d.mongo_database.channels
    guild = context.get_guild()

    if not await channels.is_in_lobby(collection, guild, context.author):
        await responses.error(context, "You are not in a lobby.")
        return

    author_voice_state = guild.get_voice_state(context.author)
    author_channel = guild.get_channel(author_voice_state.channel_id)

    clone = await channels.CloneChannel.get(collection, author_channel)

    if context.author != await clone.get_owner():
        await responses.error(context, "You are not the owner of this lobby.")
        return

    target_member = context.options.member
    target_voice_state = guild.get_voice_state(target_member)

    if target_voice_state is None or author_channel.id != target_voice_state.channel_id:
        await responses.error(context, "That member is not in the lobby.")
        return

    await clone.kick(target_member)
    await responses.info(
        context,
        "Member kicked",
        f"`{target_member.username}` has been kicked from the lobby.",
    )


@lobby.child
@lightbulb.option("member", "The member to set as the lobby owner", type=hikari.Member)
@lightbulb.command("owner", "Designates a member as the owner of the lobby channel")
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def owner(context: lightbulb.SlashContext | lightbulb.PrefixContext):
    """The lobby owner subcommand. Sets a new member as the lobby owner.

    Arguments:
        context: The command context.

    Returns:
        None.
    """
    collection = plugin.bot.d.mongo_database.channels
    guild = context.get_guild()

    if not await channels.is_in_lobby(collection, guild, context.author):
        await responses.error(context, "You are not in a lobby.")
        return

    author_voice_state = guild.get_voice_state(context.author)
    author_channel = guild.get_channel(author_voice_state.channel_id)

    clone = await channels.CloneChannel.get(collection, author_channel)

    if context.author != await clone.get_owner():
        await responses.error(context, "You are not the owner of this lobby.")
        return

    target_member = context.options.member
    target_voice_state = guild.get_voice_state(target_member)

    if target_voice_state is None or author_channel.id != target_voice_state.channel_id:
        await responses.error(context, "That member is not in the lobby.")
        return

    await clone.set_owner(target_member)
    await responses.info(
        context,
        "Owner updated",
        f"`{target_member.username}` is now the lobby owner.",
    )


def load(bot: lightbulb.BotApp) -> None:
    """Loads the temporary channels plugin.

    Arguments:
        bot: The bot instance.

    Returns:
        None.
    """
    bot.add_plugin(plugin)
