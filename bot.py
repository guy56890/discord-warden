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
    print(f"Logged in as {bot.user}")

@bot.tree.command(name="re-deploy", description="Forcefully update the bot to the newest commit on GitHub")
async def redeploy(interaction: discord.Interaction):

    if interaction.user.id != 554691397601591306:  # Replace with your Discord user ID
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    await interaction.response.send_message("Triggerer deploy… 🚀")
    async with aiohttp.ClientSession() as session:
        async with session.post(WEBHOOK_URL) as resp:
            if resp.status == 200:
                await interaction.response.send_message("Portainer webhook succes — opdatering startet.")
            else:
                text = await resp.text()
                await interaction.response.send_message(f"Fejl: {resp.status} — {text}")

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

@bot.tree.command(name="test", description="this is a new test command")
async def coinflip(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    member = interaction.user
    guild = interaction.guild
    admin_role = guild.get_role(ADMIN_ROLE_ID)

    
    await interaction.followup.send(f"doo be doo")
bot.run(TOKEN)
