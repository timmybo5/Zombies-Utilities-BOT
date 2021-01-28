"""
Pterodactyl module helper class
Ref: https://github.com/iamkubi/pydactyl
"""

import datetime
import os
from pydactyl import PterodactylClient

restart_delay = 60
next_can_restart = 0
allowed_servers = {
  "sandbox": "Sandbox Vanilla"
}

pterodactylAPI = PterodactylClient(os.getenv("PTERODACTYL_URL"),os.getenv("PTERODACTYL_TOKEN"))

def restart_server(server_name: str):

  global next_can_restart
  time_now = datetime.datetime.now()
  
  #Check can restart
  if next_can_restart > time_now.timestamp():
    seconds = round(next_can_restart-time_now.timestamp())
    seconds_str = "second"
    if seconds > 1:
      seconds_str+="s"
    return False, "restart timeout, try again in {0} {1}!".format(seconds, seconds_str)

  #Check valid server name
  server_name_full = ""

  if server_name in allowed_servers:
    server_name_full = allowed_servers[server_name]
  else:
    return False, "server not found!"

  server_id = get_server_id(server_name_full)
  pterodactylAPI.client.send_power_action(server_id, "kill")
  pterodactylAPI.client.send_power_action(server_id, "start")

  #Prevent server restarting for the next minute
  time_next_restart = time_now + datetime.timedelta(seconds = restart_delay)
  next_can_restart = time_next_restart.timestamp()

  return True, "restarting **"+server_name_full+"**..."

def get_server_id(server_name_full: str):
  list_servers_result = pterodactylAPI.client.list_servers()

  for page in list_servers_result:
      for item in page.data:
        if item['attributes']['name'] == server_name_full:
          return item['attributes']['identifier']