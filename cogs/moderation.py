import discord
import asyncio

from discord.ext import commands
from typing import Optional


class BannedUser(commands.Converter):
    '''Converter for finding banned users.'''

    async def convert(self, ctx, argument):
        '''Converts argument to a user object.'''
        banned_users = [entry.user for entry in await ctx.guild.bans()]
        user_name, user_discriminator = argument.split('#')

        kwargs = {
            'name': user_name,
            'discriminator': user_discriminator
        }

        # Search for banned used
        user = discord.utils.get(banned_users, **kwargs)

        # If banned user was found, return them
        if user is not None:
            return user

        raise commands.BadArgument(message='Banned user not found')


class TimePeriod(commands.Converter):
    '''Converter for checking time intervals.'''

    async def convert(self, ctx, argument):
        '''Converts argument to a tuple representing a period of time.'''
        amount = argument[:-1]
        unit = argument[-1]

        # Check if the amount is a digit and the unit is in the specified list
        if amount.isdigit() and unit in ['s', 'm', 'h', 'd', 'w', 'm', 'y']:
            return (int(amount), unit)

        raise commands.BadArgument(message='Not a valid period of time')


class Moderation(commands.Cog):
    '''Cog containing commands for server moderation.'''

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        '''Kicks a member from the server.'''
        await ctx.guild.kick(member, reason=reason)
        await ctx.send(f'{member} has been kicked.')

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member,
                  duration: Optional[TimePeriod]=None, *, reason=None):
        '''Bans a member from the server.'''
        await ctx.guild.ban(member, reason=reason)

        # If a duration is specified, treat ban as a temp ban
        if duration is None:
            await ctx.send(f'{member} has been banned.')
        else:
            await ctx.send(f'{member} has been temporarily banned.')

            multiplier = {
                's': 1,
                'm': 60,
                'h': 3600,
                'd': 86400,
                'w': 604800,
                'm': 2592000,
                'y': 31536000
            }

            # Wait for ban duration
            amount, unit = duration
            await asyncio.sleep(amount * multiplier[unit])

            # Check if user is still banned. If so, unban
            ban_entry = discord.utils.get(await ctx.guild.bans(), user=member)

            if ban_entry is not None:
                await ctx.guild.unban(member, reason='Tempban expired')

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user: BannedUser, *, reason=None):
        '''Unbans a user from the server.'''
        bans = await ctx.guild.bans()
        user = discord.utils.get(bans, user=user).user

        await ctx.guild.unban(user, reason=reason)
        await ctx.send(f'{user} has been unbanned.')

    @commands.command()
    async def clear(self, ctx,
                    targets: commands.Greedy[discord.Member], amount=100):
        '''Clears a specified number of messages from the channel.'''
        await ctx.message.delete()

        if targets == []:
            deleted = await ctx.message.channel.purge(limit=amount)
        else:

            def author_is_target(msg):
                '''Checks if a message is written by a target member.'''
                return msg.author in targets

            deleted = await ctx.message.channel.purge(
                limit=amount,
                check=author_is_target
            )

        await ctx.send(f'{len(deleted)} messages deleted.')


def setup(bot):
    bot.add_cog(Moderation(bot))
