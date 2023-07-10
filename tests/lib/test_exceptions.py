import lightbulb

from lib import exceptions
from unittest.mock import MagicMock


def test_evaluate_exception_with_matching_exception_instance() -> None:
    result = exceptions.evaluate_exception(
        lightbulb.OnlyInGuild(), lightbulb.OnlyInGuild
    )

    assert result


def test_evaluate_exception_with_matching_exception_cause() -> None:
    mock_exception = MagicMock()
    mock_exception.causes = [lightbulb.OnlyInGuild]

    result = exceptions.evaluate_exception(mock_exception, lightbulb.OnlyInGuild)

    assert result


def test_evaluate_exception_with_non_matching_exception_instance() -> None:
    result = exceptions.evaluate_exception(lightbulb.OnlyInDM(), lightbulb.OnlyInGuild)

    assert not result


def test_evaluate_exception_with_non_matching_exception_cause() -> None:
    mock_exception = MagicMock()
    mock_exception.causes = [lightbulb.OnlyInDM]

    result = exceptions.evaluate_exception(mock_exception, lightbulb.OnlyInGuild)

    assert not result
