import hikari
import lightbulb
import typing
import utils

CHOICES = ["rename", "lock", "unlock", "kick", "ban", "unban"]

plugin = lightbulb.Plugin("Lobbies")


async def create_template(
    channel_name: str, channel_guild: hikari.GatewayGuild
) -> hikari.GuildVoiceChannel:
    """Creates a template channel and stores the channel data in the database.

    Creates a new voice channel and pushes its channel ID into the
    guild document templates list if it exists. Otherwise, create a new guild
    document with the templates list containing the template channel ID.

    Arguments:
        channel_name: The name of the template channel.
        channel_guild: The guild to create the template channel in.

    Returns:
        The created template channel.
    """
    template_channel = await channel_guild.create_voice_channel(channel_name)

    await plugin.bot.d.db_conn.lobby_channels.update_one(
        {"guild_id": channel_guild.id},
        {"$push": {"templates": template_channel.id}},
        upsert=True,
    )

    return template_channel


async def create_clone(
    template_channel: hikari.GuildVoiceChannel, owner: hikari.Member
) -> hikari.GuildVoiceChannel:
    """Creates a clone channel and stores the channel data in the database.

    Clones a template voice channel and pushes its channel ID into the
    guild document clones list if it exists. Otherwise, create a new guild
    document with the clones list containing a document containing info about
    the clone channel.

    Arguments:
        template_channel: The template channel to clone.
        owner: The owner of the clone channel.

    Returns:
        The created clone channel.
    """
    clone_channel = await utils.clone_channel(
        template_channel, name=f"{owner.username}'s Lobby"
    )

    await plugin.bot.d.db_conn.lobby_channels.update_one(
        {"guild_id": clone_channel.guild_id},
        {
            "$push": {
                "clones": {
                    "clone_id": clone_channel.id,
                    "template_id": template_channel.id,
                    "owner_id": owner.id,
                }
            }
        },
        upsert=True,
    )

    return clone_channel


async def get_clone_document(
    channel_id: hikari.Snowflake,
) -> typing.Optional[dict]:
    """Gets the clone channel document from the database.

    Uses an aggregate to find documents containing the channel id (should be a
    single document), unwinding clones and then matching to the unwound
    document with the channel id (should also be a single document). Limits
    the result to a single document just incase.

    Arguments:
        channel_id: The ID of the channel to get.

    Returns:
        The document of the channel if it exists otherwise None.
    """
    cursor = plugin.bot.d.db_conn.lobby_channels.aggregate(
        [
            {"$match": {"clones.clone_id": channel_id}},
            {"$unwind": "$clones"},
            {"$match": {"clones.clone_id": channel_id}},
            {"$limit": 1},
        ]
    )
    documents = await cursor.to_list(length=1)

    if documents != []:
        return documents[0]

    return None


async def valid_template(channel_id: hikari.Snowflake) -> bool:
    """Determines if the channel is a valid template channel.

    Checks if there is a document that contains the channel id in its array of
    templates.

    Arguments:
        channel: The ID of the channel to check.

    Returns:
        True if the channel is a template, false if not.
    """
    document = await plugin.bot.d.db_conn.lobby_channels.find_one(
        {"templates": channel_id}
    )
    return document is not None


async def valid_clone(channel_id: hikari.Snowflake) -> bool:
    """Determines if the channel is a valid clone channel.

    Checks if there is a document that contains the channel id in its array of
    clone documents.

    Arguments:
        channel: The clone channel.

    Returns:
        True if the channel is a clone, false if not.
    """
    document = await plugin.bot.d.db_conn.lobby_channels.find_one(
        {"clones.clone_id": channel_id}
    )
    return document is not None


async def enable_command(command_name: str, guild_id: hikari.Snowflake) -> None:
    """Enables a command in a guild.

    Enables a command in a guild by removing it from the guilds list of
    disabled commands.

    Arguments:
        command_name: The name of the command.
        guild_id: The ID of the guild to enable the command in.

    Returns:
        None.
    """
    await plugin.bot.d.db_conn.lobby_disabled_commands.update_one(
        {"guild_id": guild_id}, {"$pull": {"disabled_commands": command_name}}
    )


