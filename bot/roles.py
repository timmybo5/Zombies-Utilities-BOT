"""
Discord role helper class
Ref: https://discordpy.readthedocs.io/en/v1.2.2/api.html#role
"""
import discord
import utils
import pickledb
from typing import List

db = pickledb.load('jail_data.db', True)

async def remove_all_roles(guild: discord.Guild, member: discord.Member):
  if utils.is_booster(guild, member):
    await member.edit(roles=[guild.premium_subscriber_role])
  else:
    #Will error when trying to remove a booster role
    await member.edit(roles=[])

async def set_roles(guild: discord.Guild, member: discord.Member, roles: List[discord.Role]):

  #Get old roles and save
  old_roles = get_roles(member)
  old_role_ids = []

  #If the old roles are the same as the new roles do nothing
  if old_roles == roles:
    return

  for role in old_roles:
    old_role_ids.append(role.id)

  key = "prev_roles_"+str(member.id)
  db.set(key, old_role_ids)

  #Remove old roles
  await remove_all_roles(guild, member)

  #Assign new role
  await member.add_roles(*roles)


async def restore_roles(guild: discord.Guild, member: discord.Member):
  roles = get_previous_roles(guild, member)
  await set_roles(guild, member, roles)

def get_roles(member: discord.Member):
  return member.roles

def get_previous_roles(guild: discord.Guild, member: discord.Member):
  key = "prev_roles_"+str(member.id)
  roles = []

  if db.exists(key):
    role_ids = db.get(key)

    for role_id in role_ids:

      # @everyone & Booster roles are not assignable (will throw an error)
      if (role_id == guild.default_role.id or role_id == guild.premium_subscriber_role.id):
        continue

      roles.append(discord.utils.get(guild.roles, id=role_id))

  return roles