import discord

async def throw_error(ctx, message, delay):
    '''Sends an error message.'''

    # Create error embed
    error_embed = discord.Embed(
        description=message,
        colour=discord.Colour.red()
    )

    await ctx.reply(embed=error_embed, delete_after=delay)
    await ctx.message.delete(delay=delay)