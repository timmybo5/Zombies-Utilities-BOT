# Zombie's Utilities (BOT)
A python discord bot that offers useful utility commands

## Commands
- **!jail** <@player> <time [m,h,d]>
  - !jail @Zombie Extinguisher 3h
- **!unjail** <@player>
- **!restart** <server_name> (Reboots a pterodactyl hosted server)
  - !restart sandbox
  
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
