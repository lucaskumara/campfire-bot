import discord
import logging
import os
import aiosqlite

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

async def command_prefix(bot, message):
    '''Returns the bot command prefix.'''

    # Pull guild prefix from the database
    async with aiosqlite.connect('./campfire.db') as db:
        async with db.execute('SELECT prefix FROM prefixes WHERE guildid = ?', (message.guild.id, )) as cursor:
            row = await cursor.fetchone()

    return commands.when_mentioned_or(row[0])(bot, message)

# Intantiate bot
bot = commands.Bot(
    command_prefix=command_prefix,
    help_command=HelpCommand(),
    status=discord.Status.idle,
    activity=discord.Game('@Campfire help')
)
bot.logger = logging.getLogger('bot')

# Load cogs
for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        bot.load_extension(f'cogs.{filename[:-3]}')

if __name__ == '__main__':
    bot.run(config['BOT']['TOKEN'])
