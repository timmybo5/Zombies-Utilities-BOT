# Zombie's Utilities (BOT)
A python discord bot that offers useful utility commands

## Commands
- **!jail** <@player> <time [m,h,d,w]\>
  - !jail @Zombie Extinguisher 3h
- **!unjail** <@player\>
- **!restart** <server_name\> (Reboots a pterodactyl hosted server)
  - !restart sandbox
- **!purgeraid** <date dd/mm/yyyy\> (Kicks all members that joined on that date without role)
- **!say** <message\> (Talks as the bot)
- **!profile** <steamid\> (Sends a link to the steam profile)
  - !profile STEAM_0:0:30269268

## Env
The bot requires a .env file (root dir) with the following constants
- DISCORD_TOKEN
- PTERODACTYL_URL
- PTERODACTYL_TOKEN

## Jail
For jail to work, the discord guild needs the following:
- Channels:
  - general (Released from prison message)
  - jail (Channel for the jailed members)

- Jailed role

## Raid purge
Although extremely useful (especially with the increase in discord raid bots) it can have false positives. This works best on servers that require users to pick a role in order to gain access or more privileges.

## Invite Logger
When a new member joins the bot will log what invite link they used from what user.

For the invite logger to work, the discord guild needs the following:
- Channels:  
  - invite-logs (Channel for the invite logs)

The bot also offers an API POST call to retreive a custom one-time 5 minute use invite and logs the details of that invite to the logging channel so that everyone can be tracked.

For the invite creation API you need:
- POST:
  - name ( invite requestee name )
  - steamID ( invite requestee steam id )
  - guildID ( the id of your guild )
  - channelID ( the invite channel )