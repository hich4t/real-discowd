from discord.commands import SlashCommandGroup
from discord.ext import commands
from discord import option, SelectOption
import discord, aiohttp, asyncio, io, json, time, dotenv
import modules.perms as perms
import modules.smspool as smspool

env = dotenv.dotenv_values(".env")

it = {discord.IntegrationType.user_install}

colors = [0x1c49bf, 0x059669, 0xef4444]

class SmsPoolCog(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        self.client = smspool.SMSPoolClient(env.get("SMSPOOL"))

    smspoolGroup = SlashCommandGroup("smspool", "smsstuff", integration_types=it)

    @smspoolGroup.command(name="balance", description="👛 smspool balance")
    @option(name="ephemeral", description="Make the response visible only for you", input_type=bool, required=False, default=False)
    @perms.permission("smspool")
    async def smspoolbalance(self, ctx: discord.ApplicationContext, ephemeral: bool):
        async with self.client as client:
            balance = await client.get_balance()
            return await ctx.respond(f"-# {balance}$", ephemeral=ephemeral)
    
    async def serviceAutocomplete(self, ctx: discord.AutocompleteContext):
        async with self.client as client:
            return [service.name for service in client.services if ctx.value.lower() in service.name.lower()][:25]

    def country_to_emoji(self, country_code):
        return ''.join(chr(0x1F1E6 + ord(c) - ord('A')) for c in country_code.upper())

    @commands.Cog.listener("on_interaction")
    async def purchaseInter(self, inter: discord.Interaction):
        if inter.data.get("custom_id", None) == "purchase_sms":
            _, author, service, country = inter.data["values"][0].split("_")
            if inter.user.id != int(author):
                return await inter.respond(content="-# > Not your interaction smh :man_facepalm:", ephemeral=True, delete_after=5)

            message = await inter.respond(content="🤔")            
            async with self.client as client:
                phone = await client.order_sms(service, country, 0)

                embed = discord.Embed(color=colors[0])
                embed.set_author(name="smspool.net", url="https://smspool.net/?r=0303", icon_url="https://www.smspool.net/apple-touch-icon.png")
                embed.add_field(name="Phone Number", value=phone.number, inline=True)
                embed.add_field(name="Country", value=f":flag_{client.get_country(name=phone.country).short_name.lower()}: {phone.country}", inline=True)
                embed.add_field(name="_ _", value="_ _", inline=True)
                embed.add_field(name="Service", value=phone.service, inline=True)
                embed.add_field(name="Cost", value=f"{phone.cost}$", inline=True)
                embed.add_field(name="_ _", value="_ _", inline=True)
                embed.add_field(name="Code", value="Awaiting...", inline=True)
                embed.add_field(name="Expires", value=f"<t:{phone.expiration}:R>", inline=True)

                ui = discord.ui.View(disable_on_timeout=True, timeout=phone.expires_in)
                cancel_button = discord.ui.Button(label="Refund", emoji="🪙", style=discord.ButtonStyle.danger, custom_id=f"refund_orderid_{phone.orderid}")
                resend_button = discord.ui.Button(label="Resend", emoji="🔄", style=discord.ButtonStyle.blurple, custom_id=f"resend_orderid_{phone.orderid}")

                async def wait_for_sms(resend: bool = False):
                    code = ""
                    while not code and time.time() < phone.expiration:
                        check = await client.check_sms(phone.orderid)
                        if check.success == 6:
                            return None
                        if check.sms:
                            embed.fields[6].value = check.sms
                            if not resend:
                                embed.fields.pop(7)
                            embed.color = colors[1]
                            if not resend:
                                cancel_button.disabled = True
                                ui.add_item(resend_button)
                            else:
                                resend_button.disabled = True
                            await inter.edit_original_response(embed=embed, view=ui)
                            break
                        await asyncio.sleep(5)

                async def cancel_callback(inter: discord.Interaction):
                    #_,_, orderid = inter.data.get("custom_id", None).split("_")
                    success = await client.cancel_sms(phone.orderid)
                    if success.success == 1:
                        await inter.respond(content="-# > Refunded")
                        #await message.message.delete()
                    else:
                        await inter.respond(content=f"-# > {success.message}", delete_after=5)
                
                async def resend_callback(intera: discord.Interaction):
                    reply = await client.resend_sms(phone.orderid)
                    if reply.success == 0:
                        resend_button.disabled = True
                        await inter.edit_original_response(view=ui)
                        return await intera.respond(content=f"-# > {reply.message}", delete_after = 5)
                    await wait_for_sms(resend=True)

                cancel_button.callback = cancel_callback
                resend_button.callback = resend_callback

                ui.add_item(cancel_button)
                #ui.add_item(resend_button)
                #ui.add_item(delete_button)

                await inter.edit_original_response(content="", embed=embed, view=ui)
                await wait_for_sms()

                

    @smspoolGroup.command(name="service", description="🤑 gets service prices")
    @option(name="service", description="your service here", input_type=str, autocomplete=serviceAutocomplete)
    @option(name="ephemeral", description="Make the response visible only for you", input_type=bool, required=False, default=False)
    @perms.permission("smspool")
    async def smspoolservice(self, ctx: discord.ApplicationContext, service: str, ephemeral: bool):
        async with self.client as client:
            service = client.get_service(name=service)
            success_rates = await client.retrieve_success_rate(service.id, 1, True)
    
            select = discord.ui.Select(custom_id="purchase_sms", placeholder="Order SMS", options=[SelectOption(label=rate.country.name, value=f"purchase_{ctx.author.id}_{service.id}_{rate.country.id}", description=f"{rate.low_price}$ • {rate.success_rate}%", emoji=self.country_to_emoji(rate.country.short_name)) for rate in success_rates[:10]]) # f":flag_{rate.country.short_name.lower()}:"
            ui = discord.ui.View(select, timeout=30)

            return await ctx.respond(">>> "+"\n".join(["-# :flag_{}: {} • {}$ • {}%".format(rate.country.short_name.lower(), rate.country.name, rate.low_price, rate.success_rate) for rate in success_rates[:10]]), ephemeral=ephemeral, view=ui)

def setup(bot):
    bot.add_cog(SmsPoolCog(bot))