async def disable_command(command_name: str, guild_id: hikari.Snowflake) -> None:
    """Disables a command in a guild.

    Disables a command in a guild by adding it to the guilds list of disabled
    commands.

    Arguments:
        command_name: The name of the command.
        guild_id: The ID of the guild to disable the command in.

    Returns:
        None.
    """
    await plugin.bot.d.db_conn.lobby_disabled_commands.update_one(
        {"guild_id": guild_id},
        {"$push": {"disabled_commands": command_name}},
        upsert=True,
    )


async def command_is_disabled(command_name: str, guild_id: hikari.Snowflake) -> bool:
    """Checks if a command is disabled in a guild.

    Checks if a command is disabled in a guild by checking if it is in the
    guilds list of disabled commands.

    Arguments:
        command_name: The name of the command.
        guild_id: The ID of the guild to check if the command is disabled for.

    Returns:
        True if the command is disabled otherwise false.
    """
    document = await plugin.bot.d.db_conn.lobby_disabled_commands.find_one(
        {"guild_id": guild_id, "disabled_commands": command_name}
    )
    return document is not None


async def lock_lobby(lobby: hikari.GuildVoiceChannel) -> None:
    """Locks a lobby and prevents new members from joining.

    Locks a lobby by obtaining the channel permissions and the @everyone
    role from the associated guild. If the @everyone role has existing
    permissions in the channel, modify them to revoke the ability to join the
    channel. If there are no existing permissions for the @everyone role,
    create new permissions denying the ability for the role to connect to the
    channel.

    Arguments:
        lobby: The lobby to lock.

    Returns:
        None.
    """

    def find_everyone(role):
        return role.name == "@everyone"

    channel_permissions = list(lobby.permission_overwrites.values())
    channel_guild = lobby.get_guild()
    guild_roles = list(channel_guild.get_roles().values())
    everyone_role = lightbulb.utils.find(guild_roles, find_everyone)

    # Modify existing permissions or create new permissions as needed
    if channel_permissions == []:
        channel_permissions = [
            hikari.PermissionOverwrite(
                id=everyone_role.id,
                type=hikari.PermissionOverwriteType.ROLE,
                deny=(hikari.Permissions.CONNECT),
            )
        ]
    else:
        for permission in channel_permissions:
            if permission.id == everyone_role.id:
                permission.allow = permission.allow.difference(
                    hikari.Permissions.CONNECT
                )
                permission.deny = permission.deny.union(hikari.Permissions.CONNECT)
                break

    await lobby.edit(permission_overwrites=channel_permissions)


async def unlock_lobby(lobby: hikari.GuildVoiceChannel) -> None:
    """Unlocks a lobby and allows new members to join.

    Unlocks a lobby by obtaining the channel permissions and the @everyone
    role from the associated guild. If the @everyone role has existing
    permissions in the channel, modify them to include the ability to join the
    channel. If there are no existing permissions for the @everyone role,
    create new permissions allowing the ability for the role to connect to the
    channel.

    Arguments:
        lobby: The lobby to unlock.

    Returns:
        None.
    """

    def find_everyone(role):
        return role.name == "@everyone"

    channel_permissions = list(lobby.permission_overwrites.values())
    channel_guild = lobby.get_guild()
    guild_roles = list(channel_guild.get_roles().values())
    everyone_role = lightbulb.utils.find(guild_roles, find_everyone)

    # Modify existing permissions otherwise create them from scratch
    if channel_permissions != []:
        for permission in channel_permissions:
            if permission.id == everyone_role.id:
                permission.allow = permission.allow.union(hikari.Permissions.CONNECT)
                permission.deny = permission.deny.difference(hikari.Permissions.CONNECT)
                break
    else:
        channel_permissions = [
            hikari.PermissionOverwrite(
                id=everyone_role.id,
                type=hikari.PermissionOverwriteType.ROLE,
                allow=(hikari.Permissions.CONNECT),
            )
        ]

    await lobby.edit(permission_overwrites=channel_permissions)


def lobby_is_locked(lobby: hikari.GuildVoiceChannel) -> bool:
    """Checks if a channel is currently locked for everyone.

    Checks if a channel is locked by obtaining the channel permissions and the
    @everyone role from the associated guild. If the channel has permissions
    preventing members with the @everyone role from joining, the channel is
    locked.

    Arguments:
        lobby: The lobby to check.

    Returns:
        True if the channel is locked otherwise false.
    """

    def find_everyone(role):
        return role.name == "@everyone"

    channel_permissions = list(lobby.permission_overwrites.values())
    channel_guild = lobby.get_guild()
    guild_roles = list(channel_guild.get_roles().values())
    everyone_role = lightbulb.utils.find(guild_roles, find_everyone)

    for permission in channel_permissions:
        if permission.id == everyone_role.id:
            return (permission.deny & hikari.Permissions.CONNECT) != 0

    return False


