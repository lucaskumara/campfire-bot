import hikari
import lightbulb
import typing

from utils.channels import clone_channel
from utils.exceptions import evaluate_exception
from utils.responses import info_response, error_response

CHOICES = ["rename", "lock", "unlock", "kick", "ban", "unban"]

plugin = lightbulb.Plugin("Lobbies")


async def create_template(
    channel_name: str, channel_guild: hikari.GatewayGuild
) -> hikari.GuildVoiceChannel:
    """Creates a template channel and stores the channel data in the database.

    Creates a new voice channel and pushes its channel ID into the guild document
    templates list if it exists. Otherwise, create a new guild document with the
    templates list containing the template channel ID.

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

    Clones a template voice channel and pushes its channel ID into the guild document
    clones list if it exists. Otherwise, create a new guild document with the clones
    list containing a document containing info about the clone channel.

    Arguments:
        template_channel: The template channel to clone.
        owner: The owner of the clone channel.

    Returns:
        The created clone channel.
    """
    channel_clone = await clone_channel(
        template_channel, name=f"{owner.username}'s Lobby"
    )

    await plugin.bot.d.db_conn.lobby_channels.update_one(
        {"guild_id": channel_clone.guild_id},
        {
            "$push": {
                "clones": {
                    "clone_id": channel_clone.id,
                    "template_id": template_channel.id,
                    "owner_id": owner.id,
                }
            }
        },
        upsert=True,
    )

    return channel_clone


async def get_clone_document(
    channel_id: hikari.Snowflake,
) -> typing.Optional[dict]:
    """Gets the clone channel document from the database.

    Uses an aggregate to find documents containing the channel id (should be a single
    document), unwinding clones and then matching to the unwound document with the
    channel id (should also be a single document). Limits the result to a single
    document just incase.

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

    Checks if there is a document that contains the channel id in its array of clone
    documents.

    Arguments:
        channel: The clone channel.

    Returns:
        True if the channel is a clone, false if not.
    """
    document = await plugin.bot.d.db_conn.lobby_channels.find_one(
        {"clones.clone_id": channel_id}
    )

    return document is not None


async def enable_command(command_name: str, guild: hikari.GatewayGuild) -> None:
    """Enables a command in a guild.

    Enables a command in a guild by removing it from the guilds list of disabled
    commands.

    Arguments:
        command_name: The name of the command.
        guild: The guild to enable the command in.

    Returns:
        None.
    """
    await plugin.bot.d.db_conn.lobby_disabled_commands.update_one(
        {"guild_id": guild.id}, {"$pull": {"disabled_commands": command_name}}
    )


async def disable_command(command_name: str, guild: hikari.GatewayGuild) -> None:
    """Disables a command in a guild.

    Disables a command in a guild by adding it to the guilds list of disabled commands.

    Arguments:
        command_name: The name of the command.
        guild: The guild to disable the command in.

    Returns:
        None.
    """
    await plugin.bot.d.db_conn.lobby_disabled_commands.update_one(
        {"guild_id": guild.id},
        {"$push": {"disabled_commands": command_name}},
        upsert=True,
    )


async def command_is_disabled(command_name: str, guild: hikari.GatewayGuild) -> bool:
    """Checks if a command is disabled in a guild.

    Checks if a command is disabled in a guild by checking if it is in the guilds list
    of disabled commands.

    Arguments:
        command_name: The name of the command.
        guild: The guild to check if the command is disabled in.

    Returns:
        True if the command is disabled otherwise false.
    """
    document = await plugin.bot.d.db_conn.lobby_disabled_commands.find_one(
        {"guild_id": guild.id, "disabled_commands": command_name}
    )

    return document is not None


