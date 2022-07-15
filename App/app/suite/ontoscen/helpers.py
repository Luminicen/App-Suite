def get_user_input(text: str) -> str:
    """Wrap input() to mock it in tests.

    Arguments:
        text (str): Text to be displayed to the user.

    Returns:
        str: User input.
    """

    return input(text)
