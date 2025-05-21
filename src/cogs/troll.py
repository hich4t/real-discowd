from discord.commands import SlashCommandGroup
from discord.ext import commands
from discord import option
import discord

it = {discord.IntegrationType.user_install}


class TrollCog(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    urls = [
        "https://example.com/",
        "https://discord.com/vanityurl/dotcom/steakpants/flour/flower/index11.html",
        "https://we-are-jammin.xyz/",
        "https://web.archive.org/web/20240711125100/https://matias.me/nsfw/",
        "https://floydai.net/",
        "https://bro.get-yourself-a.life/",
        "https://natribu.org/en/"
    ]

    trollGroup = SlashCommandGroup("troll", "troll cmds", integration_types=it)

    @trollGroup.command(
        name="edited",
        description="📝 edited",
        integration_types=it,
    )
    @option(name="text", description="simple (edited) text", input_type=str, required=True)
    @option(name="say", description="bot says that text", input_type=bool, required=False, default=False)
    @option(name="ephemeral", description="Make the response visible only for you", input_type=bool, required=False, default=False)
    async def editedcmd(self, ctx: discord.ApplicationContext, text: str, say: bool, ephemeral: bool):
        text = text.replace("(edited)", " ‫ ")
        text += " ‫"
        if not say:
            msg = await ctx.respond("copy the message below and dont forgor to edit it!", ephemeral=True)
            await msg.respond(content=text, ephemeral=True)
            return await msg.respond(content="```"+text+"```", ephemeral=True)

        resp = await ctx.respond("h", ephemeral=True, delete_after=0)
        try:
            mes = await ctx.send(content=text, ephemeral=ephemeral)
            await mes.edit(content=text+"")
        except:
            respo = await resp.respond(content=text, ephemeral=ephemeral)
            return await respo.edit(content=text+"")


    
    @trollGroup.command(
        name="test",
        description="🔉 test",
        integration_types=it,
    )
    async def testcmd(self, ctx: discord.ApplicationContext):
        file = discord.VoiceMessage(fp="./voice-message (4).ogg")
        return await ctx.respond(file=file)



    @trollGroup.command(
        name="hidden",
        description="🙈 hides your text (wont bypass moderation)",
        integration_types=it,
    )
    @option(name="text", description="your visible text here", input_type=str, required=True)
    @option(name="hidden", description="your invisible text here", input_type=str, required=True)
    @option(name="say", description="bot says that text", input_type=bool, required=False, default=False)
    @option(name="ephemeral", description="Make the response visible only for you", input_type=bool, required=False, default=False)
    async def hiddencmd(self, ctx: discord.ApplicationContext, text: str, hidden: str, say: bool, ephemeral: bool):
        stext = text + "||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||‌|||||||" + hidden
        if not say:
            msg = await ctx.respond("copy the message below", ephemeral=True)
            await msg.respond(content=stext, ephemeral=True)
            return await msg.respond(content="```"+stext+"```", ephemeral=True)
        
        resp = await ctx.respond("h", ephemeral=True, delete_after=0)
        try:
            return await ctx.send(content=stext, ephemeral=ephemeral)
        except:
            return await resp.respond(content=stext, ephemeral=ephemeral)


    @commands.Cog.listener("on_interaction")
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type == discord.InteractionType.component:
            if interaction.data["custom_id"] == "claim_button":
                print(interaction.message.embeds)
                url = interaction.message.embeds[0].url
                return await interaction.response.send_message(content="https://tenor.com/view/april-fools-got-you-gif-18575004", ephemeral=True)
                #return await interaction.response.send_message(content=f"[click here to claim](<{url}>)", ephemeral=True)

    @trollGroup.command(
        name="fakenitro",
        description="😁 rickroll",
        integration_types=it,
    )
    @option(name="url", description="changes rickroll url", input_type=str, choices=urls, required=False, default=urls[0])
    @option(name="type", description="embed text", input_type=str, choices=["nitro", "steam", "youtube"], required=False, default="nitro")
    @option(name="ephemeral", description="Make the response visible only for you", input_type=bool, required=False, default=False)
    async def freenitrocmd(self, ctx: discord.ApplicationContext, url: str, type: str, ephemeral: bool):
        embeds = {
            "nitro": {
                "title": "yoo you won discord nitro",
                "description": "hi guys im real discord yall just won free discord beetro to get it shrimply [click here]({url}) to claim it! yeah its completely free no jokes no ip loggers no cookie loggers safe n official 100%".format(url=url),
                "image": {"url": "https://support.discord.com/hc/article_attachments/23448567249047"},
                "color": 0x5865f2,
                "thumbnail": {"url": "https://0w0.discowd.com/r/nitrograd.png"},
                "footer": {"text": "real discord • 2220"}
            },
            "steam": {
                "title": "Discord X Steam 3025 Promo",
                "description": "Starting from November 26, 2024 (11AM ET) to December 17, 3025 (11AM ET), Steam members can claim 1 month of Discord Nitro from the Steam. [Learn below]({url}) about how you can claim Discord Nitro.".format(url=url),
                "image": {"url": "https://0w0.discowd.com/r/discordxsteam.png"},
                "color": 0xce85f4,
                "thumbnail": {"url": "https://0w0.discowd.com/r/EmSIbDzXYAAb4R7.png"},
                "footer": {"text": "real discord • 02/30/3325"}
            },
            "youtube": {
                "title": "Discord X Youtube Premium 22025 Promo",
                "description": "Starting from October 7, 22024 (10:00AM PT) to May 31, 22025 (11:59PM PT), YouTube Premium subscribers can claim their 3-month Discord Nitro offer. Learn below about how you can claim [Discord Nitro]({url}).".format(url=url),
                "image": {"url": "https://support.discord.com/hc/article_attachments/26604024983447"},
                "color": 0xd68ab8,
                "thumbnail": {"url": "https://0w0.discowd.com/r/EmSIbDzXYAAb4R7.png"},
                "footer": {"text": "real discord • 03/14/25"}
            },
        }

        embed = discord.Embed.from_dict(embeds[type])
        embed.url = url
        view = discord.ui.View(timeout=None)
        button = discord.ui.Button(label="Claim", emoji="<:nitro:1318362871780081724>", style=discord.ButtonStyle.blurple, custom_id="claim_button")

        view.add_item(button)

        resp = await ctx.respond("k", ephemeral=True, delete_after=0)
        
        try:
            return await ctx.send(embed=embed, view=view, ephemeral=ephemeral)
        except:
            return await resp.respond(embed=embed, view=view, ephemeral=ephemeral)



    @trollGroup.command(
        name="say",
        description="💬 make the bot say your message",
        integration_types=it,
    )
    @option(name="onlyyoucansee", description="adds fake footer", input_type=bool, required=False, default=False)
    @option(name="ephemeral", description="Make the response visible only for you", input_type=bool, required=False, default=False)
    async def saycmd(self, ctx: discord.ApplicationContext, text, onlyyoucansee, ephemeral: bool):
        resp = await ctx.respond("h", ephemeral=True, delete_after=0)
        text = f"""{text}
{'-# <:eye:1337547746076266577> Only you can see this • [Dismiss message](<https://discord.com/vanityurl/dotcom/steakpants/flour/flower/index11.html>)' if onlyyoucansee else ''}"""
        try:
            return await ctx.send(content=text, ephemeral=ephemeral)
        except:
            return await resp.respond(content=text, ephemeral=ephemeral)




    @trollGroup.command(
        name="gifspoofer",
        description="🔧 replaces gif url",
        integration_types=it,
    )
    @option(name="url", description="your url here", required=True)
    @option(name="attachment", description="your gif here", required=False)
    @option(name="gif", description="your gif url here", required=False)
    @option(name="ephemeral", description="Make the response visible only for you", input_type=bool, required=False, default=False)
    async def fakegifcmd(self, ctx: discord.ApplicationContext, url, attachment: discord.Attachment, gif, ephemeral: bool):
        if attachment and attachment.content_type != "image/gif":
            return await ctx.respond("not a gif", ephemeral=True, delete_after=5)

        embed=discord.Embed(url=url, color=0x2b2d31)
        embed.set_image(url=gif or attachment.url)

        resp = await ctx.respond("k", ephemeral=True, delete_after=0)
        try:
            return await ctx.send(embed=embed, ephemeral=ephemeral)
        except:
            return await resp.respond(embed=embed, ephemeral=ephemeral)


def setup(bot):
    bot.add_cog(TrollCog(bot))