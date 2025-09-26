import os
import random
import asyncio
import discord
from discord import app_commands
from discord.ext import commands
from datetime import timedelta

TOKEN = os.getenv("DISCORD_TOKEN")

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

@bot.tree.command(name="coinflip", description="Flip a coin for admin or timeout")
async def coinflip(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    member = interaction.user
    guild = interaction.guild
    admin_role = guild.get_role(ADMIN_ROLE_ID)

    if not admin_role:
        await interaction.followup.send("Admin role not found. Configure ADMIN_ROLE_ID.")
        return

    result = random.choice(["heads", "tails"])

    if result == "heads":
        try:
            await member.add_roles(admin_role)
            await interaction.followup.send("🪙 Heads! You get admin for 30 seconds.")
            await asyncio.sleep(30)
            await member.remove_roles(admin_role)
        except Exception as e:
            await interaction.followup.send(f"Error: {e}")
    else:
        try:
            await member.timeout(discord.utils.utcnow() + timedelta(hours=2))
            await interaction.followup.send("🪙 Tails! You're timed out for 2 hours.")
        except Exception as e:
            await interaction.followup.send(f"Error: {e}")

bot.run(TOKEN)
