import hikari
import lightbulb

import campfire.openai as openai
import campfire.profanity as profanity
import campfire.responses as responses

plugin = lightbulb.Plugin("Profanity Filter")


async def handle_profanity(
    message: hikari.Message,
    message_id: hikari.Snowflake,
    channel_id: hikari.Snowflake,
    guild_id: hikari.Snowflake,
) -> None:
    """Checks a message for profanity. If the message contains profanity, delete it.

    Arguments:
        message: The message to check.
        message_id: The ID of the message to check.
        channel_id: The ID of the channel the message was sent in.
        guild_id: The ID of the guild the message was sent in.

    Returns:
        None.
    """
    response = openai.prompt(
        f"""
        Determine if this message contains profanity.

        Expected Response: YES or NO

        Message: "{message}"
        """
    )

    if response == "YES" and await profanity.is_filter_enabled(plugin.bot, guild_id):
        await plugin.bot.rest.delete_message(channel_id, message_id)


async def toggle_filter(
    context: lightbulb.SlashContext | lightbulb.PrefixContext,
    guild_id: hikari.Snowflake,
) -> None:
    """Toggles the profanity filter on or off for a guild.

    Arguments:
        context: The command context.
        guild_id: The ID of the guild to toggle the profanity filter for.

    Returns:
        None.
    """
    if await profanity.is_filter_enabled(plugin.bot, guild_id):
        await profanity.disable_filter(plugin.bot, guild_id)
        await responses.info(
            context,
            "Filter disabled",
            f"Profanity will no longer be filtered from chat.",
        )
    else:
        await profanity.enable_filter(plugin.bot, guild_id)
        await responses.info(
            context,
            "Filter enabled",
            f"Profanity will now be filtered from chat.",
        )


@plugin.listener(hikari.GuildMessageCreateEvent)
async def detect_profanity_on_message(event: hikari.GuildMessageCreateEvent) -> None:
    """Detect for profanity when a message is sent."""
    await handle_profanity(
        event.content, event.message_id, event.channel_id, event.guild_id
    )


@plugin.command
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command("toggleprofanityfilter", "Toggles the profanity filter on or off")
@lightbulb.implements(lightbulb.SlashCommand, lightbulb.PrefixCommand)
async def toggle_profanity_filter(
    context: lightbulb.SlashContext | lightbulb.PrefixContext,
) -> None:
    """The toggleprofanityfilter command."""
    await toggle_filter(context, context.guild_id)


def load(bot: lightbulb.BotApp) -> None:
    """Loads the profanity filter plugin."""
    bot.add_plugin(plugin)
