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
from discord import Colour
from replit import db
from keep_alive import keep_alive
 
bot = commands.Bot(command_prefix='!')
bot.remove_command("help")
pterodactyl_maintenance = False

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
            msg = "{0.mention} has been released from prison!".format(member)
            await utils.send_success_msg(channel, msg)


#Jail
@bot.command()
async def jail(ctx, target: discord.Member, time_str):

    #Staff check
    if not utils.is_staff(ctx, ctx.message.author):
      msg = "{0.mention} the jail command is staff only!".format(ctx.message.author)
      await utils.send_failed_msg(ctx.channel, msg)
      return

    #Permission check
    if not utils.can_target(ctx.message.author, target):
      await utils.print_no_perm_str(ctx, target, "jail")
      return

    #Set jail role on target if not jailed yet
    jail_role = discord.utils.get(ctx.guild.roles, name="Jailed")
    if not jail_role in target.roles:
      await roles.set_roles(target, [jail_role])

    #Unjail time
    jail_length = utils.get_minutes_from_time_str(time_str)

    if not jail_length or jail_length < 1:
      msg = "{0.mention} invalid jail time!".format(ctx.message.author)
      await utils.send_failed_msg(ctx.channel, msg)
      return

    if jail_length > 10080:
      jail_length = 10080
      time_str = "1w"

    time_now = datetime.datetime.now()
    time_unjail = time_now + datetime.timedelta(minutes = jail_length)
   
    #Unfortunately replit db doesn't support 2d dicts (db["unjail"][str(target.id)])
    db["unjailtime_"+str(ctx.guild.id)+"_"+str(target.id)] = time_unjail.timestamp()

    #Notification
    length = utils.format_time_str(time_str)
    msg = "{0.mention} jailed {1.mention} for {2}!".format(ctx.message.author, target, length)
    await utils.send_success_msg(ctx.channel, msg)

#@jail.error
async def jail_error(ctx, error):
  await utils.send_failed_msg(ctx.channel, "!jail requires 2 arguments: @user and time")
  return

#Unjail
@bot.command()
async def unjail(ctx, target: discord.Member):

    #Staff check
    if not utils.is_staff(ctx, ctx.message.author):
      msg = "{0.mention} the unjail command is staff only!".format(ctx.message.author)
      await utils.send_failed_msg(ctx.channel, msg)
      return

    #Jailed check
    jail_role = discord.utils.get(ctx.guild.roles, name="Jailed")
    if not jail_role in target.roles:
      msg = "{0.mention} {1.name} is not jailed!".format(ctx.message.author, target)
      await utils.send_failed_msg(ctx.channel, msg)
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
    await utils.send_success_msg(ctx.channel, msg)

@unjail.error
async def unjail_error(ctx, error):
  await utils.send_failed_msg(ctx.channel, "!unjail requires an @user argument")
  return

#Restart
@bot.command()
async def restart(ctx, server_name: str):

  #Pterodactyl maintenance
  if pterodactyl_maintenance:
    await utils.send_failed_msg(ctx.channel, "The server is in maintenance!")
    return

  #Staff check
  if not utils.is_staff(ctx, ctx.message.author):
    msg = "{0.mention} the restart command is staff only!".format(ctx.message.author)
    await utils.send_failed_msg(ctx.channel, msg)
    return

  success, response = pterodactyl.restart_server(server_name)
  msg = "{0.mention} {1}".format(ctx.message.author, response)

  if not success:
      await utils.send_failed_msg(ctx.channel, msg)
  else:
    restart_embed = discord.Embed(description=msg, colour=Colour.orange())
    channel_msg = await ctx.send(embed=restart_embed)
    await asyncio.sleep(1)
    restart_embed.description = restart_embed.description+"\n\n> 1: Killing server."
    await channel_msg.edit(embed=restart_embed)
    await asyncio.sleep(1)
    restart_embed.description = restart_embed.description+"\n> 2: Starting server container."
    await channel_msg.edit(embed=restart_embed)
    await asyncio.sleep(1)
    restart_embed.description = restart_embed.description+"\n> 3: Loading Steam API...OK."
    await channel_msg.edit(embed=restart_embed)
    await asyncio.sleep(1)
    restart_embed.description = restart_embed.description+"\n> 4: Connecting anonymously to Steam Public...Logged in OK."
    await channel_msg.edit(embed=restart_embed)
    await asyncio.sleep(8)
    restart_embed.description = restart_embed.description+"\n> 5: Adding addons to filesystem."
    await channel_msg.edit(embed=restart_embed)
    await asyncio.sleep(6)
    restart_embed.description = restart_embed.description+"\n> 6: Initializing files."
    await channel_msg.edit(embed=restart_embed)
    await asyncio.sleep(13)
    restart_embed.color = Colour.green()
    restart_embed.description = restart_embed.description+"\n> 7: Server restarted!"
    await channel_msg.edit(embed=restart_embed)

@restart.error
async def restart_error(ctx, error):
  if isinstance(error, commands.MissingRequiredArgument):
    await utils.send_failed_msg(ctx.channel, "!restart requires a server_name argument.")
  else:
    await utils.send_failed_msg(ctx.channel, "Connection to server failed!")
  return

#Generic error handling
@bot.event
async def on_command_error(ctx, error):
  return

#Keep alive
keep_alive()

#Start bot
bot.run(os.getenv("DISCORD_TOKEN"))