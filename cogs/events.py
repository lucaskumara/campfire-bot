import discord
import aiosqlite
from discord.ext import commands


class Events(commands.Cog):
    '''Cog containing various bot wide events.'''

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        '''Global event handler. Not specific to certain commands.'''

        # Let the commands own error handler handle its errors
        if ctx.command is not None and ctx.command.has_error_handler():
            return

        # If the prefix failed to find a command to run
        if isinstance(error, commands.CommandNotFound):
            pass

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        '''Add server prefix to bot database.'''
        async with aiosqlite.connect('./campfire.db') as db:
            await db.execute('CREATE TABLE IF NOT EXISTS prefixes (guildid INTEGER, prefix TEXT)')
            await db.execute('INSERT INTO prefixes VALUES (?, ?)', (guild.id, '+'))
            await db.commit()

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        '''Remove server prefix from bot database.'''
        async with aiosqlite.connect('./campfire.db') as db:
            await db.execute('DELETE FROM prefixes WHERE guildid = ?', (guild.id, ))
            await db.commit()


def setup(bot):
    bot.add_cog(Events(bot))
