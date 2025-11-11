import os
import json
import discord
import random
import asyncio
import time
from discord import app_commands
from discord.ext import commands, tasks
from mcstatus import JavaServer

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.presences = True  # MUST for status tracking
intents.message_content = True

bot = commands.Bot(command_prefix="$", intents=intents)

AUTHORIZED_ID = 554691397601591306  # only this user can manage emojis & shadows
SERVER_MANAGER_ROLE_ID = 1303704931198435328  # replace with your actual role ID
GUILD_ID = 1290601628142927924  # replace with your guild/server ID


user_emojis = {}  # user_id: emoji
fish_emojis = {"🐟", "🐠", "🐡", "🦈", "🐬", "🦑", "🦐", "🦞", "🦀", "🐙", "🐋", "🐳", "🪼", "🪸", "🐚", "🐌", "🦭"}
fish_toggle = False
shadowed_users = {}  # user_id -> last known status

# --- Data persistence ---
DATA_FILE = "/discord-bot/data/data.json"

def load_data():
    global user_emojis, fish_toggle, shadowed_users
    # Make sure the directory exists
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)

    # Create the file if it doesn't exist
    if not os.path.isfile(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump({"user_emojis": {}, "fish_toggle": False, "shadowed_users": {}}, f, indent=4)

    # Load the data
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
        user_emojis = {int(k): v for k, v in data.get("user_emojis", {}).items()}
        fish_toggle = data.get("fish_toggle", False)
        shadowed_users_raw = data.get("shadowed_users", {})
        shadowed_users = {int(k): discord.Status[s] for k, s in shadowed_users_raw.items()}

def save_data():
    # Make sure the directory exists (in case deleted)
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
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

wasLastOffline = False

@bot.tree.command(name="server_status", description="Monitor or display info for a Minecraft server")
@app_commands.describe(ip="The IP of the Minecraft server to monitor (e.g. play.example.com)")
async def server_status(interaction: discord.Interaction, ip: str):
    if interaction.user.id != AUTHORIZED_ID:
        await interaction.response.send_message("You’re not authorized to use this command.", ephemeral=True)
        return

    await interaction.response.defer()

    SERVER_RULES = [
        "Don't grief anyone",
        "No cheats, hacks, x-rays or exploits",
        "Don't be a dickhead",
        "Don't hop on End before we all agree to do so",
    ]

    banner_image = "https://cdn.discordapp.com/banners/1421040299450568754/46fd58e5cc7729988520c67e6daa0819?size=1024"

    was_last_offline = False

    async def make_embed(online, status=None):
        nonlocal was_last_offline
        now = int(time.time())

        if status:
            # Extract readable name and version
            try:
                desc = getattr(status.description, "get", lambda k, d=None: d)("text", str(status.description))
            except Exception:
                desc = str(status.description)
            server_name = desc or "Unknown Server"
            server_version = getattr(status.version, "name", "Unknown Version")
        else:
            server_name = "Unknown Server"
            server_version = "Unknown Version"

        embed = discord.Embed(
            title=f"🎮 {server_name}",
            description=f"**Address:** `{ip}`\n**Version:** `{server_version}`\n**Type:**`Java Edition, Vanilla`",
            color=discord.Color.green() if online else discord.Color.red()
        )

        if online and status:
            if was_last_offline:
                interaction.channel.send("<@1316429425847308449>", timeout=1)
                was_last_offline = False

            embed.add_field(name="🟢 Status", value="ONLINE\n\u200b", inline=True)
            embed.add_field(name="👥 Players", value=f"`{status.players.online}` / `{status.players.max}`", inline=True)
            embed.add_field(name="📡 Ping", value=f"`{round(status.latency)} ms`", inline=True)
            embed.add_field(name="📜 Rules", value="\n".join(SERVER_RULES), inline=False)


            if status.players.sample:
                names = ", ".join(p.name for p in status.players.sample)
                embed.add_field(name="Online players:", value=f"> {names}", inline=False)
        else:
            embed.add_field(name="🔴 Status", value="OFFLINE\n\u200b", inline=False)
            embed.add_field(name="📜 Rules", value="\n".join(SERVER_RULES), inline=False)

            # Notify all ServerManager role members if the server just went offline
            if not was_last_offline:
                try:
                    guild = bot.get_guild(GUILD_ID)
                    if guild:
                        role = guild.get_role(SERVER_MANAGER_ROLE_ID)
                        if role:
                            for member in role.members:
                                try:
                                    dm = await member.create_dm()
                                    await dm.send(
                                        f"The server `{ip}` is offline.\nKindest regards, Warden. {random.choice(list(fish_emojis))}"
                                    )
                                    await asyncio.sleep(1)  # prevent rate limits
                                except Exception:
                                    continue
                    was_last_offline = True
                except Exception as e:
                    print(f"Failed to DM ServerManager members: {e}")

        embed.add_field(name="🕒 Last Update", value=f"<t:{now}:R>", inline=False)
        embed.set_footer(text="By guy56890", icon_url=bot.user.display_avatar.url)
        embed.set_image(url=banner_image)

        return embed

    # Initial fetch
    try:
        server = JavaServer.lookup(ip)
        status = server.status()
        online = True
    except Exception:
        online = False
        status = None

    embed = await make_embed(online, status)
    msg = await interaction.followup.send(embed=embed)

    async def update_status():
        while True:
            await asyncio.sleep(30)
            try:
                await msg.channel.fetch_message(msg.id)
            except discord.NotFound:
                print(f"Message for {ip} deleted — stopping update loop.")
                return

            try:
                server = JavaServer.lookup(ip)
                status = server.status()
                online = True
            except Exception:
                online = False
                status = None

            new_embed = await make_embed(online, status)
            await msg.edit(embed=new_embed)

    bot.loop.create_task(update_status())




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
