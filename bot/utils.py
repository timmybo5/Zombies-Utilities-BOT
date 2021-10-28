"""
Utils
"""

import re
import discord
from discord import Colour

embed_red = discord.Embed(title="Red", colour=0xFF0000)

def is_staff(ctx, member: discord.Member):
  staff_role = discord.utils.get(ctx.guild.roles, name="Staff")
  return staff_role in member.roles

def is_administrator(member: discord.Member):
  return member.guild_permissions.administrator

def is_booster(guild: discord.Guild, member: discord.Member):

  #Check if a booster role exists on the server
  if guild.premium_subscriber_role == None:
    return False

  return guild.premium_subscriber_role in member.roles

def can_target(originator: discord.Member, target: discord.Member):
  originator_top_role = originator.top_role
  target_top_role = target.top_role

  return originator_top_role >= target_top_role and not target.guild_permissions.administrator and not originator == target

async def print_no_perm_str(ctx, target: discord.Member, cmd):

  if ctx.message.author == target:
    msg = "{0.mention} you cannot {1} yourself!".format(ctx.message.author, cmd)
    await send_failed_msg(ctx.channel, msg)
    return

  msg = "{0.mention} you have no permission to {2} {1.mention}!".format(ctx.message.author, target, cmd)
  await send_failed_msg(ctx.channel, msg)

def get_minutes_from_time_str(time_str):

  multiplicator = 0

  if time_str[-1] == "m":
    multiplicator = 1
  elif time_str[-1] == "h":
    multiplicator = 60
  elif time_str[-1] == "d":
    multiplicator = 1440
  elif time_str[-1] == "w":
    multiplicator = 10080

  length = 0

  try:
      length = int(time_str[0:-1])
  except ValueError:
      return False

  minutes = multiplicator * length

  return minutes

def format_time_str(time_str):

  time_type = ""

  if time_str[-1] == "m":
    time_type = "minute"
  elif time_str[-1] == "h":
    time_type = "hour"
  elif time_str[-1] == "d":
    time_type = "day"
  elif time_str[-1] == "w":
    time_type = "week"

  length = 0

  try:
      length = int(time_str[0:-1])
  except ValueError:
      return False

  if length > 1:
    time_type+='s'

  return str(length)+" "+time_type

async def send_embed_msg(channel: discord.abc.GuildChannel, msg: str, col: discord.Color):
  embed = discord.Embed(description=msg, colour=col)
  return await channel.send(embed=embed)

async def send_failed_msg(channel: discord.abc.GuildChannel, msg: str):
  return await send_embed_msg(channel, msg, Colour.red())

async def send_success_msg(channel: discord.abc.GuildChannel, msg: str):
  return await send_embed_msg(channel, msg, Colour.green())

# https://developer.valvesoftware.com/wiki/SteamID
def steamid_to_64bit(steamid):
    steamid64 = 76561197960265728 # Base
    id_split = steamid.split(":")
    steamid64 += int(id_split[2]) * 2

    if id_split[1] == "1":
        steamid64 += 1

    return steamid64

def url_to_steamid(url):
    community_id = int(url.split("/")[-1])
    base_id = 76561197960265728
    part_id = community_id % 2 # https://developer.valvesoftware.com/wiki/SteamID#Steam_Community_ID_as_a_Steam_ID

    # Place the account number behind the equals sign and bring the community ID in front to get a reverse equation.
    # W = Z*2 + V + Y --> Z*2 = V + Y - W
    steamid = "STEAM_0:{}:{}".format(part_id,
        int(
            abs((base_id + part_id - community_id) / 2)
        )
    )
    
    return steamid

def is_steamid(steamid):
  return re.search("^STEAM_[0-5]:[01]:\d+$", steamid)
