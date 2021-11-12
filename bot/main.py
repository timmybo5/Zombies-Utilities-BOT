"""
Simple command system using command annotations
Ref:
  - https://discordpy.readthedocs.io/en/latest/ext/commands/commands.html
  - https://github.com/AnIdiotsGuide/discordjs-bot-guide/blob/master/understanding/roles.md
"""

import os
import roles
import utils
import pterodactyl
import datetime
import asyncio
import discord
import inviting
from discord.ext import commands, tasks
from discord import Colour
from replit import db
from webserver import keep_alive

intents = discord.Intents.default()
intents.members = True
intents.presences = True
intents.messages = True

bot = commands.Bot(command_prefix='!', intents=intents)
bot.remove_command("help")
bot.load_extension("inviting")

pterodactyl_maintenance = False
purge_file_path = "purged_raid_members.txt"

@bot.event
async def on_ready():
  print("Bot registered as {0.user}".format(bot))
  think.start()
  await inviting.on_ready(bot)

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
        await roles.restore_roles(guild, member)

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
  
    #Unjail time check
    jail_length = utils.get_minutes_from_time_str(time_str)

    if not jail_length or jail_length < 1:
      msg = "{0.mention} invalid jail time!".format(ctx.message.author)
      await utils.send_failed_msg(ctx.channel, msg)
      return

    #Set jail role on target if not jailed yet
    jail_role = discord.utils.get(ctx.guild.roles, name="Jailed")
    if not jail_role in target.roles:
      await roles.set_roles(ctx.guild, target, [jail_role])

    #Unjail time
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

@jail.error
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
    await roles.restore_roles(ctx.guild, target)

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

#Bot Purge
@bot.command()
async def purgeraid(ctx, date_str):

    #Administrator check
    if not utils.is_administrator(ctx.message.author):
      msg = "{0.mention} the botpurge command is administrator only!".format(ctx.message.author)
      await utils.send_failed_msg(ctx.channel, msg)
      return

    #Date validator [dd/mm/yyyy]
    purge_start_date = False
    try:
      purge_start_date = datetime.datetime.strptime(date_str, "%d/%m/%Y")
    except:
      await utils.send_failed_msg(ctx.channel, "Given date does not match format dd/mm/yyyy!")
      return

    purge_end_date = purge_start_date + datetime.timedelta(days=1)

    #Member date check
    joined_members = []
    raid_members = []
    for member in ctx.guild.members:
      if member.joined_at > purge_start_date and member.joined_at < purge_end_date:
        joined_members.append(member)

        member_roles  = roles.get_roles(member)
        if (len(member_roles) == 1):
          raid_members.append(member)

    #Message top
    purge_embed = discord.Embed(title="Purging raid members...", description="", colour=Colour.orange())
    channel_msg = await ctx.send(embed=purge_embed)
    await asyncio.sleep(1)
    purge_embed.description = purge_embed.description+"\n\n> 1: Checking "+str(len(ctx.guild.members))+" members."
    await channel_msg.edit(embed=purge_embed)
    await asyncio.sleep(1)
    purge_embed.description = purge_embed.description+"\n> 2: Found "+str(len(joined_members))+" members that joined on "+date_str+"!"
    await channel_msg.edit(embed=purge_embed)
    await asyncio.sleep(1)
    purge_embed.description = purge_embed.description+"\n> 3: Detected "+str(len(raid_members))+" possibe raid members!"
    await channel_msg.edit(embed=purge_embed)
    await asyncio.sleep(1)
    purge_embed.description = purge_embed.description+"\n\n Are you sure you want to purge "+str(len(raid_members))+" members? (y/n)"
    await channel_msg.edit(embed=purge_embed)

    #Wait for response
    response_msg = await bot.wait_for("message", check=lambda message: message.author == ctx.message.author, timeout=30.0)

    #Abort purge
    if response_msg.content.strip().lower() != 'y':
      purge_embed.color = Colour.red()
      purge_embed.description = purge_embed.description+"\n Purge aborted!"
      await channel_msg.edit(embed=purge_embed)
      return

    #Delete response
    await response_msg.delete()

    #Create empty purge file and wait for input
    purge_file = open(purge_file_path, "w")
    purge_file.close()
    purge_file = open(purge_file_path, "a")

    purge_embed.description = purge_embed.description+"\n\n **Purging**:"
    await channel_msg.edit(embed=purge_embed)

    #Purge raid members
    purged_count = 1
    for member in raid_members:

      #Content length restrictions -> split into blocks of 50 names
      if purged_count%50 == 0:
        purge_embed.color = Colour.green()
        await channel_msg.edit(embed=purge_embed)
        purge_embed = discord.Embed(description="**Purging**:", colour=Colour.orange())
        channel_msg = await ctx.send(embed=purge_embed)

      purge_file.write(str(purged_count)+". "+member.name+" - "+str(member.id)+"\n")
      purge_embed.description = purge_embed.description+"\n> "+str(purged_count)+". "+member.name
      await channel_msg.edit(embed=purge_embed)
      await member.kick(reason="Kicked due to suspected server raid activity!")
      purged_count += 1
    
    #Mark last embed as done
    purge_embed.color = Colour.green()
    await channel_msg.edit(embed=purge_embed)

    #Close and upload file
    purge_file.close()
    purge_file = open(purge_file_path, "r")
    await ctx.send(file=discord.File(purge_file))
    purge_file.close()

    msg = "{0.mention} purged {1} potential raid members that joined on {2}!".format(ctx.message.author, purged_count-1, date_str)
    await utils.send_success_msg(ctx.channel, msg)
  
