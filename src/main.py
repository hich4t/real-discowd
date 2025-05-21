import discord, aiofiles.os, dotenv
env = dotenv.dotenv_values(".env")

bot = discord.Bot(cache_app_emojis=True)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    path = "src/temp/"
    files = await aiofiles.os.listdir(path)
    for file in files:
        await aiofiles.os.remove(path+file)

bot.load_extensions("cogs")

bot.run(env.get("TOKEN"))