async def ban_member(lobby: hikari.GuildVoiceChannel, member: hikari.Member) -> None:
    """Bans a member from a lobby.

    Bans a member by obtaining the members permissions in the channel. If the
    member has existing permissions in the channel, modify them to revoke the
    ability to join the channel. If there are no existing permissions for the
    member, create new permissions denying the ability for the role to connect
    to the channel.

    Arguments:
        lobby: The lobby to ban the member in.
        member: The member to ban.

    Returns:
        None.
    """

    def find_member_permissions(permission):
        return permission.id == member.id

    all_permissions = list(lobby.permission_overwrites.values())
    member_permissions = lightbulb.utils.find(all_permissions, find_member_permissions)

    # Modify existing permissions or create new permissions as needed
    if member_permissions is None:
        new_member_permissions = hikari.PermissionOverwrite(
            id=member.id,
            type=hikari.PermissionOverwriteType.MEMBER,
            deny=(hikari.Permissions.CONNECT),
        )
        all_permissions.append(new_member_permissions)
    else:
        member_permissions.allow = member_permissions.allow.difference(
            hikari.Permissions.CONNECT
        )
        member_permissions.deny = member_permissions.deny.union(
            hikari.Permissions.CONNECT
        )

    await lobby.edit(permission_overwrites=all_permissions)


async def unban_member(lobby: hikari.GuildVoiceChannel, member: hikari.Member) -> None:
    """Unbans a member from a lobby.

    Unbans a member by obtaining the members permissions in the channel. If
    the member has existing permissions in the channel, modify them to include
    the ability to join the channel. If there are no existing permissions for
    the member, create new permissions allowing the ability for the role to
    connect to the channel.

    Arguments:
        lobby: The lobby to unban the member from.
        member: The member to unban.

    Returns:
        None.
    """

    def find_member_permissions(permission):
        return permission.id == member.id

    all_permissions = list(lobby.permission_overwrites.values())
    member_permissions = lightbulb.utils.find(all_permissions, find_member_permissions)

    # Modify existing permissions or create new permissions as needed
    if member_permissions is None:
        new_member_permissions = hikari.PermissionOverwrite(
            id=member.id,
            type=hikari.PermissionOverwriteType.MEMBER,
            allow=(hikari.Permissions.CONNECT),
        )
        all_permissions.append(new_member_permissions)
    else:
        member_permissions.allow = member_permissions.allow.union(
            hikari.Permissions.CONNECT
        )
        member_permissions.deny = member_permissions.deny.difference(
            hikari.Permissions.CONNECT
        )

    await lobby.edit(permission_overwrites=all_permissions)


def member_is_banned(lobby: hikari.GuildVoiceChannel, member: hikari.Member) -> bool:
    """Checks if a channel is currently locked for everyone.

    Checks if a member is banned by checking if the channel has permissions
    denying the member from joining. If so, the member is banned.

    Arguments:
        lobby: The lobby to check.

    Returns:
        True if the channel is locked otherwise false.
    """
    channel_permissions = list(lobby.permission_overwrites.values())

    for permission in channel_permissions:
        if permission.id == member.id:
            return (permission.deny & hikari.Permissions.CONNECT) != 0

    return False


@plugin.listener(hikari.StartedEvent)
async def clear_database(event: hikari.StartedEvent) -> None:
    """Clears any channels from the database that dont exist anymore.

    Tries to fetch all channels in the templates array and clone documents
    array. If the channel cannot be fetched, delete its entry from its correct
    spot in the database.

    Arguments:
        event: The event that was fired.

    Returns:
        None.
    """
    async for document in plugin.bot.d.db_conn.lobby_channels.find({}):
        template_ids = document.get("templates", [])
        clone_documents = document.get("clones", [])
        clone_ids = [clone["clone_id"] for clone in clone_documents]

        delete_templates = []
        delete_clones = []

        for id in template_ids:
            try:
                await plugin.bot.rest.fetch_channel(id)
            except hikari.NotFoundError:
                delete_templates.append(id)

        for id in clone_ids:
            try:
                await plugin.bot.rest.fetch_channel(id)
            except hikari.NotFoundError:
                delete_clones.append(id)

        guild_id = document["guild_id"]

        await plugin.bot.d.db_conn.lobby_channels.update_many(
            {"guild_id": guild_id}, {"$pull": {"templates": {"$in": delete_templates}}}
        )
        await plugin.bot.d.db_conn.lobby_channels.update_many(
            {"guild_id": guild_id},
            {"$pull": {"clones": {"clone_id": {"$in": delete_clones}}}},
        )


