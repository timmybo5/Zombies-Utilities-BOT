"""
Simple command system using on_message event (legacy)
"""

import discord
import os

client = discord.Client()

@client.event
async def on_ready():
  print("Bot registered as {0.user}".format(client))

commands = {}

def register_command(name, func):
  commands['!'+name] = func


@client.event
async def on_message(msg):
  
  #Do not check msgs sent by this bot
  if msg.author == client.user or not msg.content.startswith('!'):
    return

  args = msg.content.split()
  cmd = args[0]

  if cmd in commands:
    await commands[cmd](msg, args)


# Commands
async def test(msg, args):
  print(args)
  await msg.channel.send("Hello!")

register_command("test", test)

# Start bot
client.run(os.getenv("TOKEN"))