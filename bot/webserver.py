"""
Keep the bot alive on repl
Ref: https://www.youtube.com/watch?v=SPTfmiYiuok&feature=emb_title
"""

import os
import inviting
from flask import Flask, request
from threading import Thread

os.system('pip install flask[async]')
app = Flask('')

@app.route('/')
def home():
  return "Hello. I am alive!"

@app.route('/invite/create', methods = ['POST'])
async def create_invite():
  data = request.form
  invite_code = await inviting.create_invite(data['name'], data['steamID'], data['guildID'], data['channelID'])
  return invite_code

def run():
  app.run(host='0.0.0.0',port=8080)

def keep_alive():
  t = Thread(target=run)
  t.start()