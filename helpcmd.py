import discord
from discord.ext import commands

class HelpCommand(commands.HelpCommand):
    '''A custom help command to be used by the bot.'''

    def __init__(self):
        super().__init__()

    async def send_error_message(self, error_message):
        '''Send formatted error message.'''

        # Delete authors message
        await self.context.message.delete()

        # Create error embed
        error_embed = discord.Embed(
            description=error_message.replace('"', '`'),
            colour=discord.Colour.red()
        )

        await self.get_destination().send(embed=error_embed, delete_after=5)

    async def send_bot_help(self, mapping):
        '''Called when the help command is called with no arguments.'''

        # Gets the valid command prefixes
        command_prefixes = await self.context.bot.get_prefix(self.context.message)
        
        # Create help embed
        help_embed = discord.Embed(
            description=f'Here is a complete list of all the bot commands. \nThis servers command prefix is `{command_prefixes[-1]}`',
            colour=discord.Colour.orange(),
            timestamp=self.context.message.created_at
        )

        help_embed.set_author(name='Campfire', icon_url=self.context.bot.user.avatar_url)
        help_embed.set_footer(text=f'Requested by {self.context.author}', icon_url=self.context.author.avatar_url)

        # Create a field for each command except admin commands
        for cog in mapping:
            if cog is not None and cog.qualified_name != 'Admin' and cog.get_commands() != []:
                help_embed.add_field(name=cog.qualified_name, value='```\n' + f'help {cog.qualified_name}' + '```', inline=False)

        await self.context.reply(embed=help_embed)

    async def send_cog_help(self, cog):
        '''Called when the help command is called with a cog argument.'''

        # Don't show admin commands
        if cog.qualified_name == 'Admin' or cog.get_commands() == []:
            await self.send_error_message(f'No command called "{cog.qualified_name}" found.')
            return

        # Create cog embed
        cog_embed = discord.Embed(
            title=cog.qualified_name,
            description=cog.description,
            colour=discord.Colour.orange(),
            timestamp=self.context.message.created_at
        )

        cog_embed.set_author(name='Campfire', icon_url=self.context.bot.user.avatar_url)
        cog_embed.set_footer(text=f'Requested by {self.context.author}', icon_url=self.context.author.avatar_url)

        # Get commands and show usages
        command_names = [command.name for command in cog.get_commands()]
        cog_embed.add_field(name='Commands', value=f'```\n' + '\n'.join(command_names) + '```', inline=False)

        await self.context.reply(embed=cog_embed)

    async def send_command_help(self, command):
        '''Called when the help command is called with a command argument.'''

        # Don't show admin commands
        if command.cog.qualified_name == 'Admin':
            await self.send_error_message(f'No command called "{command.name}" found.')
            return

        # Create command embed
        command_embed = discord.Embed(
            title=command.name.capitalize(),
            description=command.help,
            colour=discord.Colour.orange(),
            timestamp=self.context.message.created_at
        )

        command_embed.set_author(name='Campfire', icon_url=self.context.bot.user.avatar_url)
        command_embed.add_field(name='Usage', value=f'```\n{command.usage}```', inline=False)
        command_embed.set_footer(text=f'Requested by {self.context.author}', icon_url=self.context.author.avatar_url)

        await self.context.reply(embed=command_embed)
    