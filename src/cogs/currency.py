from discord.commands import SlashCommandGroup
from discord.ext import commands
import discord, aiohttp, csv, re

it = {discord.IntegrationType.user_install}
fictionals = list(csv.DictReader(open("./src/fictionals.csv")))

class CurrencyCog(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    currencyGroup = SlashCommandGroup("currency", "currency convertor", integration_types=it)

    async def fictionalComplete(self, value):
        results = []
        for currency in fictionals:
            name = currency.get("Currency")
            game = currency.get("Game")
            matched = value in name.lower() or value in game.lower()
            #print(matched)
            if matched or value == "":
                results.append(f"{name} ({game})")

        #print(results)
        return results[:25]

    async def fictionalAutocomplete(self, ctx: discord.AutocompleteContext):
        return await self.fictionalComplete(ctx.value.lower())

    async def fictionalValueAutocomplete(self, ctx: discord.AutocompleteContext):
        value = ctx.value.lower().split(" ", 1)
        if len(value) <= 1:
            try:
                num = float(value[0])
                val = ""
            except:
                num = 1
                val = value[0]
        else:
            num = value[0]
            val = value[1]
        result = await self.fictionalComplete(val.lower())

        return [f"{num} {r}" for r in result][:25]

    @currencyGroup.command(name="fictional", description="💱 converts your fictional currency to other fictional currency")
    async def fictionalConvert(self,
        ctx: discord.ApplicationContext, 
        fromc: str = discord.Option(name="from", description="currency you want to convert from", required=True, autocomplete=fictionalValueAutocomplete), 
        to: str = discord.Option(name="to", description="currency you want to convert to", required=True, autocomplete=fictionalAutocomplete),
        ephemeral: bool = discord.Option(name="ephemeral", description="Make the response visible only for you", input_type=bool, required=False, default=False)):
        
        fromV = re.match(r"^(\d+)\s+(.+?)\s*\((.*?)\)\s*$", fromc)
        fromValue = float(fromV.group(1))
        fromPrice = 0

        toV = re.split(r"\s*\((.*?)\)\s*", to)
        toPrice = 0

        for currency in fictionals:
            if currency.get("Currency") == fromV.group(2):
                fromPrice = float(currency.get("Price of 1"))
            
            if currency.get("Currency") == toV[0]:
                toPrice = float(currency.get("Price of 1"))

        try:
            toValue = (fromValue*fromPrice)/toPrice
        except:
            toValue = 0


        return await ctx.respond(content=f"""{fromValue:.2f} {fromV.group(2)}[{fromV.group(3)}] ≈ {toValue:.2f} {toV[0]}[{toV[1]}]
-# data from [gdcolon.com/currencies](<https://gdcolon.com/currencies>)""", ephemeral=ephemeral)

    async def irlComplete(self, value: str):
        async with aiohttp.ClientSession() as session:
            r = await session.get("https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies.json")
            j = await r.json()
            value = value.lower()
            matches = [f'{name} [{abrv}]' for abrv, name in j.items() if value == abrv.lower()]
            matches += [f'{name} [{abrv}]' for abrv, name in j.items() if value in name.lower() or value in abrv.lower()]

            return list(set(matches))

    async def irlAutocomplete(self, ctx):
        if type(ctx) == discord.AutocompleteContext: value = ctx.value
        else: value = ctx
        results = await self.irlComplete(value)

        return results[:25]

    async def irlValueAutocomplete(self, ctx):
        if type(ctx) == discord.AutocompleteContext:
            value = ctx.value.lower()
        else: value = ctx
        value = value.split(" ", 1)
        if len(value) <= 1:
            try:
                num = float(value[0])
                val = ""
            except:
                num = 1
                val = value[0]
        else:
            num = value[0]
            val = value[1]
        result = await self.irlComplete(val.lower())

        return [f"{num} {r}" for r in result][:25]

    @currencyGroup.command(name="irl", description="💱 converts irl/crypto currency")
    async def irlConvert(self, ctx: discord.ApplicationContext, 
        fromc: str = discord.Option(name="from", description="currency you want to convert from", required=True, autocomplete=irlValueAutocomplete), 
        to: str = discord.Option(name="to", description="currency you want to convert to", required=True, autocomplete=irlAutocomplete),
        ephemeral: bool = discord.Option(name="ephemeral", description="Make the response visible only for you", input_type=bool, required=False, default=False)):
        
        try:
            fromV = re.match(r"^(\d+)\s+(.+?)\s*\[(.*?)\]\s*$", fromc)
            fromAbrv = fromV.group(3)
            fromFull = fromV.group(2)
            fromValue = float(fromV.group(1))
        except:
            fromc = (await self.irlValueAutocomplete(fromc))[0]
            fromV = re.match(r"^(\d+)\s+(.+?)\s*\[(.*?)\]\s*$", fromc)
            fromAbrv = fromV.group(3)
            fromFull = fromV.group(2)
            fromValue = float(fromV.group(1))
        
        try:
            toV = re.match(r"^(.*?)\s*\[(.*?)\]$", to)
            toAbrv = toV.group(2)
            toFull = toV.group(1)
            toValue = 0
        except:
            to = (await self.irlAutocomplete(to))[0]
            toV = re.match(r"^(.*?)\s*\[(.*?)\]$", to)
            toAbrv = toV.group(2)
            toFull = toV.group(1)
            toValue = 0

        async with aiohttp.ClientSession() as session:
            r = await session.get(f"https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/{fromAbrv}.json")
            j = await r.json()
            toValue = j.get(fromAbrv).get(toAbrv)

            return await ctx.respond(content=f"{fromValue:.2f} {fromFull} ≈ {(fromValue*toValue):.2f} {toFull}", ephemeral=ephemeral)
    
def setup(bot):
    bot.add_cog(CurrencyCog(bot))