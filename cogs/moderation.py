import discord
from discord.ext import commands
from typing import Union


class BannedUser(commands.Converter):
    '''Converter for finding banned users.'''

    async def convert(self, ctx, argument):
        '''Converts argument to a user object.'''
        banned_users = await ctx.guild.bans()
        user_name, user_discriminator = argument.split('#')

        # Loop through entries to locate target user
        for ban_entry in banned_users:
            user = ban_entry.user

            if (user.name, user.discriminator) == \
                    (user_name, user_discriminator):
                return user

        raise commands.BadArgument(message='Banned user not found')


class Moderation(commands.Cog):
    '''Cog containing commands for server moderation.'''

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def kick(self, ctx, member: Union[discord.Member, int], *, reason=None):
        '''Kicks a member from the server.'''
        if isinstance(member, discord.Member):
            await ctx.guild.kick(member, reason=reason)
        elif isinstance(member, int):
            await ctx.guild.kick(ctx.guild.get_member(member))
        await ctx.send(f'{member} has been kicked.')

    @commands.command()
    async def ban(self, ctx, member: Union[discord.Member, int], *, reason=None):
        '''Bans a member from the server.'''
        if isinstance(member, discord.Member):
            await ctx.guild.ban(member, reason=reason)
        elif isinstance(member, int):
            await ctx.guild.ban(ctx.guild.get_member(member))
        await ctx.send(f'{member} has been banned.')

    @commands.command()
    async def unban(self, ctx, user: Union[BannedUser, int], *, reason=None):
        '''Unbans a user from the server.'''
        if isinstance(user, BannedUser):
            await ctx.guild.unban(user, reason=reason)
        elif isinstance(user, int):
            ban_entry = discord.utils.find(lambda entry: entry.user.id == user, await ctx.guild.bans())
            user = ban_entry.user
            await ctx.guild.unban(user, reason=reason)
        await ctx.send(f'{user} has been unbanned.')


def setup(bot):
    bot.add_cog(Moderation(bot))
