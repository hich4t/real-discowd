from discord.commands import SlashCommandGroup
from discord.ext import commands
from discord import option

import discord, aiohttp, aiofiles, aiofiles.os, asyncio, re, uuid, random

from ffmpeg import Progress
from ffmpeg.asyncio import FFmpeg
from modules.catbox import upload

it = {discord.IntegrationType.user_install}
xfixupes = ["x.is-terrible.xyz", "girlcockx.com", "yiffx.com", "stupidpenisx.com", "fixupx.com", "fixvx.com", "twittpr.com", "fxtwitter.com", "vxtwitter.com"]

class isTerrible(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    twitterGroup = SlashCommandGroup("twitter", "twitter", integration_types=it)
    telegramGroup = SlashCommandGroup("telegram", "telegram", integration_types=it)
    toyhouseGroup = SlashCommandGroup("toyhouse", "toyhouse", integration_types=it)


    @twitterGroup.command(name="is-terrible", description="❌ Fixes your Twitter/X embed")
    @option(name="url", description="url", input_type=str, required=True)
    @option(name="domain", description="haha funny domain", input_type=str, choices=xfixupes, required=False, default="")
    @option(name="ephemeral", description="Make the response visible only for you", input_type=bool, required=False, default=False)
    #@twitterGroup.command(name="is-terrible", description="?? twitter/x.is-terrible.xyz | fixes your embed")
    async def twitteristerrible(self, ctx: discord.ApplicationContext, url: str, domain: str, ephemeral: bool):
        """
        api.fxtwitter.com
        api.vxtwitter.com
        """
        if domain == "": domain = random.choice(xfixupes)
        match = re.search(r"/([^/]+)/status/(\d+)", url)
        username = match.group(1)
        tid = match.group(2)
        return await ctx.respond(content=f"https://{domain}/{username}/status/{tid}", ephemeral=ephemeral)

    @telegramGroup.command(name="is-terrible", description="📃 Fixes your Telegram media")
    @option(name="attachment", description="attachment", input_type=discord.Attachment, required=True)
    @option(name="ephemeral", description="Make the response visible only for you", input_type=bool, required=False, default=False)
    async def telegramisterrible(self, ctx: discord.ApplicationContext, attachment: discord.Attachment, ephemeral: bool):
        await ctx.defer(ephemeral=ephemeral)
        async with aiofiles.open(f"./src/temp/{uuid.uuid4()}.mp4", "wb") as inputFile:
            inputPath = inputFile.name

            await attachment.save(inputPath)

        async with aiofiles.open(f"./src/temp/{uuid.uuid4()}.mp4", "wb") as outputFile:
            outputPath = outputFile.name

        ffmpeg = (
            FFmpeg()
            .option("y")
            .input(inputPath)
            .output(outputPath, vcodec="libx264", acodec="aac")
        )

        class FFmpegProgress:
            def __init__(self, ctx, ffmpeg, input_file, output_file):
                self.ctx = ctx
                self.input_file = input_file
                self.output_file = output_file
                self.duration = None
                self.ffmpeg = ffmpeg
                
            async def start(self):
                self.ffmpeg.on("stderr", self.on_stderr)
                self.ffmpeg.on("progress", self.on_progress)
                await self.ffmpeg.execute()

            async def on_stderr(self, line):
                match = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", line)
                if match:
                    h, m, s = map(float, match.groups())
                    self.duration = h * 3600 + m * 60 + s

            async def on_progress(self, progress: Progress):
                if self.duration:
                    progress_percent = (progress.time.total_seconds() / self.duration) * 100

                    bar_length = 10
                    filled_length = int(bar_length * progress_percent / 100)
                    bar = "█" * filled_length + "░" * (bar_length - filled_length)

                    await self.ctx.edit(content=f"-# > Processing video... `{progress_percent:.1f}%`\n`-# > [{bar}]` ⏳")

        progress = FFmpegProgress(ctx, ffmpeg, inputPath, outputPath)
        await progress.start()

        try:
            await ctx.edit(content="", file=discord.File(outputPath))
        except:
            async with aiohttp.ClientSession() as session:
                url = await upload(session, fp=outputPath)
                await ctx.edit(content=url)

        await aiofiles.os.remove(inputPath)
        await aiofiles.os.remove(outputPath)

    @toyhouseGroup.command(name="is-terrible", description="📷 Removes default toyhou.se watermark")
    @option(name="url", description="Raw url to watermarked image", input_type=str, required=True)
    @option(name="type", description="Type of watermark", input_type=str, choices=["center", "stretch", "tile"], required=True)
    @option(name="ephemeral", description="Make the response visible only for you", input_type=bool, required=False, default=False)
    async def toyhouseCmd(self, ctx: discord.ApplicationContext, url: str, type: str, ephemeral: bool):
        if not "toyhou.se/file" in url:
            return await ctx.respond(content="Provide correct toyhou.se url", ephemeral=True, delete_after=5)
        
        await ctx.defer(ephemeral=ephemeral)
        filename = url.split("/")[-1].split("?")[0]
        path = "./src/temp/"+filename
        async with aiohttp.ClientSession() as session:
            request = await session.get(url)
            status = request.status
            if status != 200:
                return await ctx.edit(content=f"Failed to download your image: {status}")
            
            content = await request.read()

        async with aiofiles.open(path, "wb") as file:
            await file.write(content)
        
        result = await asyncio.create_subprocess_exec(
            "python", "src/modules/toyhou.se.py", "--type", type, path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await result.communicate()
        if result.returncode == 0:
            await ctx.edit(file=discord.File(fp=path))
        else:
            print(result)
            print(stderr)
        
        await aiofiles.os.remove(path)

            



    
def setup(bot):
    bot.add_cog(isTerrible(bot))