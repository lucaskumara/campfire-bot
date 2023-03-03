import lightbulb


def evaluate_exception(
    exception: lightbulb.LightbulbError,
    exception_type: type[lightbulb.LightbulbError],
):
    """Take apart a lightbulb exception to determine what type of error it is.

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
