import hikari
import pytest

from lib import responses
from unittest.mock import MagicMock, AsyncMock, patch


@pytest.fixture
def mock_field_name() -> str:
    return "Sample Name"


@pytest.fixture
def mock_field_value() -> str:
    return "Sample Value"


@pytest.fixture
def mock_embed_title() -> str:
    return "Sample Title"


@pytest.fixture
def mock_embed_description() -> str:
    return "Sample Description"


def test_field(mock_field_name: str, mock_field_value: str) -> None:
    result = responses.Field(mock_field_name, mock_field_value, False)

    assert result.name == mock_field_name
    assert result.value == mock_field_value
    assert result.inline == False


def test_field_attach(mock_field_name: str, mock_field_value: str) -> None:
    mock_embed = MagicMock()
    mock_embed.add_field = MagicMock()

    field = responses.Field(mock_field_name, mock_field_value, False)
    field.attach(mock_embed)

    mock_embed.add_field.assert_called_once_with(
        mock_field_name, mock_field_value, inline=False
    )


def test_build_embed(mock_embed_title: str, mock_embed_description: str) -> None:
    mock_embed_icon_url = MagicMock()

    sample_embed_colour = hikari.Colour(0xE67E22)
    sample_embed_fields = [
        responses.Field(mock_field_name, mock_field_value, inline=False),
        responses.Field(mock_field_name, mock_field_value, inline=True),
    ]

    result = responses.build_embed(
        mock_embed_title,
        mock_embed_description,
        mock_embed_icon_url,
        sample_embed_colour,
        sample_embed_fields,
    )

    assert isinstance(result, hikari.Embed)
    assert result.title == mock_embed_title
    assert result.description == mock_embed_description
    assert result.author.icon is not None
    assert result.colour == sample_embed_colour

    for embed_field, field_object in zip(result.fields, sample_embed_fields):
        assert embed_field.name == field_object.name
        assert embed_field.value == field_object.value
        assert embed_field.is_inline == field_object.inline


@patch("lib.responses.build_embed", return_value=MagicMock())
@pytest.mark.asyncio
async def test_info(
    mock_build_embed: MagicMock, mock_embed_title: str, mock_embed_description: str
) -> None:
    mock_context = MagicMock()
    mock_context.respond = AsyncMock()

    await responses.info(mock_context, mock_embed_title, mock_embed_description)

    mock_context.respond.assert_awaited_once_with(embed=mock_build_embed.return_value)


@patch("lib.responses.ButtonNavigator", return_value=AsyncMock())
@pytest.mark.asyncio
async def test_paginated_info(
    mock_ButtonNavigator: AsyncMock, mock_embed_title: str, mock_embed_description: str
) -> None:
    mock_context = MagicMock()

    await responses.paginated_info(
        mock_context, mock_embed_title, mock_embed_description, []
    )

    mock_ButtonNavigator.return_value.run.assert_awaited_once_with(mock_context)


@patch("lib.responses.build_embed", return_value=MagicMock())
@pytest.mark.asyncio
async def test_error(mock_build_embed: MagicMock, mock_embed_description: str) -> None:
    mock_context = MagicMock()
    mock_context.respond = AsyncMock()

    await responses.error(mock_context, mock_embed_description)

    mock_context.respond.assert_awaited_once_with(
        embed=mock_build_embed.return_value,
        delete_after=responses.ERROR_MESSAGE_DELETE_DELAY,
    )
