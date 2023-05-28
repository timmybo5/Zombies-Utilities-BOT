"""
Invite stuff
Ref:
  - https://stackoverflow.com/questions/66662756/is-it-possible-to-split-a-discord-py-bot-across-multiple-files
  - https://medium.com/@tonite/finding-the-invite-code-a-user-used-to-join-your-discord-server-using-discord-py-5e3734b8f21f
"""

import utils
import asyncio
import discord
import re
from discord.ext import commands

bot_ref = None
invite_cache = {}

def setup(bot):
  return True

async def on_ready(bot):
    global bot_ref
    bot_ref = bot

    #Getting all the guilds our bot is in
    for guild in bot.guilds:
        # Adding each guild's invites to our dict
        invite_cache[guild.id] = await guild.invites()

async def on_member_remove(member):
    #Update cache
    invite_cache[member.guild.id] = await member.guild.invites()

#Delete any invite which does not expire after 30 minutes
async def on_invite_create(invite):
    if invite.max_age > 1800:
        await invite.delete(reason='Automatic deletion, invite expiration was set to >30 minutes.')

#Should be called from within on_member_join
async def fetch_inviter(member):

  #Getting the invites before the user joining
  invites_before_join = invite_cache[member.guild.id]

  # Getting the invites after the user joining
  invites_after_join = await member.guild.invites()

  #Loops for each invite we have for that guild
  for invite in invites_before_join:

    targ_invite = find_invite_by_code(invites_after_join, invite.code)

    if not targ_invite:
      continue

    #Check if code was used by comparing invite usages
    if invite.uses < targ_invite.uses:
      
      #Update cache
      invite_cache[member.guild.id] = invites_after_join
      
      return invite.inviter, invite.code
  
  #If the invite cache isn't updated yet look for any new invite that was created
  for invite in invites_after_join:
    if invite not in invites_before_join and invite.uses > 0:

      #Update cache
      invite_cache[member.guild.id] = invites_after_join

      return invite.inviter, invite.code

#Find invite from invite code
def find_invite_by_code(invite_list, code):

  for inv in invite_list:
    if inv.code == code:
      return inv

#Wait for another thread's task ( 10 seconds max )
async def wait_for_invite_task(invite_task, try_num):
  try:
    #Throws an error when task is not finished yet
    return invite_task.result()
  except:
    if try_num >= 20:
      return
    await asyncio.sleep(0.5)
    return await wait_for_invite_task(invite_task, try_num+1)

#Create an invite and return the invite code
async def create_invite(inviter_name, inviter_steamid, guild_id, channel_id):

  if not bot_ref:
    return "Bot is not initialised!", 400
  
  #bot_ref.guilds -> does not need any fetches + populated on_ready
  guild = discord.utils.get(bot_ref.guilds, id=int(guild_id))

  if not guild:
    return "There was a problem retrieving the guild!", 400

  #Create invite
  invite_chan = discord.utils.get(guild.channels, id=int(channel_id))
  invite = None

  if invite_chan:
    #Create invite task
    invite_reason = 'Created by {0}({1})'.format(inviter_name, inviter_steamid)
    #Unlimited uses -> if the invite gets removed then the tracker can't track it
    invite_task = bot_ref.loop.create_task(invite_chan.create_invite(max_uses=0, unique=True, max_age=300, reason=invite_reason))

    #Get task result
    invite = await wait_for_invite_task(invite_task, 1)

  if not invite or not invite.code:
    return "There was a problem creating the invite!", 400

  #Log invite creation
  log_chan = discord.utils.get(guild.channels, name="invite-logs")
  if log_chan:
      #Steamid64 for community profile link
      inviter_steamid64 = utils.steamid_to_64bit(inviter_steamid)
      #Send message (hyperlink is broken, because of create_task?)
      bot_ref.loop.create_task(log_chan.send('Invite `{0}` created by **{1}**({2}) __<https://steamcommunity.com/profiles/{3}/>__'.format(invite.code, inviter_name, inviter_steamid, inviter_steamid64)))

  return invite.url


#Find steam profile from member by searching invites
async def find_profile_for_member(member: discord.Member):

  log_chan = discord.utils.get(member.guild.channels, name="invite-logs")
  #messages = await log_chan.history(limit=None).flatten()
  #messages = await log_chan.history(limit=None).get(author__name='Test').flatten()

  messages = await log_chan.history(limit=None).flatten()
  invite_code_re = "\[`([a-zA-Z0-9]+)`\].$"
  invite_code = ""

  #find invite code for Member
  for msg in messages:
    for mention_member in msg.mentions:
      if mention_member == member:
        #find code in message
        invite_code = re.search(invite_code_re, msg.content)
        if invite_code:
          invite_code = invite_code.group(1)
          break

  if not invite_code:
    return False

  invite_steam_re = "^Invite `([a-zA-Z0-9]+)`"
  invite_steam_profile_re = "(https://.+/)>__$"
  invite_steam_profile = ""

  #find steam profile link from invite code
  for msg in messages:
    if invite_code in msg.content:
      invite_steam_msg = re.search(invite_steam_re, msg.content)
      if invite_steam_msg:
        invite_steam_profile = re.search(invite_steam_profile_re, msg.content)
        if invite_steam_profile:
          invite_steam_profile = invite_steam_profile.group(1)
          break

  if not invite_steam_profile:
    return False

  return invite_steam_profile