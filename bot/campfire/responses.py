import hikari
import lightbulb

from datetime import datetime, timezone
from hikari.components import ButtonStyle
from lightbulb.utils.nav import (
    ComponentButton as Button,
    ButtonNavigator,
    prev_page,
    next_page,
)
from lightbulb.utils.pag import EmbedPaginator

INFO_MESSAGE_COLOUR = hikari.Colour(0xE67E22)
ERROR_MESSAGE_COLOUR = None
ERROR_MESSAGE_DELETE_DELAY = 10


class Field:
    """A class to represent an embed field.

    Arguments:
        name: The name of the embed field.
        value: The value of the embed field.
        inline: Whether the field is inline or not.

    Attributes:
        name: The name of the embed field.
        vlaue: The value of the embed field.
        inline: Whether the field is inline or not.
    """

    def __init__(self, name: str, value: str, inline: bool = False):
        self.name = name
        self.value = value
        self.inline = inline

    def attach(self, embed: hikari.Embed) -> None:
        """Adds the field to an embed."""
        embed.add_field(self.name, self.value, inline=self.inline)


def build_embed(
    embed_title: str,
    embed_description: str,
    embed_icon_url: hikari.URL,
    embed_colour: hikari.Color,
    embed_fields: list[Field] = [],
) -> hikari.Embed:
    """Builds and returns a custom embed.

    Arguments:
        embed_title: The title of the embed.
        embed_description: The description of the embed.
        embed_icon: The icon of the embed.
        embed_colour: The colour of the embed.
        embed_fields: The fields to add to the embed.

    Returns:
        The build embed.
    """
    embed = hikari.Embed(
        title=embed_title,
        description=embed_description,
        colour=embed_colour,
        timestamp=datetime.now(timezone.utc),
    )

    embed.set_author(name="Campfire", icon=embed_icon_url)

    for field in embed_fields:
        field.attach(embed)

    return embed


async def info(
    context: lightbulb.SlashContext | lightbulb.PrefixContext,
    embed_title: str,
    embed_description: str,
) -> None:
    """Sends formatted response using an info embed.

    Arguments:
        context: The command context.
        embed_title: The title of the embed.
        embed_description: The description of the embed.

    Returns:
        None.
    """
    await context.respond(
        embed=build_embed(
            embed_title,
            embed_description,
            context.app.get_me().avatar_url,
            INFO_MESSAGE_COLOUR,
        )
    )


async def paginated_info(
    context: lightbulb.SlashContext | lightbulb.PrefixContext,
    embed_title: str,
    embed_description: str,
    embed_lines: list[str] = [],
) -> None:
    """Sends formatted response using a paginated info embed.

    Arguments:
        context: The command context.
        embed_title: The title of the embed.
        embed_description: The description of the embed.

    Returns:
        None.
    """
    paginator = EmbedPaginator(prefix="```", suffix="```", max_lines=10)

    @paginator.embed_factory()
    def paginated_embed_structure(index: int, content: str):
        """Specify how the paginated embed gets built."""
        embed = build_embed(
            embed_title,
            f"{embed_description} {content}",
            context.app.get_me().avatar_url,
            INFO_MESSAGE_COLOUR,
        )

        embed.set_footer(f"Page {index}")

        return embed

    for line in embed_lines:
        paginator.add_line(line)

    buttons = [
        Button("Previous", False, ButtonStyle.PRIMARY, "previous", prev_page),
        Button("Next", False, ButtonStyle.PRIMARY, "next", next_page),
    ]

    await ButtonNavigator(paginator.build_pages(), buttons=buttons).run(context)


async def error(
    context: lightbulb.SlashContext | lightbulb.PrefixContext, embed_description: str
) -> None:
    """Sends formatted response using an error embed.

    Arguments:
        context: The command context.
        embed_description: The description of the embed.

    Returns:
        None.
    """
    await context.respond(
        embed=build_embed(
            None,
            embed_description,
            context.app.get_me().avatar_url,
            ERROR_MESSAGE_COLOUR,
        )
    )
