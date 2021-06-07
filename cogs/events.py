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


def setup(bot):
    bot.add_cog(Events(bot))
