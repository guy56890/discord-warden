import os
import json
import discord
from discord import app_commands
from discord.ext import commands, tasks

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.presences = True  # MUST for status tracking
intents.message_content = True

bot = commands.Bot(command_prefix="$", intents=intents)

AUTHORIZED_ID = 554691397601591306  # only this user can manage emojis & shadows
user_emojis = {}  # user_id: emoji
fish_emojis = {"🐟", "🐠", "🐡", "🦈", "🐬", "🦑", "🦐", "🦞", "🦀", "🐙", "🐋", "🐳", "🪼", "🪸", "🐚", "🐌", "🦭"}
fish_toggle = False
shadowed_users = {}  # user_id -> last known status

DATA_FILE = "data.json"

# --- Data persistence ---
def load_data():
    global user_emojis, fish_toggle, shadowed_users
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            user_emojis = {int(k): v for k, v in data.get("user_emojis", {}).items()}
            fish_toggle = data.get("fish_toggle", False)
            shadowed_users_raw = data.get("shadowed_users", {})
            shadowed_users = {int(k): discord.Status[s] for k, s in shadowed_users_raw.items()}
    except FileNotFoundError:
        user_emojis = {}
        fish_toggle = False
        shadowed_users = {}

def save_data():
    data = {
        "user_emojis": {str(k): v for k, v in user_emojis.items()},
        "fish_toggle": fish_toggle,
        "shadowed_users": {str(k): str(v) for k, v in shadowed_users.items()}
    }
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- Bot events ---
@bot.event
async def on_ready():
    load_data()
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands.")
    except Exception as e:
        print(f"Sync error: {e}")

    await bot.change_presence(status=discord.Status.offline)
    print(f"Logged in as {bot.user}")
    channel = bot.get_channel(1435613283141947392)
    if channel:
        await channel.send("The Warden has been restarted.")

    periodic_task.start()  # start shadow loop

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

# --- Slash commands ---
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
            save_data()
            await interaction.response.send_message(f"Removed emoji for {user.mention}.", ephemeral=True)
        else:
            await interaction.response.send_message(f"No emoji set for {user.mention}.", ephemeral=True)
    else:
        user_emojis[user.id] = emoji
        save_data()
        await interaction.response.send_message(f"Set emoji {emoji} for {user.mention}.", ephemeral=True)

@bot.tree.command(name="toggle_fish", description="Start or stop the fish bombardement of Asbjørn")
async def toggle_fish(interaction: discord.Interaction):
    global fish_toggle
    if interaction.user.id != AUTHORIZED_ID:
        await interaction.response.send_message("You’re not authorized to use this command.", ephemeral=True)
        return

    fish_toggle = not fish_toggle
    save_data()
    state = "started" if fish_toggle else "stopped"
    await interaction.response.send_message(f"{state.capitalize()} the fish bombardement of Asbjørn!", ephemeral=True)

@bot.tree.command(
    name="shadow",
    description="Add a user to the shadow list",
)
@app_commands.describe(user="The user to shadow")
async def shadow(interaction: discord.Interaction, user: discord.Member):
    if interaction.user.id != AUTHORIZED_ID:
        await interaction.response.send_message("You are not allowed to use this.", ephemeral=True)
        return

    shadowed_users[user.id] = user.status
    save_data()
    await interaction.response.send_message(f"Now shadowing {user.name}", ephemeral=True)

# --- Shadow loop ---
@tasks.loop(minutes=1)
async def periodic_task():
    channel = bot.get_channel(1435613283141947392)
    if not channel:
        return

    for user_id, last_status in shadowed_users.items():
        user = channel.guild.get_member(user_id)
        if not user:
            continue

        if user.status != last_status:
            await channel.send(f"**Shadow Update for {user.name}:** Status changed {last_status} -> {user.status}")
            shadowed_users[user_id] = user.status
            save_data()

# --- Run bot ---
bot.run(TOKEN)
