import openai
import os


def prompt(message: str) -> str:
    """Prompts ChatGPT and returns its response.

    Arguments:
        message: The message to send to the model.

    Returns:
        The response from the model.
    """
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": message},
        ],
    )

    return response["choices"][0]["message"]["content"]
