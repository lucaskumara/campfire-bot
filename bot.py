import discord
import logging
import os

from discord.ext import commands
from configparser import ConfigParser
from helpcmd import HelpCommand

# Load config
config = ConfigParser()
config.read('config.ini')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s: %(name)s] %(levelname)s - %(message)s'
)

# Intantiate bot
bot = commands.Bot(
    command_prefix=commands.when_mentioned_or('+'),
    help_command=HelpCommand()
)
bot.logger = logging.getLogger('bot')

for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        bot.load_extension(f'cogs.{filename[:-3]}')

if __name__ == '__main__':
    bot.run(config['BOT']['TOKEN'])
