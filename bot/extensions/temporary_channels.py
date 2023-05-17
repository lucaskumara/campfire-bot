import hikari
import lightbulb

import lib.channels as channels
import lib.responses as responses

plugin = lightbulb.Plugin("Temporary Channels")


@plugin.listener(hikari.StartedEvent)
async def remove_old_data(event: hikari.StartedEvent) -> None:
    collection = plugin.bot.d.mongo_database.channels
    documents = await channels.get_all_documents(plugin.bot.d.mongo_database.channels)

    for document in documents:
        try:
            await plugin.bot.rest.fetch_channel(document["channel_id"])
        except:
            await channels.delete_template(collection, document["channel_id"])
            await channels.delete_clone(collection, document["channel_id"])


@plugin.listener(hikari.GuildLeaveEvent)
async def remove_guild_data(event: hikari.GuildLeaveEvent) -> None:
    collection = plugin.bot.d.mongo_database.channels

    await channels.delete_guild_data(collection, event.guild_id)


@plugin.listener(hikari.GuildChannelDeleteEvent)
async def remove_guild_channel_data(event: hikari.GuildChannelDeleteEvent) -> None:
    collection = plugin.bot.d.mongo_database.channels

    await channels.delete_template(collection, event.channel_id)
    await channels.delete_clone(collection, event.channel_id)


@plugin.listener(hikari.VoiceStateUpdateEvent)
async def template_member_join(event: hikari.VoiceStateUpdateEvent) -> None:
    if not channels.joined_a_channel(event.state):
        return

    collection = plugin.bot.d.mongo_database.channels
    channel = await plugin.bot.rest.fetch_channel(event.state.channel_id)
    template = await channels.TemplateChannel.get(collection, channel)

    if template is None:
        return

    clone = await template.spawn_clone(event.state.member, "Lobby")

    await event.state.member.edit(voice_channel=clone.channel)


@plugin.listener(hikari.VoiceStateUpdateEvent)
async def lobby_member_leave(event: hikari.VoiceStateUpdateEvent) -> None:
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
async def lobby(context: lightbulb.SlashContext | lightbulb.PrefixContext):
    pass


@lobby.child
@lightbulb.command("create", "Creates a template channel to spawn lobbies")
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def create(context: lightbulb.SlashContext | lightbulb.PrefixContext):
    collection = plugin.bot.d.mongo_databse.channels

    await channels.TemplateChannel.create(
        collection,
        context.get_guild(),
        "New Lobby - Edit Me!",
    )
    await responses.info(
        context, "Channel Created", "You lobby has been created. Feel free to edit it!"
    )


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
