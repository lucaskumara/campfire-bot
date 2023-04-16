import hikari
import lightbulb
import os

from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    bot = lightbulb.BotApp(
        token=os.getenv("TOKEN"),
        prefix=lightbulb.when_mentioned_or(["campfire ", "camp "]),
        intents=hikari.Intents.ALL,
    )

    bot.load_extensions_from("./extensions")
    bot.run(
        activity=hikari.Activity(
            name="over your servers!", type=hikari.ActivityType.WATCHING
        ),
        status=hikari.Status.IDLE,
    )
