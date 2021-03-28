import discord
from discord.ext import commands


class Admin(commands.Cog):
    '''Admin only commands to manipulate the bot.'''

    def __init__(self, bot):
        self.bot = bot
        self.delete_delay = 5

    @commands.is_owner()
    @commands.command(hidden=True)
    async def load(self, ctx, extension):
        '''Loads an extension.'''
        try:
            self.bot.load_extension(f'cogs.{extension}')
        except commands.ExtensionError as error:
            await ctx.message.add_reaction('👎')
            self.bot.logger.info(f'{error.__class__.__name__}: {error}')
        else:
            await ctx.message.add_reaction('👍')
            self.bot.logger.info(f'{extension} loaded')
        finally:
            await ctx.message.delete(delay=self.delete_delay)

    @commands.is_owner()
    @commands.command(hidden=True)
    async def unload(self, ctx, extension):
        '''Unloads an extension.'''
        try:
            self.bot.unload_extension(f'cogs.{extension}')
        except commands.ExtensionError as error:
            await ctx.message.add_reaction('👎')
            self.bot.logger.info(f'{error.__class__.__name__}: {error}')
        else:
            await ctx.message.add_reaction('👍')
            self.bot.logger.info(f'{extension} unloaded')
        finally:
            await ctx.message.delete(delay=self.delete_delay)

    @commands.is_owner()
    @commands.command(hidden=True)
    async def reload(self, ctx, extension):
        '''Reloads an extension.'''
        try:
            self.bot.reload_extension(f'cogs.{extension}')
        except commands.ExtensionError as error:
            await ctx.message.add_reaction('👎')
            self.bot.logger.info(f'{error.__class__.__name__}: {error}')
        else:
            await ctx.message.add_reaction('👍')
            self.bot.logger.info(f'{extension} reloaded')
        finally:
            await ctx.message.delete(delay=self.delete_delay)


def setup(bot):
    bot.add_cog(Admin(bot))