@plugin.listener(hikari.GuildChannelDeleteEvent)
async def on_channel_delete(event: hikari.GuildChannelDeleteEvent) -> None:
    """Deletes template/clone channels from collections if manually deleted.

    Arguments:
        event: The event that was fired.

    Returns:
        None.
    """
    channel = event.channel

    if not isinstance(channel, hikari.GuildVoiceChannel):
        return

    await plugin.bot.d.db_conn.lobby_channels.update_many(
        {"guild_id": channel.guild_id},
        {"$pull": {"templates": channel.id}},
    )
    await plugin.bot.d.db_conn.lobby_channels.update_many(
        {"guild_id": channel.guild_id},
        {"$pull": {"clones": {"clone_id": channel.id}}},
    )


@plugin.listener(hikari.VoiceStateUpdateEvent)
async def on_join_template(event: hikari.VoiceStateUpdateEvent) -> None:
    """Clones the template channel and moves member to the cloned channel.

    If a template channel is joined by a member, clones the channel and moves
    them to the clone.

    Arguments:
        event: The event that was fired.

    Returns:
        None.
    """
    voice_state = event.state
    channel_id = voice_state.channel_id

    if voice_state is None or channel_id is None:
        return

    if not await valid_template(channel_id):
        return

    member = voice_state.member
    template_channel = await plugin.bot.rest.fetch_channel(channel_id)
    clone_channel = await create_clone(template_channel, member)

    await event.state.member.edit(voice_channel=clone_channel)


@plugin.listener(hikari.VoiceStateUpdateEvent)
async def on_leave_clone(event: hikari.VoiceStateUpdateEvent) -> None:
    """Deletes the clone channel if there is nobody left in it.

    If a clone channel is left by a member, checks if the channel has no
    members left in it and deletes the channel if so.

    Arguments:
        event: The event that was fired.

    Returns:
        None.
    """
    prev_state = event.old_state

    if prev_state is None:
        return

    prev_state_channel_id = prev_state.channel_id

    if prev_state_channel_id is None:
        return

    if not await valid_clone(prev_state_channel_id):
        return

    clone_guild = prev_state.guild_id
    clone_channel_id = prev_state_channel_id

    voice_states = plugin.bot.cache.get_voice_states_view_for_channel(
        clone_guild, clone_channel_id
    )

    if list(voice_states.values()) == []:
        clone_channel = await plugin.bot.rest.fetch_channel(clone_channel_id)
        await clone_channel.delete()


@plugin.command
@lightbulb.add_checks(
    lightbulb.has_guild_permissions(hikari.Permissions.MANAGE_CHANNELS),
    lightbulb.bot_has_guild_permissions(hikari.Permissions.MANAGE_CHANNELS),
)
@lightbulb.command("lobby", "Base of lobby command group")
@lightbulb.implements(lightbulb.SlashCommandGroup)
async def lobby(ctx: lightbulb.SlashContext) -> None:
    """Base of the channel command group.

    Arguments:
        ctx: The context for the command.

    Returns:
        None.
    """
    pass


