"""
Simple command system using command annotations
Ref:
  - https://discordpy.readthedocs.io/en/latest/ext/commands/commands.html
  - https://github.com/AnIdiotsGuide/discordjs-bot-guide/blob/master/understanding/roles.md
"""

import discord
import os
import roles
import utils
import pterodactyl
import datetime
import asyncio
from discord.ext import commands, tasks
from replit import db
from keep_alive import keep_alive
 
bot = commands.Bot(command_prefix='!')
bot.remove_command("help")

@bot.event
async def on_ready():
  print("Bot registered as {0.user}".format(bot))
  think.start()

#Think: Automatic unjail
@tasks.loop(seconds=30.0)
async def think():

  time_now = datetime.datetime.now()

  for key in db.keys():
    if key.startswith("unjailtime_"):
      time_unjail = db[key]
      if time_unjail < time_now.timestamp():
        
        key_parts = key.split('_')
        guild_id = key_parts[1]
        member_id = key_parts[2]

        guild = await bot.fetch_guild(guild_id)
        member = None

        try:
          member = await guild.fetch_member(member_id)
        except:
          #Member left the guild
          del db[key]
          return

        #Restore roles
        await roles.restore_roles_no_ctx(member, guild)

        #Remove unjail time
        del db[key]

        channels = await guild.fetch_channels()

        #Send msg in all general chats
        for channel in channels:
          if channel.name.lower() == "general":
            await channel.send("{0.mention} has been released from prison!".format(member))


#Jail
@bot.command()
async def jail(ctx, target: discord.Member, time_str):

    #Staff check
    if not utils.is_staff(ctx, ctx.message.author):
      await ctx.send("{0.mention} the jail command is staff only!".format(ctx.message.author))
      return

    #Permission check
    if not utils.can_target(ctx.message.author, target):
      await utils.print_no_perm_str(ctx, target, "jail")
      return

    #Set jail role on target
    jail_role = discord.utils.get(ctx.guild.roles, name="Jailed")
    await roles.set_roles(target, [jail_role])

    #Unjail time
    jail_length = utils.get_minutes_from_time_str(time_str)

    if not jail_length or jail_length < 1:
      await ctx.send("{0.mention} invalid jail time!".format(ctx.message.author))
      return

    if jail_length > 10080:
      jail_length = 10080
      time_str = "7d"

    time_now = datetime.datetime.now()
    time_unjail = time_now + datetime.timedelta(minutes = jail_length)
   
    #Unfortunately replit db doesn't support 2d dicts (db["unjail"][str(target.id)])
    db["unjailtime_"+str(ctx.guild.id)+"_"+str(target.id)] = time_unjail.timestamp()

    #Notification
    length = utils.format_time_str(time_str)
    msg = "{0.mention} jailed {1.mention} for {2}!".format(ctx.message.author, target, length)
    await ctx.send(msg)

@jail.error
async def jail_error(ctx, error):
  await ctx.send("!jail requires 2 arguments: @user and time")
  return

#Unjail
@bot.command()
async def unjail(ctx, target: discord.Member):

    #Staff check
    if not utils.is_staff(ctx, ctx.message.author):
      await ctx.send("{0.mention} the unjail command is staff only!".format(ctx.message.author))
      return

    #Jailed check
    jail_role = discord.utils.get(ctx.guild.roles, name="Jailed")
    if not jail_role in target.roles:
      await ctx.send("{0.mention} {1.name} is not jailed!".format(ctx.message.author, target))
      return

    #Permission check
    if not utils.can_target(ctx.message.author, target):
      await utils.print_no_perm_str(ctx, target, "unjail")
      return

    #Restore roles
    await roles.restore_roles(ctx, target)

    #Remove unjail time
    key = "unjailtime_"+str(ctx.guild.id)+"_"+str(target.id)

    if key in db:
      del db[key]

    msg = "{0.mention} unjailed {1.mention}!".format(ctx.message.author, target)
    await ctx.send(msg)

@unjail.error
async def unjail_error(ctx, error):
  await ctx.send("!unjail requires a @user argument")
  return

#Restart
@bot.command()
async def restart(ctx, server_name: str):

  #Staff check
  if not utils.is_staff(ctx, ctx.message.author):
    await ctx.send("{0.mention} the restart command is staff only!".format(ctx.message.author))
    return

  success, response = pterodactyl.restart_server(server_name)

  msg = await ctx.send("{0.mention} {1}".format(ctx.message.author, response))
  if success:
    await msg.edit(content=msg.content+"\n> 1. Starting server container")
    await asyncio.sleep(1)
    await msg.edit(content=msg.content+"\n> 2. Loading Steam API...OK.")
    await asyncio.sleep(1)
    await msg.edit(content=msg.content+"\n> 3. Connecting anonymously to Steam Public...Logged in OK.")
    await asyncio.sleep(8)
    await msg.edit(content=msg.content+"\n> 4. Adding addons to filesystem.")
    await asyncio.sleep(6)
    await msg.edit(content=msg.content+"\n> 5. Initializing files.")
    await asyncio.sleep(14)
    await msg.edit(content=msg.content+"\n> 6. Server restarted!")

@restart.error
async def restart_error(ctx, error):
  await ctx.send("!restart requires a server_name argument")
  return

#Generic error handling
@bot.event
async def on_command_error(ctx, error):
  return

#Keep alive
keep_alive()

#Start bot
bot.run(os.getenv("DISCORD_TOKEN"))