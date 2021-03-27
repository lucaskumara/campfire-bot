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

def setup(bot):
    bot.add_cog(Moderation(bot))