@lobby.child
@lightbulb.command("create", "Creates a new lobby template", inherit_checks=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def create(ctx: lightbulb.SlashContext) -> None:
    """Creates a new lobby template channel in the guild.

    Called when a member uses /lobby create.

    Arguments:
        ctx: The context for the command.

    Returns:
        None.
    """
    guild = ctx.get_guild()
    bot_avatar_url = plugin.bot.get_me().avatar_url
    create_embed = utils.create_info_embed(
        "Channel created",
        "Your lobby has been created. Feel free to edit it!",
        bot_avatar_url,
    )

    await create_template("New Lobby - Edit me!", guild)
    await ctx.respond(embed=create_embed)


@lobby.child
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.ADMINISTRATOR))
@lightbulb.option("command", "The command to enable", choices=CHOICES)
@lightbulb.command("enable", "Enables the usage of a lobby command")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def enable(ctx: lightbulb.SlashContext) -> None:
    """Enables a commands usage in the guild.

    Called when a member uses /lobby enable <command>. The command can only be
    used by guild members with the administrator permission.

    Arguments:
        ctx: The context for the command.

    Returns:
        None.
    """
    command_name = ctx.options.command
    guild_id = ctx.guild_id
    bot_avatar_url = plugin.bot.get_me().avatar_url

    if not await command_is_disabled(command_name, guild_id):
        error_embed = utils.create_error_embed(
            "That command is already enabled.", bot_avatar_url
        )
        await ctx.respond(
            embed=error_embed,
            delete_after=utils.DELETE_ERROR_DELAY,
        )
        return

    enabled_embed = utils.create_info_embed(
        "Command enabled",
        f"The command `{command_name}` has been enabled.",
        bot_avatar_url,
    )

    await enable_command(command_name, guild_id)
    await ctx.respond(embed=enabled_embed)


@lobby.child
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.ADMINISTRATOR))
@lightbulb.option("command", "The command to disable", choices=CHOICES)
@lightbulb.command("disable", "Disables the usage of a lobby command")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def disable(ctx: lightbulb.SlashContext) -> None:
    """Disables a commands usage in the guild.

    Called when a member uses /lobby disable <command>. The command can only
    be used by guild members with the administrator permission.

    Arguments:
        ctx: The context for the command.

    Returns:
        None.
    """
    command_name = ctx.options.command
    guild_id = ctx.guild_id
    bot_avatar_url = plugin.bot.get_me().avatar_url

    if await command_is_disabled(command_name, guild_id):
        error_embed = utils.create_error_embed(
            "That command is already disabled.", bot_avatar_url
        )
        await ctx.respond(
            embed=error_embed,
            delete_after=utils.DELETE_ERROR_DELAY,
        )
        return

    disable_embed = utils.create_info_embed(
        "Command disabled",
        f"The command `{command_name}` has been disabled.",
        bot_avatar_url,
    )

    await disable_command(command_name, guild_id)
    await ctx.respond(embed=disable_embed)


@lobby.child
@lightbulb.option("name", "The new lobby name")
@lightbulb.command("rename", "Renames the lobby")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def rename(ctx: lightbulb.SlashContext) -> None:
    """Renames a the authors current lobby in the guild.

    Called when a member uses /lobby rename <name>.

    Arguments:
        ctx: The context for the command.

    Returns:
        None.
    """
    guild_id = ctx.guild_id
    bot_avatar_url = plugin.bot.get_me().avatar_url

    if await command_is_disabled("rename", guild_id):
        error_embed = utils.create_error_embed(
            "Sorry. This command has been disabled.", bot_avatar_url
        )
        await ctx.respond(
            embed=error_embed,
            delete_after=utils.DELETE_ERROR_DELAY,
        )
        return

    guild = ctx.get_guild()
    author_member = ctx.member
    author_voice_state = guild.get_voice_state(author_member)

    if author_voice_state is None or not await valid_clone(
        author_voice_state.channel_id
    ):
        error_embed = utils.create_error_embed(
            "You are not in a lobby.", bot_avatar_url
        )
        await ctx.respond(
            embed=error_embed,
            delete_after=utils.DELETE_ERROR_DELAY,
        )
        return

    author_channel_id = author_voice_state.channel_id
    document = await get_clone_document(author_channel_id)

    if document["clones"]["owner_id"] != author_member.id:
        error_embed = utils.create_error_embed(
            "You are not the owner of this lobby.", bot_avatar_url
        )
        await ctx.respond(
            embed=error_embed,
            delete_after=utils.DELETE_ERROR_DELAY,
        )
        return

    clean_name = ctx.options.name.strip()

    if not (1 <= len(clean_name) <= 100):
        error_embed = utils.create_error_embed(
            "The new name must be 1-100 character long.", bot_avatar_url
        )
        await ctx.respond(
            embed=error_embed,
            delete_after=utils.DELETE_ERROR_DELAY,
        )
        return

    lobby = guild.get_channel(author_channel_id)

    try:
        rename_embed = utils.create_info_embed(
            "Channel renamed",
            f"The lobby has been renamed to `{clean_name}`.",
            bot_avatar_url,
        )

        await lobby.edit(name=clean_name)
        await ctx.respond(embed=rename_embed)

    except hikari.errors.RateLimitedError as error:
        error_embed = utils.create_error_embed(
            (
                "You are being rate limited. Try again in "
                f"`{int(error.retry_after)}` seconds."
            ),
            bot_avatar_url,
        )
        await ctx.respond(
            embed=error_embed,
            delete_after=utils.DELETE_ERROR_DELAY,
        )


