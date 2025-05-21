from discord.commands import SlashCommandGroup
from discord.ext import commands
from discord import option
import discord

import json

it = {discord.IntegrationType.user_install}
tr = {
    "A": "₳",
    "B": "฿",
    "C": "₡",
    "D": "₫",
    "E": "€", 
    "F": "£",
    "G": "₲",
    "H": "₴",
    "I": "៛",
    "J": "৳",
    "K": "₭",
    "L": "₺",
    "M": "₼",
    "N": "₦",
    "O": "₪",
    "P": "₱",
    "Q": "₾",
    "R": "₹",
    "S": "$",
    "T": "₸",
    "U": "֏",
    "V": "৹",
    "W": "₩",
    "X": "¤",
    "Y": "￥",
    "Z": "₠",
    ".": "💰",
    ",": "💳",
    "-": "💰",
    "!": "💸",
    "?": "🤑",
    ":": "💱"
}
crs = {
    "А": "₳",
    "Б": "₲",
    "В": "฿",
    "Г": "₴",
    "Д": "",
    "Е": "€",
    "Е": "€",
    "Ж": "",
    "З": "",
    "С": "₡",
}

rs = {
    "`": "ё",
    "]": "ъ",
    "s": "ы",
    "'": "э",
    "`": "Ё", 
    "s": "Ы", 
    "]": "Ъ", 
    "'": "Э",
    "q": "й", "w": "ц", "e": "у", "r": "к", "t": "е", "y": "н", "u": "г", "i": "ш", "o": "щ", "p": "з",
    "a": "ф", "s": "і", "d": "в", "f": "а", "g": "п", "h": "р", "j": "о", "k": "л", "l": "д",
    "z": "я", "x": "ч", "c": "с", "v": "м", "b": "и", "n": "т", "m": "ь",
    "'": "є", "[": "х", "]": "ї", ";": "ж", ",": "б", ".": "ю",
    "Q": "Й", "W": "Ц", "E": "У", "R": "К", "T": "Е", "Y": "Н", "U": "Г", "I": "Ш", "O": "Щ", "P": "З",
    "A": "Ф", "S": "І", "D": "В", "F": "А", "G": "П", "H": "Р", "J": "О", "K": "Л", "L": "Д",
    "Z": "Я", "X": "Ч", "C": "С", "V": "М", "B": "И", "N": "Т", "M": "Ь",
    "\"": "Є", "{": "Х", "}": "Ї", ":": "Ж", "<": "Б", ">": "Ю"
}
rt = {v: k for k, v in tr.items()}
sr = {v: k for k, v in rs.items()}

dingbats = json.loads(open("./src/dingbats.json", "r").read())

class MoneyLangCog(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    mlGroup = SlashCommandGroup("translator", "tlansrator", integration_types=it)

    async def money_translator(self, text: str):
        newtext = ""

        keys = tr.keys()
        vals = tr.values()

        for i, char in enumerate(text):
            upper = char.upper()

            if upper in keys:
                if char.islower():
                    newtext += tr[char.upper()]+"​"
                else:
                    newtext += tr[char]
            elif upper in vals:
                try:
                    next = text[i+1]
                    if next == "​":
                        newtext += rt[char].lower()
                    else:
                        newtext += rt[char]
                except:
                    pass
            else:
                if char == "​": continue
                newtext += char

        return newtext

    @commands.message_command(name="rozkladka", integration_types={discord.IntegrationType.user_install, discord.IntegrationType.guild_install})
    async def rozkladka_message(self, ctx: discord.ApplicationContext, message: discord.Message):
        text = ''
        rsk = rs.keys()
        srk = sr.keys()
        for char in message.content:
            if char in rsk:
                text += rs[char]
            elif char in srk:
                text += sr[char]
            else:
                text += char
        return await ctx.respond(content=text, ephemeral=True)



    @commands.message_command(name="moneylang", integration_types={discord.IntegrationType.user_install, discord.IntegrationType.guild_install})
    async def moneylang_message(self, ctx: discord.ApplicationContext, message: discord.Message):
        text = await self.money_translator(message.content)
        return await ctx.respond(content=text, ephemeral=True)

    @mlGroup.command(name="moneylang", description="🤑 translates your message")
    @option(name="text", description="Your text here", input_type=str, required=True)
    @option(name="ephemeral", description="Make the response visible only for you", input_type=bool, required=False, default=False)
    async def moneylang_cmd(self, ctx: discord.ApplicationContext, text, ephemeral: bool):
        text = await self.money_translator(text)
        return await ctx.respond(content=text, ephemeral=ephemeral)
    




    @commands.message_command(name="wingdings", integration_types={discord.IntegrationType.user_install, discord.IntegrationType.guild_install})
    async def wingdings_message(self, ctx: discord.ApplicationContext, message: discord.Message):
        text = message.content  # Get original text
        for type, symbols in dingbats.items():
            back = {v: k for k, v in symbols.items()}

            new_text = ""
            for symbol in text:
                if symbol in back:
                    new_text += back[symbol]
                else:
                    new_text += symbol

            text = new_text

        return await ctx.respond(content=text, ephemeral=True)    

    @mlGroup.command(name="wingdings", description="omg undertale refrence")
    @option(name="text", description="Your text here", input_type=str, required=True)
    @option(name="type", description="uhhhhhh different symbosl i forgor", input_type=str, required=False, choices=["Wingdings", "Webdings", "Wingdings 2", "Wingdings 3", "Symbol"])
    @option(name="ephemeral", description="Make the response visible only for you", input_type=bool, required=False, default=False)
    async def wingdings_cmd(self, ctx: discord.ApplicationContext, text, type: str = "Wingdings", ephemeral: bool = False):
        orig = dingbats[type]
        back = {v: k for k, v in orig.items()}

        result = ""
        for char in text:
            if orig.get(char, None):
                result += orig.get(char)
            elif back.get(char, None):
                result += back.get(char)
            else:
                result += char

        return await ctx.respond(content=result, ephemeral=ephemeral)

    
def setup(bot):
    bot.add_cog(MoneyLangCog(bot))