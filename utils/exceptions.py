import lightbulb
import typing


def evaluate_exception(
    exception: lightbulb.LightbulbError,
    exception_type: typing.Type[lightbulb.LightbulbError],
):
    """Evaluates whether an exception is of or contains a specified type.

    Check if the exception type is the specified type. If it isn't, check its causes to
    see if it contains the exception type.

    Arguments:
        exception: The exception to check.
        exception_type: The type to check for.

    Returns:
        True if the except is or contains the type, false if not.
    """
    if type(exception) is exception_type:
        return True

    if hasattr(exception, "causes"):
        for cause in exception.causes:
            if type(cause) is exception_type:
                return True

    return False
