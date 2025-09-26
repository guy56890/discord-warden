# This example requires the 'message_content' intent.

import os
import discord
from discord.ext import commands


TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="$", intents=intents)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

# Classic text command (still works)
@bot.command()
async def hello(ctx):
    if ctx.author.id != 554691397601591306:
        return
    await ctx.send("Hello!")

# Slash command (requires discord.py 2.0+ or py-cord)
@bot.tree.command(name="funny", description="Do something funny!")
async def funny(interaction: discord.Interaction):
    await interaction.response.send_message("Why did the Python programmer wear glasses? Because they couldn't C#.")



bot.run(TOKEN)
