import hikari
import lightbulb
import os
import sys

from dotenv import load_dotenv


sys.path.append(os.path.abspath(".."))

load_dotenv()


if __name__ == "__main__":
    if os.name != "nt":
        import uvloop

        uvloop.install()

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
