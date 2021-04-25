import discord
import asyncio

from discord.ext import commands
from typing import Optional


class BannedUser(commands.Converter):
    '''Converter for finding banned users.'''

    async def convert(self, ctx, argument):
        '''Converts argument to a user object.'''
        banned_users = [entry.user for entry in await ctx.guild.bans()]

        # If argument could be a user id
        if argument.isdigit():
            user = discord.utils.get(banned_users, id=int(argument))
        else:

            # If argument is a users name
            if '#' not in argument:
                user = discord.utils.get(banned_users, name=argument)

            # If argument is a users name and discriminator
            else:
                user_name, user_discriminator = argument.split('#')
                kwargs = {
                    'name': user_name,
                    'discriminator': user_discriminator
                }

                user = discord.utils.get(banned_users, **kwargs)

        if user is not None:
            return user

        raise commands.UserNotFound(argument)


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
    @commands.bot_has_permissions(kick_members=True)
    async def kick(self, ctx,
                   members: commands.Greedy[commands.MemberConverter], *,
                   reason=None):
        '''Kicks a member from the server.'''
        for member in members:
            await ctx.guild.kick(member, reason=reason)

        kicked_members = [str(member) for member in members]

        embed = discord.Embed(
            description=f'Kicked `{len(members)}` member(s)',
            colour=discord.Color.orange(),
            timestamp=ctx.message.created_at
        )

        embed.set_author(
            name='Campfire',
            icon_url=self.bot.user.avatar_url
        )

        embed.add_field(
            name='Kicked members',
            value='```' + '\n'.join(kicked_members) + '```',
            inline=False
        )

        embed.add_field(
            name='Reason',
            value=f'```{reason}```',
            inline=False
        )

        embed.set_footer(
            text=f'Kicked by {ctx.author}',
            icon_url=ctx.author.avatar_url
        )

        await ctx.reply(embed=embed)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban(self, ctx,
                  members: commands.Greedy[commands.MemberConverter],
                  duration: Optional[TimePeriod]=None, *, reason=None):
        '''Bans a member from the server.'''
        for member in members:
            await ctx.guild.ban(member, reason=reason)

        banned_members = [str(member) for member in members]

        embed = discord.Embed(
            description=f'Banned `{len(members)}` member(s)',
            colour=discord.Color.orange(),
            timestamp=ctx.message.created_at
        )

        embed.set_author(
            name='Campfire',
            icon_url=self.bot.user.avatar_url
        )

        embed.add_field(
            name='Banned members',
            value='```' + '\n'.join(banned_members) + '```',
            inline=False
        )

        if duration is None:
            embed.add_field(
                name='Duration',
                value='```Permanent```'
            )
        else:
            embed.add_field(
                name='Duration',
                value=f'```{duration[0]}{duration[1]}```'
            )

        embed.add_field(
            name='Reason',
            value=f'```{reason}```',
        )

        embed.set_footer(
            text=f'Banned by {ctx.author}',
            icon_url=ctx.author.avatar_url
        )

        await ctx.reply(embed=embed)

        if duration is not None:

            # Seconds multipliers
            multiplier = {
                's': 1,
                'm': 60,
                'h': 3600,
                'd': 86400,
                'w': 604800,
                'm': 2592000,
                'y': 31536000
            }

            # Sleep for the specified duration
            amount, unit = duration
            await asyncio.sleep(amount * multiplier[unit])

            banned_users = await ctx.guild.bans()

            # Check if users are still banned. If so, unban
            for member in members:
                ban_entry = discord.utils.get(banned_users, user=member)

                if ban_entry is not None:
                    await ctx.guild.unban(member, reason='Tempban expired')

    @commands.command()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def unban(self, ctx, user: BannedUser, *, reason=None):
        '''Unbans a user from the server.'''
        bans = await ctx.guild.bans()
        user = discord.utils.get(bans, user=user).user

        await ctx.guild.unban(user, reason=reason)
        await ctx.send(f'{user} has been unbanned.')

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def clear(self, ctx,
                    targets: commands.Greedy[commands.MemberConverter],
                    amount=100):
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
