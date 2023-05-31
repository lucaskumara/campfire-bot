from lib import openai


def test_prompt():
    response = openai.prompt("Hello!")

    assert type(response) is str
    assert response != ""
