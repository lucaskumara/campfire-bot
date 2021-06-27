import discord

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