@lobby.child
@lightbulb.command("lock", "Prevents new members from joining the lobby")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def lock(ctx: lightbulb.SlashContext) -> None:
    """Locks a lobby so that new members can not join.

    Called when a member uses /lobby lock.

    Arguments:
        ctx: The context for the command.

    Returns:
        None.
    """
    guild_id = ctx.guild_id
    bot_avatar_url = plugin.bot.get_me().avatar_url

    if await command_is_disabled("lock", guild_id):
        error_embed = utils.create_error_embed(
            "Sorry. This command has been disabled.", bot_avatar_url
        )
        await ctx.respond(
            embed=error_embed,
            delete_after=utils.DELETE_ERROR_DELAY,
        )
        return

    guild = ctx.get_guild()
    author_member = ctx.member
    author_voice_state = guild.get_voice_state(author_member)

    if author_voice_state is None or not await valid_clone(
        author_voice_state.channel_id
    ):
        error_embed = utils.create_error_embed(
            "You are not in a lobby.", bot_avatar_url
        )
        await ctx.respond(
            embed=error_embed,
            delete_after=utils.DELETE_ERROR_DELAY,
        )
        return

    author_channel_id = author_voice_state.channel_id
    document = await get_clone_document(author_channel_id)

    if document["clones"]["owner_id"] != author_member.id:
        error_embed = utils.create_error_embed(
            "You are not the owner of this lobby.", bot_avatar_url
        )
        await ctx.respond(
            embed=error_embed,
            delete_after=utils.DELETE_ERROR_DELAY,
        )
        return

    channel = guild.get_channel(author_channel_id)

    if lobby_is_locked(channel):
        error_embed = utils.create_error_embed(
            "The lobby is already locked.", bot_avatar_url
        )
        await ctx.respond(
            embed=error_embed,
            delete_after=utils.DELETE_ERROR_DELAY,
        )
        return

    channel = guild.get_channel(author_channel_id)
    lock_embed = utils.create_info_embed(
        "Channel locked", "Your lobby has been locked.", bot_avatar_url
    )

    await lock_lobby(channel)
    await ctx.respond(embed=lock_embed)


@lobby.child
@lightbulb.command("unlock", "Allows new members to join the lobby")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def unlock(ctx: lightbulb.SlashContext) -> None:
    """Unlocks a lobby so that new members can join.

    Called when a member uses /lobby unlock.

    Arguments:
        ctx: The context for the command.

    Returns:
        None.
    """
    guild_id = ctx.guild_id
    bot_avatar_url = plugin.bot.get_me().avatar_url

    if await command_is_disabled("unlock", guild_id):
        error_embed = utils.create_error_embed(
            "Sorry. This command has been disabled.", bot_avatar_url
        )
        await ctx.respond(
            embed=error_embed,
            delete_after=utils.DELETE_ERROR_DELAY,
        )
        return

    guild = ctx.get_guild()
    author_member = ctx.member
    author_voice_state = guild.get_voice_state(author_member)

    if author_voice_state is None or not await valid_clone(
        author_voice_state.channel_id
    ):
        error_embed = utils.create_error_embed(
            "You are not in a lobby.", bot_avatar_url
        )
        await ctx.respond(
            embed=error_embed,
            delete_after=utils.DELETE_ERROR_DELAY,
        )
        return

    author_channel_id = author_voice_state.channel_id
    document = await get_clone_document(author_channel_id)

    if document["clones"]["owner_id"] != ctx.member.id:
        error_embed = utils.create_error_embed(
            "You are not the owner of this lobby.", bot_avatar_url
        )
        await ctx.respond(
            embed=error_embed,
            delete_after=utils.DELETE_ERROR_DELAY,
        )
        return

    channel = guild.get_channel(author_channel_id)

    if not lobby_is_locked(channel):
        error_embed = utils.create_error_embed(
            "The lobby is already unlocked.", bot_avatar_url
        )
        await ctx.respond(
            embed=error_embed,
            delete_after=utils.DELETE_ERROR_DELAY,
        )
        return

    channel = guild.get_channel(author_channel_id)
    unlock_embed = utils.create_info_embed(
        "Channel unlocked", "Your lobby has been unlocked.", bot_avatar_url
    )

    await unlock_lobby(channel)
    await ctx.respond(embed=unlock_embed)


