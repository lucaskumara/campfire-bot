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
        
        # Create help embed
        help_embed = discord.Embed(
            description='Here is a complete list of all the bot commands.',
            colour=discord.Colour.orange(),
            timestamp=self.context.message.created_at
        )

        help_embed.set_author(name='Campfire', icon_url=self.context.bot.user.avatar_url)
        help_embed.set_footer(text=f'Requested by {self.context.author}', icon_url=self.context.author.avatar_url)

        # Create a field for each command
        for cog in mapping:
            if cog is not None:

                # Filter and sort commands to only show users commands they can use
                filtered_commands = await self.filter_commands(cog.get_commands())
                filtered_commands_names = [command.name for command in filtered_commands]
                filtered_commands_names.sort()

                # Create field only if cog contains at least one command to show
                if filtered_commands != []:
                    commands_string = '```\n' + '\n'.join(filtered_commands_names) + '```'
                    help_embed.add_field(name=cog.qualified_name, value=commands_string)

        await self.context.reply(embed=help_embed)

    async def send_command_help(self, command):
        '''Called when the help command is called with a command argument.'''

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
    