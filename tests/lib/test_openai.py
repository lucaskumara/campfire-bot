from lib import openai


def test_prompt() -> None:
    response = openai.prompt("Hello!")

    assert response != ""