async def lock_lobby(lobby: hikari.GuildVoiceChannel) -> None:
    """Locks a lobby and prevents new members from joining.

    Locks a lobby by obtaining the channel permissions and the @everyone role from the
    associated guild. If the @everyone role has existing permissions in the channel,
    modify them to revoke the ability to join the channel. If there are no existing
    permissions for the @everyone role, create new permissions denying the ability for
    the role to connect to the channel.

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

    Unlocks a lobby by obtaining the channel permissions and the @everyone role from
    the associated guild. If the @everyone role has existing permissions in the
    channel, modify them to include the ability to join the channel. If there are no
    existing permissions for the @everyone role, create new permissions allowing the
    ability for the role to connect to the channel.

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
    @everyone role from the associated guild. If the channel has permissions preventing
    members with the @everyone role from joining, the channel is locked.

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

    Bans a member by obtaining the members permissions in the channel. If the member
    has existing permissions in the channel, modify them to revoke the ability to join
    the channel. If there are no existing permissions for the member, create new
    permissions denying the ability for the role to connect to the channel.

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

    Unbans a member by obtaining the members permissions in the channel. If the member
    has existing permissions in the channel, modify them to include the ability to join
    the channel. If there are no existing permissions for the member, create new
    permissions allowing the ability for the role to connect to the channel.

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

    Checks if a member is banned by checking if the channel has permissions denying the
    member from joining. If so, the member is banned.

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

    Tries to fetch all channels in the templates array and clone documents array of the
    lobby_channels database. If the channel cannot be fetched, delete its entry from
    its correct spot in the database.

    Arguments:
        event: The event that was fired.

    Returns:
        None.
    """
    channel_cursor = plugin.bot.d.db_conn.lobby_channels

    async for document in channel_cursor.find({}):
        template_ids = document.get("templates", [])
        clone_documents = document.get("clones", [])
        clone_ids = [clone["clone_id"] for clone in clone_documents]

        delete_templates = []
        delete_clones = []

        for id in template_ids:
            try:
                await plugin.bot.rest.fetch_channel(id)
            except:
                delete_templates.append(id)

        for id in clone_ids:
            try:
                await plugin.bot.rest.fetch_channel(id)
            except:
                delete_clones.append(id)

        guild_id = document["guild_id"]

        await channel_cursor.update_many(
            {"guild_id": guild_id}, {"$pull": {"templates": {"$in": delete_templates}}}
        )
        await channel_cursor.update_many(
            {"guild_id": guild_id},
            {"$pull": {"clones": {"clone_id": {"$in": delete_clones}}}},
        )


@plugin.listener(hikari.StartedEvent)
async def purge_guild_documents(event: hikari.StartedEvent) -> None:
    """Removes data of any guild the bot is no longer a part of.

    Tries to fetch all the guilds with data in the lobby_channels and
    lobby_disabled_commands databases. If the guild cannot be fetched, delete the
    document from the database.

    Arguments:
        event: The event that was fired.

    Returns:
        None.
    """
    channel_cursor = plugin.bot.d.db_conn.lobby_channels
    disabled_command_cursor = plugin.bot.d.db_conn.lobby_disabled_commands

    async for document in channel_cursor.find({}):
        guild_id = document["guild_id"]

        try:
            await plugin.bot.rest.fetch_guild(guild_id)
        except:
            await channel_cursor.delete_one({"guild_id": guild_id})

    async for document in disabled_command_cursor.find({}):
        guild_id = document["guild_id"]

        try:
            await plugin.bot.rest.fetch_guild(guild_id)
        except:
            await disabled_command_cursor.delete_one({"guild_id": guild_id})


@plugin.listener(hikari.GuildLeaveEvent)
async def delete_guild_document(event: hikari.GuildLeaveEvent) -> None:
    """Deletes guild document from the database when the bot leaves a guild.

    Arguments:
        event: The event that was fired.

    Returns:
        None.
    """
    db_filter = {"guild_id": event.guild_id}

    await plugin.bot.d.db_conn.lobby_channels.delete_one(db_filter)
    await plugin.bot.d.db_conn.lobby_disabled_commands.delete_one(db_filter)


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

    If a template channel is joined by a member, clones the channel and moves them to
    the clone.

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

    If a clone channel is left by a member, checks if the channel has no members left
    in it and deletes the channel if so.

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
    lightbulb.bot_has_guild_permissions(hikari.Permissions.MOVE_MEMBERS),
    lightbulb.guild_only,
)
@lightbulb.command("lobby", "Base of lobby command group")
@lightbulb.implements(lightbulb.SlashCommandGroup, lightbulb.PrefixCommandGroup)
async def lobby(
    context: typing.Union[lightbulb.SlashContext, lightbulb.PrefixContext]
) -> None:
    """Base of the channel command group.

    Arguments:
        context: The context for the command.

    Returns:
        None.
    """
    pass


