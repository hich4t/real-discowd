from discord.commands import SlashCommandGroup
from discord.ext import commands
from discord import option
import discord, modules.perms as perms

class PermissionsCMD(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    permsgroup = SlashCommandGroup("permissions", "luckyperms", guild_ids=[1342153810516115517])

    async def perms_autocomplete(self, ctx: discord.AutocompleteContext):
        return ["*", "smspool", "elevenlabs"][:25]

    @permsgroup.command(name="list", description="📜 lists perms")
    @option(name="permissions", description="perms", input_type=str, required=True, autocomplete=perms_autocomplete)
    @perms.permission("*")
    async def prmlist(self, ctx: discord.ApplicationContext, permissions):
        return

    @permsgroup.command(name="edit", description="📝 edits perms")
    @option(name="permissions", description="perms", input_type=str, required=True, autocomplete=perms_autocomplete)
    @option(name="user", description="discord user", input_type=discord.User, required=False)
    @perms.permission("*")
    async def prmedit(self, ctx: discord.ApplicationContext, permissions, user: discord.User):
        if user == None: user = ctx.author
        changed = await perms.change_permissions(user.id, permissions)
        changes = "\n```diff"
        for add in changed["added"]:
            changes += "\n+ "+add
        for add in changed["removed"]:
            changes += "\n- "+add
        for add in changed["unchanged"]:
            changes += "\n~ "+add
        changes += "\n```"
        return await ctx.respond(ephemeral=True, content=f"""> :pencil: edited {user.mention} perms{changes}""")


    @permsgroup.command(name="check", description="👀 checks perms")
    @option(name="user", description="discord user", input_type=discord.User, required=False)
    async def prmcheck(self, ctx: discord.ApplicationContext, user: discord.User):
        if user == None: user = ctx.author
        permis = perms.check_permissions(user.id)
        permss = ""
        for permm in permis:
            permss += "\n-# "+permm
        return await ctx.respond(ephemeral=True, content=f"{user.mention} perms: {permss}")


def setup(bot):
    bot.add_cog(PermissionsCMD(bot))