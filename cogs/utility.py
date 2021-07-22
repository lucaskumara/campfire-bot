import discord
import aiosqlite

from discord.ext import commands
from helpers import throw_error


class Utility(commands.Cog):
    '''Cog containing commands for additional server utility.'''

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener('on_guild_join')
    async def create_tags_table(self, guild):
        '''Ensures existence of tag table in database.'''
        async with aiosqlite.connect('./campfire.db') as db:
            await db.execute('CREATE TABLE IF NOT EXISTS tags (guildid INTEGER, authorid INTEGER, name TEXT, text TEXT, created TEXT, modified TEXT)')
            await db.commit()

    @commands.Cog.listener('on_guild_remove')
    async def remove_guild_tags(self, guild):
        '''Removes the guild tags from the database.'''
        async with aiosqlite.connect('./campfire.db') as db:
            await db.execute('DELETE FROM tags WHERE guildid = ?', (guild.id, ))
            await db.commit()

    @commands.group(invoke_without_command=True, usage='tag <name>')
    @commands.guild_only()
    async def tag(self, ctx, *, name):
        '''Displays a server tag in the chat. This command also has a number of subcommands that can be invoked to further manipulate the guild tags.'''

        # Pull tag from database
        async with aiosqlite.connect('./campfire.db') as db:
            async with db.execute('SELECT text FROM tags WHERE name = ? AND guildid = ?', (name, ctx.guild.id)) as cursor:
                row = await cursor.fetchone()

        # If tag doesn't exist
        if row is None:
            await throw_error(ctx, f'There is no tag named `{name}` that exists.')
            return

        await ctx.reply(row[0])

    @tag.command(usage='tag create <name>')
    @commands.guild_only()
    async def create(self, ctx, *, name):
        '''Creates a tag for global use in the server.'''

        # Check if tag already exists
        async with aiosqlite.connect('./campfire.db') as db:
            async with db.execute('SELECT name FROM tags WHERE name = ? AND guildid = ?', (name, ctx.guild.id)) as cursor:
                row = await cursor.fetchone()

        if row is not None:
            await throw_error(ctx, f'There is already a tag named `{name}` that exists.')
            return

        # Send prompt and wait for text
        create_tag_embed = discord.Embed(
            description=f'Please enter the text to be associated with this tag.',
            colour=discord.Colour.orange()
        )

        def check_author(msg):
            return ctx.author == msg.author

        text_prompt = await ctx.send(embed=create_tag_embed)
        text_message = await self.bot.wait_for('message', check=check_author)

        # Delete prompt and response
        await text_prompt.delete()
        await text_message.delete()

        # Store tag in database
        async with aiosqlite.connect('./campfire.db') as db:
            await db.execute('INSERT INTO tags VALUES (?, ?, ?, ?, ?, ?)', (ctx.guild.id, ctx.author.id, name, text_message.content, ctx.message.created_at.strftime("%m/%d/%Y %H:%M:%S"), ctx.message.created_at.strftime("%m/%d/%Y %H:%M:%S")))
            await db.commit()

        confirmation = discord.Embed(
            description=f'The tag `{name}` has been created.',
            colour=discord.Colour.orange(),
            timestamp=ctx.message.created_at
        )

        confirmation.set_author(name='Campfire', icon_url=self.bot.user.avatar_url)
        confirmation.set_footer(text=f'Created by {ctx.author}', icon_url=ctx.author.avatar_url)

        await ctx.reply(embed=confirmation)

    @tag.command(usage='tag remove <name>', aliases=['delete'])
    @commands.guild_only()
    async def remove(self, ctx, *, name):
        '''Remove an existing tag you own from the server. Members with the manage messages permission may remove tags owned by others.'''

        # Removes tag from database
        async with aiosqlite.connect('./campfire.db') as db:

            # Search database for the tag
            async with db.execute('SELECT name, authorid FROM tags WHERE name = ? AND guildid = ?', (name, ctx.guild.id)) as cursor:
                row = await cursor.fetchone()

            # If there is no tag
            if row is None:
                await throw_error(ctx, f'There is no tag named `{name}` that exists.')
                return

            # Delete tag is author is owner or author can manage messages
            if row[1] == ctx.author.id or ctx.author.guild_permissions.manage_messages:
                await db.execute('DELETE FROM tags WHERE name = ? AND guildid = ?', (name, ctx.guild.id))
                await db.commit()
            else:
                await throw_error(ctx, f'You do not own the tag `{name}` so you may not delete it.')
                return

        remove_embed = discord.Embed(
            description=f'The tag `{name}` has been removed.',
            colour=discord.Colour.orange(),
            timestamp=ctx.message.created_at
        )

        remove_embed.set_author(name='Campfire', icon_url=self.bot.user.avatar_url)
        remove_embed.set_footer(text=f'Removed by {ctx.author}', icon_url=ctx.author.avatar_url)

        await ctx.reply(embed=remove_embed)

    @tag.command(usage='tag edit <name> <text>')
    @commands.guild_only()
    async def edit(self, ctx, *, name):
        '''Updates the text of an existing tag.'''

        # Updates the tag in the database
        async with aiosqlite.connect('./campfire.db') as db:

            # Search database for the tag
            async with db.execute('SELECT name, authorid FROM tags WHERE name = ? AND guildid = ?', (name, ctx.guild.id)) as cursor:
                row = await cursor.fetchone()

            # If there is no tag
            if row is None:
                await throw_error(ctx, f'There is no tag named `{name}` that exists.')
                return

            # Delete tag is author is owner or author can manage messages
            if row[1] == ctx.author.id or ctx.author.guild_permissions.manage_messages:

                # Send prompt and wait for text
                edit_tag_embed = discord.Embed(
                    description=f'Please enter the new text to be associated with this tag.',
                    colour=discord.Colour.orange()
                )

                def check_author(msg):
                    return ctx.author == msg.author

                text_prompt = await ctx.send(embed=edit_tag_embed)
                text_message = await self.bot.wait_for('message', check=check_author)

                # Delete prompt and response
                await text_prompt.delete()
                await text_message.delete()

                # Update tag
                await db.execute('UPDATE tags SET text = ?, modified = ? WHERE name = ? AND guildid = ?', (text_message.content, ctx.message.created_at.strftime("%m/%d/%Y %H:%M:%S"), name, ctx.guild.id))
                await db.commit()

            else:
                await throw_error(ctx, f'You do not own the tag `{name}` so you may not edit it.')
                return

        confirmation = discord.Embed(
            description=f'The tag `{name}` has been updated.',
            colour=discord.Colour.orange(),
            timestamp=ctx.message.created_at
        )

        confirmation.set_author(name='Campfire', icon_url=self.bot.user.avatar_url)
        confirmation.set_footer(text=f'Edited by {ctx.author}', icon_url=ctx.author.avatar_url)

        await ctx.reply(embed=confirmation)

    @tag.command(usage='tag info <name>')
    @commands.guild_only()
    async def info(self, ctx, *, name):
        '''Shows information about a tag.'''

        # Pull tag info from database
        async with aiosqlite.connect('./campfire.db') as db:
            async with db.execute('SELECT name, authorid, created, modified FROM tags WHERE name = ? AND guildid = ?', (name, ctx.guild.id)) as cursor:
                row = await cursor.fetchone()

        if row is None:
            await throw_error(ctx, f'There is no tag named `{name}` that exists')
            return

        # Format info
        name, authorid, created, modified = row

        info_embed = discord.Embed(
            title='Tag Information',
            description=f'Tag Owner: <@{authorid}>',
            colour=discord.Colour.orange(),
            timestamp=ctx.message.created_at
        )

        info_embed.set_author(name='Campfire', icon_url=self.bot.user.avatar_url)
        info_embed.add_field(name='Created On', value=f'```{created} UTC```', inline=False)
        info_embed.add_field(name='Last Modified', value=f'```{modified} UTC```', inline=False)
        info_embed.set_footer(text=f'Requested by {ctx.author}', icon_url=ctx.author.avatar_url)

        await ctx.reply(embed=info_embed)

    @tag.command(name='list', usage='tag list [member]')
    @commands.guild_only()
    async def _list(self, ctx, member: commands.MemberConverter=None):
        '''Lists all server tags. A member can be specified to see specifically which tags they own.'''

        # If there is no member specified
        if member is None:

            # Pull all guild tags from the database
            async with aiosqlite.connect('./campfire.db') as db:
                async with db.execute('SELECT name FROM tags WHERE guildid = ?', (ctx.guild.id, )) as cursor:
                    rows = await cursor.fetchall()

            tag_names = [row[0] for row in rows]

            # If there are no server tags
            if len(tag_names) == 0:
                await throw_error(ctx, 'This server does not yet have any tags.')
                return

            list_embed = discord.Embed(
                description='Here is a list of all server tags.',
                colour=discord.Colour.orange(),
                timestamp=ctx.message.created_at
            )

            list_embed.set_author(name='Campfire', icon_url=self.bot.user.avatar_url)
            list_embed.add_field(name='Tags', value=f'```{", ".join(tag_names)}```')
            list_embed.set_footer(text=f'Requested by {ctx.author}', icon_url=ctx.author.avatar_url)

            await ctx.reply(embed=list_embed)

        else:

            # Pull tags owned by member from the database
            async with aiosqlite.connect('./campfire.db') as db:
                async with db.execute('SELECT name FROM tags WHERE guildid = ? AND authorid = ?', (ctx.guild.id, member.id)) as cursor:
                    rows = await cursor.fetchall()

            tag_names = [row[0] for row in rows]

            # If member has no owned tags
            if len(tag_names) == 0:
                await throw_error(ctx, f'{member} has not made any tags yet.')
                return

            list_embed = discord.Embed(
                description=f'Here is a list of all server tags made by `{member}`',
                colour=discord.Colour.orange(),
                timestamp=ctx.message.created_at
            )

            list_embed.set_author(name='Campfire', icon_url=self.bot.user.avatar_url)
            list_embed.add_field(name='Tags', value=f'```{", ".join(tag_names)}```')
            list_embed.set_footer(text=f'Requested by {ctx.author}', icon_url=ctx.author.avatar_url)

            await ctx.reply(embed=list_embed)


def setup(bot):
    bot.add_cog(Utility(bot))