@lobby.child
@lightbulb.command("create", "Creates a new lobby template", inherit_checks=True)
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def create(
    context: typing.Union[lightbulb.SlashContext, lightbulb.PrefixContext]
) -> None:
    """Creates a new lobby template channel in the guild.

    Arguments:
        context: The context for the command.

    Returns:
        None.
    """
    await create_template("New Lobby - Edit me!", context.get_guild())
    await info_response(
        context, "Channel created", "You lobby has been created. Feel free to edit it!"
    )


@lobby.child
@lightbulb.add_checks(
    lightbulb.has_guild_permissions(hikari.Permissions.ADMINISTRATOR),
    lightbulb.guild_only,
)
@lightbulb.option("command", "The command to enable", choices=CHOICES)
@lightbulb.command("enable", "Enables the usage of a lobby command")
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def enable(
    context: typing.Union[lightbulb.SlashContext, lightbulb.PrefixContext]
) -> None:
    """Enables a commands usage in the guild.

    The command can only be used by guild members with the administrator permission.

    Arguments:
        context: The context for the command.

    Returns:
        None.
    """
    command_name = context.options.command
    guild = context.get_guild()

    # Check if the command is already enabled in the guild
    if not await command_is_disabled(command_name, guild):
        await error_response(context, "That command is already enabled.")
        return

    await enable_command(command_name, guild)
    await info_response(
        context, "Command enabled", f"The command `{command_name}` has been enabled."
    )


@lobby.child
@lightbulb.add_checks(
    lightbulb.has_guild_permissions(hikari.Permissions.ADMINISTRATOR),
    lightbulb.guild_only,
)
@lightbulb.option("command", "The command to disable", choices=CHOICES)
@lightbulb.command("disable", "Disables the usage of a lobby command")
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def disable(
    context: typing.Union[lightbulb.SlashContext, lightbulb.PrefixContext]
) -> None:
    """Disables a commands usage in the guild.

    The command can only be used by guild members with the administrator permission.

    Arguments:
        context: The context for the command.

    Returns:
        None.
    """
    command_name = context.options.command
    guild = context.get_guild()

    # Check if the command is already disabled in the guild
    if await command_is_disabled(command_name, guild):
        await error_response(context, "That command is already disabled.")
        return

    await disable_command(command_name, guild)
    await info_response(
        context, "Command disabled", f"The command `{command_name}` has been disabled."
    )


@lobby.child
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.option("name", "The new lobby name")
@lightbulb.command("rename", "Renames the lobby")
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def rename(
    context: typing.Union[lightbulb.SlashContext, lightbulb.PrefixContext]
) -> None:
    """Renames a the authors current lobby in the guild.

    Arguments:
        context: The context for the command.

    Returns:
        None.
    """
    guild = context.get_guild()

    # Check if the command is disabled in the guild
    if await command_is_disabled("rename", guild):
        await error_response(context, "Sorry. This command has been disabled.")
        return

    author_member = context.member
    author_voice_state = guild.get_voice_state(author_member)

    # Check if the command author is not a lobby channel
    if author_voice_state is None or not await valid_clone(
        author_voice_state.channel_id
    ):
        await error_response(context, "You are not in a lobby.")
        return

    author_channel_id = author_voice_state.channel_id
    document = await get_clone_document(author_channel_id)

    # Check if the command author is not the owner of the lobby they are in
    if document["clones"]["owner_id"] != author_member.id:
        await error_response(context, "You are not the owner of this lobby")
        return

    clean_name = context.options.name.strip()

    # Check if the desired new name is too long or too short
    if not (1 <= len(clean_name) <= 100):
        await error_response(context, "The new name must be 1-100 characters long.")
        return

    lobby = guild.get_channel(author_channel_id)

    try:
        await lobby.edit(name=clean_name)
        await info_response(
            context, "Channel renamed", f"The lobby has been renamed to `{clean_name}`."
        )

    # Let the command author know if they are being rate limited
    except hikari.errors.RateLimitedError as error:
        await error_response(
            context,
            f"You are being rate limited. Try again in `{int(error.retry_after)}` seconds.",
        )


