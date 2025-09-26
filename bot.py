import os
import random
import aiohttp
import asyncio
import discord
from discord import app_commands
from discord.ext import commands
from datetime import timedelta

TOKEN = os.getenv("DISCORD_TOKEN")
WEBHOOK_URL = os.getenv("PORTAINER_WEBHOOK")

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="$", intents=intents)

# Replace with your actual role ID
ADMIN_ROLE_ID = 1421070076139798559  

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands.")
    except Exception as e:
        print(e)
    bot.change_presence(status=discord.Status.offline)
    print(f"Logged in as {bot.user}")

@bot.tree.command(name="redeploy")
async def redeploy(interaction: discord.Interaction):
    await interaction.response.defer()  # “Jeg svarer snart”
    async with aiohttp.ClientSession() as session:
        async with session.post(WEBHOOK_URL) as resp:
            print(resp)
            await interaction.followup.send("Portainer webhook succes ✅")

@bot.tree.command(name="coinflip", description="Flip a coin for admin or timeout")
async def coinflip(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    member = interaction.user
    guild = interaction.guild
    admin_role = guild.get_role(ADMIN_ROLE_ID)

    if not admin_role:
        await interaction.followup.send("Admin role not found. Configure ADMIN_ROLE_ID.")
        return
    
    await interaction.followup.send(f"Flipping a coin for {member.mention}...")
bot.run(TOKEN)
