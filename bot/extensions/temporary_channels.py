import hikari
import lightbulb

plugin = lightbulb.Plugin("Temporary Channels")


@plugin.listener(hikari.StartedEvent)
async def remove_old_data(event: hikari.StartedEvent) -> None:
    pass


@plugin.listener(hikari.GuildLeaveEvent)
async def remove_guild_data(event: hikari.GuildLeaveEvent) -> None:
    pass


@plugin.listener(hikari.GuildChannelDeleteEvent)
async def remove_guild_channel_data(event: hikari.GuildChannelDeleteEvent) -> None:
    pass


@plugin.listener(hikari.VoiceStateUpdateEvent)
async def template_member_join(event):
    pass


@plugin.listener(hikari.VoiceStateUpdateEvent)
async def lobby_member_leave(event):
    pass


@plugin.listener(hikari.VoiceStateUpdateEvent)
async def lobby_owner_leave(event):
    pass


@plugin.command
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command("lobby", "Base of the lobby command group")
@lightbulb.implements(lightbulb.SlashCommandGroup, lightbulb.PrefixCommandGroup)
async def lobby(context: lightbulb.SlashContext | lightbulb.PrefixContext):
    pass


@lobby.child
@lightbulb.command("create", "Creates a template channel to spawn lobbies")
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def create(context: lightbulb.SlashContext | lightbulb.PrefixContext):
    pass


@lobby.child
@lightbulb.command("rename", "Renames the lobby channel")
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def rename(context: lightbulb.SlashContext | lightbulb.PrefixContext):
    pass


@lobby.child
@lightbulb.command("kick", "Kicks a member from the lobby channel")
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def kick(context: lightbulb.SlashContext | lightbulb.PrefixContext):
    pass


@lobby.child
@lightbulb.command("owner", "Designates a member as the owner of the lobby channel")
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def owner(context: lightbulb.SlashContext | lightbulb.PrefixContext):
    pass


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
