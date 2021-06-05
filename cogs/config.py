import discord
import aiosqlite

from discord.ext import commands
from helpers import throw_error


class Config(commands.Cog):
    '''Cog containing commands for server configuration.'''

    def __init__(self, bot):
        self.bot = bot
        self.delete_delay = 8

    @commands.command(usage='prefix <new prefix>')
    @commands.has_permissions(administrator=True)
    async def prefix(self, ctx, *, new_prefix):
        '''Sets the bot prefix within a server.'''

        # Set the guild prefix in the database
        async with aiosqlite.connect('./campfire.db') as db:
            await db.execute('UPDATE prefixes SET prefix = ? WHERE guildid = ?', (new_prefix, ctx.guild.id))
            await db.commit()

        # Create embed
        embed = discord.Embed(
            description=f'Server prefix set to `{new_prefix}`',
            colour=discord.Colour.orange(),
            timestamp=ctx.message.created_at
        )

        embed.set_author(name='Campfire', icon_url=self.bot.user.avatar_url)
        embed.set_footer(text=f'Changed by {ctx.author}', icon_url=ctx.author.avatar_url)

        await ctx.send(embed=embed)

    @prefix.error
    async def prefix_errors(self, ctx, error):
        '''Error handler for the prefix command.'''

        # If member is not specified or specified member is not found
        if isinstance(error, commands.MissingRequiredArgument):
            await throw_error(ctx, 'Please make sure you are specifying a server prefix to set.', self.delete_delay)

        # If the author is missing permissions
        elif isinstance(error, commands.MissingPermissions):
            await throw_error(ctx, 'You don\'t have permssion to use the prefix command.', self.delete_delay)


def setup(bot):
    bot.add_cog(Config(bot))
