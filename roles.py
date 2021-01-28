"""
Discord role helper class
Ref: https://discordpy.readthedocs.io/en/v1.2.2/api.html#role
"""
import discord
from replit import db
from typing import List

async def set_roles(member: discord.Member, roles: List[discord.Role]):

  #Get old roles and save
  old_roles = get_roles(member)
  old_role_ids = []

  #If the old roles are the same as the new roles do nothing
  if old_roles == roles:
    return

  for role in old_roles:
    old_role_ids.append(role.id)

  key = "prev_roles_"+str(member.id)
  db[key] = old_role_ids

  #Remove old roles
  await member.edit(roles=[])

  #Assign new role
  await member.add_roles(*roles)


async def restore_roles(ctx, member: discord.Member):
  roles = get_previous_roles(ctx, member)
  await set_roles(member, roles)

def get_roles(member: discord.Member):
  return member.roles

def get_previous_roles(ctx, member: discord.Member):
  key = "prev_roles_"+str(member.id)
  roles = []

  if key in db:
    role_ids = db[key]

    for role_id in role_ids:

      # @everyone is not assignable (will throw an error)
      if role_id == ctx.guild.default_role.id:
        continue

      roles.append(discord.utils.get(ctx.guild.roles, id=role_id))

  return roles

async def restore_roles_no_ctx(member: discord.Member, guild: discord.Guild):
  key = "prev_roles_"+str(member.id)
  roles = []

  if key in db:
    role_ids = db[key]

    for role_id in role_ids:

      # @everyone is not assignable (will throw an error)
      if role_id == guild.default_role.id:
        continue

      roles.append(discord.utils.get(guild.roles, id=role_id))

  #Remove old roles
  await member.edit(roles=[])

  #Restore old roles
  await member.add_roles(*roles)