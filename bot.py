import lightbulb
import configparser
import json

config = configparser.ConfigParser()
config.read("config.ini")

if config.has_option("OPTIONAL", "GUILDS"):
    guilds = json.loads(config.get("OPTIONAL", "GUILDS"))
else:
    guilds = []

bot = lightbulb.BotApp(token=config.get("BOT", "TOKEN"), default_enabled_guilds=guilds)

if __name__ == "__main__":
    bot.load_extensions_from("./extensions")
    bot.run()
