import os
import discord
from discord import app_commands
from discord.ext import commands, tasks

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="$", intents=intents)

AUTHORIZED_ID = 554691397601591306  # only this user can manage emojis
user_emojis = {}  # user_id: emoji
fish_emojis = {"🐟", "🐠", "🐡", "🦈", "🐬",  "🐟",  # fish
    "🦑",  # squid
    "🦐",  # shrimp
    "🦞",  # lobster
    "🦀",  # crab
    "🐙",  # octopus
    "🐋",  # whale
    "🐳",  # spouting whale
    "🪼",  # jellyfish
    "🪸",  # coral
    "🐚",  # spiral shell
    "🐌",  # snail (sometimes aquatic)
    "🦭",  # seal (marine)}
}
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
    await bot.get_channel(1435613283141947392).send("The Warden has been restarted.")

    periodic_task.start()  # start the shadow loop


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

shadowed_users = {}  # user_id -> last known status/activities
AUTHORIZED_SHADOW_ID = 554691397601591306  # same as before, only you can use the shadow command

@bot.tree.command(
    name="shadow",
    description="Add a user to the shadow list",
)
@app_commands.describe(user="The user to shadow")
async def shadow(interaction: discord.Interaction, user: discord.Member):
    if interaction.user.id != AUTHORIZED_SHADOW_ID:
        await interaction.response.send_message("You are not allowed to use this.", ephemeral=True)
        return

    shadowed_users[user.id] = {
        "status": user.status,
        "activities": user.activities
    }
    await interaction.response.send_message(f"Now shadowing {user.name}", ephemeral=True)


@tasks.loop(minutes=5)
async def periodic_task():
    channel = bot.get_channel(1435613283141947392)
    if not channel:
        return

    for user_id, last in shadowed_users.items():
        user = channel.guild.get_member(user_id)
        if not user:
            continue

        messages = []

        # Check status change
        if user.status != last["status"]:
            messages.append(f"Status changed: {last['status']} -> {user.status}")
            last["status"] = user.status

        # Check activity change
        if user.activities != last["activities"]:
            act_old = ', '.join([a.name for a in last["activities"]]) if last["activities"] else "None"
            act_new = ', '.join([a.name for a in user.activities]) if user.activities else "None"
            messages.append(f"Activities changed: {act_old} -> {act_new}")
            last["activities"] = user.activities

        if messages:
            await channel.send(f"**Shadow Update for {user.name}:**\n" + "\n".join(messages))

# --- END OF SHADOWING CODE ---

bot.run(TOKEN)