@lobby.child
@lightbulb.option("member", "The member to kick", type=hikari.Member)
@lightbulb.command("kick", "Kicks a member from the lobby")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def kick(ctx: lightbulb.SlashContext) -> None:
    """Kicks a member from the lobby.

    Called when a member uses /lobby kick <member>.

    Arguments:
        ctx: The context for the command.

    Returns:
        None.
    """
    guild_id = ctx.guild_id
    bot_avatar_url = plugin.bot.get_me().avatar_url

    if await command_is_disabled("kick", guild_id):
        error_embed = utils.create_error_embed(
            "Sorry. This command has been disabled.", bot_avatar_url
        )
        await ctx.respond(
            embed=error_embed,
            delete_after=utils.DELETE_ERROR_DELAY,
        )
        return

    guild = ctx.get_guild()
    author_member = ctx.member
    author_voice_state = guild.get_voice_state(author_member)

    if author_voice_state is None or not await valid_clone(
        author_voice_state.channel_id
    ):
        error_embed = utils.create_error_embed(
            "You are not in a lobby.", bot_avatar_url
        )
        await ctx.respond(
            embed=error_embed,
            delete_after=utils.DELETE_ERROR_DELAY,
        )
        return

    author_channel_id = author_voice_state.channel_id
    document = await get_clone_document(author_channel_id)

    if document["clones"]["owner_id"] != author_member.id:
        error_embed = utils.create_error_embed(
            "You are not the owner of this lobby.", bot_avatar_url
        )
        await ctx.respond(
            embed=error_embed,
            delete_after=utils.DELETE_ERROR_DELAY,
        )
        return

    target_member = ctx.options.member
    target_voice_state = guild.get_voice_state(target_member)

    if target_voice_state is None or author_channel_id != target_voice_state.channel_id:
        error_embed = utils.create_error_embed(
            "That member is not in the lobby.", bot_avatar_url
        )
        await ctx.respond(
            embed=error_embed,
            delete_after=utils.DELETE_ERROR_DELAY,
        )
        return

    kick_embed = utils.create_info_embed(
        "Member kicked",
        f"`{target_member.username}` has been kicked from the lobby.",
        bot_avatar_url,
    )

    await target_member.edit(voice_channel=None)
    await ctx.respond(embed=kick_embed)


@lobby.child
@lightbulb.option("member", "The member to ban", type=hikari.Member)
@lightbulb.command("ban", "Bans a member from the lobby")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def ban(ctx: lightbulb.SlashContext) -> None:
    """Bans a member from the lobby.

    Called when a member uses /lobby ban <member>.

    Arguments:
        ctx: The context for the command.

    Returns:
        None.
    """
    guild_id = ctx.guild_id
    bot_avatar_url = plugin.bot.get_me().avatar_url

    if await command_is_disabled("ban", guild_id):
        error_embed = utils.create_error_embed(
            "Sorry. This command has been disabled.", bot_avatar_url
        )
        await ctx.respond(
            embed=error_embed,
            delete_after=utils.DELETE_ERROR_DELAY,
        )
        return

    guild = ctx.get_guild()
    author_member = ctx.member
    author_voice_state = guild.get_voice_state(author_member)

    if author_voice_state is None or not await valid_clone(
        author_voice_state.channel_id
    ):
        error_embed = utils.create_error_embed(
            "You are not in a lobby.", bot_avatar_url
        )
        await ctx.respond(
            embed=error_embed,
            delete_after=utils.DELETE_ERROR_DELAY,
        )
        return

    author_channel_id = author_voice_state.channel_id
    document = await get_clone_document(author_channel_id)

    if document["clones"]["owner_id"] != author_member.id:
        error_embed = utils.create_error_embed(
            "You are not the owner of this lobby.", bot_avatar_url
        )
        await ctx.respond(
            embed=error_embed,
            delete_after=utils.DELETE_ERROR_DELAY,
        )
        return

    author_channel = guild.get_channel(author_channel_id)
    target_member = ctx.options.member
    target_voice_state = guild.get_voice_state(target_member)

    if member_is_banned(author_channel, target_member):
        error_embed = utils.create_error_embed(
            "That member is already banned.", bot_avatar_url
        )
        await ctx.respond(
            embed=error_embed,
            delete_after=utils.DELETE_ERROR_DELAY,
        )
        return

    if (
        target_voice_state is not None
        and author_channel_id == target_voice_state.channel_id
    ):
        await target_member.edit(voice_channel=None)

    ban_embed = utils.create_info_embed(
        "Member banned",
        f"`{target_member.username}` has been banned from the lobby.",
        bot_avatar_url,
    )

    await ban_member(author_channel, target_member)
    await ctx.respond(embed=ban_embed)


