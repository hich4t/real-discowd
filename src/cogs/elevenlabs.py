from discord.commands import SlashCommandGroup
from discord.ext import commands
from discord import option
import discord, aiohttp, asyncio, io, json, time, dotenv
import modules.perms as perms
from modules.catbox import upload

it = {discord.IntegrationType.user_install}

env = dotenv.dotenv_values(".env")
IIkey = env.get("IILABSAPI")
print(IIkey)
languages = {'English': 'en', 'Japanese': 'ja', 'Chinese': 'zh', 'German': 'de', 'Hindi': 'hi', 'French': 'fr', 'Korean': 'ko', 'Portuguese': 'pt', 'Italian': 'it', 'Spanish': 'es', 'Indonesian': 'id', 'Dutch': 'nl', 'Turkish': 'tr', 'Filipino': 'fil', 'Polish': 'pl', 'Swedish': 'sv', 'Bulgarian': 'bg', 'Romanian': 'ro', 'Arabic': 'ar', 'Czech': 'cs', 'Greek': 'el', 'Finnish': 'fi', 'Croatian': 'hr', 'Malay': 'ms', 'Slovak': 'sk', 'Danish': 'da', 'Tamil': 'ta', 'Ukrainian': 'uk', 'Russian': 'ru'}


class IILabsCog(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    IIlabs = SlashCommandGroup("elevenlabs", "elevenlabs ahh commands", integration_types=it)

    async def IIlabsLanguage(self, ctx: discord.AutocompleteContext):
        return [name for name,id in languages.items() if ctx.value.lower() in name.lower()][:25]

    @IIlabs.command(name="tokens", description="✨ tokens left")
    @option(name="ephemeral", description="Make the response visible only for you", input_type=bool, required=False, default=False)
    @perms.permission("elevenlabs")
    async def iitokens(self, ctx: discord.ApplicationContext, ephemeral: bool):
        async with aiohttp.ClientSession(headers={"xi-api-key": IIkey}) as session:
            r = await session.get("https://api.elevenlabs.io/v1/user/subscription")
            j = await r.json()
            s = r.status
            if s != 200:
                return await ctx.respond(f"""somethign went wrong {s}
-# {j}""", ephemeral=ephemeral)
            
            used = j.get("character_count")
            limit = j.get("character_limit")
            tokens = limit-used
            return await ctx.respond(f"""-# 🏷 used: {used} ({round((used/limit)*100)}%)
-# 📝 remaining: {tokens}""", ephemeral=ephemeral)

    async def dubdow(self, ctx: discord.ApplicationContext, headers, dubid: str, donotping: bool = True):
        async with aiohttp.ClientSession() as session:
            lang = dubid[-2:]
            print(f"https://api.elevenlabs.io/v1/dubbing/{dubid.strip(lang)}/audio/{lang}")
            dubR = await session.get(f"https://api.elevenlabs.io/v1/dubbing/{dubid.strip(lang)}/audio/{lang}", headers=headers)

            if dubR.status != 200:
                jj = await dubR.json()
                return await ctx.edit(content=f"""something went wrong: {dubR.status}
{jj}""") 
            dubContent = await dubR.content.read()
            #print(dubContent)
            message = f"-# {f'{ctx.author.mention} ' if not donotping else ''}{dubid}"+"\n"
            
            try:
                print("trying uploading 2 discord")
                file = discord.File(fp=io.BytesIO(dubContent), filename="video.mp4")
                return await ctx.edit(content=message, file=file)
            except discord.errors.NotFound:
                try:
                    print("trying uploading 2 user's dms")
                    file = discord.File(fp=io.BytesIO(dubContent), filename="video.mp4")
                    return await ctx.author.send(content=message, file=file)
                except Exception as e:
                    print("trying uploading 2 catbox moe user's dms")
                    print(e)
                    url = await upload(session, io=dubContent)
                    return await ctx.author.send(content=message+url)
            except discord.errors.HTTPException:
                print("trying uploading 2 catbox moe")
                url = url = await upload(session, io=dubContent)
                return await ctx.edit(content=message+url)

    @IIlabs.command(name="download", description="📩 downloads your dub")
    @option(name="dubid", description="dub id", required=True)
    @option(name="ephemeral", description="Make the response visible only for you", input_type=bool, required=False, default=False)
    @perms.permission("elevenlabs")
    async def iidownload(self, ctx: discord.ApplicationContext, dubid, ephemeral):
        headers={"xi-api-key": IIkey}
        await ctx.defer(ephemeral=ephemeral)
        
        return await self.dubdow(ctx, headers, dubid)

    @IIlabs.command(name="dub", description="🤖 dubs your video")
    @option(name="target_language", description="The Target language to dub the content into.", input_type=str, required=True, autocomplete=IIlabsLanguage)
    @option(name="attachment", description="video", required=False)
    @option(name="url", description="URL of the source video/audio file.", input_type=str, required=False)
    @option(name="source_language", description="source language", input_type=str, required=False, default="auto")
    @option(name="num_speakers", description="number of speakers", input_type=int, required=False, default=0)
    @option(name="start_time", description="Start time of the source video/audio file.", input_type=int, required=False, default=0)
    @option(name="end_time", description="End time of the source video/audio file.", input_type=int, required=False, default=0)
    @option(name="use_profanity_filter", description="[BETA] Whether transcripts should have profanities censored with the words ‘[censored]’", input_type=bool, required=False, default=False)
    @option(name="ephemeral", description="Make the response visible only for you", input_type=bool, required=False, default=False)
    @option(name="donotping", description="No longer pings you", input_type=bool, required=False, default=False)
    @perms.permission("elevenlabs")
    async def iidub(self, ctx: discord.ApplicationContext, target_language, attachment: discord.Attachment, url: str, source_language, num_speakers, start_time, end_time, use_profanity_filter, ephemeral: bool, donotping: bool):
        if url == "" and attachment == None:
            return await ctx.respond("no attachment?", ephemeral=True)
        await ctx.defer(ephemeral=ephemeral)
        async with aiohttp.ClientSession() as session:
            baseUrl = "https://api.elevenlabs.io/v1/dubbing"
            headers={"xi-api-key": IIkey}
            attachurl = url or attachment.url
            attachRequest = await session.get(attachurl)
            attachStatus = attachRequest.status

            if attachStatus != 200:
                return await ctx.respond(f"foiled to load attachment {attachStatus}", ephemeral=True)
            
            attachContent = await attachRequest.content.read()

            form = aiohttp.FormData()
            form.add_field("target_lang", languages[target_language])
            form.add_field("source_lang", source_language)
            form.add_field("num_speakers", str(num_speakers))
            form.add_field("start_time", str(start_time))
            form.add_field("end_time", str(end_time))
            form.add_field("use_profanity_filter", str(use_profanity_filter).lower())
            form.add_field("watermark", "true")
            form.add_field("file", io.BytesIO(attachContent), filename="input.mp4", content_type="video/mp4")

            r = await session.post(baseUrl, headers=headers, data=form)
            s = r.status
            h = r.headers
            j = await r.json()

            #print(s, h, j)

            if s != 200:
                return await ctx.edit(content=f"""something went wrong: {s}
{json.dumps(j)}""")

            dubId = j.get("dubbing_id")
            est = j.get("expected_duration_sec")
            current = time.time()
            await ctx.edit(content=f""":cooking: let him cook. `{dubId}{languages[target_language]}`
-# est <t:{round(current+est)}:R>""")
            while True:
                waitR = await session.get(f"https://api.elevenlabs.io/v1/dubbing/{dubId}", headers=headers)
                waitS = waitR.status
                waitJ = await waitR.json()
                status = waitJ.get("status")
                error = waitJ.get("error")
                if status == "dubbed":
                    break
                if error != None:
                    return await ctx.edit(content=f"something went wrong: {waitS} {error}")
                if time.time() > current+est*2:
                    return await ctx.edit(content=f"something went wrong: waited 4 2 long :sob:")
            
            return await self.dubdow(ctx, headers, f"{dubId}{languages[target_language]}", donotping)


def setup(bot):
    bot.add_cog(IILabsCog(bot))