import discord
from discord import app_commands, ui
from discord.ext import commands
from cogs import utils, embeds
from datetime import datetime

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @classmethod
    async def event_callback(cls, interaction: discord.Interaction):
        if interaction.data['custom_id'].startswith('bot::tickets::new'):
            if interaction.user.id in utils.config['blacklist']:
                await interaction.response.send_message("You do not have permission to create tickets!")
                return
            modal = cls.modals.Ticket()
            modal.set_data(
                placeholder=interaction.data['custom_id'].split('-')[1],
                member = interaction.user,
                viewCreator = cls.views.TicketControl
            )
            await interaction.response.send_modal(modal)
        else:
            await interaction.response.defer()

    class views:
        class InitialState(ui.View):
            def __init__(self):
                super().__init__(timeout=None)
                for key, val in utils.config['ticketCategories'].items(): self.add_item(self.b_generic(val[0], key, val[1]))


            class b_generic(ui.Button):
                def __init__(self, name, customID, emoji):
                    super().__init__(label=name, emoji=emoji, custom_id="bot::tickets::new-" + customID)
                
                async def callback(self, interaction: discord.Interaction): pass
        
        class TicketControl(ui.View):
            def __init__(self, channelID):
                self.channelID = channelID
                super().__init__(timeout=None)
                self.add_item(self.b_close(channelID))
                self.add_item(self.b_lock(channelID))

            class b_close(ui.Button):
                def __init__(self, channelID):
                    super().__init__(label="Close", emoji="❎", style=discord.ButtonStyle.danger, custom_id=f"bot::tickets::close-{channelID}", disabled=True)
                async def callback(self, interaction: discord.Interaction): pass
            
            class b_lock(ui.Button):
                def __init__(self, channelID):
                    super().__init__(label="Lock", emoji="🔒", style=discord.ButtonStyle.secondary, custom_id=f"bot::tickets::lock-{channelID}", disabled=True)
                async def callback(self, interaction: discord.Interaction): pass

    class modals:
        class Ticket(ui.Modal, title="Create a new ticket"):
            i_description = ui.TextInput(label="Description of issue", placeholder="Describe your issue", style=discord.TextStyle.long, max_length=1024)

            def set_data(self, *, placeholder: str, member: discord.Member, viewCreator: callable):
                self.category = placeholder
                self.member = member
                self.viewCreator = viewCreator

            async def on_submit(self, interaction):
                await interaction.response.defer()
                cat = interaction.guild.get_channel(utils.config['snowflakes']['ticketsCategory'])
                ticketChannel = await interaction.guild.create_text_channel(
                    f"t-{str(utils.config['ticketNum']).zfill(4)}",
                    category=cat,
                    topic=self.i_description.value,
                    overwrites={
                        self.member: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True)
                    }
                )
                conf = utils.config
                conf['ticketNum'] += 1
                utils.set_config(conf)
                embed = discord.Embed(title=f'New Ticket from {self.member.display_name}', color=discord.Color.blurple(), timestamp=datetime.now())
                embed.add_field(name='User', value=self.member.mention, inline=True)
                embed.add_field(name='Type', value=self.category, inline=True)
                embed.add_field(name='Issue', value=self.i_description.value, inline=False)
                embed.set_footer(text='Submitted at')
                view = self.viewCreator(ticketChannel.id)
                await ticketChannel.send(embed=embed, view=view)

    @commands.command()
    async def show(self, ctx):
        await ctx.message.delete()
        await ctx.send(embed=discord.Embed(title="Create Ticket", description="Click button below to create a new ticket"), view=self.views.InitialState())
    
    @commands.group(aliases=['cat'])
    @commands.is_owner()
    async def categories(self, ctx):
        if ctx.invoked_subcommand is None: await ctx.send(embed=embeds.presets.help_categories())
    
    @categories.command(name='list')
    async def categories_list(self, ctx):
        embed = discord.Embed(title='Categories', description='List of available categories', color=discord.Color.blurple())
        for key, item in utils.config['ticketCategories'].items():
            embed.add_field(name=f"`{key}`", value=f"{item[1]} {item[0]}", inline=False)
        await ctx.send(embed=embed)

    @categories.command(name='add')
    async def categories_add(self, ctx, catID, emoji, *, name):
        conf = utils.config
        conf['ticketCategories'][catID] = [name, emoji]
        utils.set_config(conf)
        embed = discord.Embed(title='Successfully added category', description=f'`{catID}`: {emoji} {name}', color=discord.Color.brand_green())
        await ctx.send(embed=embed)

    @categories.command(name='remove')
    async def categories_remove(self, ctx, catID):
        conf = utils.config
        if catID in conf['ticketCategories']:
            del conf['ticketCategories'][catID]
            utils.set_config(conf)
            embed = discord.Embed(title='Successfully removed category', description=f'`{catID}`', color=discord.Color.brand_green())
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title='Category not found', description=f'`{catID}`', color=discord.Color.brand_red())
            await ctx.send(embed=embed)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Tickets(bot))