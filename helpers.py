import discord
import asyncio

async def throw_error(ctx, message):
    '''Sends an error message.'''

    # Delete the error message after 8 seconds
    delay = 8

    # Create error embed
    error_embed = discord.Embed(
        description=message,
        colour=discord.Colour.red()
    )

    await ctx.reply(embed=error_embed, delete_after=delay)
    await ctx.message.delete(delay=delay)


class Pages:

    def __init__(self, bot, pages):
        self.bot = bot
        self.pages = pages
        self.current_page = 0

    async def start(self, ctx):

        # Send message and add reactions
        msg = await ctx.reply(embed=self.pages[self.current_page])
        await msg.add_reaction('⬅️')
        await msg.add_reaction('➡️')

        # Give bot some time to send and react
        await asyncio.sleep(2)

        def check(reaction, user):
            '''Only work if reacting to the message.'''
            return reaction.message == msg

        # Continue checking for reactions
        while True:

            # Wait for a reaction, if no reaction for 60 sceonds, remove reactions
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=60, check=check)
                await msg.remove_reaction(reaction, user)
            except asyncio.TimeoutError:
                await msg.clear_reactions()
                break

            # If back arrow is clicked, show previous page
            if str(reaction.emoji) == '⬅️':
                if self.current_page != 0:
                    self.current_page -= 1
                    await msg.edit(embed=self.pages[self.current_page])

            # If forwards arrow is clicked show next page
            elif str(reaction.emoji) == '➡️':
                if self.current_page != len(self.pages) - 1:
                    self.current_page += 1
                    await msg.edit(embed=self.pages[self.current_page])
