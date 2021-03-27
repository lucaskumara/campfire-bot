import discord
from discord.ext import commands


class Moderation(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def kick(self, ctx, member : discord.Member, *, reason=None):
        '''Kicks a member from the server.'''
        await ctx.guild.kick(member, reason=reason)
        await ctx.send(f'{member} has been kicked.')

    @commands.command()
    async def ban(self, ctx, member : discord.Member, *, reason=None):
        '''Bans a member from the server.'''
        await ctx.guild.ban(member, reason=reason)
        await ctx.send(f'{member} has been banned.')

    @commands.command()
    async def unban(self, ctx, member, *, reason=None):
        '''Unbans a member from the server.'''
        banned_users = await ctx.guild.bans()
        member_name, member_discriminator = member.split('#')

        for ban_entry in banned_users:
            user = ban_entry.user

            if (user.name, user.discriminator) == (member_name, member_discriminator):
                await ctx.guild.unban(user)
                await ctx.send(f'{user} has been unbanned.')
                return

def setup(bot):
    bot.add_cog(Moderation(bot))