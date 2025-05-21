from discord.commands import SlashCommandGroup
from discord.ext import commands
from discord import option

import discord, aiohttp, aiofiles, aiofiles.os, asyncio, re, uuid, time, io, base64, dotenv
from modules.catbox import upload

env = dotenv.dotenv_values(".env")
it = {discord.IntegrationType.user_install}

class utilityCog(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    utilityroup = SlashCommandGroup("utility", "iforgor", integration_types=it)

    async def altdownloader(self, filename: str, args: list):
        try:
            result = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await result.communicate()
            if result.returncode == 0:
                files = await aiofiles.os.listdir("./src/temp")
                files_downloaded = []
                for file in files:
                    if filename.split(".")[0] in file:
                        files_downloaded.append("./src/temp/"+file)
                return files_downloaded
            else:
                print(result)
                print(stderr)
                raise Exception()
        except Exception as e:
            print(e)

        return []
        


    async def cobaltdownloader(self, url: str, downloadMode: str):
        try:
            async with aiohttp.ClientSession(headers={"Accept": "application/json", "Content-Type": "application/json", "User-Agent": "insomnia/10.3.1"}) as session:
                body = {"url": url, "downloadMode":downloadMode, "filenameStyle": "nerdy"}

                response = await session.post(env.get("COBALT_INSTANCE"), json=body)
                status = response.status
                text = await response.text()
                print(status, text)
                data = await response.json()

                files = []

                async def downloader(session: aiohttp.ClientSession, url):
                    response = await session.get(url)
                    print(response.status)
                    content = await response.read()
                    
                    filename = response.headers.get("Content-Disposition", url.split("/")[-1].split("?")[0]).split("filename=")[-1].replace('"', "")
                    filename = "src/temp/"+filename
                    if response.status == 200 and len(content) != 0:
                        async with aiofiles.open(filename, "wb") as file:
                            await file.write(content)
                            return filename

                if data.get("status") in ["tunnel", "redirect"]:
                    file = await downloader(session, data.get("url"))
                    files.append(file)
                elif data.get("picker"):
                    tasks = [downloader(session, pick.get("url")) for pick in data.get("picker")]
                    if data.get("audio"): tasks.append(downloader(session, data.get("audio")))

                    files = await asyncio.gather(*tasks)

                return [file for file in files if file]
        except Exception as e: 
            print(e)
            return []
            
    @utilityroup.command(name="download", description="📩 Downloads your media")
    @option(name="url", description="url", input_type=str, required=True)
    @option(name="download_mode", description="download mode", input_type=str, choices=["auto", "audio"], required=False, default="auto")
    @option(name="ephemeral", description="Make the response visible only for you", input_type=bool, required=False, default=False)
    async def utilitydownloaderCmd(self, ctx: discord.ApplicationContext, url: str, download_mode: str, ephemeral: bool):
        await ctx.defer(ephemeral=ephemeral)
        async with asyncio.timeout(300):
            t1 = time.time()

            source = "[cobalt.tools](<https://cobalt.tools/>)"
            print(f"trying {source}")

            files = await self.cobaltdownloader(url, download_mode)
            if len(files) == 0:
                source = "[yt-dlp](<https://github.com/yt-dlp/yt-dlp>)"
                print(f"trying {source}")
                filename = str(uuid.uuid4())+".%(ext)s"
                args = [
                    "yt-dlp",
                    "-f", "bv*[vcodec=vp9]+ba/b" if download_mode == "auto" else "ba",
                    "--cookies-from-browser", "firefox"
                ]
                print(download_mode)
                if download_mode == "auto":
                    args.extend(["--merge-output-format", "mp4"])
                elif download_mode == "audio":
                    args.extend(["-x", "--audio-format", "mp3", "--audio-quality", "0"])

                args.extend(["-P", "./src/temp/", "-o", filename, url])

                files = await self.altdownloader(filename, args)

            if len(files) == 0:
                source = "[gallery-dl](<https://github.com/mikf/gallery-dl>)"
                print(f"trying {source}")
                uuid_name = str(uuid.uuid4()).split("-")[0]
                filename = uuid_name+"{title}.{extension}"
                args = ["gallery-dl", "--range", "1-10", "--ignore-config", "-o", "base-directory=./src/temp", "-o", "directory=.", "-o", "filename="+filename, url]
                #args = ["gallery-dl", "--range", "10", "--filename", f'"{filename}"', url]
                files = await self.altdownloader(uuid_name, args)

            if len(files) == 0:
                return await ctx.edit(content="-# > foiled to download your media 😔")
            
            t2 = time.time()

            try:
                chunks = [files[i:i + 10] for i in range(0, len(files), 10)] 
                await ctx.edit(content=f"-# > took {t2-t1:.2f}s • source: {source}", files=[discord.File(fp=file) for file in chunks[0]])
                if len(chunks) > 1:
                    for chunk in chunks[1:]:
                        await ctx.respond(files=[discord.File(fp=file) for file in chunk])
                    #t3 = time.time()
                    #await ctx.edit(content=f"-# > took {t2-t1:.2f}+{t3-t2:.2f}s.\n-# > source: {source}")
            except:
                async with aiohttp.ClientSession() as session:
                    urls = await asyncio.gather(*[upload(session, fp=file) for file in files])
                    t3 = time.time()
                    await ctx.edit(content=f"-# > took {t3-t1:.2f}s • source: {source}\n"+"\n-# - ".join(urls))
            await asyncio.gather(*[aiofiles.os.remove(file) for file in files])

    def generate_waveform_from_text(self,text: str):
        """Convert text into a waveform pattern"""
        letter_map = {
            'A': [0, 128, 255, 128, 0],
            'B': [255, 128, 64, 128, 255],
            'C': [255, 128, 0, 128, 255],
            # Add more letters as needed
        }
        waveform = []
        for char in text.upper():
            waveform.extend(letter_map.get(char, [128]))  # Default to a neutral value if no match
        return base64.b64encode(bytes(waveform)).decode()

    @utilityroup.command(name="voicemessage", description="🔊 Audio to Voice Message")
    @option(name="attachment", description="attachment", input_type=discord.Attachment, required=True)
    @option(name="ephemeral", description="Make the response visible only for you", input_type=bool, required=False, default=False)
    async def voicemessageCmd(self, ctx: discord.ApplicationContext, attachment: discord.Attachment, ephemeral: bool):
        filename = f"src/temp/{uuid.uuid4()}.ogg"
        print(attachment.waveform)
        waveform = self.generate_waveform_from_text("abc")
        await attachment.save(filename)
        await ctx.respond(file=discord.VoiceMessage(fp=filename, waveform=waveform), ephemeral=ephemeral)
        await aiofiles.os.remove(filename)

    @utilityroup.command(name="webhook", description="✨ Creates webhook", integration_types={discord.IntegrationType.guild_install})
    async def createwebhookCmd(self, ctx: discord.ApplicationContext):
        if not ctx.author.guild_permissions.manage_webhooks:
            return await ctx.respond(content="no `Manage Webhooks` perms", ephemeral=True, delete_after=5)
        try:
            webhook = await ctx.channel.create_webhook(name="real discowd", reason=f"Slash Command by {ctx.author.name}")
            return await ctx.respond(content=webhook.url, ephemeral=True)
        except Exception as e:
            return await ctx.respond(content=e, ephemeral=True)
    


def setup(bot):
    bot.add_cog(utilityCog(bot))