@lobby.child
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command("lock", "Prevents new members from joining the lobby")
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def lock(
    context: typing.Union[lightbulb.SlashContext, lightbulb.PrefixContext]
) -> None:
    """Locks a lobby so that new members can not join.

    Arguments:
        context: The context for the command.

    Returns:
        None.
    """
    guild = context.get_guild()

    # Check if the command is disabled in the guild
    if await command_is_disabled("lock", guild):
        await error_response(context, "Sorry. This command has been disabled.")
        return

    author_member = context.member
    author_voice_state = guild.get_voice_state(author_member)

    # Check if the command author is not a lobby channel
    if author_voice_state is None or not await valid_clone(
        author_voice_state.channel_id
    ):
        await error_response(context, "You are not in a lobby.")
        return

    author_channel_id = author_voice_state.channel_id
    document = await get_clone_document(author_channel_id)

    # Check if the command author is not the owner of the lobby they are in
    if document["clones"]["owner_id"] != author_member.id:
        await error_response(context, "You are not the owner of this lobby.")
        return

    channel = guild.get_channel(author_channel_id)

    # Check if the lobby is already locked
    if lobby_is_locked(channel):
        await error_response(context, "The lobby is already locked.")
        return

    await lock_lobby(channel)
    await info_response(context, "Channel locked", "Your lobby has been locked.")


@lobby.child
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command("unlock", "Allows new members to join the lobby")
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def unlock(
    context: typing.Union[lightbulb.SlashContext, lightbulb.PrefixContext]
) -> None:
    """Unlocks a lobby so that new members can join.

    Arguments:
        context: The context for the command.

    Returns:
        None.
    """
    guild = context.get_guild()

    # Check if the command is disabled in the guild
    if await command_is_disabled("unlock", guild):
        await error_response(context, "Sorry. This command has been disabled.")
        return

    author_member = context.member
    author_voice_state = guild.get_voice_state(author_member)

    # Check if the command author is not a lobby channel
    if author_voice_state is None or not await valid_clone(
        author_voice_state.channel_id
    ):
        await error_response(context, "You are not in a lobby.")
        return

    author_channel_id = author_voice_state.channel_id
    document = await get_clone_document(author_channel_id)

    # Check if the command author is not the owner of the lobby they are in
    if document["clones"]["owner_id"] != author_member.id:
        await error_response(context, "You are not the owner of this lobby.")
        return

    channel = guild.get_channel(author_channel_id)

    # Check if the lobby is already unlocked
    if not lobby_is_locked(channel):
        await error_response(context, "The lobby is already unlocked.")
        return

    await unlock_lobby(channel)
    await info_response(context, "Channel unlocked", "Your lobby has been unlocked.")


@lobby.child
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.option("member", "The member to kick", type=hikari.Member)
@lightbulb.command("kick", "Kicks a member from the lobby")
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def kick(
    context: typing.Union[lightbulb.SlashContext, lightbulb.PrefixContext]
) -> None:
    """Kicks a member from the lobby.

    Arguments:
        context: The context for the command.

    Returns:
        None.
    """
    guild = context.get_guild()

    # Check if the command is disabled in the guild
    if await command_is_disabled("kick", guild):
        await error_response(context, "Sorry. This command has been disabled.")
        return

    author_member = context.member
    author_voice_state = guild.get_voice_state(author_member)

    # Check if the command author is not a lobby channel
    if author_voice_state is None or not await valid_clone(
        author_voice_state.channel_id
    ):
        await error_response(context, "You are not in a lobby.")
        return

    author_channel_id = author_voice_state.channel_id
    document = await get_clone_document(author_channel_id)

    # Check if the command author is not the owner of the lobby they are in
    if document["clones"]["owner_id"] != author_member.id:
        await error_response(context, "You are not the owner of this lobby.")
        return

    target_member = context.options.member
    target_voice_state = guild.get_voice_state(target_member)

    # Check if the target is not in the lobby
    if target_voice_state is None or author_channel_id != target_voice_state.channel_id:
        await error_response(context, "That member is not in the lobby.")
        return

    await target_member.edit(voice_channel=None)
    await info_response(
        context,
        "Member kicked",
        f"`{target_member.username}` has been kicked from the lobby.",
    )


