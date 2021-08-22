import discord
import aiosqlite
import copy

from discord.ext import commands
from helpers import throw_error, Pages


class Tags(commands.Cog):
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
        '''Displays a server tag in the chat.'''

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

        # Limit tag names to 54 characters
        if len(name) > 54:
            await throw_error(ctx, 'Tag names cannot exceed 54 characters.')
            return

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

        # Create embed
        list_embed = discord.Embed(
            colour=discord.Colour.orange(),
            timestamp=ctx.message.created_at
        )

        # If there is no member specified
        if member is None:

            # Pull all guild tags from the database
            async with aiosqlite.connect('./campfire.db') as db:
                async with db.execute('SELECT name FROM tags WHERE guildid = ?', (ctx.guild.id, )) as cursor:
                    rows = await cursor.fetchall()

            # If there are no server tags
            if len(rows) == 0:
                await throw_error(ctx, 'This server does not yet have any tags.')
                return

            # Set embed description
            list_embed.description = 'Here is a list of all server tags.'

        else:

            # Pull tags owned by member from the database
            async with aiosqlite.connect('./campfire.db') as db:
                async with db.execute('SELECT name FROM tags WHERE guildid = ? AND authorid = ?', (ctx.guild.id, member.id)) as cursor:
                    rows = await cursor.fetchall()

            # If member has no owned tags
            if len(rows) == 0:
                await throw_error(ctx, f'{member} has not made any tags yet.')
                return

            # Set embed description
            list_embed.description = f'Here is a list of all server tags made by `{member}`'

        # Modify embed
        list_embed.set_author(name='Campfire', icon_url=self.bot.user.avatar_url)
        list_embed.set_footer(text=f'Requested by {ctx.author}', icon_url=ctx.author.avatar_url)

        # Create pages
        pages = []
        tag_names = [row[0] for row in rows]
        tag_count = len(tag_names)
        start = 0

        while start <= tag_count:

            # Pointer 10 indexes ahead of start
            end = start + 10

            # If end exceeds tag count, set to the actual tag count
            if end > tag_count:
                end = tag_count

            # Get up to 10 tags and make a string
            page_tags = tag_names[start:end]
            tag_string = '\n'.join([f'• {tag}' for tag in page_tags])

            # Add string to field and add the embed to pages
            list_embed.add_field(name='Tags', value=f'```{tag_string}```')
            pages.append(copy.deepcopy(list_embed))

            # Clear fields and increment start
            list_embed.clear_fields()
            start += 10

        # Add page counts to pages
        page_count = len(pages)
        for i in range(page_count):
            pages[i].title = f'Page {i + 1}/{page_count}'

        # Use Pages to paginate the message
        paginator = Pages(self.bot, pages)
        await paginator.start(ctx)

    @tag.error
    async def tag_errors(self, ctx, error):
        '''Error handler for the tag command.'''

        # If a tag is not specified
        if isinstance(error, commands.MissingRequiredArgument):
            await throw_error(ctx, f'Please make sure you specify a valid tag to view.')

        # If the command is used in a dm
        elif isinstance(error, commands.NoPrivateMessage):
            await throw_error(ctx, 'You can\'t use this command in a direct message.')

        else:
            raise error

    @create.error
    async def create_errors(self, ctx, error):
        '''Error handler for the create subcommand.'''

        # If a tag is not specified
        if isinstance(error, commands.MissingRequiredArgument):
            await throw_error(ctx, f'Please make sure you specify a unique name for the tag.')

        # If the command is used in a dm
        elif isinstance(error, commands.NoPrivateMessage):
            await throw_error(ctx, 'You can\'t use this command in a direct message.')

        else:
            raise error

    @remove.error
    async def remove_errors(self, ctx, error):
        '''Error handler for the remove subcommand.'''

        # If a tag is not specified
        if isinstance(error, commands.MissingRequiredArgument):
            await throw_error(ctx, f'Please make sure you specify a valid tag to remove.')

        # If the command is used in a dm
        elif isinstance(error, commands.NoPrivateMessage):
            await throw_error(ctx, 'You can\'t use this command in a direct message.')

        else:
            raise error

    @edit.error
    async def edit_errors(self, ctx, error):
        '''Error handler for the edit subcommand.'''

        # If a tag is not specified
        if isinstance(error, commands.MissingRequiredArgument):
            await throw_error(ctx, f'Please make sure you specify a valid tag to edit.')

        # If the command is used in a dm
        elif isinstance(error, commands.NoPrivateMessage):
            await throw_error(ctx, 'You can\'t use this command in a direct message.')

        else:
            raise error

    @info.error
    async def info_errors(self, ctx, error):
        '''Error handler for the info subcommand.'''

        # If a tag is not specified
        if isinstance(error, commands.MissingRequiredArgument):
            await throw_error(ctx, f'Please make sure you specify a valid tag to view its information.')

        # If the command is used in a dm
        elif isinstance(error, commands.NoPrivateMessage):
            await throw_error(ctx, 'You can\'t use this command in a direct message.')

        else:
            raise error

    @_list.error
    async def list_errors(self, ctx, error):
        '''Error handler for the list subcommand.'''

        # If the specified member is not found
        if isinstance(error, commands.MemberNotFound):
            await throw_error(ctx, 'Please make sure you are specifying a valid server member to see their tags.')

        # If the command is used in a dm
        elif isinstance(error, commands.NoPrivateMessage):
            await throw_error(ctx, 'You can\'t use this command in a direct message.')

        else:
            raise error


def setup(bot):
    bot.add_cog(Tags(bot))
