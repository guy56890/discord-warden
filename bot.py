# This example requires the 'message_content' intent.

import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    if message.author.id != 554691397601591306:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

client.run('MTQyMTA0MDI5OTQ1MDU2ODc1NA.GTz_No.b_FLndK5QtSiDJlzozEOIzUQvcN5kwi2tnzj0g')
