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
                user = discord.utils.get(banned_users, name=user_name, discriminator=user_discriminator)

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
    async def kick(self, ctx, member: commands.MemberConverter, *, reason=None):
        '''Kicks a member from the server.'''

        # Kick member
        await ctx.guild.kick(member, reason=reason)

        # Create embed
        embed = discord.Embed(
            description=f'Kicked `{member}`',
            colour=discord.Colour.orange(),
            timestamp=ctx.message.created_at
        )

        # Modify embed
        embed.set_author(name='Campfire', icon_url=self.bot.user.avatar_url)
        embed.add_field(name='Reason', value=f'```{reason}```', inline=False)
        embed.set_footer(text=f'Kicked by {ctx.author}', icon_url=ctx.author.avatar_url)

        await ctx.reply(embed=embed)

    @commands.command()
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def masskick(self, ctx, members: commands.Greedy[commands.MemberConverter], *, reason=None):
        '''Kicks multiple members from the server.'''

        # Create confirmation embed and check
        confirmation_embed = discord.Embed(
            description=f'Are you sure you would like to ban {len(members)} members? (Y/N)',
            colour=discord.Color.orange()
        )

        def confirmation(msg):
            return msg.content.lower() in ['y', 'yes', 'n', 'no']
            
        # Send confirmation prompt and wait for response
        confirmation_prompt = await ctx.send(embed=confirmation_embed)
        confirmation_choice = await self.bot.wait_for('message', check=confirmation)

        # Delete confirmation prompt and response
        await confirmation_prompt.delete()
        await confirmation_choice.delete()

        # Try to kick all members and store the ones that were kicked
        kicked_members = members[:]
        for member in members:
            try:
                await ctx.guild.kick(member, reason=reason)
            except:
                kicked_members.remove(member)

        # Create string of kicked members
        kicked_members_string = '\n'.join([str(member) for member in kicked_members]) or None

        # Create final embed
        embed = discord.Embed(
            description=f'Successfully kicked `{len(kicked_members)}/{len(members)}` member(s)',
            colour=discord.Color.orange(),
            timestamp=ctx.message.created_at
        )

        # Modify embed
        embed.set_author(name='Campfire', icon_url=self.bot.user.avatar_url)
        embed.add_field(name='Kicked members', value=f'```{kicked_members_string}```', inline=False)
        embed.add_field(name='Reason', value=f'```{reason}```', inline=False)
        embed.set_footer(text=f'Kicked by {ctx.author}', icon_url=ctx.author.avatar_url)

        await ctx.reply(embed=embed)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban(self, ctx, members: commands.Greedy[commands.MemberConverter], duration: Optional[TimePeriod]=None, *, reason=None):
        '''Bans a member from the server.'''

        # If no member was specified
        if members == []:
            embed = discord.Embed(description='You must specify at least one member to ban.')
            await ctx.reply(embed=embed)
            return

        banned_members = members[:]

        # Ban members
        for member in members:
            try:
                await ctx.guild.ban(member, reason=reason)
            except:
                banned_members.remove(member)

        # Create string of banned members
        banned_members_string = '\n'.join([str(member) for member in banned_members]) or None

        # Create embed
        embed = discord.Embed(
            description=f'Successfully banned `{len(banned_members)}/{len(members)}` member(s)',
            colour=discord.Color.orange(),
            timestamp=ctx.message.created_at
        )

        # Modify embed
        embed.set_author(name='Campfire', icon_url=self.bot.user.avatar_url)
        embed.add_field(name='Banned members', value=f'```{banned_members_string}```', inline=False)

        # Create field based on existence of tempban
        if duration is None:
            embed.add_field(name='Duration', value='```Permanent```')
        else:
            embed.add_field(name='Duration', value=f'```{duration[0]}{duration[1]}```')

        embed.add_field(name='Reason', value=f'```{reason}```', inline=False)
        embed.set_footer(text=f'Banned by {ctx.author}', icon_url=ctx.author.avatar_url)

        await ctx.reply(embed=embed)

        # Handle tempban
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

            # Check if users are still banned. If so, unban
            for member in members:
                ban_entry = discord.utils.get(await ctx.guild.bans(), user=member)

                if ban_entry is not None:
                    await ctx.guild.unban(member, reason='Tempban expired')

    @commands.command()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def unban(self, ctx, user: BannedUser, *, reason=None):
        '''Unbans a user from the server.'''

        # Ban user
        if discord.utils.get(await ctx.guild.bans(), user=user) is not None:
            await ctx.guild.unban(user, reason=reason)

        # Create embed
        embed = discord.Embed(
            description=f'Successfully unbanned `{user}`',
            colour=discord.Color.orange(),
            timestamp=ctx.message.created_at
        )

        # Modify embed
        embed.set_author(name='Campfire', icon_url=self.bot.user.avatar_url)
        embed.add_field(name='Reason', value=f'```{reason}```', inline=False)
        embed.set_footer(text=f'Unbanned by {ctx.author}', icon_url=ctx.author.avatar_url)

        await ctx.reply(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def clear(self, ctx, targets: commands.Greedy[commands.MemberConverter], amount=100):
        '''Clears a specified number of messages from the channel.'''
        await ctx.message.delete()

        # Delete all messages within limit
        if targets == []:
            deleted = await ctx.message.channel.purge(limit=amount)

        # Delete all messages by targets
        else:

            def author_is_target(msg):
                '''Checks if a message is written by a target member.'''
                return msg.author in targets

            deleted = await ctx.message.channel.purge(limit=amount, check=author_is_target)

        await ctx.send(f'{len(deleted)} messages deleted.')


def setup(bot):
    bot.add_cog(Moderation(bot))
