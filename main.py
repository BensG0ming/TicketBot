import discord
from discord.ext import commands
from discord.ui import View, Button
import random
import asyncio
from keep_alive import keep_alive

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

open_tickets = {}


@bot.event
async def on_ready():
    print(f'✅ Bot đã đăng nhập dưới tên: {bot.user}')


# View để gửi panel tạo ticket
class TicketPanelView(View):

    def __init__(self, author_id):
        super().__init__(timeout=None)
        self.author_id = author_id

    @discord.ui.button(label="🎫 Mở Ticket",
                       style=discord.ButtonStyle.green,
                       custom_id="open_ticket")
    async def open_ticket(self, interaction: discord.Interaction,
                          button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "❌ Bạn không được phép dùng nút này!", ephemeral=True)
            return

        if interaction.user.id in open_tickets:
            await interaction.response.send_message(
                "⚠️ Bạn đã có ticket đang mở!", ephemeral=True)
            return

        guild = interaction.guild
        username = interaction.user.name.lower().replace(" ", "-")
        random_id = random.randint(1000, 9999)
        channel_name = f"ticket-{username}-{random_id}"

        # 🔥 Tạo hoặc lấy category
        category_name = "🎫 Tickets"
        category = discord.utils.get(guild.categories, name=category_name)
        if category is None:
            category = await guild.create_category(
                name=category_name, reason="Tạo category cho ticket")

        # 🛡️ Quyền riêng
        overwrites = {
            guild.default_role:
            discord.PermissionOverwrite(read_messages=False),
            interaction.user:
            discord.PermissionOverwrite(read_messages=True,
                                        send_messages=True),
            guild.me:
            discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        # 📁 Tạo channel ticket
        ticket_channel = await guild.create_text_channel(
            channel_name,
            overwrites=overwrites,
            category=category,
            reason="Tạo ticket mới")
        open_tickets[interaction.user.id] = ticket_channel.id

        # 📩 Gửi embed + nút đóng
        embed = discord.Embed(
            title="🎟️ Ticket hỗ trợ",
            description=
            "Hãy nói rõ món hàng mà bạn muốn mua. Staff sẽ phản hồi sớm nhất có thể. <@1317392633022255105>",
            color=discord.Color.blurple())
        embed.set_footer(text="Bấm nút 🔒 Close để đóng ticket.")

        await ticket_channel.send(content=f"{interaction.user.mention}",
                                  embed=embed,
                                  view=CloseTicketView(interaction.user.id,
                                                       random_id))
        await interaction.response.send_message(
            f"✅ Ticket đã được tạo tại: {ticket_channel.mention}",
            ephemeral=True)


# View để đóng ticket
class CloseTicketView(View):

    def __init__(self, user_id, random_id):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.random_id = random_id

    @discord.ui.button(label="🔒 Close",
                       style=discord.ButtonStyle.red,
                       custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction,
                           button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "🚫 Bạn không thể đóng ticket của người khác!", ephemeral=True)
            return

        channel = interaction.channel
        username = interaction.user.name.lower().replace(" ", "-")
        new_name = f"closed-{username}-{self.random_id}"

        await interaction.response.send_message("⏳ Đang đóng ticket...")

        try:
            await channel.edit(name=new_name)
            await channel.set_permissions(interaction.user,
                                          send_messages=False)
            await channel.send("✅ Ticket đã được đóng. Sẽ tự xóa sau 3 giây.")
            await asyncio.sleep(3)
            await channel.delete(reason="Ticket đóng")
            open_tickets.pop(interaction.user.id, None)
        except Exception as e:
            await channel.send(f"❌ Lỗi khi đóng ticket: {e}")


# Command tạo panel
@bot.command()
async def ticket(ctx):
    embed = discord.Embed(
        title="📩 Hệ thống hỗ trợ",
        description=
        "Bấm nút bên dưới để tạo một ticket riêng tư với đội ngũ hỗ trợ.",
        color=discord.Color.green())

    embed.set_footer(
        text=f"{ctx.guild.name}",
        icon_url=ctx.guild.icon.url if ctx.guild.icon else discord.Embed.Empty)

    view = TicketPanelView(ctx.author.id)
    await ctx.send(embed=embed, view=view)


keep_alive()

# Khởi chạy bot
bot.run(TOKEN)