@lobby.child
@lightbulb.option("member", "The member to unban", type=hikari.Member)
@lightbulb.command("unban", "Unbans a member from the lobby")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def unban(ctx: lightbulb.SlashContext) -> None:
    """Unbans a member from the lobby.

    Called when a member uses /lobby ban <member>.

    Arguments:
        ctx: The context for the command.

    Returns:
        None.
    """
    guild_id = ctx.guild_id
    bot_avatar_url = plugin.bot.get_me().avatar_url

    if await command_is_disabled("unban", guild_id):
        error_embed = utils.create_error_embed(
            "Sorry. This command has been disabled.", bot_avatar_url
        )
        await ctx.respond(
            embed=error_embed,
            delete_after=utils.DELETE_ERROR_DELAY,
        )
        return

    guild = ctx.get_guild()
    author_member = ctx.member
    author_voice_state = guild.get_voice_state(author_member)

    if author_voice_state is None or not await valid_clone(
        author_voice_state.channel_id
    ):
        error_embed = utils.create_error_embed(
            "You are not in a lobby.", bot_avatar_url
        )
        await ctx.respond(
            embed=error_embed,
            delete_after=utils.DELETE_ERROR_DELAY,
        )
        return

    author_channel_id = author_voice_state.channel_id
    document = await get_clone_document(author_channel_id)

    if document["clones"]["owner_id"] != author_member.id:
        error_embed = utils.create_error_embed(
            "You are not the owner of this lobby.", bot_avatar_url
        )
        await ctx.respond(
            embed=error_embed,
            delete_after=utils.DELETE_ERROR_DELAY,
        )
        return

    author_channel = guild.get_channel(author_channel_id)
    target_member = ctx.options.member

    if not member_is_banned(author_channel, target_member):
        error_embed = utils.create_error_embed(
            "That member is not banned.", bot_avatar_url
        )
        await ctx.respond(
            embed=error_embed,
            delete_after=utils.DELETE_ERROR_DELAY,
        )
        return

    unban_embed = utils.create_info_embed(
        "Member unbanned",
        f"`{target_member.username}` has been unbanned from the lobby.",
        bot_avatar_url,
    )

    await unban_member(author_channel, target_member)
    await ctx.respond(embed=unban_embed)


@lobby.set_error_handler()
async def channel_errors(event: lightbulb.CommandErrorEvent) -> bool:
    """Handles errors for the lobby command and its various subcommands.

    Arguments:
        event: The event that was fired.

    Returns:
        True if the exception can be handled, false if not.
    """
    exception = event.exception
    bot_avatar_url = plugin.bot.get_me().avatar_url

    if isinstance(exception, lightbulb.MissingRequiredPermission):
        error_embed = utils.create_error_embed(
            "You don't have permission to use this command.", bot_avatar_url
        )
        await event.context.respond(
            embed=error_embed,
            delete_after=utils.DELETE_ERROR_DELAY,
        )
        return True

    elif isinstance(exception, lightbulb.BotMissingRequiredPermission):
        error_embed = utils.create_error_embed(
            "I am missing the permissions required to do that.",
            bot_avatar_url,
        )
        await event.context.respond(
            embed=error_embed,
            delete_after=utils.DELETE_ERROR_DELAY,
        )
        return True

    return False


def load(bot: lightbulb.BotApp) -> None:
    """Loads the 'Lobbies' plugin. Called when extension is loaded.

    Arguments:
        bot: The bot application to add the plugin to.

    Returns:
        None.
    """
    bot.add_plugin(plugin)
