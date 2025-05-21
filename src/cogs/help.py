from discord.ext import commands

import discord

it = {discord.IntegrationType.user_install}

class helpCog(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @commands.slash_command(name="help", description="📑 Help", integration_types=it)
    async def helpCmd(self, ctx: discord.ApplicationContext):
        return await ctx.respond(content="✅", ephemeral=True)

def setup(bot):
    bot.add_cog(helpCog(bot))