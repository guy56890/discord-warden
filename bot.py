import os
import discord
from discord import app_commands
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="$", intents=intents)

AUTHORIZED_ID = 554691397601591306  # only this user can manage emojis
user_emojis = {}  # user_id: emoji
fish_emojis = {"🐟", "🐠", "🐡", "🦈", "🐬"}
fish_toggle = False


@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands.")
    except Exception as e:
        print(f"Sync error: {e}")

    await bot.change_presence(status=discord.Status.offline)
    print(f"Logged in as {bot.user}")


@bot.tree.command(name="coinflip", description="Flip a coin for admin or timeout")
async def coinflip(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    await interaction.followup.send(f"Flipping a coin for {interaction.user.mention}...")


@bot.tree.command(name="emoji", description="Add or remove a user's emoji reaction")
@app_commands.describe(user="The user to modify", emoji="The emoji to assign (leave blank to remove)")
async def emoji_cmd(interaction: discord.Interaction, user: discord.User, emoji: str = None):
    if interaction.user.id != AUTHORIZED_ID:
        await interaction.response.send_message("You’re not authorized to use this command.", ephemeral=True)
        return

    if emoji is None:
        if user.id in user_emojis:
            del user_emojis[user.id]
            await interaction.response.send_message(f"Removed emoji for {user.mention}.", ephemeral=True)
        else:
            await interaction.response.send_message(f"No emoji set for {user.mention}.", ephemeral=True)
    else:
        user_emojis[user.id] = emoji
        await interaction.response.send_message(f"Set emoji {emoji} for {user.mention}.", ephemeral=True)

@bot.tree.command(name="toggle_fish", description="Start or stop the fish bombardement of Asbjørn")
async def emoji_cmd(interaction: discord.Interaction):
    global fish_toggle
    if interaction.user.id != AUTHORIZED_ID:
        await interaction.response.send_message("You’re not authorized to use this command.", ephemeral=True)
        return

    if fish_toggle != True:
        fish_toggle = True
        await interaction.response.send_message(f"Started the fish bombardement of Asbjørn!")

    else:
        fish_toggle = False
        await interaction.response.send_message(f"Stopped the fish bombardement of Asbjørn!")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.author.id == 426986093355859968 and fish_toggle:
        for fish_emoji in fish_emojis:
            try:
                await message.add_reaction(fish_emoji)
            except discord.HTTPException:
                continue

    emoji = user_emojis.get(message.author.id)
    if emoji:
        try:
            await message.add_reaction(emoji)
        except discord.HTTPException:
            pass

    await bot.process_commands(message)


bot.run(TOKEN)
