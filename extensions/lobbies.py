import hikari
import lightbulb
import utils

plugin = lightbulb.Plugin('Lobbies')


async def create_template(
    channel_name: str,
    channel_guild: hikari.GatewayGuild
) -> hikari.GuildVoiceChannel:
    '''Creates a template channel and stores the channel data in the database.

    Creates a new template channel with a specified name and stores its ID as 
    well as its guild's ID in the lobby_templates collection.

    Arguments:
        channel_name: The name of the template channel.
        channel_guild: The guild to create the template channel in.

    Returns:
        The created template channel.
    '''
    template_channel = await channel_guild.create_voice_channel(channel_name)

    await plugin.bot.database.lobby_templates.insert_one({
        'guild_id': template_channel.guild_id,
        'channel_id': template_channel.id
    })

    return template_channel


async def create_clone(
    template_channel: hikari.GuildVoiceChannel,
    owner: hikari.Member
) -> hikari.GuildVoiceChannel:
    '''Creates a clone channel and stores the channel data in the database.

    Creates a new clone channel and uses the owners to generate a channel 
    name. Then stores the clone channels ID, guild ID, its template channels
    ID, and its owners ID in the lobby_clones collection.

    Arguments:
        template_channel: The name of the template channel to clone.
        owner: The owner of the clone channel.

    Returns:
        The created clone channel.
    '''
    clone_channel = await utils.clone_channel(
        template_channel,
        name=f'{owner.username}\'s Lobby'
    )

    await plugin.bot.database.lobby_clones.insert_one({
        'guild_id': clone_channel.guild_id,
        'channel_id': clone_channel.id,
        'template_id': template_channel.id,
        'owner_id': owner.id
    })

    return clone_channel


async def valid_template(channel_id: hikari.Snowflake) -> bool:
    '''Determines if the channel is a valid template channel.

    Arguments:
        channel_id: The ID of the channel to check.

    Returns:
        True if the channel is a template, false if not.
    '''
    document = await plugin.bot.database.lobby_templates.find_one({
        'channel_id': channel_id
    })
    return document is not None


async def valid_clone(channel_id: hikari.Snowflake) -> bool:
    '''Determines if the channel is a valid clone channel.

    Arguments:
        channel_id: The ID of the channel to check.

    Returns:
        True if the channel is a clone, false if not.
    '''
    document = await plugin.bot.database.lobby_clones.find_one({
        'channel_id': channel_id
    })
    return document is not None


@plugin.listener(hikari.GuildChannelDeleteEvent)
async def on_channel_delete(event: hikari.GuildChannelDeleteEvent) -> None:
    '''Deletes template/clone channels from collections if manually deleted.

    If a voice channel is deleted manually, removes any instance of it 
    from the lobby_templates and lobby_clones collections.

    Arguments:
        event: The event that was fired. (GuildChannelDeleteEvent)

    Returns:
        None.
    '''
    channel = event.channel

    if not isinstance(channel, hikari.GuildVoiceChannel):
        return

    await plugin.bot.database.lobby_templates.delete_many({
        'guild_id': channel.guild_id,
        'channel_id': channel.id
    })
    await plugin.bot.database.lobby_clones.delete_many({
        'guild_id': channel.guild_id,
        'channel_id': channel.id
    })


@plugin.listener(hikari.VoiceStateUpdateEvent)
async def on_join_template(event: hikari.VoiceStateUpdateEvent) -> None:
    '''Clones the template channel and moves user to the cloned channel.

    If a template channel is joined by a user, clone the channel and move them 
    to the clone.

    Arguments:
        event: The event that was fired. (VoiceStateUpdateEvent)

    Returns:
        None.
    '''
    if event.state is None or event.state.channel_id is None:
        return

    if not await valid_template(event.state.channel_id):
        return

    template_channel = await plugin.bot.rest.fetch_channel(
        event.state.channel_id
    )
    clone_channel = await create_clone(template_channel, event.state.member)

    await event.state.member.edit(voice_channel=clone_channel)


@plugin.listener(hikari.VoiceStateUpdateEvent)
async def on_leave_clone(event: hikari.VoiceStateUpdateEvent) -> None:
    '''Deletes the clone channel if there is nobody left in it.

    If a clone channel is left by a user, check if the channel is now empty and
    delete it if so.

    Arguments:
        event: The event that was fired. (VoiceStateUpdateEvent)

    Returns:
        None.
    '''
    if event.old_state is None or event.old_state.channel_id is None:
        return

    if not await valid_clone(event.old_state.channel_id):
        return

    voice_states = plugin.bot.cache.get_voice_states_view_for_channel(
        event.old_state.guild_id,
        event.old_state.channel_id
    )

    if list(voice_states.values()) == []:
        clone_channel = await plugin.bot.rest.fetch_channel(
            event.old_state.channel_id
        )
        await clone_channel.delete()


@plugin.command
@lightbulb.add_checks(
    lightbulb.has_guild_permissions(hikari.Permissions.MANAGE_CHANNELS),
    lightbulb.bot_has_guild_permissions(hikari.Permissions.MANAGE_CHANNELS)
)
@lightbulb.command('lobby', 'Base of lobby command group')
@lightbulb.implements(lightbulb.SlashCommandGroup)
async def lobby(ctx: lightbulb.SlashContext) -> None:
    '''Base of the channel command group.

    Arguments:
        ctx: The context for the command.

    Returns:
        None.
    '''
    pass


@lobby.child
@lightbulb.command(
    'create',
    'Creates a new lobby template',
    inherit_checks=True,
    ephemeral=True
)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def create(ctx: lightbulb.SlashContext) -> None:
    '''Creates a new lobby template channel in the server.

    Called when a user uses /lobby create

    Arguments:
        ctx: The context for the command.

    Returns:
        None. 
    '''
    await create_template('New Lobby - Edit me!', ctx.get_guild())
    await ctx.respond(
        embed=utils.create_info_embed(
            'Channel created',
            'Your lobby has been created. Feel free to edit it!',
            plugin.bot.get_me().avatar_url,
            timestamp=True
        )
    )


@lobby.set_error_handler()
async def channel_errors(event: lightbulb.CommandErrorEvent) -> bool:
    '''Handles errors for the channel command and its various subcommands.

    Arguments:
        event: The event that was fired. (CommandErrorEvent)

    Returns:
        True if the exception can be handled, false if not.
    '''
    exception = event.exception

    if isinstance(exception, lightbulb.MissingRequiredPermission):
        await event.context.respond(
            embed=utils.create_error_embed(
                'You don\'t have permission to use this command.',
                plugin.bot.get_me().avatar_url,
                timestamp=True
            ),
            delete_after=utils.DELETE_ERROR_DELAY
        )
        return True

    elif isinstance(exception, lightbulb.BotMissingRequiredPermission):
        await event.context.respond(
            embed=utils.create_error_embed(
                'I am missing the permissions required to do that.',
                plugin.bot.get_me().avatar_url,
                timestamp=True
            ),
            delete_after=utils.DELETE_ERROR_DELAY
        )
        return True

    return False


def load(bot: lightbulb.BotApp) -> None:
    '''Loads the 'Lobbies' plugin. Called when extension is loaded.

    Arguments:
        bot: The bot application to add the plugin to.

    Returns:
        None.
    '''
    bot.add_plugin(plugin)