@purgeraid.error
async def purgeraid_error(ctx, error):
  await utils.send_failed_msg(ctx.channel, "!purgeraid requires a date [dd/mm/yyyy] argument")
  return

#Say your message as the bot
@bot.command()
async def say(ctx, *, message):

    #Administrator check
    if not utils.is_administrator(ctx.message.author):
      msg = "{0.mention} the say command is administrator only!".format(ctx.message.author)
      await utils.send_failed_msg(ctx.channel, msg)
      return

    #Delete command message
    await ctx.message.delete()

    #Send message in channel
    await ctx.channel.send(message)

#Get Steam profile link from steamid or member
@bot.command()
async def profile(ctx, steamid: str):

  if '@' in steamid:
    member_id = int(steamid.strip('<@!>'))
    member = ctx.guild.get_member(member_id)
    
    # Notify user we are searching
    profile_embed = discord.Embed(description="{0.mention} Searching profile...".format(ctx.message.author), colour=Colour.orange())
    profile_msg = await ctx.send(embed=profile_embed)

    # Get link from Member
    profile_link = await inviting.find_profile_for_member(member)

    if profile_link:
      profile_embed.description = "{0.mention} the profile for **{1}** is __<{2}>__".format(ctx.message.author, member.name, profile_link)
      profile_embed.color = Colour.green()
    else:
      profile_embed.description = "{0.mention} the profile for **{1}** could not be retrieved!".format(ctx.message.author, member.name)
      profile_embed.color = Colour.red()

    await profile_msg.edit(embed=profile_embed)
    return
  
  #Check if steamid has correct format
  if not utils.is_steamid(steamid):
    msg = "{0.mention} {1} is not a valid SteamID!".format(ctx.message.author, steamid.replace('@',''))
    await utils.send_failed_msg(ctx.channel, msg)
    return

  #Steamid64 for community profile link
  inviter_steamid64 = utils.steamid_to_64bit(steamid)

  msg = "{0.mention} the profile for **{1}** is __<https://steamcommunity.com/profiles/{2}/>__".format(ctx.message.author, steamid, inviter_steamid64)
  await utils.send_success_msg(ctx.channel, msg)

@profile.error
async def profile_error(ctx, error):
  await utils.send_failed_msg(ctx.channel, "!profile requires a SteamID [STEAM_0:0:11101] or @user argument")
  return

@bot.command
async def steamid(ctx, url: str):

    # Check if URL links to the Steam Community, is a decimal value and within the length limit
    if not utils.is_valid_url(url):
        msg = "{0.mention} __<{1}>__ is not a valid Steam community URL!".format(ctx.message.author, url)
        await utils.send_failed_msg(ctx.channel, msg)
        return

    steamid = utils.url_to_steamid(url)

    msg = "{0.mention} the SteamID for __<{1}>__ is `{2}`".format(ctx.message.author, url, steamid)
    await utils.send_success_msg(ctx.channel, msg)

@steamid.error
async def steamid_error(ctx, error):
  await utils.send_failed_msg(ctx.channel, "!steamid requires a Steam Community URL argument")
  return

#Invite logger
@bot.event
async def on_member_join(member):

    #Get inviter
    inviter, invite_code = await inviting.fetch_inviter(member)

    #Get logging channel
    log_chan = discord.utils.get(member.guild.channels, name="invite-logs")
    if log_chan:
      if (not inviter or not invite_code):
        await log_chan.send('**{0.name}**({0.mention}) was invited by ERROR'.format(member))
      else:
        await log_chan.send('**{0.name}**({0.mention}) was invited by **{1.name}**({1.mention}) [`{2}`].'.format(member, inviter, invite_code))

@bot.event
async def on_member_remove(member):
  await inviting.on_member_remove(member)

#Generic error handling
@bot.event
async def on_command_error(ctx, error):
  return

#Keep alive
keep_alive()

#Start bot
bot.run(os.getenv("DISCORD_TOKEN"))