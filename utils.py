"""
Utils
"""
import discord

def is_staff(ctx, member: discord.Member):
  staff_role = discord.utils.get(ctx.guild.roles, name="Staff")
  return staff_role in member.roles

def can_target(originator: discord.Member, target: discord.Member):
  originator_top_role = originator.top_role
  target_top_role = target.top_role

  return originator_top_role >= target_top_role and not target.guild_permissions.administrator and not originator == target

async def print_no_perm_str(ctx, target: discord.Member, cmd):

  if ctx.message.author == target:
    await ctx.send("{0.mention} you cannot {1} yourself!".format(ctx.message.author, cmd))
    return

  await ctx.send("{0.mention} you have no permission to {2} {1.mention}!".format(ctx.message.author, target, cmd))

def get_minutes_from_time_str(time_str):

  multiplicator = 0

  if time_str[-1] == "m":
    multiplicator = 1
  elif time_str[-1] == "h":
    multiplicator = 60
  elif time_str[-1] == "d":
    multiplicator = 1440

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

  length = 0

  try:
      length = int(time_str[0:-1])
  except ValueError:
      return False

  if length > 1:
    time_type+='s'

  return str(length)+" "+time_type