@lobby.child
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.option("member", "The member to ban", type=hikari.Member)
@lightbulb.command("ban", "Bans a member from the lobby")
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def ban(
    context: typing.Union[lightbulb.SlashContext, lightbulb.PrefixContext]
) -> None:
    """Bans a member from the lobby.

    Arguments:
        context: The context for the command.

    Returns:
        None.
    """
    guild = context.get_guild()

    # Check if the command is disabled in the guild
    if await command_is_disabled("ban", guild):
        await error_response(context, "Sorry. This command has been disabled.")
        return

    author_member = context.member
    author_voice_state = guild.get_voice_state(author_member)

    # Check if the command author is not a lobby channel
    if author_voice_state is None or not await valid_clone(
        author_voice_state.channel_id
    ):
        await error_response(context, "You are not in a lobby.")
        return

    author_channel_id = author_voice_state.channel_id
    document = await get_clone_document(author_channel_id)

    # Check if the command author is not the owner of the lobby they are in
    if document["clones"]["owner_id"] != author_member.id:
        await error_response(context, "You are not the owner of this lobby.")
        return

    author_channel = guild.get_channel(author_channel_id)
    target_member = context.options.member
    target_voice_state = guild.get_voice_state(target_member)

    # Check if the target is already banned in the lobby
    if member_is_banned(author_channel, target_member):
        await error_response(context, "That member is already banned.")
        return

    if (
        target_voice_state is not None
        and author_channel_id == target_voice_state.channel_id
    ):
        await target_member.edit(voice_channel=None)

    await ban_member(author_channel, target_member)
    await info_response(
        context,
        "Member banned",
        f"`{target_member.username}` has been banned from the lobby.",
    )


@lobby.child
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.option("member", "The member to unban", type=hikari.Member)
@lightbulb.command("unban", "Unbans a member from the lobby")
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def unban(
    context: typing.Union[lightbulb.SlashContext, lightbulb.PrefixContext]
) -> None:
    """Unbans a member from the lobby.

    Arguments:
        context: The context for the command.

    Returns:
        None.
    """
    guild = context.get_guild()

    # Check if the command is disabled in the guild
    if await command_is_disabled("unban", guild):
        await error_response(context, "Sorry. This command has been disabled.")
        return

    author_member = context.member
    author_voice_state = guild.get_voice_state(author_member)

    # Check if the command author is not a lobby channel
    if author_voice_state is None or not await valid_clone(
        author_voice_state.channel_id
    ):
        await error_response(context, "You are not in a lobby.")
        return

    author_channel_id = author_voice_state.channel_id
    document = await get_clone_document(author_channel_id)

    # Check if the command author is not the owner of the lobby they are in
    if document["clones"]["owner_id"] != author_member.id:
        await error_response(context, "You are not the owner of this lobby.")
        return

    author_channel = guild.get_channel(author_channel_id)
    target_member = context.options.member

    # Check if the target is not already banned in the lobby
    if not member_is_banned(author_channel, target_member):
        await error_response(context, "That member is not banned.")
        return

    await unban_member(author_channel, target_member)
    await info_response(
        context,
        "Member unbanned",
        f"`{target_member.username}` has been unbanned from the lobby.",
    )


@lobby.set_error_handler()
async def channel_errors(event: lightbulb.CommandErrorEvent) -> bool:
    """Handles errors for the lobby command and its various subcommands.

    Arguments:
        event: The event that was fired.

    Returns:
        True if the exception can be handled, false if not.
    """
    exception = event.exception

    if evaluate_exception(exception, lightbulb.OnlyInGuild):
        return False

    elif evaluate_exception(exception, lightbulb.MissingRequiredPermission):
        await error_response(
            event.context, "You don't have permission to use that command."
        )
        return True

    elif evaluate_exception(exception, lightbulb.BotMissingRequiredPermission):
        await error_response(
            event.context,
            "I need permission to manage channels and move members to do that.",
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
