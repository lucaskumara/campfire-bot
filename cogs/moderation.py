import discord
from discord.ext import commands


class BannedUser(commands.Converter):
    '''Converter for finding banned users.'''

    async def convert(self, ctx, argument):
        '''Converts argument to a user object.'''
        banned_users = await ctx.guild.bans()
        user_name, user_discriminator = argument.split('#')

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
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        '''Kicks a member from the server.'''
        await ctx.guild.kick(member, reason=reason)
        await ctx.send(f'{member} has been kicked.')

    @commands.command()
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        '''Bans a member from the server.'''
        await ctx.guild.ban(member, reason=reason)
        await ctx.send(f'{member} has been banned.')

    @commands.command()
    async def unban(self, ctx, user: BannedUser, *, reason=None):
        '''Unbans a user from the server.'''
        await ctx.guild.unban(user)
        await ctx.send(f'{user} has been unbanned.')


def setup(bot):
    bot.add_cog(Moderation(bot))
