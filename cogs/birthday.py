import discord
import aiosqlite
import asyncio

from discord.ext import commands, tasks
from datetime import datetime, timezone

from discord.ext.commands.core import command


class DateConverter(commands.Converter):
    '''Converter for validating dates.'''

    days_in_months = {
        '01': 31,
        '02': 28, # Ignoring leap years
        '03': 31,
        '04': 30,
        '05': 31,
        '06': 30,
        '07': 31,
        '08': 31,
        '09': 30,
        '10': 31,
        '11': 30,
        '12': 31
    }

    async def convert(self, ctx, argument):
        '''Converts argument a dictionary of the date.'''

        # Extract month and day from argument
        month, day = argument.split('/')

        # Check if month and day are valid
        if month in self.days_in_months and day.isdigit() and int(day) <= self.days_in_months[month]:
            return {'month': month, 'day': day}
        
        raise commands.BadArgument()

class TimezoneConverter(commands.Converter):
    '''Converter for validating timezones.'''

    timezones = [
        'UTC-11',
        'UTC-10',
        'UTC-9',
        'UTC-8',
        'UTC-7',
        'UTC-6',
        'UTC-5',
        'UTC-4',
        'UTC-3',
        'UTC-2',
        'UTC-1',
        'UTC',
        'UTC+1',
        'UTC+2',
        'UTC+3',
        'UTC+4',
        'UTC+5',
        'UTC+6',
        'UTC+7',
        'UTC+8',
        'UTC+9',
        'UTC+10',
        'UTC+11',
        'UTC+12',
        'UTC+13',
        'UTC+14'
    ]

    async def convert(self, ctx, argument):
        '''Converts argument a dictionary of the date.'''

        if argument.upper() in self.timezones:
            return argument.upper()

        raise commands.BadArgument()


class Birthday(commands.Cog):
    '''Cog containing events and tasks for birthday tracking.'''

    def __init__(self, bot):
        self.bot = bot
        self.timezones = { # Hours on a 24 hour clock in UTC when each tz is at midnight
            'UTC-11': 11,
            'UTC-10': 10,
            'UTC-9': 9,
            'UTC-8': 8,
            'UTC-7': 7,
            'UTC-6': 6,
            'UTC-5': 5,
            'UTC-4': 4,
            'UTC-3': 3,
            'UTC-2': 2,
            'UTC-1': 1,
            'UTC': 0,
            'UTC+1': 23,
            'UTC+2': 22,
            'UTC+3': 21,
            'UTC+4': 20,
            'UTC+5': 19,
            'UTC+6': 18,
            'UTC+7': 17,
            'UTC+8': 16,
            'UTC+9': 15,
            'UTC+10': 14,
            'UTC+11': 13,
            'UTC+12': 12,
            'UTC+13': 11,
            'UTC+14': 10
        }

    @commands.Cog.listener('on_ready')
    async def start_task(self):
        '''Start task when the bot is ready.'''
        self.announce_bday.start()

    @commands.Cog.listener('on_guild_join')
    async def create_birthday_table(self, guild):
        '''Ensures existence of the birthday table in database.'''
        async with aiosqlite.connect('./campfire.db') as db:
            await db.execute('CREATE TABLE IF NOT EXISTS birthdays (memberid INTEGER, guildid INTEGER, date TEXT, timezone INTEGER)')
            await db.commit()

    @commands.Cog.listener('on_guild_remove')
    async def remove_guild_birthdays(self, guild):
        '''Removes the birthdays from the database.'''
        async with aiosqlite.connect('./campfire.db') as db:
            await db.execute('DELETE FROM birthdays WHERE guildid = ?', (guild.id, ))
            await db.commit()

    @commands.Cog.listener('on_member_remove')
    async def remove_member_birthdays(self, member):
        '''Remove members birthday upon leaving.'''
        async with aiosqlite.connect('./campfire.db') as db:
            await db.execute('DELETE FROM birthdays WHERE guildid = ? AND memberid = ?', (member.guild.id, member.id))
            await db.commit()

    @commands.group(invoke_without_command=True, aliases=['bday'], usage='birthday')
    async def birthday(self, ctx):
        '''Shows the birthday subcommands.'''

        # Create embed
        embed = discord.Embed(
            colour=discord.Colour.orange(),
            description='Here are the subcommands for the birthday command.',
            timestamp=ctx.message.created_at
        )

        # Create string of subcommands
        subcommands = [f'birthday {command.name}' for command in list(ctx.command.commands)]
        subcommand_string = '\n'.join(subcommands)

        # Modify embed
        embed.set_author(name='Campfire', icon_url=self.bot.user.avatar_url)
        embed.add_field(name='Tags', value=f'```{subcommand_string}```')
        embed.set_footer(text=f'Requested by {ctx.author}', icon_url=ctx.author.avatar_url)

        await ctx.reply(embed=embed)

    @birthday.command(aliases=['setd'], usage='birthday setdate <date>')
    async def setdate(self, ctx, date: DateConverter):
        '''Sets the members birthday.'''
        await ctx.reply(date)

    @birthday.command(aliases=['settz'], usage='birthday settimezone <timezone>')
    async def settimezone(self, ctx, timezone: TimezoneConverter):
        await ctx.reply(timezone)

    @tasks.loop(hours=1)
    async def announce_bday(self):
        '''Announce birthdays at 12am for the corresponding timezone.'''

        # Get the current time in utc
        time = datetime.now(tz=timezone.utc)

        # Check if the task was triggered in the last minute of the hour
        if time.minute == 59:

            # Wait until the minute ends
            await asyncio.wait(60 - time.second)

            # Loop through guilds and check for birthdays
            for guild in self.bot.guilds:

                # Check for any birthdays on this day
                async with aiosqlite.connect('./campfire.db') as db:
                    async with db.execute('SELECT memberid FROM birthdays WHERE timezone = ? AND guildid = ?', (time.hour, guild.id)) as cursor:
                        rows = await cursor.fetchall()

                if guild.system_channel is not None:
                    await guild.system_channel.send(rows)


def setup(bot):
    bot.add_cog(Birthday(bot))