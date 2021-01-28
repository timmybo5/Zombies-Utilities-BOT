"""
Keep the bot alive on repl
Ref: https://www.youtube.com/watch?v=SPTfmiYiuok&feature=emb_title
"""

from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Hello. I am alive!"

def run():
  app.run(host='0.0.0.0',port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()