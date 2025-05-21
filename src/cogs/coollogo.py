from discord.commands import SlashCommandGroup
from discord.ext import commands, pages
from discord import option
import discord, aiohttp, json, io, re

with open("./src/logos.json", "r") as f:
    logos = json.load(f)
    logoDict = {}
    for logo in logos:
        logoDict[logo["name"]] = logo

tagsformated = {}
for style in logos:
    for tag in style.get("tags", []):
        tagged = tagsformated.get(tag, None)
        if not tagged:
            tagsformated[tag] = [style]
        else:
            tagsformated[tag].append(style)


it = {discord.IntegrationType.user_install}
shadows = ["No Shadow", "Sharp", "Light Blur", "Medium Blur", "Heavy Blur"]
alignments = ["Top Left", "Top Center", "Top Right", "Middle Left", "Centered", "Middle Right", "Bottom Left", "Bottom Center", "Bottom Right"]
fileFormats = [".GIF", ".GIF w/ Transparency", ".GIF w/ Transparency No Dither", ".JPG", ".PNG", ".PNG w/ Transparency", ".PSD (Photoshop w/ Layers)", ".XCF (Native Gimp Format)"]


class CutenprettylogoCog(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    cnplGroup = SlashCommandGroup("cooltext", "cooltext commands", integration_types=it)

    async def tag_autocomplete(self, ctx: discord.AutocompleteContext):
        return [f'{tag} ({len(val)})' for tag,val in tagsformated.items() if ctx.value.lower() in tag.lower()][:25]

    async def logo_autocomplete(self, ctx: discord.AutocompleteContext):
        return [logo["name"] for logo in logos if ctx.value.lower() in logo["name"].lower()][:25]
    
    @cnplGroup.command(
        name="preview",
        description="🔍 search your favorite style",
        integration_types=it,   
    )
    @option(name="tag", description="Choose tag style", input_type=str, autocomplete=tag_autocomplete, required=False, default="")
    @option(name="ephemeral", description="Make the response visible only for you", input_type=bool, required=False, default=False)
    async def cutenprettytextgenerator(self, ctx: discord.ApplicationContext, tag: str, ephemeral: bool):
        actualtag = None
        if tag:
            actualtag = re.match(r'(\w+) \(([^)]+)\)', tag)
            actualtag = actualtag.group(1)
        
        pageGroups = []
        everyPage = []
        print(actualtag)

        async def gen_embed(logo):
            embed = discord.Embed(url=f"https://cooltext.com/Logo-Design-{logo.get('name')}", title=logo.get('name'))
            embed.set_image(url=logo.get("preview"))
            embed.set_footer(text= ', '.join(logo.get("tags")))
            return embed
        
        for tag,logos in tagsformated.items():
            pageGroup = pages.PageGroup(pages=[], default=actualtag==tag, label=f"{tag} ({len(logos)})")
            for logo in logos:
                embed = await gen_embed(logo)
                pageGroup.pages.append(embed)

            pageGroups.append(pageGroup)

        for logo in logoDict.values():
            embed = await gen_embed(logo)
            everyPage.append(embed)

        pageGroups.insert(0, pages.PageGroup(pages=everyPage, default=actualtag==None, label=f"All ({len(logoDict.keys())})"))
        paginator = pages.Paginator(pages=pageGroups[:25], show_menu=True)
        return await paginator.respond(interaction=ctx.interaction, ephemeral=ephemeral)

    @cnplGroup.command(
        name="gen",
        description="✨ generate a text logo in a cute and pretty style.",
        integration_types=it,
    )
    @option(name="text", description="text", input_type=str, required=True)
    @option(name="logo", description="Choose a logo style", input_type=str, autocomplete=logo_autocomplete, required=True)
    @option(name="size", description="font size", input_type=int, required=False, default=40)
    @option(name="alignment", description="alignment", input_type=str, required=False, default=alignments[0], choices=alignments)
    @option(name="effect", description="effect val (amount of glitter, fire rotation etc.)", input_type=int, required=False, default=15)
    @option(name="textcolor1", description="main text color", input_type=str, required=False, default="#FF0000")
    @option(name="textcolor2", description="text color2", input_type=str, required=False, default="#FF0000")
    @option(name="textcolor3", description="text color3", input_type=str, required=False, default="#FF0000")
    @option(name="shadowcolor", description="shadow color", input_type=str, required=False, default="#000000")
    @option(name="backgroundcolor", description="background color", input_type=str, required=False, default="#FFFFFF")
    @option(name="transparent", description="transparent", input_type=int, required=False, default=1)
    @option(name="fileformat", description="file format", input_type=str, required=False, default=fileFormats[0], choices=fileFormats)
    @option(name="ephemeral", description="Make the response visible only for you", input_type=bool, required=False, default=False)
    async def cutenprettytextgenerator(self, ctx: discord.ApplicationContext, text: str, logo: str, size: int, alignment: str, effect: int, textcolor1: str, textcolor2: str, textcolor3: str, shadowcolor: str, backgroundcolor: str, transparent: int, fileformat: str, ephemeral: bool):
        selected_logo = logoDict.get(logo, None)
        if not selected_logo:
            return await ctx.respond("Invalid logo selected.", ephemeral=True)
        await ctx.defer(ephemeral=ephemeral)
        print(selected_logo)
        logo_id = selected_logo["id"]

        api_url = "https://cooltext.com/PostChange"

        params = {
            "LogoID": int(logo_id), 
            "Text": text,  
            "FontSize": size,

            "Color1_color": textcolor1, # glow color
            "Color2_color": textcolor2,  # outer
            "Color3_color": textcolor3, # inner
            "Integer14_color": shadowcolor, # shadow color

            "BackgroundColor_color": backgroundcolor,

            "FileFormat": fileFormats.index(fileformat)+1, # gif, gif trans, gif trans no dither, jpg, png, png trans

            "Boolean1": transparent, # transparent

            "Integer1": effect, # fire rotation, glitter count, border width
            #"Integer5": 1, # shadow shape, no shade, sharp, light, medium, high blurs
            #"Integer6": 10, # shadow opacity
            
            #"Integer7": 0, # shadow offset x
            #"Integer8": 0, # shadow offset y
            "Integer9": alignments.index(alignment), # alignment

            #"Integer10": 600, # size x
            #"Integer11": 600, # size y
            "Integer12": 1, # size x auto
            "Integer13": 1, # size y auto
        }
        print(params)
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            async with session.post(api_url, params=params) as response:
                if response.status != 200:
                    return await ctx.respond(f"Failed to generate logo: {response.status}", ephemeral=True)
                
                data = await response.json()
                logo_url = data.get('renderLocation')

                if not logo_url:
                    return await ctx.respond("Error generating the logo.")

                r = await session.get(logo_url)
                c = await r.content.read()
                file = discord.File(fp=io.BytesIO(c), filename="image.gif")

                embed = discord.Embed(color=0x2b2d31)
                embed.set_author(name="cooltext.com", url="https://cooltext.com/")
                embed.set_image(url="attachment://image.gif")
                return await ctx.edit(embed=embed, file=file)

def setup(bot):
    bot.add_cog(CutenprettylogoCog(bot))